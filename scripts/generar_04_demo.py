#!/usr/bin/env python3
# Regenera sql/04_demo.sql (datos de demostracion). Uso: python3 scripts/generar_04_demo.py sql/04_demo.sql
# Base: la grilla real del viernes 20-11-2026 de Canal 11 TVU. Para cambiar los datos, edite este archivo y regenere.
# Genera sql/04_demo.sql a partir de la grilla real del viernes 20-11-2026 (Canal 11 TVU).
import sys
OUT = sys.argv[1]
S = []   # sentencias
def add(s): S.append(s.strip().rstrip(';') + ';')
def q(s): return "'" + str(s).replace("'", "''") + "'"
HOY = "((now() AT TIME ZONE 'America/La_Paz')::date)"
def D(off): return f"({HOY} + ({off}))"
def TS(off, t, extra=""): return f"(({D(off)} + TIME '{t}'){extra})"
def U(email): return f"(SELECT id_usuario FROM usuario WHERE email = {q(email)})"
def PG(n): return f"(SELECT id_programa FROM programa WHERE nombre = {q(n)})"

ADM = 'larzekaobnc@gmail.com'; ANA = 'ana.rojas@gmail.com'; JOSE = 'jose.perez@ficct.uagrm.edu.bo'
PEDRO = 'pedro.vaca@hotmail.com'; CARLA = 'produccion.canal11@gmail.com'

add("-- DATOS DE DEMOSTRACION (se cargan con ./scripts/ejecutar.sh local --poblar, que BORRA la base local y la vuelve a crear).")
# ---------------------------------------------------------------- usuarios
for ci, nom, ape, mail, tel, rol in [
    ('5812345', 'Ana María', 'Rojas Paz', ANA, '70012345', 'ENCARGADO'),
    ('6123456', 'José Luis', 'Pérez Mamani', JOSE, '70123456', 'ENCARGADO'),
    ('7234567', 'Pedro', 'Vaca Suárez', PEDRO, '70234567', 'PROGRAMADOR'),
    ('5555555', 'Carla', 'Méndez Rivero', CARLA, '70345678', 'PRODUCCION')]:
    add(f"INSERT INTO usuario (ci, nombre, apellido, email, telefono, rol, fecha_registro) VALUES ({q(ci)}, {q(nom)}, {q(ape)}, {q(mail)}, {q(tel)}, {q(rol)}, now() - interval '30 days') ON CONFLICT (email) DO NOTHING")

# ---------------------------------------------------------------- programas (los de la grilla real)
PROGRAMAS = [
 ('Butaca Once', 'Ciclo de cine del canal', 'PELICULA', 100, 'Séptimo arte'),
 ('Serie', 'Series de cine y televisión', 'SERIE', 180, 'Séptimo arte'),
 ('Noticias Internacionales', 'Resumen de noticias del mundo', 'NOTICIERO', 27, 'Noticias'),
 ('Buenos Días Santa Cruz', 'Programa matutino en vivo', 'REVISTA', 105, 'Informa, variedad'),
 ('Buenas Noches Santa Cruz', 'Programa nocturno en vivo', 'REVISTA', 60, 'Informa, variedad'),
 ('Cocina - Desayunos', 'Recetas de desayuno', 'OTRO', 25, 'Cocina'),
 ('Cocina - Almuerzos', 'Recetas de almuerzo', 'OTRO', 15, 'Culinario'),
 ('Jardinería', 'Cuidado de plantas y jardines', 'OTRO', 12, 'Jardinería'),
 ('Aprendemos Juntos', 'Programa de superación personal', 'OTRO', 44, 'Superación'),
 ('Economía al Día', 'Resumen económico', 'NOTICIERO', 12, 'Noticias'),
 ('Deportivo 11', 'Programa deportivo', 'REVISTA', 25, 'Deportivo'),
 ('Un mensaje a la conciencia', 'Espacio de reflexión', 'OTRO', 5, 'Reflexión'),
 ('Informe Once', 'Noticiero del canal (ediciones de mediodía y de la tarde)', 'NOTICIERO', 85, 'Noticias'),
 ('Avances de la Hora', 'Titulares en vivo', 'NOTICIERO', 3, 'Noticias'),
 ('Noticias UAGRM', 'Noticias de la universidad', 'NOTICIERO', 3, 'Institucional'),
 ('Facultades por dentro', 'Espacio institucional sobre las facultades', 'OTRO', 4, 'Institucional'),
 ('Sostenimiento General', 'Espacio de concientización', 'OTRO', 5, 'Sostenimiento'),
 ('Dibujos Animados', 'Programación infantil', 'OTRO', 26, 'Infantil'),
 ('Documentales del Once', 'Documentales culturales', 'DOCUMENTAL', 25, 'Cultural'),
 ('Alenbo', 'Espacio institucional', 'OTRO', 5, 'Institucional'),
]
for n, d, t, m, g in PROGRAMAS:
    add(f"INSERT INTO programa (nombre, descripcion, tipo, duracion_min, genero, clasificacion) VALUES ({q(n)}, {q(d)}, {q(t)}, {m}, {q(g)}, 'ATP')")

