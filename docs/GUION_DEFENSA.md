# Guion de la demostración (defensa)

Datos basados en la **grilla real del viernes 20-11-2026** de Canal 11 TVU (programas, horarios y duraciones reales: Informe Once,
Buenos Días Santa Cruz, Butaca Once, Deportivo 11, tandas LUNA, etc.). Los días anteriores repiten esa estructura con otros contenidos
y los contenidos de las notas de noticias son representativos (el canal no publica su parrilla).

## Preparación (la mañana de la defensa)

```bash
./scripts/compilar.sh
./scripts/ejecutar.sh local --poblar     # BORRA la base local y la recarga: "hoy" pasa a ser el día de la defensa
./scripts/ejecutar.sh local              # deje esta terminal abierta (el sistema corriendo)
```

Abra **http://localhost:58025** (los correos: respuestas y avisos). Los comandos se mandan desde otra terminal:

```bash
./pruebas/cmd.sh <usuario> '<comando>'     # usuarios: admin, ana (Prensa), jose (Prensa), pedro (Programación), carla (Producción)
```

`{HOY}`, `{AYER}` y `{MANANA}` se reemplazan por la fecha. Al arrancar llega solo un correo **«Parrilla en riesgo»** (mañana no está lista)
y, al minuto, el **recordatorio** por los materiales pendientes: ese es el hilo de la demostración.

## 1. El problema y la parrilla real (1 min)

```bash
./pruebas/cmd.sh pedro 'mosPar["{HOY}"]'                 # la grilla del día: 42 bloques, 24 h
./pruebas/cmd.sh ana   'lisLea["{HOY}","12:30"]'         # orden de las notas de Informe Once (antes: WhatsApp) con hora de entrada
./pruebas/cmd.sh admin 'conPar["{AYER}"]'                # programado vs. emitido de ayer (97,6 %)
```

## 2. Alerta automática: la parrilla de mañana no está lista (3 min)

Llegó el correo «Parrilla en riesgo: {MANANA}». Se ve qué falta y se corrige:

```bash
./pruebas/cmd.sh pedro 'estPar["{MANANA}"]'                                   # 3 bloques por resolver
./pruebas/cmd.sh ana   'valMat["AJ-D+1","APROBADO","Revisado"]'               # Prensa aprueba lo que registró Programación
./pruebas/cmd.sh jose  'valMat["IO1-D+1-06","APROBADO","Revisada"]'
./pruebas/cmd.sh jose  'valMat["IO1-D+1-07","APROBADO","Revisada"]'
./pruebas/cmd.sh ana   'eliLea["{MANANA}","12:30","IO1-D+1-08"]'              # la nota rechazada (audio con ruido) sale de la escaleta
./pruebas/cmd.sh ana   'insLea["{MANANA}","12:30","8","NOT-LIBRE-01"]'        # y entra otra aprobada
./pruebas/cmd.sh pedro 'estPar["{MANANA}"]'                                   # todo listo
./pruebas/cmd.sh pedro 'pubPar["{MANANA}"]'                                   # publicar: llega el correo con el orden a Producción y Prensa
```

Regla a mostrar: **quien registra un material no lo valida**:

```bash
./pruebas/cmd.sh ana 'valMat["PEND-NOT-01","APROBADO","Me lo apruebo"]'       # error: lo registró ella misma
```

## 3. Plazo de revisión: recordatorio y escalamiento (2 min, sin hacer nada)

`PEND-DOC-01` y `PEND-NOT-01` están pendientes. Al minuto llega el **recordatorio** a Prensa; a los 2 minutos, el **escalamiento** al administrador
(plazos cortos solo en el perfil local). El sistema nunca aprueba por tiempo.

```bash
./pruebas/cmd.sh admin 'lisMat["VENCIDO"]'                                    # los que ya recibieron aviso
./pruebas/cmd.sh jose  'valMat["PEND-NOT-01","APROBADO","Revisada"]'          # Prensa responde y el aviso deja de repetirse
```

## 4. Cambios de último momento (sin WhatsApp) (2 min)

Con la parrilla de mañana ya publicada:

```bash
./pruebas/cmd.sh pedro 'camBlo["{MANANA}","13:55","SER-LIBRE-01"]'            # cambia la serie de la tarde: aviso a Producción y Prensa
./pruebas/cmd.sh ana   'modLea["{MANANA}","12:30","NOT-LIBRE-01","1"]'        # una nota pasa a abrir el noticiero: aviso a Producción y Programación
```

## 5. Emisión y trazabilidad (2 min)

```bash
./pruebas/cmd.sh carla 'insEmi["{HOY}","HH:MM","HH:MM:SS","HH:MM:SS","EMITIDO"]'   # un bloque de hoy que ya empezó
./pruebas/cmd.sh carla 'insEmi["{MANANA}","20:00","20:00:00","21:00:00","EMITIDO"]' # error: ese bloque todavía no empieza
./pruebas/cmd.sh admin 'lisAud["escaleta"]'                                   # quién cambió qué (los avisos del sistema salen como «(sistema)»)
./pruebas/cmd.sh admin 'repCum["{AYER}","{HOY}"]'                             # cumplimiento diario
./pruebas/cmd.sh admin 'repPau["{AYER}","{HOY}"]'                             # spots por anunciante
```

Si un bloque de hoy termina sin registrarse, 30 minutos después llega la alerta «Emisión sin registrar» a Producción.

## 6. Validaciones de materiales (1 min)

```bash
./pruebas/cmd.sh ana   'insMat["DEMO-EXT","Prueba","PROMO","","30","MP4","/promos/demo.mov"]'                  # error: la extensión no coincide con el formato
./pruebas/cmd.sh pedro 'insMat["DEMO-DUP","Promo Canal 11: 53 años contigo","PROMO","","25","MP4","/promos/otra.mp4"]'  # se registra, pero avisa «posible duplicado»
```

## Si algo falla

- **Correos que no aparecen:** recuerde que el sistema los lee cada 3 s; mire http://localhost:58025 y refresque.
- **Empezar de cero:** `./scripts/ejecutar.sh local --poblar` (con el sistema detenido).
- **Mailpit/Docker caído:** `./scripts/ejecutar.sh local` lo vuelve a levantar solo.
