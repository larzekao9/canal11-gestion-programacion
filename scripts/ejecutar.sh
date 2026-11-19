#!/bin/bash
# Ejecuta el sistema con un PERFIL de configuracion. El perfil es obligatorio para no tocar lo real por error.
#
#   ./scripts/ejecutar.sh local                      todo local: base PostgreSQL local + Mailpit (correo de prueba). Lo prepara solo.
#   ./scripts/ejecutar.sh real                       base y correo del curso (usa config.properties)
#   ./scripts/ejecutar.sh local --instalar           crea las tablas en la base local     (igual con real)
#   ./scripts/ejecutar.sh local --lote pruebas/cu9.txt
#   ./scripts/ejecutar.sh real  --probar "help" correo@remitente.com
#
# Compilar es igual para los dos: ./scripts/compilar.sh (el codigo es el mismo, solo cambia la configuracion).
cd "$(dirname "$0")/.." || exit 1

PERFIL="$1"
case "$PERFIL" in
  local) CONFIG="config.local.properties" ;;
  real)  CONFIG="config.properties" ;;
  *) sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;;
esac
shift

preparar_local() {
  # 1) archivo de configuracion local (se crea una sola vez desde el ejemplo)
  if [ ! -f "$CONFIG" ]; then
    sed "s/USUARIO/$(whoami)/" config.local.properties.example > "$CONFIG"
    echo "[local] Creado $CONFIG"
  fi
  # 2) PostgreSQL local
  if ! pg_isready -q -h localhost 2>/dev/null; then
    echo "[local] No hay un PostgreSQL corriendo en localhost:5432. Inicielo (ej. brew services start postgresql@16) y repita."
    exit 1
  fi
  if ! psql -h localhost -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='canal11_local'" | grep -q 1; then
    createdb -h localhost canal11_local && psql -h localhost -d canal11_local -qc "CREATE EXTENSION IF NOT EXISTS btree_gist"
    echo "[local] Creada la base canal11_local"
  fi
  # 3) Mailpit (correo de prueba) en Docker
  if ! docker info >/dev/null 2>&1; then
    echo "[local] Docker apagado: abriendolo..."
    open -a Docker 2>/dev/null
    for i in $(seq 1 30); do docker info >/dev/null 2>&1 && break; sleep 3; done
  fi
  if ! docker info >/dev/null 2>&1; then
    echo "[local] No se pudo usar Docker. Inicielo y repita."
    exit 1
  fi
  if [ "$(docker ps -q -f name=^canal11-mail$)" = "" ]; then
    if [ "$(docker ps -aq -f name=^canal11-mail$)" != "" ]; then
      docker start canal11-mail >/dev/null
    else
      mkdir -p .local && echo 'grupo12sa:clave' > .local/pop3auth
      docker run -d --name canal11-mail -v "$PWD/.local:/cfg" -e MP_POP3_AUTH_FILE=/cfg/pop3auth \
        -e MP_SMTP_AUTH_ACCEPT_ANY=1 -e MP_SMTP_AUTH_ALLOW_INSECURE=1 \
        -p 55025:1025 -p 55110:1110 -p 58025:8025 axllent/mailpit:v1.33.1 >/dev/null
    fi
    sleep 2
    echo "[local] Mailpit listo: ver correos en http://localhost:58025"
  fi
  # 4) tablas (solo la primera vez)
  if ! psql -h localhost -d canal11_local -tAc "SELECT to_regclass('canal11.usuario')" | grep -q usuario; then
    echo "[local] Instalando las tablas..."
    java -Dcanal11.config="$CONFIG" -cp "out:lib/postgresql-42.7.4.jar" canal11.App --instalar || exit 1
  fi
}

if [ "$PERFIL" = "local" ]; then
  preparar_local
elif [ ! -f "$CONFIG" ]; then
  echo "Falta $CONFIG: copie config.properties.example como config.properties y complete las contrasenas."
  exit 1
fi

echo "[$PERFIL] configuracion: $CONFIG"
java -Dcanal11.config="$CONFIG" -cp "out:lib/postgresql-42.7.4.jar" canal11.App "$@"
