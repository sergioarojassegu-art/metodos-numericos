import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from routers import raices, integracion, interpolacion, optimizacion

app = FastAPI(
    title="API de Métodos Numéricos",
    description="Backend robusto y desacoplado donde cada endpoint está dedicado exclusivamente a un solo método numérico.",
    version="1.0.0"
)

# Configuración de CORS permitiendo orígenes seguros y desarrollo
allowed_origins = [
    "https://frontend-seven-ruddy-69.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
env_frontend_url = os.environ.get("FRONTEND_URL")
if env_frontend_url and env_frontend_url not in allowed_origins:
    allowed_origins.append(env_frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if os.environ.get("STRICT_CORS") == "true" else ["*"],
    allow_origin_regex=r"https://frontend.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manejador global para errores de valor y validación de expresiones matemáticas
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "success": False}
    )

# Manejador para formatear errores de validación de Pydantic con mensajes comprensibles
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        msg = err.get("msg", "")
        if "greater than or equal to 1" in msg or "greater than 0" in msg:
            errors.append(f"El campo '{field}' debe ser un valor positivo válido.")
        else:
            errors.append(f"Error en el campo '{field}': {msg}")
    
    clean_message = " | ".join(errors) if errors else "Error de validación en los datos enviados."
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": clean_message, "success": False}
    )

# Registro de routers por categoría y método
app.include_router(raices.router)
app.include_router(integracion.router)
app.include_router(interpolacion.router)
app.include_router(optimizacion.router)

@app.get("/api/info")
def read_root():
    return {
        "status": "online",
        "message": "Bienvenido a la API de Métodos Numéricos.",
        "documentation": "/docs"
    }

# Servir Frontend React compilado si existe
dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
assets_path = os.path.join(dist_path, "assets")

if os.path.isdir(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    if full_path.startswith("raices") or full_path.startswith("integracion") or full_path.startswith("interpolacion") or full_path.startswith("optimizacion") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
        pass
    file_candidate = os.path.join(dist_path, full_path)
    if full_path and os.path.isfile(file_candidate):
        return FileResponse(file_candidate)
    index_file = os.path.join(dist_path, "index.html")
    if os.path.isfile(index_file):
        return FileResponse(index_file)
    return {"message": "API de Métodos Numéricos activa. Accede a /docs"}
