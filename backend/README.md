# Backend de Métodos Numéricos con FastAPI

Backend modular en Python utilizando **FastAPI**, donde **cada endpoint está dedicado exclusivamente a un solo método numérico**, extrayendo e implementando fielmente los algoritmos del cuaderno [metodos_numericos.ipynb](file:///c:/Users/USUARIO/Documents/Metodos%20numericos/metodos_numericos.ipynb).

---

## 📁 Arquitectura del Backend

```text
backend/
├── main.py                     # Instancia principal de FastAPI y configuración de CORS
├── requirements.txt            # Dependencias del backend (fastapi, uvicorn, numpy, scipy, sympy)
├── run.bat                     # Script de inicio rápido del servidor
├── models/
│   ├── __init__.py
│   └── schemas.py              # Validación de entradas (Pydantic) y esquemas de respuesta
├── utils/
│   ├── __init__.py
│   └── math_parser.py          # Parser seguro y cálculo de derivadas analíticas con SymPy
└── routers/
    ├── __init__.py
    ├── raices.py               # Endpoints para métodos de raíces
    ├── integracion.py          # Endpoints para métodos de integración numérica
    ├── interpolacion.py        # Endpoints para interpolación y regresión
    └── optimizacion.py         # Endpoints para métodos de optimización
```

---

## 🚀 Endpoints Dedicados (1 Método = 1 Endpoint)

### 1. Métodos de Raíces (`/raices`)
- `POST /raices/biseccion`: Bisección con cálculo de error relativo porcentual.
- `POST /raices/falsa-posicion`: Regula Falsi respetando el signo de \(f(a)\) y \(f(b)\).
- `POST /raices/secante`: Método de la secante con dos puntos \(x_0, x_1\).
- `POST /raices/newton-raphson`: Newton-Raphson con soporte de derivada automática (SymPy) o manual.

### 2. Métodos de Integración Numérica (`/integracion`)
- `POST /integracion/trapecio`: Regla del trapecio compuesta con subintervalos \(n\).
- `POST /integracion/simpson-13`: Simpson 1/3 (requiere \(n\) par).
- `POST /integracion/simpson-38`: Simpson 3/8 (requiere \(n\) múltiplo de 3).

### 3. Interpolación y Ajuste (`/interpolacion`)
- `POST /interpolacion/directa`: Matriz de Vandermonde / polinomio interpolante evaluado en \(x_e\).
- `POST /interpolacion/regresion`: Ajuste por mínimos cuadrados (Lineal, Polinomial, Exponencial, Potencia) con \(R^2\) y error cuadrático (\(SSE\)).

### 4. Métodos de Optimización (`/optimizacion`)
- `POST /optimizacion/seccion-dorada`: Búsqueda de la razón áurea tanto univariada como multivariada por coordenadas cíclicas (max/min).

---

## 🛠️ Cómo Ejecutar el Servidor

1. **Activar el entorno virtual e iniciar:**
   ```powershell
   .\backend_env\Scripts\activate
   uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
   *O simplemente haz doble clic en `backend/run.bat`.*

2. **Documentación Swagger interactiva:**
   Abre en tu navegador: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
