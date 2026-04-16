@echo off
TITLE Generador BCR Lluvias
echo ============================================
echo   INICIANDO GENERADOR DE LLUVIAS BCR
echo ============================================
echo.
echo 1. Abriendo la interfaz en el navegador...
start "" "%~dp0frontend\index.html"

echo 2. Encendiendo el servidor de datos...
echo (No cierres esta ventana mientras uses la app)
echo.
cd /d "%~dp0backend"
python -m uvicorn app:app --host 127.0.0.1 --port 8000
pause
