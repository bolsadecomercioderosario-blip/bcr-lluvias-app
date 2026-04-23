from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from scraper import get_rainfall_metadata, create_animated_video_from_data

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Definir rutas absolutas respecto a este archivo (backend/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# La carpeta static ahora contendrá tanto archivos del sistema como la UI
STATIC_DIR = os.path.join(BASE_DIR, "static")
# Nueva ruta consolidada para el frontend
FRONTEND_DIR = os.path.join(STATIC_DIR, "ui")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(FRONTEND_DIR, exist_ok=True)

# 1. Endpoints de API (Primero para evitar que el mount los tape)
@app.get("/api/generar_pieza")
async def generar(background_tasks: BackgroundTasks):
    top_5, texto, imagen_url = get_rainfall_metadata()
    # Path local para el mapa
    map_local_path = os.path.join(STATIC_DIR, "mapa_lluvias.jpg")
    background_tasks.add_task(video_generation_task, top_5, map_local_path)
    return {
        "texto": texto,
        "imagen_url": imagen_url,
        "video_status": "processing"
    }

@app.get("/api/video_status")
def get_video_status():
    if video_status["ready"]:
        return {"status": "ready", "video_url": video_status["url"]}
    if video_status["error"]:
        return {"status": "error", "message": video_status["error"]}
    return {"status": "processing"}

# 2. Archivos estáticos del sistema (Mapas/Videos)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 3. Frontend unificado (Servido desde la raíz)
# Al estar dentro de static/ui, es totalmente autónomo en Render
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

video_status = {"ready": False, "error": None, "url": None}

def video_generation_task(top_5, map_path):
    global video_status
    video_status["ready"] = False
    video_status["error"] = None
    try:
        import time
        timestamp = int(time.time())
        filename = f"historia_lluvias_{timestamp}.mp4"
        output_path = os.path.join(STATIC_DIR, filename)
        
        # Cleanup old videos (optional but recommended)
        for f in os.listdir(STATIC_DIR):
            if f.startswith("historia_lluvias_") and f.endswith(".mp4"):
                try:
                    os.remove(os.path.join(STATIC_DIR, f))
                except:
                    pass
            
        create_animated_video_from_data(top_5, map_path, output_mp4=output_path)
        video_status["url"] = f"/static/{filename}"
        video_status["ready"] = True
    except Exception as e:
        print(f"Error en tarea de video: {e}")
        video_status["error"] = str(e)
