# Laboratorio de Métodos Numéricos

Proyecto completo e interactivo para la resolución paso a paso de los 11 métodos numéricos exigidos por la rúbrica oficial.

**Autores:** Sergio Rojas y Braiyan Murcia

---

## 🚀 Requisitos Previos

- **Python**: 3.10 o superior (recomendado 3.11 o 3.12).
- **Node.js**: 18.0 o superior con `npm`.

---

## 🛠️ Instalación y Ejecución

### 1. Clonar o descomprimir el proyecto
Abre una terminal en la carpeta raíz del proyecto.

### 2. Configurar el Backend (Python / FastAPI)

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual:
# En Windows (cmd/PowerShell):
.\venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor backend en el puerto 8000
python -m uvicorn backend.main:app --reload --port 8000
```
El backend estará disponible en: [http://127.0.0.1:8000](http://127.0.0.1:8000)
Documentación interactiva Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Configurar el Frontend (React / Vite)

En una nueva terminal:

```bash
cd frointed

# Instalar dependencias
npm install

# Iniciar en modo desarrollo
npm run dev
```
La aplicación web estará disponible en: [http://localhost:5173](http://localhost:5173)

*(Alternativamente, al compilar con `npm run build`, FastAPI sirve directamente la interfaz estática desde [http://127.0.0.1:8000](http://127.0.0.1:8000))*.

---

## 📊 Métodos Numéricos Implementados

1. **Raíces de Ecuaciones No Lineales**:
   - Bisección
   - Falsa Posición (Regula Falsi)
   - Secante
   - Newton-Raphson

2. **Integración Numérica**:
   - Regla del Trapecio
   - Regla de Simpson 1/3
   - Regla de Simpson 3/8

3. **Interpolación y Ajuste de Curvas**:
   - Interpolación Polinómica Directa (Sistema de Vandermonde)
   - Regresión por Mínimos Cuadrados (Lineal, Polinomial, Exponencial, Potencia)

4. **Optimización No Lineal**:
   - Sección Áurea Univariada (Máximo / Mínimo)
   - Sección Áurea Multivariada (Por coordenadas, Máximo / Mínimo)
