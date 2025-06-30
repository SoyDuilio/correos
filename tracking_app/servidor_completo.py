# ==============================================================================
# SERVIDOR COMPLETO DE ENVÍO Y TRACKING DE CORREOS - v3.0
# Integrado con plantillas profesionales y función de "darse de baja"
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
LOG_ENVIOS_CSV = "log_envios.csv"
LOG_APERTURAS_TXT = "log_aperturas.txt"
LOG_UNSUBSCRIBE_TXT = "log_unsubscribe.txt"  # <-- NUEVO LOG

# TU NOMBRE Y TELÉFONO PARA LAS PLANTILLAS
TU_NOMBRE_REMITENTE = "Duilio Restuccia" # <-- RELLENA ESTO
TU_TELEFONO_REMITENTE = "WhatsApp: 974089434"      # <-- RELLENA ESTO

URL_SERVIDOR_TRACKING = "https://correos.yasta.cloud"

# -----------------
# 3. PLANTILLAS DE CORREO HTML
# -----------------

# Elige cuál de las dos plantillas quieres usar descomentando la línea correspondiente.
# Por defecto, usaremos la "Visionario Estratégico".

plantilla_activa = "visionario" # Cambia a "solucionador" para usar la otra plantilla

def obtener_cuerpo_html(plantilla_nombre, datos):
    """Genera el HTML del correo basado en una plantilla y los datos del destinatario."""

    # --- Plantilla 1: El Visionario Estratégico ---
    plantilla_visionario = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; font-size: 16px; line-height: 1.6;">
        <p>{datos['saludo']} Congresista {datos['apellido']},</p>
        <p>Mi nombre es {datos['nombre_remitente']}, y como consultor tecnológico sigo de cerca la intersección entre la política y la innovación.</p>
        <p>Ante el inminente retorno al sistema bicameral, la próxima campaña de reelección será un escenario sin precedentes. La competencia será mayor y la capacidad para <strong>gestionar un electorado de manera inteligente será el factor decisivo.</strong></p>
        <p>Con esta visión, he desarrollado un <strong>CRM Político</strong> diseñado no para el trabajo de hoy, sino para la victoria de mañana. Esta plataforma le permite a usted y a su equipo:</p>
        <ul>
            <li><strong>Construir un activo de datos propio:</strong> Centralizar cada contacto, simpatizante y necesidad ciudadana en una base de datos segura y segmentable.</li>
            <li><strong>Medir el pulso real:</strong> Conocer con precisión el impacto de sus eventos y la penetración de su mensaje en el territorio.</li>
            <li><strong>Actuar con agilidad:</strong> Movilizar bases y comunicar mensajes clave de forma directa y personalizada, sin depender de intermediarios.</li>
        </ul>
        <p>Esta no es una herramienta genérica, es un sistema de inteligencia para su capital político. El 90% del desarrollo está completado y me encantaría ofrecerle una <strong>sesión estratégica privada de 15 minutos</strong> la próxima semana para mostrarle cómo puede obtener una ventaja decisiva.</p>
        <p>Un cordial saludo,</p>
        <p>
            <strong>{datos['nombre_remitente']}</strong><br>
            Consultor Estratégico en Tecnología<br>
            {datos['telefono_remitente']}
        </p>
        {datos['tracking_pixel']}
        <p style="font-size:12px; color:#777777;">
          Recibes este correo porque considero que esta herramienta puede ser de alto valor estratégico para tu labor.
          Si no deseas recibir futuras comunicaciones, puedes <a href="{datos['unsubscribe_link']}" style="color:#777777;">darte de baja aquí</a>.
        </p>
    </body>
    </html>
    """
    
    # --- Plantilla 2: El Solucionador de Problemas ---
    plantilla_solucionador = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; font-size: 16px; line-height: 1.6;">
        <p>{datos['saludo']} Congresista {datos['apellido']},</p>
        <p>Cada día, su equipo y usted interactúan con cientos de ciudadanos, reciben peticiones y recogen datos valiosos en el campo. Mi pregunta es: <strong>¿dónde se almacena y cómo se aprovecha esa información?</strong></p>
        <p>Como consultor tecnológico, he visto que a menudo estos datos terminan en hojas de Excel, notas de WhatsApp o se pierden. Esa información dispersa es <strong>capital político desaprovechado.</strong></p>
        <p>Para solucionar este problema de raíz, he construido un <strong>CRM Político</strong>. Una plataforma centralizada que permite a su equipo:</p>
        <ul>
            <li><strong>Registrar cada interacción al instante</strong>, desde un celular, durante una visita a cualquier pueblo o distrito.</li>
            <li><strong>Saber quién es quién:</strong> Tener fichas detalladas de líderes vecinales, simpatizantes y ciudadanos con sus necesidades específicas.</li>
            <li><strong>Organizar el trabajo territorial</strong> y hacer seguimiento a los compromisos de forma eficiente.</li>
        </ul>
        <p>Mi objetivo es simple: que su equipo dedique menos tiempo a la administración y más tiempo a la acción política efectiva. El MVP de la herramienta está casi listo y me gustaría ofrecerle una <strong>demostración práctica de 15 minutos</strong> para su equipo o para usted.</p>
        <p>Quedo a su disposición.</p>
        <p>
            <strong>{datos['nombre_remitente']}</strong><br>
            Especialista en Optimización de Procesos Digitales<br>
            {datos['telefono_remitente']}
        </p>
        {datos['tracking_pixel']}
        <p style="font-size:12px; color:#777777;">
          Recibes este correo porque considero que esta herramienta puede ser de alto valor estratégico para tu labor.
          Si no deseas recibir futuras comunicaciones, puedes <a href="{datos['unsubscribe_link']}" style="color:#777777;">darte de baja aquí</a>.
        </p>
    </body>
    </html>
    """

    if plantilla_nombre == "visionario":
        return plantilla_visionario
    elif plantilla_nombre == "solucionador":
        return plantilla_solucionador
    else:
        # Una plantilla por defecto por si acaso
        return f"<p>Error: Plantilla '{plantilla_nombre}' no encontrada.</p>"