# ---------------------------------------------------------------- materiales
MATS = {}   # codigo -> dict
def mat(cod, titulo, prog, dur, tipo='PROGRAMA', reg=PEDRO, val=None, reg_ts=None, val_ts=None,
        estado='APROBADO', obs=None, activo=True, fmt='MP4', ruta=None, desc=None):
    if cod in MATS: return cod
    if val is None: val = ANA if reg in (PEDRO,) else JOSE
    ruta = ruta or f"/servidor/{cod.lower()}.{fmt.lower()}"
    MATS[cod] = dict(cod=cod, titulo=titulo, prog=prog, dur=dur, tipo=tipo, reg=reg, val=val, reg_ts=reg_ts or TS(-10, '10:00'),
                     val_ts=val_ts or TS(-10, '13:00'), estado=estado, obs=obs, activo=activo, fmt=fmt, ruta=ruta, desc=desc)
    return cod

# ---- catalogos de contenido (los titulos del dia 0 son los de la grilla real)
FILMS = [("El asesino del alfabeto", 5871), ("Mi prima, el amor y yo", 5261), ("Un verano en la costa", 5400),
         ("La carta perdida", 5640), ("Corazón de barrio", 5100), ("Detrás del espejo", 5520)]
SERIES = [("Días soleados", 10724), ("El caso de la jueza Karelina", 11052), ("Amor sin fronteras", 10500), ("La herencia", 10800)]
FILM_SLOTS = {-2: (4, 2, 3, 5), -1: (5, 3, 4, 1), 0: (1, 0, 1, 0), 1: (0, 2, 5, 3)}     # f0000, f0326, f0504, f2300
SERIE_SLOTS = {-2: (2, 3), -1: (1, 2), 0: (0, 1), 1: (0, 3)}
COC_DES = {0: "Sándwich de tostadas francesas y Pan, atún y huevos", -1: "Panqueques con frutas y Huevos revueltos con champiñones",
           -2: "Avena con frutas y miel y Tostadas con palta", 1: "Omelette de verduras y Jugo de naranja natural"}
COC_ALM = {0: "Pechugas de pollo con salsa y champiñones y Estofado de ternera con patatas", -1: "Locro de gallina y Sopa de maní",
           -2: "Majadito de charque y Fideos con tuco", 1: "Pique macho y Ensalada de la casa"}
JARD = {0: "Reino monera y Renueva tu jardín en primavera", -1: "Cómo cuidar las orquídeas", -2: "Riego eficiente en verano", 1: "Plantas medicinales del hogar"}
AJ = {0: "Cuando dejamos de dormir, dejamos de vivir", -1: "El poder de los hábitos", -2: "Aprender a decir que no", 1: "Metas y disciplina"}
MENS = {0: "Para casarse hay que estar seguros", -1: "La gratitud cambia la mirada", -2: "El valor del perdón", 1: "Tiempo en familia"}
SOST = {0: "Diez acciones para cuidar el medio ambiente", -1: "Separar la basura en casa", -2: "Ahorro de agua", 1: "Reciclar en la universidad"}
DIB = {0: "Érase una vez el espacio, los saurios", -1: "Érase una vez el espacio, los planetas", -2: "Érase una vez el espacio, las estrellas", 1: "Érase una vez el espacio, la Luna"}
FAC = {0: "Ingeniería electromecánica", -1: "Ciencias de la Salud", -2: "Humanidades", 1: "Ciencias Agrícolas"}
DOC = {0: ("Viajar en tren, Francia; Saint Gervais Les Bains", 1498), -1: ("Viajar en tren, Suiza; Zermatt", 1500), -2: ("Viajar en tren, Italia; Cinque Terre", 1490), 1: ("Viajar en tren, Austria; Hallstatt", 1505)}

