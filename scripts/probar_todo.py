#!/usr/bin/env python3
"""
Prueba de punta a punta de TODO el sistema, caso de uso por caso de uso, con el flujo real:
  comando por correo (SMTP a Mailpit) -> el sistema lo lee por POP3 -> ejecuta -> responde por correo -> avisos a los demas usuarios.
Cada paso dice si se esperaba exito o error, comprueba la respuesta que llego y los avisos que se mandaron.

Uso (desde la carpeta del proyecto, con Docker y PostgreSQL local encendidos):
    python3 scripts/probar_todo.py                  # todo: reinicia los datos (--poblar), arranca el sistema y prueba CU1 a CU8 (unos 10 min)
    python3 scripts/probar_todo.py --cu 3,5         # solo esos casos de uso
    python3 scripts/probar_todo.py --sin-poblar     # no reinicia los datos (fallan los pasos que crean algo que ya existe)
    python3 scripts/probar_todo.py --sin-plazos     # no espera el recordatorio/escalamiento (ahorra ~2 min)
    python3 scripts/probar_todo.py -v               # muestra el texto de cada respuesta

Los correos quedan en http://localhost:58025 para revisarlos despues. Es SOLO para el perfil local.
"""
import argparse, json, os, re, signal, smtplib, subprocess, sys, time, urllib.request
from datetime import datetime, timedelta
from email.message import EmailMessage
from zoneinfo import ZoneInfo

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAILPIT = "http://localhost:58025"
BUZON = "grupo12sa@tecnoweb.org.bo"
USUARIOS = {"admin": "larzekaobnc@gmail.com", "ana": "ana.rojas@gmail.com", "jose": "jose.perez@ficct.uagrm.edu.bo",
            "pedro": "pedro.vaca@hotmail.com", "carla": "produccion.canal11@gmail.com"}
EMAILS = {v: k for k, v in USUARIOS.items()}
V, R, A, G, N = "\033[32m", "\033[31m", "\033[33m", "\033[90m", "\033[0m"
TZ = ZoneInfo("America/La_Paz")

# ------------------------------------------------------------------ utilidades
def api(path, metodo="GET"):
    req = urllib.request.Request(MAILPIT + path, method=metodo)
    with urllib.request.urlopen(req, timeout=10) as r:
        cuerpo = r.read()
        try:
            return json.loads(cuerpo or b"{}")
        except ValueError:   # el DELETE de Mailpit responde "ok", sin JSON
            return {}

def correos():
    return api("/api/v1/messages?limit=500").get("messages", [])

def texto_de(id_):
    d = api(f"/api/v1/message/{id_}")
    t = d.get("Text") or re.sub(r"<[^>]+>", " ", d.get("HTML", ""))
    return re.sub(r"\s+", " ", t).strip()

def enviar(de, asunto):
    m = EmailMessage()
    m["From"], m["To"], m["Subject"] = de, BUZON, asunto
    m.set_content(".")
    with smtplib.SMTP("localhost", 55025, timeout=10) as s:
        s.send_message(m)

def fechas():
    hoy = datetime.now(TZ).date()
    f = lambda n: (hoy + timedelta(days=n)).isoformat()
    return {"HOY": f(0), "AYER": f(-1), "ANTEAYER": f(-2), "MANANA": f(1), "EN2": f(2), "EN3": f(3)}

def conf(clave, defecto=""):
    try:
        for l in open(os.path.join(RAIZ, "config.local.properties"), encoding="utf-8"):
            if l.startswith(clave + "="):
                return l.split("=", 1)[1].strip()
    except OSError:
        pass
    return defecto

def sql(consulta):
    r = subprocess.run(["psql", "-h", "localhost", "-U", conf("db.usuario"), "-d", conf("db.nombre", "canal11_local"), "-tA", "-F", "|",
                        "-c", "SET search_path TO canal11; " + consulta], capture_output=True, text=True)
    return [l for l in r.stdout.strip().splitlines() if l and l != "SET"]

