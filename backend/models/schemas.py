from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

# --- Modelos de Entrada (Requests) ---

class StoppingCriterion(BaseModel):
    criterio: Optional[str] = Field("cifras", description="Criterio de parada: 'cifras' (Cifras significativas), 'tol' (Tolerancia %), o 'it' (Iteraciones máximas)")
    cifras: Optional[int] = Field(None, ge=1, le=16, description="Número de cifras significativas deseadas (m >= 1)")
    tol: Optional[float] = Field(None, gt=0, description="Tolerancia del error porcentual (tol > 0)")
    it: Optional[int] = Field(None, ge=1, description="Número máximo de iteraciones (it >= 1)")

class BiseccionRequest(BaseModel):
    f: str = Field(..., description="Función en términos de x, ej. 'x^3 - x - 2'")
    a: Any = Field(..., description="Límite inferior del intervalo (xl)")
    b: Any = Field(..., description="Límite superior del intervalo (xu)")
    criterio: Optional[str] = Field("cifras", description="'cifras', 'tol', o 'it'")
    cifras: Optional[int] = Field(None, ge=1, le=16, description="Número de cifras significativas")
    tol: Optional[float] = Field(None, gt=0, description="Tolerancia porcentual")
    it: Optional[int] = Field(None, ge=1, description="Número máximo de iteraciones")

class FalsaPosicionRequest(BaseModel):
    f: str = Field(..., description="Función en términos de x, ej. 'x^3 - x - 2'")
    a: Any = Field(..., description="Límite inferior del intervalo (xl)")
    b: Any = Field(..., description="Límite superior del intervalo (xu)")
    criterio: Optional[str] = Field("cifras", description="'cifras', 'tol', o 'it'")
    cifras: Optional[int] = Field(None, ge=1, le=16, description="Número de cifras significativas")
    tol: Optional[float] = Field(None, gt=0, description="Tolerancia porcentual")
    it: Optional[int] = Field(None, ge=1, description="Número máximo de iteraciones")

class SecanteRequest(BaseModel):
    f: str = Field(..., description="Función en términos de x, ej. 'x^3 - x - 2'")
    x0: Any = Field(..., description="Punto inicial x_(i-1)")
    x1: Any = Field(..., description="Punto inicial x_i")
    criterio: Optional[str] = Field("cifras", description="'cifras', 'tol', o 'it'")
    cifras: Optional[int] = Field(None, ge=1, le=16, description="Número de cifras significativas")
    tol: Optional[float] = Field(None, gt=0, description="Tolerancia porcentual")
    it: Optional[int] = Field(None, ge=1, description="Número máximo de iteraciones")

class NewtonRaphsonRequest(BaseModel):
    f: str = Field(..., description="Función en términos de x, ej. 'x^3 - x - 2'")
    df: Optional[str] = Field(None, description="Derivada f'(x). Si se omite, se calcula simbólicamente")
    x0: Any = Field(..., description="Punto inicial x0")
    criterio: Optional[str] = Field("cifras", description="'cifras', 'tol', o 'it'")
    cifras: Optional[int] = Field(None, ge=1, le=16, description="Número de cifras significativas")
    tol: Optional[float] = Field(None, gt=0, description="Tolerancia porcentual")
    it: Optional[int] = Field(None, ge=1, description="Número máximo de iteraciones")

class TrapecioRequest(BaseModel):
    f: str = Field(..., description="Función f(x)")
    a: Any = Field(..., description="Límite inferior de integración (número o expresión como 'pi')")
    b: Any = Field(..., description="Límite superior de integración (número o expresión como 'pi')")
    n: Optional[int] = Field(default=None, description="Número de subintervalos (n >= 1)")
    criterio: Optional[str] = Field("cifras", description="'cifras', 'tol', o 'it'")
    cifras: Optional[int] = Field(None, ge=1, le=16, description="Número de cifras significativas")
    tol: Optional[float] = Field(None, gt=0, description="Tolerancia porcentual")
    it: Optional[int] = Field(None, ge=1, description="Número de iteraciones / subintervalos máximos")

