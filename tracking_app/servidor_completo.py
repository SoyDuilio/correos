# ==============================================================================
# SERVIDOR COMPLETO DE ENVÍO Y TRACKING DE CORREOS - v2 (con saludo por género)
# Creado para correos.yasta.cloud
# ==============================================================================

# -----------------
# 1. IMPORTS
# -----------------
import csv
import smtplib
import ssl
from email.message import EmailMessage
import time
import uuid
import os
import datetime
import html
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response

# -----------------
# 2. CONFIGURACIÓN
# -----------------
MI_EMAIL = "restucciaduilio@gmail.com"
MI_CONTRASENA = "qsrtwnhdmplhtqev"
ARCHIVO_CSV_DESTINATARIOS = "mis_correos.csv"
LOG_ENVIOS_CSV = "log_envios.csv" # Archivo para registrar a quién corresponde cada ID
LOG_APERTURAS_TXT = "log_aperturas.txt"

# IMPORTANTE: Esta debe ser la IP pública o dominio de tu servidor.
# Si estás probando en local, puedes usar un servicio como ngrok.
URL_SERVIDOR_TRACKING = "https://correos.yasta.cloud" 

# -----------------
# 3. LÓGICA DE ENVÍO
# -----------------
def enviar_correos():
    """Función principal que lee el CSV y envía los correos con tracking y saludo personalizado."""
    print("--- INICIANDO PROCESO DE ENVÍO DE CORREOS (v2) ---")
    try:
        # ... (La lógica para abrir el log de envíos es la misma) ...

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as servidor:
            servidor.login(MI_EMAIL, MI_CONTRASENA)
            print("Autenticación SMTP correcta.")

            with open(ARCHIVO_CSV_DESTINATARIOS, mode='r', encoding='utf-8') as archivo_destinatarios:
                lector_csv = csv.reader(archivo_destinatarios)
                next(lector_csv)

                # ========= CAMBIO IMPORTANTE AQUÍ =========
                # Ahora leemos 4 columnas: nombre, sexo, apellido, email
                for nombre, sexo, apellido, email_destino in lector_csv:
                    # Determinamos el saludo correcto
                    saludo = "Estimada" if sexo.upper() == "F" else "Estimado"

                    tracking_id = str(uuid.uuid4())
                    
                    with open(LOG_ENVIOS_CSV, mode='a', newline='', encoding='utf-8') as log_file:
                        log_writer = csv.writer(log_file)
                        timestamp_envio = time.strftime("%Y-%m-%d %H:%M:%S")
                        log_writer.writerow([timestamp_envio, tracking_id, email_destino])

                    url_pixel = f"{URL_SERVIDOR_TRACKING}/track/{tracking_id}"
                    html_pixel = f'<img src="{url_pixel}" width="1" height="1" alt="">'
                    
                    # --- PLANTILLA DEL CORREO (con saludo personalizado) ---
                    cuerpo_html = f"""
                    <html>
                        <body>
                            <p>{saludo} Congresista {apellido},</p>
                            <p>Mi nombre es [Tu Nombre] y soy un consultor tecnológico...</p>
                            <p>...</p>
                            <p><b>[Tu Nombre]</b></p>
                            {html_pixel}
                        </body>
                    </html>
                    """
                    
                    msg = EmailMessage()
                    msg['Subject'] = "Propuesta: Herramienta de CRM Político"
                    msg['From'] = MI_EMAIL
                    msg['To'] = email_destino
                    msg.add_alternative(cuerpo_html, subtype='html')

                    servidor.send_message(msg)
                    print(f"✅ Correo enviado a {saludo} {nombre} {apellido} ({email_destino}).")
                    time.sleep(2)

        return "Proceso de envío completado exitosamente."
    except ValueError:
        error_msg = f"❌ ERROR: Revisa tu archivo CSV. Debe tener 4 columnas: nombre,sexo,apellido,email"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"❌ ERROR INESPERADO DURANTE EL ENVÍO: {e}"
        print(error_msg)
        return error_msg

# -----------------
# 4. LÓGICA DEL SERVIDOR WEB (FastAPI) - Sin cambios
# -----------------
PIXEL_TRANSPARENTE_GIF = b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
tracking_map = {}

def cargar_tracking_map():
    if not os.path.exists(LOG_ENVIOS_CSV): return
    with open(LOG_ENVIOS_CSV, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        try: next(reader)
        except StopIteration: return
        for row in reader:
            if len(row) >= 3: tracking_map[row[1]] = row[2]
    print(f"Mapa de seguimiento cargado/actualizado con {len(tracking_map)} registros.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando aplicación y cargando mapa de seguimiento...")
    cargar_tracking_map()
    yield
    print("La aplicación se ha detenido.")

app = FastAPI(lifespan=lifespan)

@app.get("/correos", response_class=HTMLResponse)
async def panel_de_control():
    html_content = """
    <html>
        <head><title>Panel de Control - Envío de Correos</title>
            <style> body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f2f5; margin: 0; } .container { text-align: center; padding: 40px; background-color: white; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); } button { background-color: #007bff; color: white; border: none; padding: 15px 30px; font-size: 16px; border-radius: 5px; cursor: pointer; margin-bottom: 20px;} a { color: #007bff; text-decoration: none; } </style>
        </head>
        <body>
            <div class="container">
                <h1>Panel de Control de Envíos</h1>
                <p>Presiona el botón para iniciar el envío de correos a la lista.</p>
                <form action="/enviar" method="post"><button type="submit">Iniciar Envío de Correos</button></form>
                <a href="/logs" target="_blank">Ver Log de Aperturas</a>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/enviar")
async def trigger_send_emails():
    resultado = enviar_correos()
    cargar_tracking_map()
    return HTMLResponse(f"<h1>Proceso de envío finalizado.</h1><p>{resultado}</p><p><a href='/correos'>Volver al panel</a></p>")

@app.get("/track/{tracking_id}")
async def track_email_open(tracking_id: str, request: Request):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    email_destinatario = tracking_map.get(tracking_id, "ID Desconocido")
    log_line = f"APERTURA | Fecha: {timestamp} | Email: {email_destinatario} | IP: {request.client.host}\n"
    print(f"✅ {log_line.strip()}")
    with open(LOG_APERTURAS_TXT, "a", encoding='utf-8') as f:
        f.write(log_line)
    return Response(content=PIXEL_TRANSPARENTE_GIF, media_type="image/gif")

@app.get("/logs", response_class=HTMLResponse)
async def view_logs():
    log_content = ""
    try:
        with open(LOG_APERTURAS_TXT, "r", encoding='utf-8') as f:
            lines = f.readlines()
            lines.reverse()
            log_content = "".join([html.escape(line) for line in lines])
    except FileNotFoundError:
        log_content = "Aún no se ha registrado ninguna apertura."
    html_page = f"""
    <html>
        <head><title>Log de Aperturas</title><meta http-equiv="refresh" content="30">
            <style> body {{ font-family: monospace; background-color: #1e1e1e; color: #d4d4d4; padding: 20px; }} h1 {{ color: #569cd6; }} pre {{ white-space: pre-wrap; word-wrap: break-word; font-size: 14px;}} </style>
        </head>
        <body><h1>Log de Aperturas (lo más nuevo arriba)</h1><pre>{log_content}</pre></body>
    </html>
    """
    return HTMLResponse(content=html_page)