# notas "en vivo" de cada programa (el orden de transmision: lo que Prensa mandaba por WhatsApp)
NOTAS = {
 'IO1': ["Admisión UAGRM: calendario de inscripciones", "Avance de obras en la Ciudad Universitaria", "Transporte: rutas hacia el campus",
         "Mercados: precios del día", "Salud: campaña de vacunación en barrios", "Facultades: cierre de la gestión académica",
         "Policial: balance de la jornada", "Clima: frente frío en el oriente"],
 'IO2': ["Titulares de la tarde", "Economía: dólar y canasta familiar", "Educación: calendario de exámenes", "Cultura: agenda del fin de semana",
         "Deportes: resultados del día", "Tráfico: puntos críticos de la ciudad"],
 'BDSC': ["Bienvenida y titulares del día", "Entrevista con el invitado del día", "Pronóstico del tiempo", "Tránsito y vialidad",
          "Salud y bienestar", "Agenda cultural del fin de semana"],
 'BNSC': ["Resumen del día", "Entrevista nocturna", "Cultura y espectáculos", "Opinión: tema de la semana", "Despedida y avance de mañana"],
 'DEP': ["Resumen de la fecha del campeonato local", "Entrevista a deportista universitario", "Tabla de posiciones", "Agenda deportiva"],
}
NOTA_PROG = {'IO1': 'Informe Once', 'IO2': 'Informe Once', 'BDSC': 'Buenos Días Santa Cruz', 'BNSC': 'Buenas Noches Santa Cruz', 'DEP': 'Deportivo 11'}
NOTA_DUR = {'IO1': 540, 'IO2': 420, 'BDSC': 900, 'BNSC': 600, 'DEP': 300}

def lab(d): return f"D{d:+d}" if d else "D0"
def regts(d, hh): return TS(d - 1, hh)            # se registra el dia anterior
def valts(d, hh): return TS(d - 1, hh)

# problemas de la parrilla del dia +1 (borrador) para la demostracion de "parrilla en riesgo"
PEND = {('IO1', 6), ('IO1', 7)}; RECH = {('IO1', 8)}

def nota_codes(d, key, n_override=None):
    cods = []
    for i, t in enumerate(NOTAS[key] if n_override is None else NOTAS[key][:n_override], 1):
        c = f"{key}-{lab(d)}-{i:02d}"
        est, obs, val_by, vts = 'APROBADO', None, JOSE, valts(d, '17:00')
        if d == 1 and (key, i) in PEND: est, val_by, vts = 'PENDIENTE', None, None
        if d == 1 and (key, i) in RECH: est, obs, val_by, vts = 'RECHAZADO', 'Audio con ruido en la entrevista', JOSE, TS(0, '07:50')
        titulo = t if d == 0 else f"{t} ({lab(d)})"
        mat(c, titulo, NOTA_PROG[key], NOTA_DUR[key], reg=ANA, val=val_by, reg_ts=regts(d, '15:30') if est != 'PENDIENTE' else TS(0, '07:30'),
            val_ts=vts, estado=est, obs=obs, ruta=f"/prensa/{lab(d).lower()}/{key.lower()}_{i:02d}.mp4")
        cods.append(c)
    return cods