# ------------------------------------------------------------------ casos
class Caso:
    def __init__(s, cu, user, cmd, esperado="ok", contiene=None, avisos=None, nota=None):
        s.cu, s.user, s.cmd, s.esperado, s.contiene, s.avisos, s.nota = cu, user, cmd, esperado, contiene, avisos or [], nota

OK, ERR = "ok", "err"
def casos_de(cu, F):
    c = lambda *a, **k: Caso(cu, *a, **k)
    L = []
    if cu == 0:   # interprete y ayuda
        L += [c("pedro", 'help'), c("pedro", 'help["3"]', contiene="camBlo"),
              c("ana", 'RE: lisPro["*"]', nota="prefijo RE: del correo"), c("ana", 'lisPro[“*”]', nota="comillas tipograficas del celular"),
              c("pedro", 'lisUsr["*"]', ERR, contiene="Quiso decir"), c("pedro", 'mosPar[]', ERR, contiene="necesita"),
              c("desconocido@gmail.com", 'help', ERR, nota="remitente que no es usuario")]
    if cu == 1:
        L += [c("admin", 'lisUsu["*"]'), c("admin", 'mosUsu["7234567"]', contiene="Vaca"),
              c("admin", 'insUsu["8000001","Rosa","Quiroga Vaca","rosa.quiroga@gmail.com","71111111","PROGRAMADOR"]'),
              c("admin", 'insUsu["8000002","Rosa","Quiroga Vaca","rosa.quiroga@gmail.com","71111112","PROGRAMADOR"]', ERR, nota="correo repetido"),
              c("admin", 'insUsu["8000003","Luis","Soto","luis@gmail.com","","JEFE"]', ERR, nota="rol invalido"),
              c("admin", 'modUsu["8000001","8000001","Rosa","Quiroga Vaca","rosa.quiroga@gmail.com","71111111","ENCARGADO"]'),
              c("admin", 'eliUsu["8000001"]'), c("admin", 'actUsu["8000001"]'),
              c("pedro", 'lisUsu["*"]', ERR, contiene="permiso", nota="solo el administrador gestiona usuarios")]
    if cu == 2:
        L += [c("pedro", 'lisPro["*"]'), c("carla", 'mosPro["Informe Once"]'),
              c("pedro", 'insPro["Programa E2E","Programa de prueba","OTRO","30","Prueba","ATP"]'),
              c("pedro", 'insPro["Programa E2E","otro","OTRO","30","Prueba","ATP"]', ERR, nota="nombre repetido"),
              c("pedro", 'modPro["Programa E2E","Programa E2E","Programa editado","OTRO","45","Prueba","ATP"]'),
              c("pedro", 'eliPro["Programa E2E"]'),
              c("pedro", 'eliPro["Informe Once"]', ERR, nota="tiene bloques programados"),
              c("carla", 'insPro["Otro E2E","x","OTRO","30","x","ATP"]', ERR, contiene="permiso")]
    if cu == 3:
        e2 = F["EN2"]
        L += [c("pedro", 'lisPar["*"]'), c("carla", f'mosPar["{F["HOY"]}"]'), c("pedro", 'mosPar["2099-01-01"]', ERR, nota="no existe"),
              c("pedro", f'insPar["{F["AYER"]}"]', ERR, contiene="pasada", nota="no se crean parrillas pasadas"),
              c("pedro", f'insPar["{e2}"]'), c("pedro", f'insPar["{e2}"]', ERR, nota="ya existe"),
              c("pedro", f'insBlo["{e2}","00:00","02:00","PROGRAMA","Butaca Once","BUT-LIBRE-01"]'),
              c("pedro", f'insBlo["{e2}","01:00","03:00","PROGRAMA","Butaca Once","BUT-01"]', ERR, contiene="solapa"),
              c("pedro", f'insBlo["{e2}","02:00","03:00","PROGRAMA","Serie","SER-LIBRE-01"]', ERR, contiene="no cabe"),
              c("pedro", f'insBlo["{e2}","02:00","05:00","PROGRAMA","Serie","SER-LIBRE-01"]'),
              c("pedro", f'insBlo["{e2}","05:00","06:00","PAUSA_COMERCIAL","","BUT-01"]', ERR, nota="una pausa no lleva material"),
              c("pedro", f'insBlo["{e2}","05:00","06:00","PROGRAMA","Butaca Once","SPOT-ADM-01"]', ERR, contiene="SPOT"),
              c("pedro", f'insBlo["{e2}","05:00","06:00","PROGRAMA","Butaca Once","PEND-DOC-01"]', ERR, nota="material de otro programa"),
              c("pedro", f'insBlo["{e2}","19:00","19:15","PAUSA_COMERCIAL","",""]'),
              c("pedro", f'insBlo["{e2}","20:00","24:00","PROGRAMA","Butaca Once","BUT-01"]', nota="hora_fin 24:00 = fin del dia"),
              c("pedro", f'insBlo["{e2}","22:00","25:00","PROGRAMA","Butaca Once","BUT-01"]', ERR, nota="hora invalida"),
              c("pedro", f'insBlo["{e2}","15:00","17:00","PROGRAMA","Butaca Once","BUT-02"]'),
              c("pedro", f'eliBlo["{e2}","15:00"]'),
              c("carla", f'insPar["{F["EN3"]}"]', ERR, contiene="permiso"),
              c("pedro", f'pubPar["{e2}"]', contiene="Cobertura", nota="avisa huecos y cobertura de las 24 h",
                avisos=[("Parrilla publicada", ["carla", "ana", "jose"])]),
              c("pedro", f'insBlo["{e2}","06:00","07:00","PROGRAMA","Butaca Once","BUT-01"]', ERR, contiene="PUBLICADA"),
              c("pedro", f'eliPar["{e2}"]', ERR, contiene="PUBLICADA"),
              c("pedro", f'camBlo["{e2}","20:00","BUT-02"]', contiene="cambiado", avisos=[("Cambio en la parrilla", ["carla", "ana", "jose"])],
                nota="cambio de ultimo momento con la parrilla publicada"),
              c("pedro", f'camBlo["{e2}","20:00","PEND-DOC-01"]', ERR, nota="material pendiente"),
              c("pedro", f'camBlo["{e2}","19:00","BUT-01"]', ERR, nota="una pausa no lleva material"),
              c("pedro", f'camBlo["{F["HOY"]}","00:00","BUT-02"]', ERR, contiene="ya empez", nota="el bloque ya salio al aire"),
              c("carla", f'camBlo["{e2}","20:00","BUT-01"]', ERR, contiene="permiso"),
              c("ana", f'insLea["{e2}","20:00","1","NOT-LIBRE-01"]', ERR, contiene="noticiero", nota="la escaleta solo va en noticieros"),
              c("carla", f'lisLea["{F["HOY"]}","12:30"]', contiene="Informe Once")]
    if cu == 4:
        L += [c("ana", 'lisMat["PENDIENTE"]'), c("ana", 'mosMat["PEND-DOC-01"]'),
              c("pedro", 'insMat["E2E-01","Documental de prueba","PROGRAMA","Documentales del Once","1500","MP4","/e2e/doc01.mp4"]'),
              c("pedro", 'insMat["E2E-01","otro","PROGRAMA","Documentales del Once","1500","MP4","/e2e/doc99.mp4"]', ERR, nota="codigo repetido"),
              c("pedro", 'insMat["E2E-99","otro","PROGRAMA","Documentales del Once","1500","MP4","/e2e/doc01.mp4"]', ERR, nota="ruta repetida (archivo duplicado)"),
              c("pedro", 'insMat["E2E-98","Otro","PROGRAMA","Documentales del Once","1500","MP4","/e2e/doc98.mov"]', ERR, contiene="debe terminar", nota="la extension debe coincidir con el formato"),
              c("pedro", 'insMat["E2E-97","Documental de prueba","PROGRAMA","Documentales del Once","1500","MP4","/e2e/doc97.mp4"]', contiene="Posible duplicado", nota="mismo titulo, tipo y duracion"),
              c("pedro", 'modMat["E2E-01","Documental de prueba (editado)","PROGRAMA","Documentales del Once","1500","MP4","/e2e/doc01.mp4"]'),
              c("pedro", 'eliMat["E2E-97"]'), c("pedro", 'eliMat["E2E-01"]'),
              c("pedro", 'eliMat["BUT-01"]', ERR, nota="esta en parrillas publicadas"),
              c("pedro", 'insMat["E2E-PLAZO","Material para el plazo de revision","PROGRAMA","Documentales del Once","1200","MP4","/e2e/plazo.mp4"]',
                nota="queda PENDIENTE: debe disparar recordatorio y escalamiento"),
              c("admin", 'lisMat["VENCIDO"]'),
              c("carla", 'insMat["E2E-CARLA","x","SPOT","","30","MP4","/e2e/c.mp4"]', ERR, contiene="permiso")]
    if cu == 5:
        m = F["MANANA"]
        L += [c("pedro", 'insMat["E2E-02","Spot de prueba","SPOT","","30","MP4","/e2e/spot02.mp4"]'),
              c("pedro", 'valMat["E2E-02","APROBADO","ok"]', ERR, contiene="permiso", nota="Programacion no valida"),
              c("ana", 'valMat["E2E-02","APROBADO","Correcto"]', avisos=[("Material aprobado", ["pedro"])], nota="Prensa valida y se avisa a quien lo registro"),
              c("ana", 'valMat["E2E-02","APROBADO","otra vez"]', ERR, nota="ya esta aprobado"),
              c("pedro", 'insMat["E2E-03","Spot a rechazar","SPOT","","30","MP4","/e2e/spot03.mp4"]'),
              c("ana", 'valMat["E2E-03","RECHAZADO",""]', ERR, contiene="observaci", nota="rechazar exige observacion"),
              c("ana", 'valMat["E2E-03","RECHAZADO","Audio con ruido"]', avisos=[("Material rechazado", ["pedro"])]),
              c("ana", 'valMat["PEND-NOT-01","APROBADO","Me lo apruebo"]', ERR, contiene="usted mismo", nota="quien registra no valida"),
              c("pedro", f'estPar["{m}"]', contiene="por resolver", nota="la parrilla de mañana no esta lista"),
              c("ana", 'valMat["AJ-D+1","APROBADO","Revisado"]'), c("jose", 'valMat["IO1-D+1-06","APROBADO","Revisada"]'),
              c("jose", 'valMat["IO1-D+1-07","APROBADO","Revisada"]'),
              c("ana", f'eliLea["{m}","12:30","IO1-D+1-08"]', nota="la nota rechazada sale de la escaleta"),
              c("ana", f'insLea["{m}","12:30","8","NOT-LIBRE-01"]', nota="y entra otra aprobada"),
              c("pedro", f'estPar["{m}"]', contiene="todo está aprobado"),
              c("pedro", f'pubPar["{m}"]', avisos=[("Parrilla publicada", ["carla", "ana", "jose"])]),
              c("pedro", f'camBlo["{m}","13:55","SER-LIBRE-01"]', avisos=[("Cambio en la parrilla", ["carla", "ana", "jose"])]),
              c("ana", f'modLea["{m}","12:30","NOT-LIBRE-01","1"]', avisos=[("orden del noticiero", ["carla", "pedro"])], nota="cambia el orden del noticiero publicado"),
              c("ana", f'insLea["{m}","12:30","1","NOT-LIBRE-01"]', ERR, nota="la nota ya esta en la escaleta"),
              c("ana", f'insLea["{m}","12:30","12","NOT-LIBRE-02"]', ERR, contiene="no es válido", nota="orden fuera de rango"),
              c("ana", f'insLea["{m}","12:30","9","PEND-NOT-01"]', ERR, contiene="APROBADAS", nota="solo notas aprobadas"),
              c("ana", f'insLea["{m}","12:30","9","NOT-LIBRE-02"]', nota="entra una mas"),
              c("ana", f'insLea["{m}","12:30","10","NOT-LIBRE-03"]', ERR, contiene="no cabe", nota="la escaleta no puede durar mas que el bloque"),
              c("pedro", f'insLea["{m}","12:30","1","NOT-LIBRE-03"]', ERR, contiene="permiso", nota="la escaleta es de Prensa"),
              c("ana", f'lisLea["{m}","12:30"]', contiene="NOT-LIBRE-01")]
    if cu == 6:
        e3 = F["EN3"]
        L += [c("pedro", 'lisPau["*"]'), c("pedro", 'mosPau["LUNA - Tanda comercial"]'),
              c("pedro", f'insPau["Pauta E2E","Anunciante E2E","{F["HOY"]}","{e3}","50"]'),
              c("pedro", f'insPau["Pauta E2E","otro","{F["HOY"]}","{e3}","50"]', ERR, nota="nombre repetido"),
              c("pedro", f'insPau["Pauta mal","x","{e3}","{F["HOY"]}","50"]', ERR, nota="fechas invertidas"),
              c("pedro", f'insPar["{e3}"]'), c("pedro", f'insBlo["{e3}","19:00","19:15","PAUSA_COMERCIAL","",""]'),
              c("pedro", f'insBlo["{e3}","10:00","12:00","PROGRAMA","Butaca Once","BUT-01"]'),
              c("pedro", f'insSpo["Pauta E2E","SPOT-ADM-01","{e3}","19:00","19:00:00"]'),
              c("pedro", f'insSpo["Pauta E2E","SPOT-ADM-01","{e3}","19:00","19:00:00"]', ERR, nota="esa hora ya esta ocupada"),
              c("pedro", f'insSpo["Pauta E2E","SPOT-ADM-01","{e3}","19:00","19:20:00"]', ERR, nota="fuera de la pausa"),
              c("pedro", f'insSpo["Pauta E2E","BUT-01","{e3}","19:00","19:01:00"]', ERR, contiene="SPOT", nota="el material no es un spot"),
              c("pedro", f'insSpo["Pauta E2E","SPOT-ADM-01","{e3}","10:00","10:00:00"]', ERR, nota="no es una pausa comercial"),
              c("pedro", f'insSpo["Pauta E2E","SPOT-ADM-01","{F["HOY"]}","08:45","08:55:00"]', nota="un spot en la parrilla de hoy (ya publicada)"),
              c("pedro", f'eliSpo["{F["HOY"]}","08:55:00"]'), c("pedro", f'eliSpo["{e3}","19:00:00"]'),
              c("pedro", 'eliPau["Pauta E2E"]'), c("pedro", 'eliPau["LUNA - Tanda comercial"]', ERR, nota="tiene spots programados"),
              c("carla", 'insPau["Pauta carla","x","2030-01-01","2030-02-01","5"]', ERR, contiene="permiso")]
    if cu == 7:
        ini = sql(f"SELECT to_char(b.hora_inicio,'HH24:MI'), to_char(b.hora_fin,'HH24:MI:SS') FROM bloque b JOIN parrilla p ON p.id_parrilla=b.id_parrilla "
                  f"WHERE p.fecha='{F['HOY']}' AND b.hora_inicio <= (now() AT TIME ZONE 'America/La_Paz')::time AND NOT EXISTS "
                  f"(SELECT 1 FROM emision e WHERE e.id_bloque=b.id_bloque) ORDER BY b.hora_inicio LIMIT 2")
        fut = sql(f"SELECT to_char(b.hora_inicio,'HH24:MI'), to_char(b.hora_fin,'HH24:MI:SS') FROM bloque b JOIN parrilla p ON p.id_parrilla=b.id_parrilla "
                  f"WHERE p.fecha='{F['HOY']}' AND b.hora_inicio > (now() AT TIME ZONE 'America/La_Paz')::time ORDER BY b.hora_inicio LIMIT 1")
        h = F["HOY"]
        if ini:
            a, fa = ini[0].split("|")
            L += [c("carla", f'insEmi["{h}","{a}","{a}:03","{fa}","EMITIDO"]', nota=f"bloque de las {a}, que ya empezo y no tenia emision"),
                  c("carla", f'insEmi["{h}","{a}","{a}:03","{fa}","EMITIDO"]', ERR, nota="ya tiene emision registrada"),
                  c("carla", f'insEmi["{h}","{a}","{fa}","{a}:03","EMITIDO"]', ERR, nota="fin anterior al inicio")]
            if len(ini) > 1:
                b2, _ = ini[1].split("|")
                L.append(c("pedro", f'insEmi["{h}","{b2}","","","NO_EMITIDO"]', nota="Programacion tambien puede registrar; bloque no emitido"))
        else:
            L.append(c("carla", 'help', nota="(no hay bloques de hoy sin emision: se omiten los insEmi OK)"))
        if fut:
            f_, _ = fut[0].split("|")
            L.append(c("carla", f'insEmi["{h}","{f_}","{f_}:00","{f_}:30","EMITIDO"]', ERR, contiene="todavía no empieza", nota="el bloque no ha empezado"))
        L += [c("carla", f'insEmi["{F["MANANA"]}","20:00","20:00:00","21:00:00","EMITIDO"]', ERR, contiene="todavía no empieza", nota="no se registra lo que aun no salio al aire"),
              c("carla", 'insEmi["2099-01-01","20:00","20:00:00","21:00:00","EMITIDO"]', ERR),
              c("ana", f'insEmi["{h}","00:00","00:00:00","00:27:00","EMITIDO"]', ERR, contiene="permiso"),
              c("ana", f'conPar["{h}"]', contiene="Cumplimiento"), c("ana", f'conPar["{F["AYER"]}"]', contiene="Cumplimiento"),
              c("admin", 'lisAud["*"]'), c("admin", 'lisAud["escaleta"]'), c("admin", 'lisAud["material"]'),
              c("admin", f'lisAud["{h}"]'), c("pedro", 'lisAud["*"]', ERR, contiene="permiso", nota="solo el administrador")]
    if cu == 8:
        d, h = F["ANTEAYER"], F["HOY"]
        L += [c("pedro", f'repPro["{d}","{h}"]', contiene="Total"), c("ana", f'repMat["{d}","{h}"]'), c("pedro", f'repPau["{d}","{h}"]'),
              c("pedro", f'repCum["{d}","{h}"]', contiene="Cumplimiento"), c("admin", f'repCum["{d}","{h}"]'),
              c("pedro", f'repCum["{h}","{d}"]', ERR, nota="desde mayor que hasta"), c("pedro", f'repCum["{d}","2099-01-01"]', ERR, nota="rango mayor a 366 dias"),
              c("ana", f'repPro["{d}","{h}"]', ERR, contiene="permiso"), c("carla", f'repCum["{d}","{h}"]', ERR, contiene="permiso")]
    return L

