# Cambios para reflejar en `Canal11_Documentacion_P1.docx`

(Lista de lo que cambió en el código; el .docx no se tocó.)

## 1. Actores
- Agregar el actor **Producción** (rol `PRODUCCION`): área que arma y transmite la señal. Consulta todo y registra la emisión real.
- Mapeo de áreas a roles: Prensa → `ENCARGADO` · Programación → `PROGRAMADOR` · Producción → `PRODUCCION` · dirección/sistemas → `ADMINISTRADOR`.
- Todo lugar que diga "tres roles/actores" pasa a **cuatro**.

## 2. Tabla de permisos
- `PRODUCCION`: todos los comandos de consulta (los de permiso TODOS: `lisPro`, `mosPro`, `lisPar`, `mosPar`, `estPar`, `lisMat`, `mosMat`, `lisPau`, `mosPau`, `conPar`, `help`) **y `insEmi`**. No puede `insPar`, `insMat`, `insUsu` ni ningún otro comando de escritura.
- `insEmi` (CU7): antes ADMINISTRADOR, PROGRAMADOR → ahora **ADMINISTRADOR, PROGRAMADOR, PRODUCCION**.
- El resto de permisos no cambia (`lisAud` y CU1 siguen solo ADMINISTRADOR; `repPro`/`repPau`/`repCum` ADM+PROGRAMADOR; `repMat` ADM+ENCARGADO).
- Texto de ayuda de `insUsu`/`modUsu`: rol = ADMINISTRADOR, PROGRAMADOR, ENCARGADO o PRODUCCION.

## 3. Tabla de diseño lógico
- `usuario.rol`: CHECK ampliado a `('ADMINISTRADOR','PROGRAMADOR','ENCARGADO','PRODUCCION')` (`usuario_rol_check`). Enum `RolUsuario` con `PRODUCCION`.
- `usuario`: índice único `ux_usuario_email_lower` sobre `lower(email)`.
- `bloque`: CHECK `ck_bloque_tipo` (PROGRAMA ⇒ `id_programa` no nulo; PAUSA_COMERCIAL ⇒ `id_programa` y `id_material` nulos) y restricción de exclusión `ex_bloque_sin_solape` (EXCLUDE USING gist: misma `id_parrilla` y rango `[hora_inicio, hora_fin)` solapado; requiere la extensión `btree_gist`).
- `spot`: trigger `trg_validar_spot` / función `fn_validar_spot` (BEFORE INSERT OR UPDATE OF `id_bloque`, `id_material`, `hora`): bloque PAUSA_COMERCIAL, `hora` en `[hora_inicio, hora_fin)`, material SPOT y APROBADO.
- Índices nuevos en FK: `bloque(id_programa)`, `bloque(id_material)`, `material(id_programa)`, `material(registrado_por)`, `material(validado_por)`, `spot(id_pauta)`, `spot(id_material)`.
- Las restricciones marcadas "(propuesto)" en el diagrama UML ya **no son propuestas**: están aplicadas.
- `auditoria.id_usuario`: se mantiene la FK sin `ON DELETE SET NULL` (decisión: los usuarios solo se dan de baja lógica; SET NULL borraría quién hizo cada cambio). Se descarta la sugerencia E del documento de observaciones.
- Reemplazar el diagrama ER por `docs/Canal11_Diagrama_UML_2.5.png` (ojo: esa imagen aún muestra `RolUsuario` sin PRODUCCION y las notas "(propuesto)"; corregirlo en el diagrama fuente).

## 4. Comandos de `insEmi` (CU7)
`insEmi["fecha","hora_inicio","inicio_real","fin_real","estado"]` — sin cambio de parámetros; ahora lo puede enviar Producción además de Administrador y Programador. Quien lo envía queda en `emision.registrado_por`.

## 5. Instalación y pruebas
- Nuevo `sql/03_mejoras.sql` (repetible); `--instalar` lo ejecuta tras `01` y `02`, verifica antes los datos existentes y avisa si no puede crear `btree_gist`.
- Mensajes nuevos: "El horario se solapa con otro bloque de la parrilla." (23P01) y los mensajes del trigger de spots.
- Pruebas: `pruebas/cu1.txt` (usuario PRODUCCION y permisos), `pruebas/cu7.txt` (Producción cierra el bloque de las 13:00) y `pruebas/bd_restricciones.sql`.

## 6. Avisos automáticos, escaleta y reglas del flujo (nuevo)
- **Origen:** levantamiento, problemas 1, 3 y 5 (WhatsApp era "push"; el sistema solo contestaba). Ahora avisa por correo: parrilla publicada y cambios (a Producción y Prensa), orden del noticiero (a Producción y Programación), resultado de `valMat` (a quien registró), recordatorio y escalamiento de revisión (Prensa → administrador), material rechazado sin corregir, parrilla en riesgo y emisión sin registrar. Detalle y destinatarios en el README.
- **Comandos nuevos (5):** `camBlo` (cambia el material de un bloque aún no iniciado, incluso con la parrilla publicada), `lisLea`, `insLea`, `modLea`, `eliLea` (escaleta del noticiero: orden de las notas). Total: 44 comandos. Permisos: `camBlo` ADMINISTRADOR y PROGRAMADOR; `insLea`/`modLea`/`eliLea` ADMINISTRADOR y ENCARGADO; `lisLea` todos.
- **Tablas nuevas:** `escaleta` (`id_bloque`, `orden`, `id_material`, `registrado_por`; `UNIQUE` diferible por orden) y `aviso_enviado` (`tipo`, `clave`). **Columnas nuevas en `material`:** `pendiente_desde`, `ultimo_aviso`, `avisos`. El trigger `fn_validar_publicacion` ahora acepta un bloque PROGRAMA sin material propio si tiene escaleta con todas sus notas APROBADAS.
- **Reglas de negocio nuevas:** quien registra un material no lo valida; no se crean ni publican parrillas pasadas; `insEmi` solo registra bloques que ya empezaron; `hora_fin` acepta `24:00`; `pubPar` avisa huecos al inicio y al final del día y la cobertura (canal 24/7); la extensión de la `ruta` debe coincidir con el `formato`; aviso de posible duplicado (mismo título, tipo y duración).
- **Configuración nueva (`config.properties`):** `revision.*`, `alerta.*`, `notificaciones.activas`, `app.zona` y `app.ahora`.
- **Pruebas:** `pruebas/cu9.txt`; en `--lote` la línea `@ahora AAAA-MM-DDTHH:MM` simula el paso del tiempo (los cu1–cu8 ahora la usan para que sus fechas de 2030/2031 sean futuras).

