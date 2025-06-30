# ==============================================================================
# SERVIDOR COMPLETO DE ENVÍO Y TRACKING DE CORREOS - v3.1
# Con "preheader" optimizado para la bandeja de entrada.
# ==============================================================================

# ... (todos los imports son los mismos) ...
import csv, smtplib, ssl, time, uuid, os, datetime, html
from email.message import EmailMessage
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response

# -----------------
# 2. CONFIGURACIÓN
# -----------------
MI_EMAIL = "restucciaduilio@gmail.com"
MI_CONTRASENA = "qsrtwnhdmplhtqev"
ARCHIVO_CSV_DESTINATARIOS = "somos_peru.csv"
LOG_ENVIOS_CSV = "log_envios.csv"
LOG_APERTURAS_TXT = "log_aperturas.txt"
LOG_UNSUBSCRIBE_TXT = "log_unsubscribe.txt"

TU_NOMBRE_REMITENTE = "Duilio Restuccia" # <-- ¡Rellena esto!
TU_TELEFONO_REMITENTE = "WhatsApp: 974089434"      # <-- ¡Rellena esto!

URL_SERVIDOR_TRACKING = "https://correos.yasta.cloud"

LINKEDIN_LINK ="https://www.linkedin.com/in/duiliorestuccia/"

# ========= ¡NUEVA CONFIGURACIÓN DEL GANCHO! =========
# Elige una de estas opciones o escribe la tuya. Este texto aparecerá en la bandeja de entrada.
PREHEADER_TEXT = "Bicameralidad 2026"


# ----------------------------------------------------
# 3. PLANTILLAS DE CORREO HTML (VERSIÓN REVISADA v3.3)
# ----------------------------------------------------

plantilla_activa = "visual" # Elige "directo" o "visual"

def obtener_cuerpo_html(plantilla_nombre, datos):
    """Genera el HTML del correo con el gancho al principio y el link de LinkedIn integrado."""

    # --- Plantilla 1: El Directo y Ejecutivo (CON LINKEDIN INTEGRADO) ---
    plantilla_directo = f"""
    <!DOCTYPE html>
    <html>
    <body>
        <!-- Preheader oculto -->
        <span style="display:none; font-size:1px; color:#ffffff; line-height:1px; max-height:0px; max-width:0px; opacity:0; overflow:hidden;">
            {datos['preheader_text']}
        </span>
        
        <div style="font-family: Arial, sans-serif; font-size: 16px; line-height: 1.6;">
            <p>{datos['saludo']} Congresista {datos['nombre']} {datos['apellido']},</p>

            <!-- ======================= LÍNEA MODIFICADA ======================= -->
            <p>Mi nombre es {datos['nombre_remitente']}, soy <a href="{datos['linkedin_link']}" style="color: #007bff; text-decoration: none;">consultor tecnológico</a> y le escribo para presentarle una herramienta estratégica diseñada para las próximas elecciones.</p>
            <!-- ================================================================ -->
            
            <p><strong>El objetivo es darle una ventaja competitiva a USted como Congesista (futuro Diputado o Senador) y a su agrupación política, permitiéndoles:</strong></p>
            <ul style="padding-left: 20px;">
                <li><strong>Fidelizar simpatizantes:</strong> Unificar en una base de datos propia cada contacto, líder y necesidad ciudadana.</li>
                <li><strong>Medir el impacto real</strong> de su trabajo en campo y optimizar su estrategia territorial.</li>
                <li><strong>Movilizar sus bases</strong> de forma directa y ágil, sin intermediarios, con una plataforma de comunicación directa (sin usar WhatsApp, ni SMS).</li>
            </ul>

            <p>El próximo escenario político exigirá herramientas de este nivel -basado en datos- para asegurar todo tipo de éxitos electorales. Me encantaría ofrecerle una <strong>sesión estratégica privada de 15 minutos</strong>.</p>
            <p>Solo escríbame.</p>
            <p>Un cordial saludo,</p>
            <p>
                <strong>{datos['nombre_remitente']}</strong><br>
                Consultor Estratégico en Tecnología<br>
                {datos['telefono_remitente']}
            </p>
            {datos['tracking_pixel']}
            <p style="font-size:12px; color:#777777;">
              Recibes este correo porque considero que esta herramienta puede ser de alto valor.
              Si no deseas recibir futuras comunicaciones, puedes <a href="{datos['unsubscribe_link']}" style="color:#777777;">darte de baja aquí</a>.
            </p>
        </div>
    </body>
    </html>
    """
    
    # --- Plantilla 2: El Visual con Headline ---
    # Usa un titular para ser aún más disruptivo y fácil de escanear.
    plantilla_visual = f"""
    <!DOCTYPE html>
    <html>
    <body>
        <!-- Preheader oculto -->
        <span style="display:none; font-size:1px; color:#ffffff; line-height:1px; max-height:0px; max-width:0px; opacity:0; overflow:hidden;">
            {datos['preheader_text']}
        </span>
        
        <div style="font-family: Arial, sans-serif; font-size: 16px; line-height: 1.6;">
            <p>{datos['saludo']} Congresista {datos['nombre']} {datos['apellido']},</p>
            <p>Soy {datos['nombre_remitente']}, <a href="{datos['linkedin_link']}" style="color: #007bff; text-decoration: none;">consultor tecnológico</a>.</p>

            <div style="border-left: 3px solid #007bff; padding-left: 15px; margin: 20px 0;">
                <h3 style="margin-top: 0;">Una Ventaja Estratégica para la Bicameralidad 2026 y Eleccione Geneales</h3>
                <p style="margin-bottom: 0;">He desarrollado un CRM Político que le permite <strong>centralizar su data, medir su impacto y movilizar a sus electores</strong> de forma directa.</p>
            </div>

            <p>El retorno a la bicameralidad y las elecciones generales demandarán una gestión de electorado más inteligente y ágil. Esta herramienta, que le permitirá hacer Analítica de Datos, está diseñada precisamente para ese desafío.</p>
            <p>Le propongo una <strong>demostración privada de 15 minutos</strong> para explorar cómo puede beneficiar su trabajo, el de su agrupación y su próxima campaña.</p>

            <p>Quedo a su disposición, solo escríbame.</p>
            <p>
                <strong>{datos['nombre_remitente']}</strong><br>
                Consultor Estratégico en Tecnología<br>
                {datos['telefono_remitente']}
            </p>
            {datos['tracking_pixel']}
            <p style="font-size:12px; color:#777777;">
              Recibes este correo porque considero que esta herramienta puede ser de alto valor.
              Si no deseas recibir futuras comunicaciones, puedes <a href="{datos['unsubscribe_link']}" style="color:#777777;">darte de baja aquí</a>.
            </p>
        </div>
    </body>
    </html>
    """

    if plantilla_nombre == "directo":
        return plantilla_directo
    elif plantilla_nombre == "visual":
        return plantilla_visual
    else:
        return "<p>Error: Plantilla no encontrada.</p>"

