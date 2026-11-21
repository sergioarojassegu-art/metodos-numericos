@echo off
echo Iniciando Servidor Frontend...
cd /d "%~dp0\frointed\dist"
python -m http.server 5173
pause