BLOQUES = {}   # dia -> lista de (ini, fin, tipo, programa, tipo_fuente, extra)
def grilla(d):
    f0, f1, f2, f3 = FILM_SLOTS[d]; s1, s2 = SERIE_SLOTS[d]
    L = lab(d)
    def film(i, cod_suffix): n, du = FILMS[i]; return mat(f"BUT-{i+1:02d}", n, 'Butaca Once', du, reg=PEDRO, reg_ts=TS(-20, '11:00'), val_ts=TS(-20, '15:00'), ruta=f"/servidor/cine/but_{i+1:02d}.mp4")
    def serie(i): n, du = SERIES[i]; return mat(f"SER-{i+1:02d}", n, 'Serie', du, reg=PEDRO, reg_ts=TS(-20, '11:30'), val_ts=TS(-20, '15:30'), ruta=f"/servidor/series/ser_{i+1:02d}.mp4")
    def pre(code, titulo, prog, dur, hh='16:00', reg=PEDRO):
        return mat(f"{code}-{L}", titulo, prog, dur, reg=reg, reg_ts=regts(d, hh), val_ts=valts(d, '18:00'), ruta=f"/servidor/{L.lower()}/{code.lower()}.mp4")
    b = []
    P = lambda ini, fin, prog, cod: b.append((ini, fin, 'PROGRAMA', prog, 'mat', cod))
    E = lambda ini, fin, prog, key, n=None: b.append((ini, fin, 'PROGRAMA', prog, 'esc', nota_codes(d, key, n)))
    C = lambda ini, fin: b.append((ini, fin, 'PAUSA_COMERCIAL', None, 'pausa', None))
    P('00:00:00', '00:27:00', 'Butaca Once', film(f0, 0))
    P('00:27:00', '03:26:00', 'Serie', serie(s1))
    P('03:26:00', '05:04:00', 'Butaca Once', film(f1, 0))
    P('05:04:00', '06:32:00', 'Butaca Once', film(f2, 0))
    P('06:32:00', '07:00:00', 'Noticias Internacionales', pre('NI-A', 'Noticias internacionales - edición matutina', 'Noticias Internacionales', 1620, '18:30', ANA))
    E('07:00:00', '08:45:00', 'Buenos Días Santa Cruz', 'BDSC')
    C('08:45:00', '09:00:00')
    P('09:00:00', '09:25:00', 'Cocina - Desayunos', pre('COCD', COC_DES[d], 'Cocina - Desayunos', 1500))
    P('09:25:00', '09:30:00', 'Sostenimiento General', pre('SOST', SOST[d], 'Sostenimiento General', 300))
    P('09:30:00', '09:42:00', 'Jardinería', pre('JARD', JARD[d], 'Jardinería', 720))
    b.append(('09:42:00', '09:45:00', 'PROGRAMA', 'Avances de la Hora', 'av', '0942'))
    C('09:45:00', '10:00:00')
    P('10:00:00', '10:45:00', 'Aprendemos Juntos', pre('AJ', AJ[d], 'Aprendemos Juntos', 2633))
    C('10:45:00', '11:00:00')
    P('11:00:00', '11:15:00', 'Cocina - Almuerzos', pre('COCA', COC_ALM[d], 'Cocina - Almuerzos', 900))
    C('11:15:00', '11:30:00')
    P('11:30:00', '11:42:00', 'Economía al Día', pre('ECO', f"Economía al día - edición {L}", 'Economía al Día', 720, '18:00', ANA))
    b.append(('11:42:00', '11:45:00', 'PROGRAMA', 'Avances de la Hora', 'av', '1142'))
    C('11:45:00', '12:00:00')
    E('12:00:00', '12:25:00', 'Deportivo 11', 'DEP')
    P('12:25:00', '12:30:00', 'Un mensaje a la conciencia', pre('MENS', MENS[d], 'Un mensaje a la conciencia', 300))
    E('12:30:00', '13:55:00', 'Informe Once', 'IO1')
    P('13:55:00', '17:00:00', 'Serie', serie(s2))
    C('17:00:00', '17:15:00')
    P('17:15:00', '17:42:00', 'Dibujos Animados', pre('DIB', DIB[d], 'Dibujos Animados', 1554))
    b.append(('17:42:00', '17:45:00', 'PROGRAMA', 'Avances de la Hora', 'av', '1742'))
    C('17:45:00', '18:00:00')
    P('18:00:00', '18:12:00', 'Economía al Día', f"ECO-{L}")
    P('18:12:00', '18:15:00', 'Noticias UAGRM', pre('UAGRM-A', f"Noticias UAGRM - edición de la tarde ({L})", 'Noticias UAGRM', 180, '17:30', ANA))
    C('18:15:00', '18:30:00')
    P('18:30:00', '18:55:00', 'Deportivo 11', pre('DEPR', f"Deportivo 11 (repetición) {L}", 'Deportivo 11', 1500, '13:00', ANA))
    P('18:55:00', '19:00:00', 'Un mensaje a la conciencia', f"MENS-{L}")
    E('19:00:00', '19:55:00', 'Informe Once', 'IO2')
    P('19:55:00', '20:00:00', 'Facultades por dentro', pre('FAC', FAC[d], 'Facultades por dentro', 240))
    E('20:00:00', '21:00:00', 'Buenas Noches Santa Cruz', 'BNSC')
    P('21:00:00', '21:45:00', 'Aprendemos Juntos', f"AJ-{L}")
    C('21:45:00', '22:00:00')
    n, du = DOC[d]
    P('22:00:00', '22:25:00', 'Documentales del Once', pre('DOCU', n, 'Documentales del Once', du))
    P('22:25:00', '22:30:00', 'Alenbo', pre('ALEN', 'Alenbo # 01', 'Alenbo', 300))
    P('22:30:00', '22:57:00', 'Noticias Internacionales', pre('NI-B', 'Noticias internacionales - edición nocturna', 'Noticias Internacionales', 1620, '19:00', ANA))
    P('22:57:00', '23:00:00', 'Noticias UAGRM', pre('UAGRM-B', f"Noticias UAGRM - edición de la noche ({L})", 'Noticias UAGRM', 180, '17:45', ANA))
    P('23:00:00', '23:59:59', 'Butaca Once', film(f3, 0))
    return b