# -----------------
# 4. LÓGICA DE ENVÍO (Actualizada para pasar el preheader)
# -----------------
def enviar_correos():
    """Función principal que lee el CSV y envía los correos."""
    print("--- INICIANDO PROCESO DE ENVÍO DE CORREOS (v3.1) ---")
    try:
        # ... (la lógica de apertura de logs y smtp es la misma) ...
        # ... conexión, login, etc ...
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as servidor:
            servidor.login(MI_EMAIL, MI_CONTRASENA)
            print("Autenticación SMTP correcta.")

            with open(ARCHIVO_CSV_DESTINATARIOS, mode='r', encoding='utf-8') as archivo_destinatarios:
                lector_csv = csv.reader(archivo_destinatarios)
                next(lector_csv)

                for nombre, sexo, apellido, email_destino in lector_csv:
                    # ... (lógica de saludo, tracking_id, guardado en log es la misma) ...
                    saludo = "Estimada" if sexo.upper() == "F" else "Estimado"
                    tracking_id = str(uuid.uuid4())
                    
                    with open(LOG_ENVIOS_CSV, mode='a', newline='', encoding='utf-8') as log_file:
                        log_writer = csv.writer(log_file)
                        timestamp_envio = time.strftime("%Y-%m-%d %H:%M:%S")
                        log_writer.writerow([timestamp_envio, tracking_id, email_destino])
                    
                    # Preparamos los datos para la plantilla, INCLUYENDO EL PREHEADER
                    datos_plantilla = {
                        "preheader_text": PREHEADER_TEXT, # <-- NUEVO
                        "saludo": saludo,
                        "nombre": nombre,
                        "apellido": apellido,
                        "nombre_remitente": TU_NOMBRE_REMITENTE,
                        "telefono_remitente": TU_TELEFONO_REMITENTE,
                        "linkedin_link": LINKEDIN_LINK,
                        "tracking_pixel": f'<img src="{URL_SERVIDOR_TRACKING}/track/{tracking_id}" width="1" height="1" alt="">',
                        "unsubscribe_link": f"{URL_SERVIDOR_TRACKING}/unsubscribe/{tracking_id}"
                    }
                    
                    cuerpo_html = obtener_cuerpo_html(plantilla_activa, datos_plantilla)
                    
                    msg = EmailMessage()
                    msg['Subject'] = "CRM Político para la próxima campaña"
                    msg['From'] = f"{TU_NOMBRE_REMITENTE} <{MI_EMAIL}>"
                    msg['To'] = email_destino
                    msg.add_alternative(cuerpo_html, subtype='html')

                    servidor.send_message(msg)
                    print(f"✅ Correo enviado a {saludo} {nombre} {apellido} ({email_destino}).")
                    time.sleep(2)

        return "Proceso de envío completado exitosamente."
    except Exception as e:
        # ... (manejo de errores es el mismo) ...
        error_msg = f"❌ ERROR INESPERADO DURANTE EL ENVÍO: {e}"
        print(error_msg)
        return error_msg

# -----------------
# 5. LÓGICA DEL SERVIDOR WEB (FastAPI)
# -----------------
# (Esta parte del código no necesita cambios, es idéntica a la versión anterior)
# ...
# ... (cargar_tracking_map, lifespan, panel_de_control, trigger_send_emails, track_email_open, unsubscribe_user, view_logs)
# ...

# --- El resto de tu código FastAPI sigue aquí tal cual ---
# Por brevedad, no lo repito, pero debes mantenerlo.
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

@app.get("/", response_class=HTMLResponse)
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
    cargar_tracking_map()
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