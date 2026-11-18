# Guía de desarrollo — Canal 11 (Programación y Contenidos)

Esta guía es para quien continúe el proyecto. Explica **qué ya está hecho**, **cómo correrlo**, **cómo funciona por dentro**, **dónde está cada cosa** y **cómo implementar cada fase que falta**, usando el CU1 (ya terminado) como modelo.

> Regla de oro: **copie el CU1**. Cada CU nuevo se hace igual: `D*` (SQL) → `N*` (reglas) → `P*` (HTML) → conectar en el `Despachador` → probar con un archivo de `pruebas/`.

---

## 1. Estado actual

| Fase | Qué incluye | Estado |
|---|---|---|
| 0 | Sockets POP3/SMTP, **hilo** de verificación de correo con oyente, intérprete del asunto, plantilla HTML, `help`, catálogo de los 39 comandos, tablas | ✅ Terminado |
| 1 | **CU1 Gestión de Usuarios** (`lisUsu`, `mosUsu`, `insUsu`, `modUsu`, `eliUsu`, `actUsu`) + **auditoría** automática + validador con todos los errores juntos + correos de cualquier proveedor + asuntos con `RE:`/`Fwd:` + sugerencia de comando parecido | ✅ Terminado y probado (BD y servidor de correo de prueba). **Pendiente:** probar en el servidor del curso desde la facultad |
| 2 | CU2 Programas + CU4 Materiales (`DPrograma/NPrograma/PPrograma`, `DMaterial/NMaterial/PMaterial`) | ✅ Compila. **Pendiente:** correr `pruebas/cu2.txt` y `pruebas/cu4.txt` contra la BD |
| 3 | CU3 Parrilla y bloques (`DParrilla/DBloque/NParrilla/PParrilla`) | ✅ Compila. **Pendiente:** correr `pruebas/cu3.txt` contra la BD |
| 4 | CU5 Validar estado de emisión (`NValidacion`, `PValidacion`; `DMaterial.validar`) | ✅ Compila. **Pendiente:** correr `pruebas/cu5.txt` contra la BD |
| 5 | CU6 Pauta y spots (`DPauta/DSpot`, `NPauta/NSpot`, `PPauta`) | ✅ Compila. **Pendiente:** correr `pruebas/cu6.txt` contra la BD |
| 6 | CU7 Emisión real, conciliación y `lisAud` (`DEmision`, `NEmision`, `PEmision`, `PAuditoria`; `DAuditoria.listar`) | ✅ Compila. **Pendiente:** correr `pruebas/cu7.txt` contra la BD |
| 7 | CU8 Reportes (`DReporte`, `NReporte`, `PReporte`) | ✅ Compila. **Pendiente:** correr `pruebas/cu8.txt` contra la BD |
| 8 | Logs `access.log` / `error.log` | ✅ |
| 9 | **Endurecer la BD** (`sql/03_mejoras.sql`: CHECK de bloque, exclusión de solapes, trigger de spots, email único sin mayúsculas, índices FK) y **rol `PRODUCCION`** | ✅ Probado en PostgreSQL 16 local: `--instalar` dos veces, lotes `cu1`–`cu8` y `pruebas/bd_restricciones.sql` |

**Los 39 comandos de los 8 casos de uso ya están implementados** (ninguno dice "en desarrollo"). Lo que falta es **probar todo contra la BD y el servidor de correo del curso**: correr, en este orden, `pruebas/cu1.txt`, `cu2`, `cu4`, `cu5`, `cu3`, `cu6`, `cu7` y `cu8`, y revisar los HTML de `salida/`.

---

## 2. Cómo correrlo

Requisitos: Java 17 o superior (`java -version`). No usa Maven ni frameworks; el driver de PostgreSQL está en `lib/`.

```bat
copy config.properties.example config.properties   (y completar las contraseñas)
compilar.bat
ejecutar.bat --instalar                             (crea el esquema canal11, tablas y mejoras; se puede repetir)
ejecutar.bat                                        (revisa el buzón cada 10 s y responde)
```