# -----------------
# 4. LÓGICA DE ENVÍO
# -----------------
def enviar_correos():
    """Función principal que lee el CSV y envía los correos."""
    print("--- INICIANDO PROCESO DE ENVÍO DE CORREOS (v3.0) ---")
    try:
        # Preparamos el log de envíos
        with open(LOG_ENVIOS_CSV, mode='a', newline='', encoding='utf-8') as log_file:
            log_writer = csv.writer(log_file)
            if log_file.tell() == 0:
                log_writer.writerow(['timestamp', 'tracking_id', 'email_destinatario'])

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as servidor:
            servidor.login(MI_EMAIL, MI_CONTRASENA)
            print("Autenticación SMTP correcta.")

            with open(ARCHIVO_CSV_DESTINATARIOS, mode='r', encoding='utf-8') as archivo_destinatarios:
                lector_csv = csv.reader(archivo_destinatarios)
                next(lector_csv)

                for nombre, sexo, apellido, email_destino in lector_csv:
                    saludo = "Estimada" if sexo.upper() == "F" else "Estimado"
                    tracking_id = str(uuid.uuid4())
                    
                    # Guardamos el registro ANTES de enviar
                    with open(LOG_ENVIOS_CSV, mode='a', newline='', encoding='utf-8') as log_file:
                        log_writer = csv.writer(log_file)
                        timestamp_envio = time.strftime("%Y-%m-%d %H:%M:%S")
                        log_writer.writerow([timestamp_envio, tracking_id, email_destino])

                    # Preparamos los datos para la plantilla
                    datos_plantilla = {
                        "saludo": saludo,
                        "apellido": apellido,
                        "nombre_remitente": TU_NOMBRE_REMITENTE,
                        "telefono_remitente": TU_TELEFONO_REMITENTE,
                        "tracking_pixel": f'<img src="{URL_SERVIDOR_TRACKING}/track/{tracking_id}" width="1" height="1" alt="">',
                        "unsubscribe_link": f"{URL_SERVIDOR_TRACKING}/unsubscribe/{tracking_id}" # <-- NUEVO
                    }
                    
                    # Obtenemos el cuerpo del correo de la plantilla activa
                    cuerpo_html = obtener_cuerpo_html(plantilla_activa, datos_plantilla)
                    
                    msg = EmailMessage()
                    msg['Subject'] = "Propuesta Estratégica: CRM Político para la próxima campaña"
                    msg['From'] = MI_EMAIL
                    msg['To'] = email_destino
                    msg.add_alternative(cuerpo_html, subtype='html')

                    servidor.send_message(msg)
                    print(f"✅ Correo enviado a {saludo} {nombre} {apellido} ({email_destino}).")
                    time.sleep(2)

        return "Proceso de envío completado exitosamente."
    except ValueError:
        error_msg = f"❌ ERROR: Revisa tu archivo CSV '{ARCHIVO_CSV_DESTINATARIOS}'. Debe tener 4 columnas: nombre,sexo,apellido,email"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"❌ ERROR INESPERADO DURANTE EL ENVÍO: {e}"
        print(error_msg)
        return error_msg