# materiales de los "Avances de la hora" (3 min, en vivo) y escaletas de una nota
for d in (-2, -1, 0, 1):
    pass
DIAS = (-2, -1, 0, 1)
for d in DIAS:
    BLOQUES[d] = grilla(d)
# avances: una nota por avance
def avance_mat(d, hhmm):
    c = f"AV{hhmm}-{lab(d)}"
    mat(c, f"Titulares de las {hhmm[:2]}:{hhmm[2:]}" + ("" if d == 0 else f" ({lab(d)})"), 'Avances de la Hora', 150, reg=ANA, val=JOSE,
        reg_ts=regts(d, '16:00'), val_ts=valts(d, '17:30'), ruta=f"/prensa/{lab(d).lower()}/av{hhmm}.mp4")
    return c

# ---------------------------------------------------------------- spots y pautas
PAUTAS = [  # nombre, anunciante, desde, hasta, max
 ('Campaña Admisiones UAGRM', 'UAGRM - Admisiones', -30, 60, 900),
 ('Mensajes de interés público CRE', 'Cooperativa Rural de Electrificación (CRE)', -10, 40, 900),
 ('Posgrado UAGRM', 'UAGRM - Posgrado', -30, 60, 900),
 ('Colegio Médico - Salud', 'Colegio Médico de Santa Cruz', -15, 45, 900),
 ('LUNA - Tanda comercial', 'LUNA', -60, 90, 2500),
]
for n, a, i, f, m in PAUTAS:
    add(f"INSERT INTO pauta (anunciante, nombre, fecha_inicio, fecha_fin, max_pases) VALUES ({q(a)}, {q(n)}, {D(i)}, {D(f)}, {m})")
SPOTS = {  # codigo: (titulo, dur, pauta)
 'SPOT-LUNA-01': ('LUNA - Comercial 1', 30, 'LUNA - Tanda comercial'), 'SPOT-LUNA-02': ('LUNA - Comercial 2', 30, 'LUNA - Tanda comercial'),
 'SPOT-LUNA-03': ('LUNA - Comercial 3', 20, 'LUNA - Tanda comercial'), 'SPOT-LUNA-04': ('LUNA - Comercial 4', 30, 'LUNA - Tanda comercial'),
 'SPOT-ADM-01': ('Admisiones UAGRM 2027: inscríbete ya', 30, 'Campaña Admisiones UAGRM'), 'SPOT-ADM-02': ('Admisiones UAGRM: fechas y requisitos', 20, 'Campaña Admisiones UAGRM'),
 'SPOT-CRE-01': ('CRE: uso seguro de la electricidad', 30, 'Mensajes de interés público CRE'), 'SPOT-CRE-02': ('CRE: ahorro de energía', 20, 'Mensajes de interés público CRE'),
 'SPOT-MED-01': ('Colegio Médico: campaña de vacunación', 30, 'Colegio Médico - Salud'), 'SPOT-POS-01': ('Posgrado UAGRM: maestrías y diplomados', 30, 'Posgrado UAGRM'),
}
for c, (t, du, p) in SPOTS.items():
    mat(c, t, None, du, tipo='SPOT', reg=PEDRO, reg_ts=TS(-25, '10:00'), val_ts=TS(-25, '12:00'), ruta=f"/spots/{c.lower()}.mp4")
SPOT_ORDER = ['SPOT-LUNA-01', 'SPOT-ADM-01', 'SPOT-LUNA-02', 'SPOT-CRE-01', 'SPOT-LUNA-03', 'SPOT-MED-01', 'SPOT-POS-01', 'SPOT-LUNA-04', 'SPOT-ADM-02', 'SPOT-CRE-02']