### Herramientas de prueba (no necesitan correo)

| Comando | Qué hace |
|---|---|
| `ejecutar.bat --probar "lisUsu[\"*\"]" larzekaobnc@gmail.com` | Procesa un asunto como si llegara de ese remitente. La respuesta queda en `salida\respuesta.html` (ábrala en el navegador) |
| `ejecutar.bat --lote pruebas\cu1.txt` | Ejecuta todas las líneas `remitente \| asunto` del archivo. Respuestas en `salida\01.html`, `02.html`... y un resumen OK/ERROR en consola |
| `ejecutar.bat --buzon` | Lista los correos del buzón **sin borrarlos** y dice cuáles se responderían |
| `ejecutar.bat --enviar-prueba correo@x.com` | Envía la ayuda a ese correo (prueba del SMTP) |

### Mejoras de BD y rol PRODUCCION (fase 9)
- `Instalador.leerSentencias` respeta los bloques `$$ ... $$` (funciones plpgsql y `DO`). Antes de `03_mejoras.sql` revisa los datos existentes y, si hay bloques solapados, bloques con tipo inconsistente o emails repetidos con otra capitalización, lo informa y se detiene.
- `ErrorBD` traduce `23P01` (solape), `P0001` (mensajes del trigger de spots), `ck_bloque_tipo` y el índice de email.
- Programación (`PROGRAMADOR`) además registra, modifica y da de baja sus propios materiales (`ADM_ENC_PRO`); `valMat` sigue siendo de `ENCARGADO`.
- Producción (`PRODUCCION`) recibe los comandos de consulta (`TODOS`) y además `insEmi`. Mapeo: Prensa → `ENCARGADO`, Programación → `PROGRAMADOR`, Producción → `PRODUCCION`, dirección/sistemas → `ADMINISTRADOR`.
- El trigger se dispara solo al cambiar `id_bloque`, `id_material` o `hora`: `DEmision.actualizarSpots` (`UPDATE spot SET estado`) no revalida el material.
- Probar la BD: `psql -d BASE -f pruebas/bd_restricciones.sql` (cada prueba imprime OK/FALLO y todo se deshace con ROLLBACK).

### Problemas conocidos del servidor del curso
- **El SMTP solo reenvía a Gmail desde la red de la facultad.** Desde otra red el error es `550 Relaying denied`. El sistema igual lee y procesa; solo falla la respuesta.
- A veces `tecnoweb.org.bo` no responde (ni DNS ni IP). Si `--instalar` dice `UnknownHostException`, el servidor está caído: pruebe más tarde.
- **Al arrancar, el sistema borra todos los correos del buzón** (a los que no son comandos no les responde).

### Probar sin el servidor del curso (base y correo locales)
Si tiene Docker, puede levantar un PostgreSQL y un servidor de correo de prueba (Mailpit, con POP3 y SMTP) y apuntar `config.properties` a ellos. Use una carpeta aparte con su propio `config.properties` y una copia de `sql/` para no tocar la configuración real.

```bat
docker run -d --name canal11-pg -e POSTGRES_USER=grupo12sa -e POSTGRES_PASSWORD=prueba -e POSTGRES_DB=db_grupo12sa -p 55499:5432 postgres:16-alpine

rem archivo pop3auth con una linea:  grupo12sa:prueba
docker run -d --name canal11-mail -v "%CD%:/cfg" -e MP_POP3_AUTH_FILE=/cfg/pop3auth -e MP_SMTP_AUTH_ACCEPT_ANY=1 -e MP_SMTP_AUTH_ALLOW_INSECURE=1 -p 55025:1025 -p 55110:1110 -p 58025:8025 axllent/mailpit:v1.33.1
```