# -----------------
# 5. LÓGICA DEL SERVIDOR WEB (FastAPI)
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

@app.get("/", response_class=HTMLResponse) # <-- Cambié la ruta del panel a la raíz
async def panel_de_control():
    html_content = """
    <html>
        <head><title>Panel de Control - Envíos YASTA</title>
            <style> body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f2f5; margin: 0; } .container { text-align: center; padding: 40px; background-color: white; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); } button { background-color: #007bff; color: white; border: none; padding: 15px 30px; font-size: 16px; border-radius: 5px; cursor: pointer; margin-bottom: 20px;} .links a { margin: 0 10px; color: #007bff; text-decoration: none; } </style>
        </head>
        <body>
            <div class="container">
                <h1>Panel de Control de Envíos</h1>
                <p>Presiona el botón para iniciar el envío de correos a la lista.</p>
                <form action="/enviar" method="post"><button type="submit">Iniciar Envío de Correos</button></form>
                <div class="links">
                    <a href="/logs/aperturas" target="_blank">Ver Log de Aperturas</a>
                    <a href="/logs/bajas" target="_blank">Ver Log de Bajas</a>
                </div>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/enviar")
async def trigger_send_emails():
    resultado = enviar_correos()
    cargar_tracking_map() # Recargamos el mapa por si se añadieron nuevos envíos
    return HTMLResponse(f"<h1>Proceso de envío finalizado.</h1><p>{html.escape(resultado)}</p><p><a href='/'>Volver al panel</a></p>")

@app.get("/track/{tracking_id}")
async def track_email_open(tracking_id: str, request: Request):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    email_destinatario = tracking_map.get(tracking_id, "ID Desconocido")
    log_line = f"APERTURA | Fecha: {timestamp} | Email: {email_destinatario} | IP: {request.client.host}\n"
    print(f"✅ {log_line.strip()}")
    with open(LOG_APERTURAS_TXT, "a", encoding='utf-8') as f:
        f.write(log_line)
    return Response(content=PIXEL_TRANSPARENTE_GIF, media_type="image/gif")

# --- NUEVO ENDPOINT PARA DARSE DE BAJA ---
@app.get("/unsubscribe/{tracking_id}")
async def unsubscribe_user(tracking_id: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    email_destinatario = tracking_map.get(tracking_id, "ID Desconocido")
    log_line = f"BAJA | Fecha: {timestamp} | Email: {email_destinatario}\n"
    print(f"🚫 {log_line.strip()}")
    with open(LOG_UNSUBSCRIBE_TXT, "a", encoding='utf-8') as f:
        f.write(log_line)
    
    html_page = """
    <html>
        <head><title>Solicitud Procesada</title></head>
        <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
            <h2>Tu solicitud ha sido procesada.</h2>
            <p>Has sido eliminado de nuestra lista de contactos. No recibirás más correos.</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_page, status_code=200)

# --- ENDPOINT MEJORADO PARA VER LOGS ---
@app.get("/logs/{tipo_log}", response_class=HTMLResponse)
async def view_logs(tipo_log: str):
    log_files = {
        "aperturas": {"path": LOG_APERTURAS_TXT, "title": "Log de Aperturas"},
        "bajas": {"path": LOG_UNSUBSCRIBE_TXT, "title": "Log de Bajas (Unsubscribe)"}
    }

    if tipo_log not in log_files:
        return HTMLResponse("<h1>Log no encontrado</h1>", status_code=404)

    log_info = log_files[tipo_log]
    log_content = ""
    try:
        with open(log_info["path"], "r", encoding='utf-8') as f:
            lines = f.readlines()
            lines.reverse()
            log_content = "".join([html.escape(line) for line in lines])
    except FileNotFoundError:
        log_content = f"Aún no se ha registrado ninguna entrada en este log."

    html_page = f"""
    <html>
        <head><title>{log_info['title']}</title><meta http-equiv="refresh" content="30">
            <style> body {{ font-family: monospace; background-color: #1e1e1e; color: #d4d4d4; padding: 20px; }} h1 {{ color: #569cd6; }} pre {{ white-space: pre-wrap; word-wrap: break-word; font-size: 14px;}} a {{color: #ce9178;}}</style>
        </head>
        <body><h1>{log_info['title']} (lo más nuevo arriba)</h1><p><a href="/">Volver al Panel</a></p><pre>{log_content}</pre></body>
    </html>
    """
    return HTMLResponse(content=html_page)