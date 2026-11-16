# Canal 11 — Sistema de Gestión de Programación y Contenidos

Tecnología Web (INF513) · Grupo 12 SA · Subsistema 12: Gestión de Programación y Contenidos (BMS, Tráfico).

Sistema operado por **correo electrónico**: el usuario escribe un comando en el **asunto**, el sistema lo lee por POP3,
consulta la base de datos PostgreSQL y responde por SMTP con un correo HTML (tablas).
Java puro, sin frameworks. POP3 y SMTP programados con `Socket`.

## Arquitectura (3 capas)

```
src/canal11/
  App.java          arranca el hilo de correo y procesa lo que llega: POP3 -> procesar -> SMTP
  config/           Config (lee config.properties)
  comunicacion/     HiloCorreo + OyenteCorreo (hilo que revisa el buzon), ClientePOP3, ClienteSMTP, Correo, MimeUtil   (sockets)
  presentacion/     Interprete (asunto), Despachador (catalogo y permisos), Ayuda (help), Html (plantilla)
  negocio/          N* (reglas de negocio y validaciones), Rol, Usuario
  datos/            D* (SQL con PreparedStatement), Conexion, Instalador
sql/                01_tablas.sql, 02_datos.sql   (esquema canal11)
```

## Puesta en marcha

1. Copiar `config.properties.example` como `config.properties` y completar las contraseñas.
2. `compilar.bat`
3. `ejecutar.bat --instalar` — crea el esquema `canal11` y sus tablas en `db_grupo12sa`.
4. `ejecutar.bat` — revisa `grupo12sa@tecnoweb.org.bo` cada 10 s y responde.

Herramientas de prueba:

| Comando | Para qué |
|---|---|
| `ejecutar.bat --probar "help" larzekaobnc@gmail.com` | Procesa un asunto sin correo; guarda la respuesta en `salida/respuesta.html` |
| `ejecutar.bat --lote pruebas\cu1.txt` | Ejecuta una batería de pruebas; respuestas en `salida/01.html`, `02.html`... |
| `ejecutar.bat --buzon` | Lista los correos del buzón sin borrarlos |
| `ejecutar.bat --enviar-prueba correo@destino.com` | Envía la ayuda a un correo (prueba del SMTP) |

> El servidor SMTP del curso solo reenvía a correos externos (Gmail) desde la red de la facultad.

## Uso

Formato del asunto: `comando["parametro1","parametro2",...]`

1. `help` → casos de uso disponibles para su rol.
2. `help["3"]` → comandos del CU3 con parámetros y ejemplo.
3. Copiar el ejemplo, cambiar los valores y enviarlo.

El usuario se identifica por el correo del remitente (Gmail, Outlook/Hotmail, Yahoo, UAGRM o cualquier otro);
su rol define qué comandos puede usar. Si responde o reenvía un correo, los prefijos `RE:` / `Fwd:` se ignoran.
Si escribe mal un comando, la respuesta sugiere el correcto.

## Comandos por caso de uso

**Para continuar el desarrollo, leer [docs/GUIA_DESARROLLO.md](docs/GUIA_DESARROLLO.md).**

Acciones: `lis` listar · `mos` mostrar · `ins` insertar · `mod` modificar · `eli` eliminar (baja lógica).
Sin IDs: cada registro se referencia por un dato conocido (usuario por CI o email, programa por nombre,
material por código, parrilla por fecha, bloque por fecha + hora, pauta por nombre).

| CU | Comandos |
|---|---|
| CU1 Gestión de Usuarios | `lisUsu` `mosUsu` `insUsu` `modUsu` `eliUsu` `actUsu` |
| CU2 Catálogo de Programas | `lisPro` `mosPro` `insPro` `modPro` `eliPro` |
| CU3 Confeccionar y Controlar la Parrilla | `lisPar` `mosPar` `insPar` `eliPar` `insBlo` `eliBlo` `pubPar` |
| CU4 Materiales de Video | `lisMat` `mosMat` `insMat` `modMat` `eliMat` |
| CU5 Validar Estado de Emisión | `valMat` `estPar` |
| CU6 Pauta Publicitaria e Insertar Spots | `lisPau` `mosPau` `insPau` `eliPau` `insSpo` `eliSpo` |
| CU7 Conciliar Emisión Real, Registrar Auditoría | `insEmi` `conPar` `lisAud` |
| CU8 Reportes y Estadísticas | `repPro` `repMat` `repPau` `repCum` |

## Avance

| Fase | Contenido | Estado |
|---|---|---|
| 0 | Infraestructura: sockets POP3/SMTP, hilo de verificación de correo, intérprete, plantilla HTML, `help`, catálogo de comandos, tablas | ✅ |
| 1 | CU1 Usuarios (con reactivación) + auditoría + validaciones + correos de cualquier proveedor + `RE:`/`Fwd:` + sugerencia de comando | ✅ (falta prueba en el servidor del curso) |
| 2 | CU2 Programas, CU4 Materiales | ✅ (compila; falta correr `pruebas/cu2.txt` y `cu4.txt` contra la BD) |
| 3 | CU3 Parrilla | ✅ (compila; falta correr `pruebas/cu3.txt` contra la BD) |
| 4 | CU5 Validación | ✅ (compila; falta correr `pruebas/cu5.txt` contra la BD) |
| 5 | CU6 Pauta y spots | ✅ (compila; falta correr `pruebas/cu6.txt` contra la BD) |
| 6 | CU7 Emisión y conciliación | ✅ (compila; falta correr `pruebas/cu7.txt` contra la BD) |
| 7 | CU8 Reportes | ✅ (compila; falta correr `pruebas/cu8.txt` contra la BD) |
