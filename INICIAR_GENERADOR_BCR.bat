@echo off
TITLE Generador BCR Lluvias v2.0
echo ============================================
echo   INICIANDO GENERADOR DE LLUVIAS BCR
echo ============================================
echo.
echo 1. Encendiendo el servidor unificado...
echo.
echo (No cierres esta ventana mientras uses la app)

cd /d "%~dp0backend"

:: Iniciamos el navegador cargando la URL del servidor local en lugar del archivo
:: Esperamos 2 segundos para asegurar que el servidor este levantando
start "" http://127.0.0.1:8000

python -m uvicorn app:app --host 127.0.0.1 --port 8000
pause
