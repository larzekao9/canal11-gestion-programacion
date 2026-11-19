#!/bin/bash
# Manda un comando al buzon local (Mailpit) como un usuario del canal. Requiere ./scripts/ejecutar.sh local corriendo.
#   ./pruebas/cmd.sh ana 'lisLea["{HOY}","12:30"]'
# Usuarios: admin, ana (Prensa), jose (Prensa), pedro (Programacion), carla (Produccion) o un correo completo.
# En el comando, {HOY}, {AYER} y {MANANA} se reemplazan por la fecha (hora de La Paz).
cd "$(dirname "$0")/.." || exit 1
case "$1" in
  admin) E=larzekaobnc@gmail.com ;;
  ana)   E=ana.rojas@gmail.com ;;
  jose)  E=jose.perez@ficct.uagrm.edu.bo ;;
  pedro) E=pedro.vaca@hotmail.com ;;
  carla) E=produccion.canal11@gmail.com ;;
  *)     E="$1" ;;
esac
export TZ=America/La_Paz
HOY=$(date +%F)
AYER=$(date -v-1d +%F 2>/dev/null || date -d yesterday +%F)
MANANA=$(date -v+1d +%F 2>/dev/null || date -d tomorrow +%F)
CMD="$2"; CMD="${CMD//\{HOY\}/$HOY}"; CMD="${CMD//\{AYER\}/$AYER}"; CMD="${CMD//\{MANANA\}/$MANANA}"
echo "[$E] $CMD"
python3 scripts/enviar_local.py "$E" "$CMD"
