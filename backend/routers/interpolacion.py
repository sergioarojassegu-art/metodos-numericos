import math
import warnings
import numpy as np
from fastapi import APIRouter, HTTPException
from models.schemas import (
    InterpolacionDirectaRequest,
    RegresionLinealRequest,
    NumericalResponse
)

router = APIRouter(prefix="/interpolacion", tags=["Métodos de Interpolación y Ajuste"])

@router.post("/directa", response_model=NumericalResponse)
def resolver_interpolacion_directa(req: InterpolacionDirectaRequest):
    """
    Interpolación polinómica directa según rúbrica:
    Polinomio de grado n con n+1 puntos, resolviendo el sistema.
    Muestra: datos cargados, coeficientes, ecuación del polinomio,
    gráfica de los datos con la curva ajustada y evaluación en un x dado (xe).
    """
    x = np.array(req.x, dtype=float)
    y = np.array(req.y, dtype=float)

    if len(x) != len(y):
        raise HTTPException(status_code=400, detail="Las listas x e y deben tener la misma longitud.")
    if len(x) < 2:
        raise HTTPException(status_code=400, detail="Se requieren al menos 2 puntos para interpolar.")
    if len(np.unique(x)) != len(x):
        raise HTTPException(status_code=400, detail="Los valores de x deben ser todos distintos entre sí para interpolación directa.")

    n = len(x)
    degree = n - 1

    # Resolver el sistema Vandermonde V * a = y para obtener los coeficientes del polinomio exacto
    try:
        # V[:, j] = x**(degree - j)
        V = np.vander(x, n)
        coeffs = np.linalg.solve(V, y)
    except np.linalg.LinAlgError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error en Interpolación Directa: El sistema de ecuaciones Vandermonde no tiene solución única (matriz singular o mal condicionada). Detalle: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error resolviendo el sistema de Vandermonde para interpolación directa: {str(e)}"
        )

    poly = np.poly1d(coeffs)
    xe = float(req.xe)
    ye = float(poly(xe))

    # Formatear ecuación limpia: p(x) = c_n*x^n + ... + c_0
    terms = []
    for deg_idx, c in enumerate(coeffs):
        power = degree - deg_idx
        if abs(c) > 1e-9:
            sign = "+ " if (c > 0 and terms) else ("- " if c < 0 and terms else ("-" if c < 0 else ""))
            c_abs = abs(c)
            c_str = f"{c_abs:.4f}".rstrip('0').rstrip('.')
            if power == 0:
                terms.append(f"{sign}{c_str}")
            elif power == 1:
                terms.append(f"{sign}{c_str}*x")
            else:
                terms.append(f"{sign}{c_str}*x^{power}")
    poly_str = " ".join(terms) if terms else "0"

    steps = []
    for i in range(n):
        # Evaluación de la fila correspondiente del sistema de Vandermonde y término polinómico
        row_vander = [f"{float(x[i])**(degree - j):.4g}" for j in range(n)]
        vander_str = "[" + ", ".join(row_vander) + "]"
        calc_term = float(poly(x[i]))
        steps.append({
            "i": i + 1,
            "xᵢ": round(float(x[i]), 6),
            "yᵢ": round(float(y[i]), 6),
            "Fila Vandermonde V[i,:]": vander_str,
            "P(xᵢ) calculado": round(calc_term, 6)
        })

    x_min, x_max = min(np.min(x), xe), max(np.max(x), xe)
    margin = abs(x_max - x_min) * 0.2 if x_max != x_min else 1.0
    x_curve = np.linspace(x_min - margin, x_max + margin, 180).tolist()
    y_curve = [float(poly(val)) for val in x_curve]

    # Coeficientes legibles
    coeffs_dict = {f"a_{degree - i}": round(float(c), 6) for i, c in enumerate(coeffs)}

    return NumericalResponse(
        success=True,
        method="Interpolación Directa",
        converged=True,
        summary={
            "Valor interpolado p(x)": round(ye, 6),
            "Punto evaluado (x)": xe,
            "Grado del polinomio": degree,
            "Puntos cargados": n,
            "Ecuación del polinomio": f"p(x) = {poly_str}"
        },
        steps=steps,
        plot_data={
            "x_points": x.tolist(),
            "y_points": y.tolist(),
            "x_eval": xe,
            "y_eval": ye,
            "x_curve": x_curve,
            "y_curve": y_curve,
            "polynomial": f"p(x) = {poly_str}",
            "coefficients": coeffs_dict,
            "x_label": "x",
            "y_label": "y = p(x)"
        },
        details=f"Polinomio obtenido: p(x) = {poly_str} | Evaluación: p({xe}) = {ye:.6f}"
    )

