from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from scraper import get_rainfall_metadata, create_animated_video_from_data

app = FastAPI()

# Configuración de CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Definir rutas absolutas respecto a este archivo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# La carpeta static está dentro de backend
STATIC_DIR = os.path.join(BASE_DIR, "static")
# La carpeta frontend está fuera de backend (o un nivel arriba)
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

os.makedirs(STATIC_DIR, exist_ok=True)

# Montar archivos estáticos del sistema (mapas, videos generados)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Montar archivos del frontend (html, js, css)
app.mount("/ui", StaticFiles(directory=FRONTEND_DIR), name="ui")

video_status = {"ready": False, "error": None}

def video_generation_task(top_5, map_path):
    global video_status
    video_status["ready"] = False
    video_status["error"] = None
    try:
        output_path = os.path.join(STATIC_DIR, "historia_lluvias.mp4")
        if os.path.exists(output_path):
            os.remove(output_path)
            
        create_animated_video_from_data(top_5, map_path, output_mp4=output_path)
        video_status["ready"] = True
    except Exception as e:
        print(f"Error en tarea de video: {e}")
        video_status["error"] = str(e)

# Ruta raíz para servir la aplicación
@app.get("/")
async def read_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/api/generar_pieza")
async def generar(background_tasks: BackgroundTasks):
    top_5, texto, imagen_url = get_rainfall_metadata()
    
    # El mapa se descarga en backend/static/mapa_lluvias.jpg
    background_tasks.add_task(video_generation_task, top_5, os.path.join(STATIC_DIR, "mapa_lluvias.jpg"))
    
    return {
        "texto": texto,
        "imagen_url": imagen_url,
        "video_status": "processing"
    }

@app.get("/api/video_status")
def get_video_status():
    if video_status["ready"]:
        return {"status": "ready", "video_url": "/static/historia_lluvias.mp4"}
    if video_status["error"]:
        return {"status": "error", "message": video_status["error"]}
    return {"status": "processing"}