`config.properties` de prueba:
```properties
mail.usuario=grupo12sa
mail.password=prueba
pop3.host=localhost
pop3.puerto=55110
smtp.host=localhost
smtp.puerto=55025
db.host=localhost
db.puerto=55499
db.password=prueba
app.intervalo=3
```
Luego `--instalar`, `--lote`, o `ejecutar.bat` para probar el hilo completo. Para "recibir" correos, envíelos por SMTP a `localhost:55025` (con un `From:` registrado y el comando en el `Subject:`). Las respuestas se ven en http://localhost:58025 (hasta que el hilo las borre en la vuelta siguiente; en consola aparecen como *Ignorado ... Canal 11 | ...*). Al terminar: `docker rm -f canal11-pg canal11-mail`.

> Mailpit numera los correos del más nuevo al más viejo; el servidor del curso (Dovecot) del más viejo al más nuevo. Por eso, en la prueba local, varios comandos enviados juntos se procesan en orden inverso.

---

## 3. Cómo funciona (recorrido de un correo)

```
Gmail / Outlook / UAGRM...                          Servidor del curso (mail.tecnoweb.org.bo)
   │  Asunto: mosUsu["7654321"]                              │
   └──────────── SMTP ──────────────► buzón grupo12sa ◄──────┘
                                           │
HiloCorreo (Thread, cada N segundos)  ── POP3 (ClientePOP3: USER, PASS, STAT, TOP, DELE, QUIT)
   │  remitente = primera cabecera válida: From → Reply-To → Return-Path → Sender
   │  avisa al oyente:  OyenteCorreo.alRecibirCorreos(lista)
   ▼
App.alRecibirCorreos(...)
   │  ¿es comando y no es spam/rebote/respuesta propia?  (App.debeResponderse)
   ▼
Despachador.procesar(asunto, remitente)               ← capa de PRESENTACIÓN
   1. Interprete.leer(asunto)        → quita "RE:", "Fwd:", "RV:"... → nombre "mosUsu" + parámetros ["7654321"]
   2. NUsuario.identificar(remitente) → quién es y su rol (si no está registrado: error)
   3. ¿existe el comando? (si no, sugiere el más parecido: lisUsr → lisUsu)
      ¿su rol lo permite? ¿cantidad de parámetros correcta?
   4. ejecuta la Accion registrada  → PUsuario.mostrar(...)
          │
          ▼
      NUsuario.mostrar("7654321")                     ← capa de NEGOCIO (validaciones y reglas)
          │
          ▼
      DUsuario.obtener(id)                            ← capa de DATOS (SQL con PreparedStatement)
   5. PUsuario arma el HTML (Html.ficha + comandos sugeridos)
   6. Despachador lo envuelve en la plantilla (Html.pagina)
   ▼
App → ClienteSMTP.enviar(remitente, "Canal 11 | Usuario ...", html)  ── SMTP (HELO, MAIL FROM, RCPT TO, DATA, QUIT)
```

Si algo falla en cualquier punto, el `Despachador` atrapa la excepción y responde un correo de **Error** con el detalle. El programa nunca se cae por un correo malo.

---

## 4. Dónde está cada cosa

