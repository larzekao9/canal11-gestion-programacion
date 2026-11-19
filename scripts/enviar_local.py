#!/usr/bin/env python3
"""Manda un comando al buzon local (Mailpit) como si fuera un correo. Requiere ./scripts/ejecutar.sh local corriendo.
Uso: python3 scripts/enviar_local.py ana.rojas@gmail.com 'lisMat["PENDIENTE"]'
Las respuestas y avisos se ven en http://localhost:58025"""
import sys, smtplib
from email.message import EmailMessage

if len(sys.argv) != 3:
    sys.exit(__doc__)
m = EmailMessage()
m['From'], m['To'], m['Subject'] = sys.argv[1], 'grupo12sa@tecnoweb.org.bo', sys.argv[2]
m.set_content('.')
with smtplib.SMTP('localhost', 55025) as s:
    s.send_message(m)
print('enviado')