@router.post("/regresion", response_model=NumericalResponse)
def resolver_regresion(req: RegresionLinealRequest):
    """
    Regresión por mínimos cuadrados según rúbrica:
    - Datos cargados.
    - Coeficientes o ecuación y coeficiente de determinación R².
    - Gráfica de los datos con la curva ajustada.
    - Evaluación en un x dado (opcional si provisto en req.xe).
    - Selector del polinomio (Lineal, Polinomial grado g, Exponencial, Potencia).
    """
    x = np.array(req.x, dtype=float)
    y = np.array(req.y, dtype=float)

    if len(x) != len(y):
        raise HTTPException(status_code=400, detail="Las listas x e y deben tener la misma longitud.")
    if len(x) < 2:
        raise HTTPException(status_code=400, detail="Se necesitan al menos 2 datos para la regresión.")

    unique_x = np.unique(x)
    if len(unique_x) < 2:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Los valores de x no pueden ser todos iguales (todos los puntos tienen x = {x[0]}). "
                "Una línea vertical tiene pendiente infinita o indeterminada, por lo que el problema está "
                "mal condicionado y no admite una función de regresión unívoca."
            )
        )

    n = len(x)
    model = (req.mod or "Lineal").capitalize()
    formula_str = ""
    y_pred = np.zeros(n)
    coeffs_dict = {}

    def safe_polyfit(x_data, y_data, deg):
        try:
            rank_warning_cls = getattr(getattr(np, "exceptions", None), "RankWarning", UserWarning)
            with warnings.catch_warnings():
                warnings.simplefilter("error", rank_warning_cls)
                return np.polyfit(x_data, y_data, deg)
        except Exception as w:
            raise HTTPException(
                status_code=400,
                detail=f"El ajuste está mal condicionado o es numéricamente inestable: {str(w)}"
            )

    if model == "Lineal":
        coeffs = safe_polyfit(x, y, 1) # [pendiente m, intercepto b]
        m, b = float(coeffs[0]), float(coeffs[1])
        y_pred = np.polyval(coeffs, x)
        sign = "+" if b >= 0 else "-"
        formula_str = f"y = {m:.4f}*x {sign} {abs(b):.4f}"
        coeffs_dict = {"Pendiente (m)": round(m, 6), "Intercepto (b)": round(b, 6)}
        predict_fn = lambda xv: np.polyval(coeffs, xv)

    elif model == "Polinomial":
        g = int(req.g) if req.g is not None else 2
        if g < 1:
            raise HTTPException(status_code=400, detail="El grado del polinomio debe ser mayor o igual a 1.")
        if g >= n:
            raise HTTPException(status_code=400, detail=f"El grado del polinomio ({g}) debe ser menor que el número de datos ({n}).")
        if len(unique_x) <= g:
            raise HTTPException(
                status_code=400,
                detail=f"Para un ajuste polinomial de grado {g} se requieren al menos {g + 1} valores distintos de x. Se recibieron {len(unique_x)} valores distintos."
            )
        coeffs = safe_polyfit(x, y, g)
        y_pred = np.polyval(coeffs, x)
        poly = np.poly1d(coeffs)
        
        # Construcción limpia y matemática de la ecuación polinomial: c_g*x^g + ... + c_1*x + c_0
        terms = []
        for deg_idx, c in enumerate(coeffs):
            power = g - deg_idx
            if abs(c) > 1e-9:
                sign = "+ " if (c > 0 and terms) else ("- " if c < 0 and terms else ("-" if c < 0 else ""))
                c_abs = abs(c)
                c_str = f"{c_abs:.4f}".rstrip('0').rstrip('.')
                if power == 0:
                    terms.append(f"{sign}{c_str}")
                elif power == 1:
                    terms.append(f"{sign}{c_str}*x")
                else:
                    terms.append(f"{sign}{c_str}*x^{power}")
        formula_str = f"y = {' '.join(terms)}" if terms else "y = 0"
        
        coeffs_dict = {f"a_{g - i}": round(float(c), 6) for i, c in enumerate(coeffs)}
        predict_fn = lambda xv: np.polyval(coeffs, xv)

    elif model == "Exponencial":
        if np.any(y <= 0):
            raise HTTPException(
                status_code=400,
                detail="Para el modelo exponencial, todos los valores de y deben ser estrictamente positivos (> 0)."
            )
        ln_y = np.log(y)
        b_exp, ln_a = safe_polyfit(x, ln_y, 1)
        a_exp = float(np.exp(ln_a))
        b_exp = float(b_exp)
        y_pred = a_exp * np.exp(b_exp * x)
        formula_str = f"y = {a_exp:.4f} * e^({b_exp:.4f}*x)"
        coeffs_dict = {"a": round(a_exp, 6), "b": round(b_exp, 6)}
        predict_fn = lambda xv: a_exp * np.exp(b_exp * np.array(xv))

    elif model == "Potencia":
        if np.any(x <= 0) or np.any(y <= 0):
            raise HTTPException(
                status_code=400,
                detail="Para el modelo de potencia, todos los valores de x e y deben ser estrictamente mayores que cero (> 0)."
            )
        ln_x = np.log(x)
        ln_y = np.log(y)
        b_pow, ln_a = safe_polyfit(ln_x, ln_y, 1)
        a_pow = float(np.exp(ln_a))
        b_pow = float(b_pow)
        y_pred = a_pow * (x ** b_pow)
        formula_str = f"y = {a_pow:.4f} * x^({b_pow:.4f})"
        coeffs_dict = {"a": round(a_pow, 6), "b": round(b_pow, 6)}
        predict_fn = lambda xv: a_pow * (np.array(xv) ** b_pow)

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Modelo no soportado: '{req.mod}'. Use Lineal, Polinomial, Exponencial o Potencia."
        )

    # Coeficiente de determinación R^2 y error cuadrático
    residuals = y - y_pred
    sse = float(np.sum(residuals ** 2))
    sst = float(np.sum((y - np.mean(y)) ** 2))
    r2 = float(1.0 - (sse / sst)) if sst != 0 else 1.0

    # Evaluación en punto x dado (xe) si se proporciona
    ye_eval = None
    if req.xe is not None:
        try:
            ye_eval = float(predict_fn(float(req.xe)))
        except Exception:
            ye_eval = None

    steps = []
    for i in range(n):
        steps.append({
            "i": i + 1,
            "xᵢ": round(float(x[i]), 6),
            "yᵢ": round(float(y[i]), 6),
            "ŷᵢ (predicho)": round(float(y_pred[i]), 6),
            "Residuo eᵢ": round(float(residuals[i]), 6)
        })

    x_min, x_max = np.min(x), np.max(x)
    if req.xe is not None:
        x_min = min(x_min, float(req.xe))
        x_max = max(x_max, float(req.xe))

    margin = abs(x_max - x_min) * 0.2 if x_max != x_min else 1.0
    x_curve = np.linspace(x_min - margin, x_max + margin, 180)
    try:
        y_curve = predict_fn(x_curve).tolist()
    except Exception:
        y_curve = []

    summary_data = {
        "Ecuación del modelo": formula_str,
        "Coeficiente R²": round(r2, 6),
        "Error cuadrático (Σe²)": round(sse, 6),
        "Puntos cargados": n
    }
    if ye_eval is not None:
        summary_data[f"Evaluación en x={req.xe}"] = round(ye_eval, 6)

    return NumericalResponse(
        success=True,
        method=f"Regresión ({model})",
        converged=True,
        summary=summary_data,
        steps=steps,
        plot_data={
            "x_points": x.tolist(),
            "y_points": y.tolist(),
            "x_curve": x_curve.tolist(),
            "y_curve": y_curve,
            "equation": formula_str,
            "coefficients": coeffs_dict,
            "r2": r2,
            "sse": sse,
            "x_eval": float(req.xe) if req.xe is not None else None,
            "y_eval": ye_eval,
            "x_label": "x",
            "y_label": "y"
        },
        details=f"Ajuste {model}: {formula_str} con R² = {r2:.4f}" + (f" | y({req.xe}) = {ye_eval:.6f}" if ye_eval is not None else "")
    )