# ---------------------------------------------------------------- materiales sueltos para la demostracion
mat('NOT-LIBRE-01', 'Nota libre 1: inauguración de laboratorio', 'Informe Once', 480, reg=ANA, val=JOSE, reg_ts=TS(-1, '16:00'), val_ts=TS(-1, '18:00'), ruta='/prensa/libres/not_libre_01.mp4')
mat('NOT-LIBRE-02', 'Nota libre 2: feria de ciencias en el campus', 'Informe Once', 420, reg=ANA, val=JOSE, reg_ts=TS(-1, '16:10'), val_ts=TS(-1, '18:05'), ruta='/prensa/libres/not_libre_02.mp4')
mat('NOT-LIBRE-03', 'Nota libre 3: entrevista al rector', 'Informe Once', 600, reg=ANA, val=JOSE, reg_ts=TS(-1, '16:20'), val_ts=TS(-1, '18:10'), ruta='/prensa/libres/not_libre_03.mp4')
mat('BUT-LIBRE-01', 'La última función', 'Butaca Once', 5460, reg=PEDRO, val=ANA, reg_ts=TS(-3, '11:00'), val_ts=TS(-3, '14:00'), ruta='/servidor/cine/but_libre_01.mp4')
mat('SER-LIBRE-01', 'Serie nueva: Capítulo piloto', 'Serie', 10400, reg=PEDRO, val=ANA, reg_ts=TS(-3, '11:30'), val_ts=TS(-3, '14:30'), ruta='/servidor/series/ser_libre_01.mp4')
mat('PROMO-52', 'Promo Canal 11: 53 años contigo', None, 25, tipo='PROMO', reg=PEDRO, val=ANA, reg_ts=TS(-8, '10:00'), val_ts=TS(-8, '12:00'), ruta='/promos/promo_53.mp4')
mat('PROMO-BUTACA', 'Promo Butaca Once: ciclo de estreno', None, 20, tipo='PROMO', reg=PEDRO, val=ANA, reg_ts=TS(-8, '10:10'), val_ts=TS(-8, '12:10'), ruta='/promos/promo_butaca.mp4')
mat('BAJA-01', 'Spot vencido (dado de baja)', None, 30, tipo='SPOT', reg=PEDRO, val=ANA, reg_ts=TS(-40, '10:00'), val_ts=TS(-40, '12:00'), activo=False, ruta='/spots/baja_01.mp4')
# pendientes de hoy (para mostrar el recordatorio de revision y valMat en vivo)
mat('PEND-DOC-01', 'Documental: Selvas de Bolivia', 'Documentales del Once', 1500, reg=PEDRO, val=None, estado='PENDIENTE', reg_ts=TS(0, '08:00'), val_ts=None, ruta='/servidor/doc/pend_doc_01.mp4')
mat('PEND-NOT-01', 'Nota pendiente: balance de la semana', 'Informe Once', 540, reg=ANA, val=None, estado='PENDIENTE', reg_ts=TS(0, '08:05'), val_ts=None, ruta='/prensa/pend_not_01.mp4')

# ---------------------------------------------------------------- escribir materiales
# (los de la grilla se registran al generar los bloques de cada dia)
for d in DIAS:
    for (ini, fin, tipo, prog, kind, extra) in BLOQUES[d]:
        if kind == 'av':
            avance_mat(d, extra)
# el dia +1 tiene materiales PENDIENTES (borrador con problemas)
def material_sql(m):
    pend = m['estado'] == 'PENDIENTE'
    return (f"INSERT INTO material (codigo, id_programa, titulo, tipo, duracion_seg, formato, ruta, estado, observacion, registrado_por, fecha_registro, "
            f"validado_por, fecha_validacion, activo, pendiente_desde) VALUES ({q(m['cod'])}, {PG(m['prog']) if m['prog'] else 'NULL'}, {q(m['titulo'])}, "
            f"{q(m['tipo'])}, {m['dur']}, {q(m['fmt'])}, {q(m['ruta'])}, {q(m['estado'])}, {q(m['obs']) if m['obs'] else 'NULL'}, {U(m['reg'])}, {m['reg_ts']}, "
            f"{U(m['val']) if m['val'] else 'NULL'}, {m['val_ts'] if m['val_ts'] and m['val'] else 'NULL'}, {'TRUE' if m['activo'] else 'FALSE'}, "
            f"{'now()' if pend else m['reg_ts']})")
# D+1: el material de aprendemos juntos y una pelicula pendientes
MATS['AJ-D+1'].update(estado='PENDIENTE', val=None, val_ts=None, reg_ts=TS(0, '07:45'))
for m in list(MATS.values()):
    pass

# orden de insercion: programas ya estan; materiales
for m in MATS.values():
    add(material_sql(m))

# ---------------------------------------------------------------- parrillas, bloques, escaletas, spots
CRE_USER = PEDRO
for d in DIAS:
    pub = d <= 0
    add(f"INSERT INTO parrilla (fecha, estado, creado_por, fecha_creacion) VALUES ({D(d)}, 'BORRADOR', {U(PEDRO)}, {TS(d - 3 if d > -2 else -5, '09:00')})")