```
canal11-programacion/
├── src/canal11/
│   ├── App.java                  main: arranca el hilo y es su oyente (procesa y responde); opciones --instalar, --probar, --lote, --buzon, --enviar-prueba
│   ├── config/Config.java        lee config.properties
│   ├── comunicacion/             protocolos de correo con Socket
│   │   ├── HiloCorreo.java       Runnable: revisa el buzón cada N segundos y avisa al oyente (nunca se detiene por un error)
│   │   ├── OyenteCorreo.java     interfaz: alRecibirCorreos(List<Correo>)
│   │   ├── ClientePOP3.java      leer y borrar correos (puerto 110); remitente From → Reply-To → Return-Path → Sender
│   │   ├── ClienteSMTP.java      enviar la respuesta HTML (puerto 25)
│   │   ├── Correo.java           remitente + asunto
│   │   └── MimeUtil.java         tildes en asuntos (RFC 2047) y extraer el email del "From"
│   ├── presentacion/             CAPA DE PRESENTACIÓN
│   │   ├── Despachador.java      ★ catálogo de comandos (por CU) + permisos + manejo de errores
│   │   ├── Interprete.java       separa el asunto en comando y parámetros
│   │   ├── Ayuda.java            help y help["N"]
│   │   ├── Html.java             plantilla y componentes: pagina, tabla, ficha, codigo, exito, error, info, lista
│   │   ├── PUsuario.java         ★ CU1: arma las respuestas HTML de usuarios
│   │   ├── Comando, CasoUso, Accion, Respuesta, ComandoException
│   ├── negocio/                  CAPA DE NEGOCIO
│   │   ├── NUsuario.java         ★ CU1: reglas de usuarios
│   │   ├── NAuditoria.java       registrar(...) — llamar en cada alta/modificación/baja
│   │   ├── Validador.java        ★ validaciones (junta todos los errores)
│   │   ├── NegocioException, Rol, Usuario
│   └── datos/                    CAPA DE DATOS
│       ├── DUsuario.java         ★ CU1: SQL de usuarios
│       ├── DAuditoria.java       INSERT en auditoria
│       ├── Conexion.java         abre la conexión (esquema canal11) y leerFilas()
│       ├── ErrorBD.java          traduce errores de PostgreSQL a español
│       └── Instalador.java       ejecuta los .sql
├── sql/01_tablas.sql             las 9 tablas (ya están todas, no hace falta crear más)
├── sql/02_datos.sql              datos iniciales (admin)
├── sql/03_mejoras.sql            restricciones, trigger fn_validar_spot, índices y rol PRODUCCION (repetible)
├── pruebas/cu1.txt               batería de pruebas del CU1 (modelo para las demás)
├── pruebas/bd_restricciones.sql  demuestra que la BD rechaza datos inválidos (psql -f; no deja datos)
├── docs/GUIA_DESARROLLO.md       esta guía
├── compilar.bat / ejecutar.bat
└── config.properties(.example)
```

★ = archivos que conviene leer primero.

---

## 5. Convenciones (respetarlas en todos los CU)

### 5.1 Nombres de comandos
3 letras de la acción + 3 de la entidad: `lis` listar · `mos` mostrar · `ins` insertar · `mod` modificar · `eli` eliminar (baja lógica). Acciones propias del CU: `pub` publicar, `val` validar, `est` estado, `con` conciliar, `rep` reporte.

### 5.2 Sin IDs: claves naturales
El usuario **nunca** tiene que adivinar un ID. Cada entidad se referencia por un dato que conoce:

| Entidad | Se referencia por | Ejemplo |
|---|---|---|
| usuario | CI o email | `mosUsu["7654321"]` |
| programa | nombre | `mosPro["Noticiero Central"]` |
| material | código (lo inventa quien lo registra) | `mosMat["NOT-2011"]` |
| parrilla | fecha | `mosPar["2026-11-20"]` |
| bloque | fecha + hora de inicio | `eliBlo["2026-11-20","20:00"]` |
| pauta | nombre | `mosPau["Navidad Banco Sol"]` |
| spot | fecha + hora del spot | `eliSpo["2026-12-05","20:30:00"]` |

Las tablas ya tienen esas columnas como `UNIQUE`. En la capa de datos, cree un método `buscarId(referencia)` que busque por la clave natural y, si es un número, también por ID (ver `DUsuario.buscarId`).

### 5.3 Respuestas que guían
- Listados: agregar una columna con el comando `mos...` ya rellenado (ver `PUsuario.listar`).
- Detalle (`mos`) e inserción (`ins`): mostrar `Html.ficha(...)` y una sección **Acciones** con los comandos `mod`/`eli` ya rellenados con los datos reales (ver `PUsuario.acciones`). Así el usuario copia, cambia un valor y envía.

