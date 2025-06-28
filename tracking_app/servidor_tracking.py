from fastapi import FastAPI, Request
from fastapi.responses import Response
import datetime
import csv
import os

LOG_ENVIOS_CSV = "log_envios.csv"
LOG_APERTURAS_TXT = "log_aperturas.txt" # Archivo incremental de resultados
PIXEL_TRANSPARENTE_GIF = b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"

app = FastAPI()

# Creamos un diccionario para cargar los IDs y tener una búsqueda rápida
tracking_map = {}

def cargar_tracking_map():
    """Carga los datos del CSV a un diccionario en memoria para búsquedas rápidas."""
    if not os.path.exists(LOG_ENVIOS_CSV):
        print(f"Advertencia: El archivo '{LOG_ENVIOS_CSV}' no existe. No se podrá identificar a los destinatarios.")
        return
    
    with open(LOG_ENVIOS_CSV, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        # Saltamos la cabecera si existe
        try:
            next(reader)
        except StopIteration:
            return # Archivo vacío
            
        for row in reader:
            # row[1] es el tracking_id, row[2] es el email
            if len(row) >= 3:
                tracking_map[row[1]] = row[2]
    print(f"Mapa de seguimiento cargado con {len(tracking_map)} registros.")


@app.on_event("startup")
async def startup_event():
    """Esta función se ejecuta cuando el servidor FastAPI arranca."""
    cargar_tracking_map()


@app.get("/track/{tracking_id}")
async def track_email_open(tracking_id: str, request: Request):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client_ip = request.client.host
    user_agent = request.headers.get('user-agent', 'N/A')
    
    # Buscamos el email correspondiente al ID
    email_destinatario = tracking_map.get(tracking_id, "ID Desconocido")
    
    # Creamos la línea de log que vamos a guardar
    log_line = f"APERTURA | Fecha: {timestamp} | Email: {email_destinatario} | IP: {client_ip} | ID: {tracking_id} | User-Agent: {user_agent}\n"
    
    # Imprimimos en la consola del servidor (para feedback inmediato)
    print(f"✅ {log_line.strip()}")
    
    # Guardamos la línea en el archivo de texto de forma incremental
    with open(LOG_APERTURAS_TXT, "a", encoding='utf-8') as f:
        f.write(log_line)
    
    # Devolvemos la imagen invisible
    return Response(content=PIXEL_TRANSPARENTE_GIF, media_type="image/gif")

@app.get("/")
async def root():
    return {"message": "Servidor de tracking funcionando."}