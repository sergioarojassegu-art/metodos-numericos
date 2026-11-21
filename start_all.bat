@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
echo ===================================================
echo   Laboratorio de Métodos Numéricos - Inicio
echo ===================================================

cd /d "%~dp0"

:: 1. Detectar o configurar entorno virtual de Python
set "PYTHON_EXE="
if exist "%~dp0backend_env\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0backend_env\Scripts\python.exe"
    echo [OK] Entorno virtual detectado en backend_env.
) else (
    echo [AVISO] No se encontró la carpeta 'backend_env'. Verificando Python del sistema...
    where python >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python no está instalado ni en el PATH del sistema.
        echo Por favor instale Python 3.10+ y cree el entorno ejecutando:
        echo   python -m venv backend_env
        echo   backend_env\Scripts\pip install -r requirements.txt
        pause
        exit /b 1
    ) else (
        echo Creando automáticamente el entorno virtual 'backend_env'...
        python -m venv backend_env
        if errorlevel 1 (
            echo [ERROR] No se pudo crear el entorno virtual. Usando Python del sistema.
            set "PYTHON_EXE=python"
        ) else (
            set "PYTHON_EXE=%~dp0backend_env\Scripts\python.exe"
            echo Instalando dependencias en backend_env...
            "%PYTHON_EXE%" -m pip install --upgrade pip
            "%PYTHON_EXE%" -m pip install -r requirements.txt
        )
    )
)

echo Iniciando Backend FastAPI en el puerto 8000...
start "Backend FastAPI" cmd /k "cd /d "%~dp0" && "%PYTHON_EXE%" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

timeout /t 2 >nul

echo Iniciando Frontend Web en el puerto 5173...
start "Frontend Web" cmd /k "cd /d "%~dp0\frointed\dist" && "%PYTHON_EXE%" -m http.server 5173"

timeout /t 1 >nul
start http://127.0.0.1:5173

echo ===================================================
echo Servidores iniciados correctamente en segundo plano.
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:5173
echo ===================================================