class Simpson13Request(BaseModel):
    f: str = Field(..., description="Función f(x)")
    a: Any = Field(..., description="Límite inferior de integración (número o expresión como 'pi')")
    b: Any = Field(..., description="Límite superior de integración (número o expresión como 'pi')")
    n: Optional[int] = Field(default=None, description="Número de subintervalos (debe ser par y >= 2)")
    criterio: Optional[str] = Field("cifras", description="'cifras', 'tol', o 'it'")
    cifras: Optional[int] = Field(None, ge=1, le=16, description="Número de cifras significativas")
    tol: Optional[float] = Field(None, gt=0, description="Tolerancia porcentual")
    it: Optional[int] = Field(None, ge=1, description="Número de iteraciones / subintervalos máximos")

class Simpson38Request(BaseModel):
    f: str = Field(..., description="Función f(x)")
    a: Any = Field(..., description="Límite inferior de integración (número o expresión como 'pi')")
    b: Any = Field(..., description="Límite superior de integración (número o expresión como 'pi')")
    n: Optional[int] = Field(default=None, description="Número de subintervalos (múltiplo de 3 y >= 3)")
    criterio: Optional[str] = Field("cifras", description="'cifras', 'tol', o 'it'")
    cifras: Optional[int] = Field(None, ge=1, le=16, description="Número de cifras significativas")
    tol: Optional[float] = Field(None, gt=0, description="Tolerancia porcentual")
    it: Optional[int] = Field(None, ge=1, description="Número de iteraciones / subintervalos máximos")

class InterpolacionDirectaRequest(BaseModel):
    x: List[float] = Field(..., description="Lista de puntos en x")
    y: List[float] = Field(..., description="Lista de puntos en y")
    xe: float = Field(..., description="Punto x donde se desea evaluar el polinomio")

class RegresionLinealRequest(BaseModel):
    x: List[float] = Field(..., description="Lista de puntos en x")
    y: List[float] = Field(..., description="Lista de puntos en y")
    mod: str = Field(default="Lineal", description="Modelo: 'Lineal', 'Polinomial', 'Exponencial', 'Potencia'")
    g: Optional[int] = Field(default=1, ge=1, description="Grado del polinomio si el modelo es Polinomial (g >= 1)")
    xe: Optional[float] = Field(None, description="Punto x donde se desea evaluar el modelo ajustado")

class SeccionDoradaRequest(BaseModel):
    tipo: str = Field(default="Univariada", description="'Univariada' o 'Multivariada'")
    obj: str = Field(default="Minimizar", description="'Minimizar' o 'Maximizar'")
    # Campos univariada
    f: Optional[str] = Field(None, description="Función f(x) para univariada")
    a: Optional[Any] = Field(None, description="Límite inferior para univariada (xl)")
    b: Optional[Any] = Field(None, description="Límite superior para univariada (xu)")
    # Campos multivariada
    fm: Optional[str] = Field(None, description="Función multivariada f(x, y, ...)")
    vars: Optional[List[str]] = Field(None, description="Nombres de las variables, ej. ['x', 'y']")
    lo: Optional[List[Any]] = Field(None, description="Límites inferiores por variable")
    hi: Optional[List[Any]] = Field(None, description="Límites superiores por variable")
    # Criterios comunes
    criterio: Optional[str] = Field("cifras", description="'cifras', 'tol' o 'it'")
    cifras: Optional[int] = Field(None, ge=1, le=16, description="Cifras significativas")
    tol: Optional[float] = Field(None, gt=0, description="Tolerancia porcentual")
    it: Optional[int] = Field(None, ge=1, description="Iteraciones máximas")

# --- Modelos de Salida (Responses) ---

class NumericalResponse(BaseModel):
    success: bool
    method: str
    converged: Optional[bool] = Field(None, description="Indica si el método convergió exitosamente")
    summary: Dict[str, Any] = Field(..., description="Resumen estadístico del método")
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="Pasos e iteraciones detalladas")
    plot_data: Dict[str, Any] = Field(default_factory=dict, description="Datos procesados para graficar")
    details: Optional[str] = None