for d in DIAS:
    for ni, (ini, fin, tipo, prog, kind, extra) in enumerate(BLOQUES[d]):
        if tipo == 'PAUSA_COMERCIAL':
            add(f"INSERT INTO bloque (id_parrilla, id_programa, id_material, hora_inicio, hora_fin, tipo) SELECT pr.id_parrilla, NULL, NULL, TIME '{ini}', TIME '{fin}', 'PAUSA_COMERCIAL' FROM parrilla pr WHERE pr.fecha = {D(d)}")
        elif kind == 'mat':
            add(f"INSERT INTO bloque (id_parrilla, id_programa, id_material, hora_inicio, hora_fin, tipo) SELECT pr.id_parrilla, {PG(prog)}, (SELECT id_material FROM material WHERE codigo = {q(extra)}), TIME '{ini}', TIME '{fin}', 'PROGRAMA' FROM parrilla pr WHERE pr.fecha = {D(d)}")
        else:
            add(f"INSERT INTO bloque (id_parrilla, id_programa, id_material, hora_inicio, hora_fin, tipo) SELECT pr.id_parrilla, {PG(prog)}, NULL, TIME '{ini}', TIME '{fin}', 'PROGRAMA' FROM parrilla pr WHERE pr.fecha = {D(d)}")
        # escaleta
        if kind == 'esc':
            for i, c in enumerate(extra, 1):
                add(f"INSERT INTO escaleta (id_bloque, orden, id_material, registrado_por, fecha_registro) SELECT b.id_bloque, {i}, m.id_material, {U(ANA)}, {TS(d - 1, '17:30')} FROM bloque b JOIN parrilla pr ON pr.id_parrilla = b.id_parrilla, material m WHERE pr.fecha = {D(d)} AND b.hora_inicio = TIME '{ini}' AND m.codigo = {q(c)}")
        if kind == 'av':
            c = f"AV{extra}-{lab(d)}"
            add(f"INSERT INTO escaleta (id_bloque, orden, id_material, registrado_por, fecha_registro) SELECT b.id_bloque, 1, m.id_material, {U(ANA)}, {TS(d - 1, '17:30')} FROM bloque b JOIN parrilla pr ON pr.id_parrilla = b.id_parrilla, material m WHERE pr.fecha = {D(d)} AND b.hora_inicio = TIME '{ini}' AND m.codigo = {q(c)}")
# spots de las tandas LUNA
for d in DIAS:
    t = 0
    for (ini, fin, tipo, prog, kind, extra) in BLOQUES[d]:
        if tipo != 'PAUSA_COMERCIAL': continue
        h, mi, _ = [int(x) for x in ini.split(':')]
        for k in range(6):
            cod = SPOT_ORDER[(t * 3 + d + 2 + k) % len(SPOT_ORDER)]
            pauta = SPOTS[cod][2]
            seg = k * 40
            hh = f"{h:02d}:{mi + seg // 60:02d}:{seg % 60:02d}"
            add(f"INSERT INTO spot (id_pauta, id_material, id_bloque, hora, estado) SELECT p.id_pauta, m.id_material, b.id_bloque, TIME '{hh}', 'PROGRAMADO' FROM pauta p, material m, bloque b JOIN parrilla pr ON pr.id_parrilla = b.id_parrilla WHERE p.nombre = {q(pauta)} AND m.codigo = {q(cod)} AND pr.fecha = {D(d)} AND b.hora_inicio = TIME '{ini}'")
        t += 1
# publicar D-2, D-1, D0 (el trigger verifica materiales aprobados)
for d in (-2, -1, 0):
    add(f"UPDATE parrilla SET estado = 'PUBLICADA', fecha_publicacion = {TS(d - 1, '17:30')} WHERE fecha = {D(d)}")