### 5.4 Validaciones (como las revisa el ingeniero)
Siempre con `Validador`, **antes** de tocar la base, y juntando todos los errores:

```java
Validador v = new Validador();
String nombre = v.texto(p.get(0), "nombre", 120);       // obligatorio, sin espacios de más
String tipo   = v.opcion(p.get(2), "tipo", TIPOS);      // una de las opciones
Integer dur   = v.entero(p.get(3), "duracion_min", 1, 600);
LocalDate f   = v.fecha(p.get(4), "fecha");
v.verificar();          // si hubo errores: responde TODOS juntos y no sigue
// ... reglas de negocio (repetidos, estados) → v.error("...") y otra vez v.verificar()
```

Métodos disponibles: `texto`, `textoOpcional`, `nombre` (solo letras), `codigo`, `ci`, `email`, `telefono`, `entero(min,max)`, `opcion`, `fecha`, `hora`, `error`, `verificar`. Todos limpian espacios (`"  Ana   Maria "` → `"Ana Maria"`) y tratan `""` o `"   "` como vacío.

**Correos de cualquier proveedor.** El remitente se identifica por su email, así que debe funcionar con Gmail, Outlook/Hotmail, Yahoo, UAGRM (`@ficct.uagrm.edu.bo`, `@est.uagrm.edu.bo`) o dominios propios:
- `ClientePOP3.obtener` toma el remitente de la primera cabecera con un email válido: `From` → `Reply-To` → `Return-Path` → `Sender`.
- `MimeUtil.extraerEmail` usa la dirección entre `< >` (aunque el nombre visible traiga comas, tildes u otro email) y la pasa a minúsculas.
- La búsqueda del usuario no distingue mayúsculas (`lower(email)`).
- El mismo patrón de email está en `MimeUtil.EMAIL` y `Validador.EMAIL`: si cambia uno, cambie el otro. Acepta `+etiqueta`, `_`, `-`, `'` y subdominios; rechaza `ana@gmail`, `ana..rojas@`, `.ana@`, espacios, `@@`.

Lo que ya hace el sistema por usted (no repetirlo): prefijos `RE:`/`Fwd:`/`RV:`/`FW:` en el asunto, comando inexistente (con sugerencia del más parecido, ya armado con los mismos parámetros), rol sin permiso, cantidad de parámetros incorrecta (muestra una tabla esperado vs. recibido), remitente no registrado o dado de baja, comillas sin cerrar, errores de la base traducidos (`ErrorBD`).

### 5.5 Bajas y reactivación
Las bajas son lógicas (`activo = false`). Cada entidad con `eli...` debe poder recuperarse: en el CU1 existe `actUsu`. En las respuestas de `mos...`, la sección Acciones muestra "Dar de baja" si el registro está activo y "Reactivar" si no (ver `PUsuario.acciones`). En los demás CU, si el ingeniero lo pide, agregar `act...` igual que `actUsu` (método `reactivar` en `D*`, `N*` y `P*`, acción `NAuditoria.REACTIVAR`).

### 5.6 Auditoría (RF-29)
En cada `ins`, `mod`, `eli` (y `pub`, `val`...) llamar, después de guardar:
```java
auditoria.registrar(quien, NAuditoria.INSERTAR, "programa", id, "Noticiero Central (NOTICIERO, 60 min)", "insPro");
```

### 5.7 Capas: qué va en cada una
| Capa | Puede | No puede |
|---|---|---|
| `D*` datos | SQL con `PreparedStatement`, devolver `String[]` / `List<String[]>` / ids | validar, armar HTML |
| `N*` negocio | validar, reglas, llamar a `D*`, auditar, lanzar `NegocioException` | SQL, HTML |
| `P*` presentación | leer `p.get(i)`, llamar a `N*`, armar HTML con `Html.*` | SQL, reglas |

---

## 6. Receta: implementar un CU (ejemplo CU2 Programas)