# ------------------------------------------------------------------ ejecucion
def esperar(cond, segundos, paso=0.5):
    t = time.time()
    while time.time() - t < segundos:
        r = cond()
        if r:
            return r
        time.sleep(paso)
    return None

def correr(c, vistos, verbose, F):
    de = USUARIOS.get(c.user, c.user)
    cmd = c.cmd
    antes = {m["ID"] for m in correos()}
    t0 = time.time()
    enviar(de, cmd)
    def respuesta():
        for m in correos():
            if m["ID"] not in antes and m["Subject"].startswith("Canal 11 |") and any(t["Address"].lower() == de.lower() for t in m["To"]):
                return m
    resp = esperar(respuesta, 25)
    seg = time.time() - t0
    problemas, extra = [], []
    if not resp:
        problemas.append("no llego la respuesta en 25 s")
        titulo, cuerpo, fue_error = "(sin respuesta)", "", None
    else:
        titulo = resp["Subject"].replace("Canal 11 | ", "")
        cuerpo = texto_de(resp["ID"])
        fue_error = titulo == "Error"
        if c.esperado == OK and fue_error: problemas.append("se esperaba exito y respondio Error: " + cuerpo[cuerpo.find("No se pudo"):][:200])
        if c.esperado == ERR and not fue_error: problemas.append(f"se esperaba un error y respondio «{titulo}»")
        if c.contiene and c.contiene.lower() not in cuerpo.lower(): problemas.append(f"la respuesta no contiene «{c.contiene}»")
    # avisos esperados (se mandan en segundo plano)
    nuevos = []
    if c.avisos:
        def todos():
            nuevos[:] = [m for m in correos() if m["ID"] not in antes and m is not resp and m["ID"] != (resp or {}).get("ID")]
            for asunto, dest in c.avisos:
                for u in dest:
                    if not any(asunto.lower() in m["Subject"].lower() and USUARIOS[u].lower() in [t["Address"].lower() for t in m["To"]] for m in nuevos):
                        return False
            return True
        if not esperar(todos, 15):
            for asunto, dest in c.avisos:
                for u in dest:
                    if not any(asunto.lower() in m["Subject"].lower() and USUARIOS[u].lower() in [t["Address"].lower() for t in m["To"]] for m in nuevos):
                        problemas.append(f"falto el aviso «{asunto}» a {u}")
    ok = not problemas
    marca = f"{V}✔{N}" if ok else f"{R}✘{N}"
    esp = "éxito" if c.esperado == OK else "error"
    print(f"  {marca} {G}[{c.user:6}]{N} {cmd[:100]}")
    print(f"      {G}esperado: {esp} · respuesta: «{titulo}» · {seg:.1f} s{N}" + (f" · {A}{c.nota}{N}" if c.nota else ""))
    for p in problemas: print(f"      {R}→ {p}{N}")
    for asunto, dest in c.avisos:
        if ok: print(f"      {G}✉ aviso «{asunto}» → {', '.join(dest)}{N}")
    if verbose and cuerpo: print(f"      {G}{cuerpo[:400]}{N}")
    return ok

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cu", default="0,1,2,3,4,5,6,7,8"); ap.add_argument("--sin-poblar", action="store_true")
    ap.add_argument("--sin-plazos", action="store_true"); ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    os.chdir(RAIZ)
    cus = [int(x) for x in a.cu.split(",")]
    completo = set(cus) >= set(range(0, 9))
    try:
        api("/api/v1/info")
    except Exception:
        sys.exit("Mailpit no responde en http://localhost:58025. Ejecute primero ./scripts/ejecutar.sh local una vez (levanta Docker y Mailpit) y deténgalo con Ctrl+C.")
    if not a.sin_poblar:
        print(f"{A}Reiniciando los datos de la base local (--poblar)...{N}")
        r = subprocess.run(["./scripts/ejecutar.sh", "local", "--poblar"], capture_output=True, text=True)
        if r.returncode: sys.exit(r.stdout + r.stderr)
        print("  " + [l for l in r.stdout.splitlines() if "Datos cargados" in l][-1].strip())
    t_poblar = time.time()
    api("/api/v1/messages", "DELETE")
    os.makedirs("salida", exist_ok=True)
    log = open("salida/sistema_e2e.log", "w")
    sistema = subprocess.Popen(["./scripts/ejecutar.sh", "local"], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        if not esperar(lambda: "Revisando cada" in open("salida/sistema_e2e.log").read(), 60, 1):
            sys.exit("El sistema no arrancó. Vea salida/sistema_e2e.log")
        time.sleep(5)   # la primera vuelta del buzon solo toma nota de lo que ya habia
        print(f"{A}Sistema corriendo (log: salida/sistema_e2e.log). Correos: {MAILPIT}{N}\n")
        F = fechas()
        res = {}
        if completo:
            print(f"{A}ARRANQUE · alerta automática de parrilla en riesgo (mañana no está lista){N}")
            ok = bool(esperar(lambda: sum("riesgo" in m["Subject"].lower() or "urgente" in m["Subject"].lower() for m in correos()) >= 3, 40))
            print(f"  {V+'✔' if ok else R+'✘'}{N} llegó «Parrilla en riesgo» a Programación y Prensa\n")
            res["arranque"] = [ok]
        nombres = {0: "Interprete y ayuda", 1: "CU1 Usuarios", 2: "CU2 Programas", 3: "CU3 Parrilla, bloques, camBlo y escaleta", 4: "CU4 Materiales",
                   5: "CU5 Validación, parrilla de mañana y avisos", 6: "CU6 Pautas y spots", 7: "CU7 Emisión y auditoría", 8: "CU8 Reportes"}
        for cu in cus:
            print(f"{A}━━ {nombres[cu]} ━━{N}")
            res[nombres[cu]] = [correr(c, None, a.verbose, F) for c in casos_de(cu, F)]
            print()
        if completo and not a.sin_plazos:
            print(f"{A}PLAZO DE REVISIÓN · recordatorio y escalamiento de materiales pendientes{N}")
            falta = 150 - (time.time() - t_poblar)
            if falta > 0: print(f"  {G}esperando hasta {falta:.0f} s para que venzan los plazos (1 y 2 min)...{N}")
            f = lambda asunto, user: lambda: any(asunto in m["Subject"] and USUARIOS[user].lower() in [t["Address"].lower() for t in m["To"]] for m in correos())
            r1 = bool(esperar(f("Recordatorio", "ana"), max(5, falta + 20))); r2 = bool(esperar(f("Escalamiento", "admin"), max(5, falta + 20)))
            print(f"  {V+'✔' if r1 else R+'✘'}{N} «Recordatorio: materiales pendientes de revisión» llegó a Prensa")
            print(f"  {V+'✔' if r2 else R+'✘'}{N} «Escalamiento: materiales sin revisar» llegó al administrador\n")
            res["plazos"] = [r1, r2]
        # resumen
        print(f"{A}━━ RESUMEN ━━{N}")
        total = bien = 0
        for k, v in res.items():
            total += len(v); bien += sum(v)
            print(f"  {V+'✔' if all(v) else R+'✘'}{N} {k}: {sum(v)}/{len(v)}")
        asuntos = {}
        for m in correos():
            if not m["Subject"].startswith("Canal 11 |"): continue
            k = re.sub(r"[:(].*", "", m["Subject"].replace("Canal 11 | ", "")).strip()
            asuntos[k] = asuntos.get(k, 0) + 1
        print(f"\n  Correos que mandó el sistema: {sum(asuntos.values())} (respuestas y avisos). Revíselos en {MAILPIT}")
        print(f"\n  {V if bien == total else R}{bien}/{total} pasos correctos{N}")
        return 0 if bien == total else 1
    finally:
        try: os.killpg(sistema.pid, signal.SIGTERM)
        except Exception: pass
        subprocess.run(["pkill", "-f", "canal11.App"], capture_output=True)

if __name__ == "__main__":
    sys.exit(main())