# ---------------------------------------------------------------- emisiones reales
INCID = {(-2, '09:30:00'): 'NO_EMITIDO', (-1, '19:00:00'): 'PARCIAL', (-2, '12:00:00'): 'PARCIAL'}
for d in (-2, -1, 0):
    for ni, (ini, fin, tipo, prog, kind, extra) in enumerate(BLOQUES[d]):
        vivo = kind == 'esc' or kind == 'av'
        delay = (ni * 7 + d * 3) % (35 if vivo else 6)
        est = INCID.get((d, ini), 'EMITIDO')
        cond = f"AND b.hora_fin <= ((now() AT TIME ZONE 'America/La_Paz')::time)" if d == 0 else ""
        fin_real = f"(pr.fecha + b.hora_fin)" + ("" if fin == '23:59:59' else f" + interval '{(ni * 5) % 20} seconds'")
        if est == 'EMITIDO':
            add(f"INSERT INTO emision (id_bloque, inicio_real, fin_real, estado, registrado_por, fecha_registro) SELECT b.id_bloque, (pr.fecha + b.hora_inicio) + interval '{delay} seconds', {fin_real}, 'EMITIDO', {U(CARLA)}, {fin_real} + interval '3 minutes' FROM bloque b JOIN parrilla pr ON pr.id_parrilla = b.id_parrilla WHERE pr.fecha = {D(d)} AND b.hora_inicio = TIME '{ini}' {cond}")
        elif est == 'PARCIAL':
            add(f"INSERT INTO emision (id_bloque, inicio_real, fin_real, estado, registrado_por, fecha_registro) SELECT b.id_bloque, (pr.fecha + b.hora_inicio) + interval '{delay} seconds', (pr.fecha + b.hora_fin) - interval '10 minutes', 'PARCIAL', {U(CARLA)}, (pr.fecha + b.hora_fin) + interval '3 minutes' FROM bloque b JOIN parrilla pr ON pr.id_parrilla = b.id_parrilla WHERE pr.fecha = {D(d)} AND b.hora_inicio = TIME '{ini}'")
        else:
            add(f"INSERT INTO emision (id_bloque, inicio_real, fin_real, estado, registrado_por, fecha_registro) SELECT b.id_bloque, (pr.fecha + b.hora_inicio), NULL, 'NO_EMITIDO', {U(CARLA)}, (pr.fecha + b.hora_fin) + interval '3 minutes' FROM bloque b JOIN parrilla pr ON pr.id_parrilla = b.id_parrilla WHERE pr.fecha = {D(d)} AND b.hora_inicio = TIME '{ini}'")
add("UPDATE spot SET estado = 'EMITIDO' WHERE id_bloque IN (SELECT id_bloque FROM emision WHERE estado = 'EMITIDO')")

# ---------------------------------------------------------------- auditoria historica
add("INSERT INTO auditoria (id_usuario, accion, entidad, id_entidad, detalle, comando, fecha) SELECT registrado_por, 'INSERTAR', 'material', id_material, codigo || ' ' || titulo || ' (' || tipo || ', ' || duracion_seg || ' s, ' || formato || ')', 'insMat', fecha_registro FROM material")
add("INSERT INTO auditoria (id_usuario, accion, entidad, id_entidad, detalle, comando, fecha) SELECT validado_por, 'VALIDAR', 'material', id_material, codigo || ': PENDIENTE -> ' || estado || coalesce(' (' || observacion || ')', ''), 'valMat', fecha_validacion FROM material WHERE validado_por IS NOT NULL")
add("INSERT INTO auditoria (id_usuario, accion, entidad, id_entidad, detalle, comando, fecha) SELECT creado_por, 'INSERTAR', 'parrilla', id_parrilla, 'Parrilla del ' || fecha || ' (BORRADOR)', 'insPar', fecha_creacion FROM parrilla")
add("INSERT INTO auditoria (id_usuario, accion, entidad, id_entidad, detalle, comando, fecha) SELECT creado_por, 'PUBLICAR', 'parrilla', id_parrilla, 'Parrilla del ' || fecha || ' publicada', 'pubPar', fecha_publicacion FROM parrilla WHERE estado = 'PUBLICADA'")
add("INSERT INTO auditoria (id_usuario, accion, entidad, id_entidad, detalle, comando, fecha) SELECT registrado_por, 'INSERTAR', 'emision', id_emision, 'Emision ' || estado, 'insEmi', fecha_registro FROM emision")

hdr = "-- Datos de demostracion de Canal 11 TVU. Generado a partir de la grilla real del viernes 20-11-2026 (dia 0 = hoy al cargar).\n" \
      "-- Dias -2 y -1: parrillas publicadas y emitidas (mismos programas y horarios, con otros contenidos). Dia 0: la grilla real, publicada y emitida hasta ahora.\n" \
      "-- Dia +1: BORRADOR con materiales pendientes/rechazados (para mostrar la alerta de parrilla en riesgo). No se cargan en la base del curso.\n"
open(OUT, 'w', encoding='utf-8').write(hdr + '\n'.join(S) + '\n')
print(len(S), 'sentencias;', len(MATS), 'materiales')
