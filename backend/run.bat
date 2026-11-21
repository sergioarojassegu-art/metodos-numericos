@echo off
echo Iniciando Servidor Backend FastAPI de Metodos Numericos...
cd /d "%~dp0"
call ..\backend_env\Scripts\activate
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
pause