**Paso 1 — Datos: `datos/DPrograma.java`** (copiar `DUsuario`)
```java
private static final String SELECT = "SELECT id_programa, nombre, coalesce(descripcion,''), tipo, duracion_min,"
        + " coalesce(genero,''), coalesce(clasificacion,''), CASE WHEN activo THEN 'Sí' ELSE 'No' END FROM programa";
public List<String[]> listar(String tipo) ...           // tipo null = todos
public String[] obtener(int id) ...
public Integer buscarId(String referencia) ...         // por nombre (lower) o por ID
public boolean existeNombre(String nombre, int excluirId) ...
public int insertar(...) ... / public int modificar(int id, ...) ... / public int darDeBaja(int id) ...
```

**Paso 2 — Negocio: `negocio/NPrograma.java`** (copiar `NUsuario`)
- `insertar(Usuario quien, List<String> p)`: validar con `Validador`, verificar nombre único, insertar, auditar, devolver id.
- `modificar`, `eliminar` con `resolver(referencia)` que usa `buscarId`.
- Reglas propias en la sección 7.

**Paso 3 — Presentación: `presentacion/PPrograma.java`** (copiar `PUsuario`)
- `listar`, `mostrar`, `insertar`, `modificar`, `eliminar` → cada uno devuelve `new Respuesta(titulo, html)`.

**Paso 4 — Conectar en `Despachador.registrarCasosDeUso()`**
```java
PPrograma programa = new PPrograma();
cmd(2, "lisPro", "...", p("filtro"), "lisPro[\"*\"]", TODOS, programa::listar);   // antes decía null
```
El `help` se actualiza solo (desaparece "en desarrollo").

**Paso 5 — Probar: `pruebas/cu2.txt`** (copiar `cu1.txt`) con casos correctos, errores de validación, repetidos y permisos. Correr `ejecutar.bat --lote pruebas\cu2.txt` y revisar los `.html`.

**Paso 6 — Documento:** para el CU, en el informe: comandos, flujo principal, flujos alternativos (cada error de la prueba es uno) y diagramas.

---

## 7. Especificación de las fases que faltan

Las tablas ya existen en `sql/01_tablas.sql`. Los comandos, parámetros, ejemplos y roles ya están en el `Despachador` (léalos con `help["N"]`). Aquí van las **reglas de negocio** que debe programar cada `N*`.

### Fase 2 — CU2 Programas (`programa`)
- `nombre` único (no distingue mayúsculas). `tipo` ∈ NOTICIERO, REVISTA, PELICULA, DOCUMENTAL, SERIE, OTRO.
- `duracion_min` entero 1–600. `descripcion`, `genero`, `clasificacion` opcionales.
- `lisPro["*"]` todos; `lisPro["PELICULA"]` por tipo.
- `eliPro`: baja lógica. **No** permitir si el programa tiene bloques en parrillas de hoy en adelante.

### Fase 2 — CU4 Materiales (`material`)
- `codigo` único, con `Validador.codigo` (letras, números, guion). Se guarda en mayúsculas.
- `tipo` ∈ PROGRAMA, SPOT, PROMO. Si tipo = PROGRAMA, el programa (por nombre) es obligatorio; si es SPOT/PROMO puede ir `""`.
- `ruta` única → **resuelve los archivos duplicados del levantamiento**: si la ruta ya existe, responder con el código del material existente.
- `formato` ∈ MP4, MOV, MXF. `duracion_seg` 1–86400.
- Estado inicial PENDIENTE; `registrado_por` = quien envía.
- `modMat`: si cambia ruta o duración de un material APROBADO, vuelve a PENDIENTE.
- `eliMat`: no permitir si está en una parrilla PUBLICADA o en un spot programado.

### Fase 3 — CU3 Parrilla (`parrilla`, `bloque`)
- `insPar`: una parrilla por fecha; estado BORRADOR; `creado_por` = quien envía.
- `insBlo`: la parrilla debe estar en BORRADOR; `hora_fin > hora_inicio`; **no solapar** con otros bloques del mismo día; programa activo; si tipo = PROGRAMA, el programa es obligatorio; el material (si se da) debe existir.
- `mosPar`: tabla de bloques ordenada por hora (hora inicio–fin, tipo, programa, material, estado del material).
- `eliBlo` / `eliPar`: solo en BORRADOR.
- `pubPar`: revisar y publicar. Errores que **impiden** publicar: parrilla sin bloques, bloques PROGRAMA sin material o con material no APROBADO. **Avisos** (no impiden): huecos entre bloques. Al publicar: estado PUBLICADA y `fecha_publicacion = now()`. Esto **reemplaza el envío del orden por WhatsApp** del levantamiento: la parrilla publicada es la única fuente del orden de transmisión.

### Fase 4 — CU5 Validar estado de emisión
- `valMat`: estado ∈ APROBADO, RECHAZADO. Si RECHAZADO, la observación es obligatoria. Guarda `validado_por` y `fecha_validacion`. Solo desde PENDIENTE (o RECHAZADO → APROBADO tras corregir).
- `estPar`: por cada bloque del día: LISTO (material aprobado), PENDIENTE, RECHAZADO, SIN MATERIAL; y un resumen "N de M bloques listos".

### Fase 5 — CU6 Pauta y spots (`pauta`, `spot`)
- Alcance: solo **tráfico** (ubicar spots). Clientes, contratos y facturación son del subsistema 13 (Comercial), por eso el anunciante es solo un texto.
- `insPau`: nombre único; `fecha_fin >= fecha_inicio`; `max_pases` 1–10000.
- `insSpo`: el material debe ser tipo SPOT y APROBADO; la fecha dentro de la vigencia de la pauta; el bloque (fecha + hora_pausa) debe ser PAUSA_COMERCIAL; `hora_spot` dentro de ese bloque; no superar `max_pases`; no repetir hora en el mismo bloque; la suma de duraciones no puede exceder la pausa.
- `mosPau`: datos de la pauta + tabla de spots + pases usados / disponibles.

### Fase 6 — CU7 Emisión, conciliación y auditoría
- `insEmi`: un registro por bloque (fecha + hora_inicio). Horas reales HH:MM:SS del mismo día. `registrado_por` = quien envía.
- `conPar`: por bloque: hora programada, hora real, desviación en segundos, estado (EMITIDO / PARCIAL / NO_EMITIDO / SIN REGISTRO) y % de cumplimiento del día.
- `lisAud`: leer `auditoria` (más recientes primero, máximo 100). Filtro `*`, nombre de entidad o fecha AAAA-MM-DD. Mostrar usuario, acción, entidad, detalle, comando y fecha. La tabla ya se llena desde el CU1.

### Fase 7 — CU8 Reportes
Todos reciben `desde`, `hasta` (AAAA-MM-DD, `desde <= hasta`, máximo 366 días) y usan `GROUP BY` en SQL:
- `repPro`: horas programadas por tipo de programa (suma de `hora_fin - hora_inicio` de bloques PROGRAMA).
- `repMat`: cantidad de materiales por estado y tipo registrados en el rango.
- `repPau`: por anunciante: spots programados, emitidos, no emitidos.
- `repCum`: por día: bloques programados, emitidos, % de cumplimiento.
Mostrar una tabla con totales al final.

---

## 8. Checklist antes de dar una fase por terminada
- [ ] Compila (`compilar.bat`) sin errores.
- [ ] Los comandos del CU ya no dicen "en desarrollo" en `help["N"]`.
- [ ] `pruebas/cuN.txt` con casos correctos, de validación, repetidos y de permisos; todos dan el resultado esperado.
- [ ] Cada alta/modificación/baja aparece en `auditoria`.
- [ ] Las respuestas traen los comandos siguientes ya rellenados.
- [ ] Probado con correo real desde la red de la facultad.
- [ ] Actualizada la tabla de la sección 1 de esta guía y el README.
