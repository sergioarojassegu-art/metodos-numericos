import numpy as np
import scipy.integrate as integrate
from fastapi import APIRouter, HTTPException
from models.schemas import (
    TrapecioRequest,
    Simpson13Request,
    Simpson38Request,
    NumericalResponse
)
from utils.math_parser import parse_function_1d, parse_scalar

router = APIRouter(prefix="/integracion", tags=["Métodos de Integración"])

def format_err_display(err: float | str, target_tol: float = None):
    if err == "N/A" or err is None:
        return "N/A"
    if not isinstance(err, (int, float)):
        return err
    if err == 0.0:
        return 0.0
    if abs(err) < 1e-4:
        return f"{err:.6e}"
    return round(err, 6)

def compute_approx_error(curr: float, prev: float | None):
    """
    Calcula el error aproximado porcentual relativo entre aproximaciones consecutivas:
    err_pct = (|curr - prev| / |curr|) * 100%
    Manejo matemático riguroso:
    - Si prev es None (1ra iteración): no hay aproximación anterior -> (None, "N/A")
    - Si curr == prev (convergencia exacta): error relativo = (0.0, 0.0)
    - Si |curr| < 1e-14 y |curr - prev| < 1e-14: las dos aproximaciones están prácticamente en cero
      y la diferencia entre ellas es despreciable (< 1e-14) -> (0.0, 0.0)
    - Si |curr| < 1e-14 pero |curr - prev| >= 1e-14: división por cero o inestabilidad severa del
      error relativo -> (None, "Indefinido (|I| ≈ 0)")
    - En cualquier otro caso: división normal -> (err_pct, format_err_display(err_pct))
    """
    if prev is None:
        return None, "N/A"
    diff = abs(curr - prev)
    if diff == 0.0:
        return 0.0, 0.0
    denom = abs(curr)
    if denom < 1e-14:
        if diff < 1e-14:
            return 0.0, 0.0
        else:
            return None, "Indefinido (|I| ≈ 0)"
    err_pct = (diff / denom) * 100.0
    if not np.isfinite(err_pct):
        return None, "Indefinido"
    return err_pct, format_err_display(err_pct)

def get_stop_params(criterio: str | None, cifras: int | None, tol: float | None, it: int | None, default_it: int = 20):
    if it is not None and int(it) < 1:
        raise HTTPException(
            status_code=400,
            detail="El número de iteraciones debe ser un entero mayor o igual a 1."
        )

    crit = (criterio or "").lower()
    if cifras is not None or crit == "cifras":
        m = int(cifras) if cifras is not None else 4
        if m < 1:
            raise HTTPException(status_code=400, detail="El número de cifras significativas debe ser al menos 1.")
        target_tol_pct = 0.5 * (10.0 ** (2 - m))
        use_error_stop = True
        crit_desc = f"{m} cifras significativas (tolerancia = {target_tol_pct:.6g} %)"
    elif tol is not None or crit == "tol":
        t = float(tol) if tol is not None else 0.0001
        if t <= 0:
            raise HTTPException(status_code=400, detail="La tolerancia debe ser estrictamente positiva (> 0).")
        target_tol_pct = t
        use_error_stop = True
        crit_desc = f"tolerancia porcentual = {target_tol_pct:.6g} %"
    else:
        target_tol_pct = 0.0
        use_error_stop = False
        crit_desc = "número fijo de iteraciones"

    if it is not None:
        max_it = int(it)
    else:
        max_it = 200 if use_error_stop else default_it

    return use_error_stop, target_tol_pct, max_it, crit_desc

def calc_trapecio_raw(f, a: float, b: float, n_sub: int):
    h = (b - a) / n_sub
    x_nodes = [a + i * h for i in range(n_sub + 1)]
    y_nodes = [f(x) for x in x_nodes]
    integral = 0.5 * y_nodes[0] + sum(y_nodes[1:n_sub]) + 0.5 * y_nodes[n_sub]
    integral *= h
    return integral, h, x_nodes, y_nodes

def calc_simpson13_raw(f, a: float, b: float, n_sub: int):
    h = (b - a) / n_sub
    x_nodes = [a + i * h for i in range(n_sub + 1)]
    y_nodes = [f(x) for x in x_nodes]
    suma_impares = sum(y_nodes[i] for i in range(1, n_sub, 2))
    suma_pares = sum(y_nodes[i] for i in range(2, n_sub, 2))
    integral = (h / 3.0) * (y_nodes[0] + 4.0 * suma_impares + 2.0 * suma_pares + y_nodes[n_sub])
    return integral, h, x_nodes, y_nodes

def calc_simpson38_raw(f, a: float, b: float, n_sub: int):
    h = (b - a) / n_sub
    x_nodes = [a + i * h for i in range(n_sub + 1)]
    y_nodes = [f(x) for x in x_nodes]
    suma_resto = sum(y_nodes[i] for i in range(1, n_sub) if i % 3 != 0)
    suma_mult3 = sum(y_nodes[i] for i in range(3, n_sub, 3))
    integral = (3.0 * h / 8.0) * (y_nodes[0] + 3.0 * suma_resto + 2.0 * suma_mult3 + y_nodes[n_sub])
    return integral, h, x_nodes, y_nodes

@router.post("/trapecio", response_model=NumericalResponse)
def resolver_trapecio(req: TrapecioRequest):
    """
    Método del Trapecio según rúbrica:
    Columnas: Iteración, n, h, integral aproximada, error aproximado (%)
    Valida subintervalos (n >= 1) y permite parada por cifras significativas o iteraciones fijas.
    Secuencia de subintervalos: n = 1, 2, 3, 4...
    """
    try:
        f, sym = parse_function_1d(req.f)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        a = parse_scalar(req.a, "límite inferior a")
        b = parse_scalar(req.b, "límite superior b")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if a == b:
        raise HTTPException(status_code=400, detail="Los límites de integración a y b deben ser distintos.")

    use_error_stop, target_tol_pct, max_it, crit_desc = get_stop_params(
        req.criterio, req.cifras, req.tol, req.it, default_it=int(req.n) if req.n else 10
    )

    # Si el usuario especificó un n objetivo
    target_n = None
    if req.n is not None and not (not use_error_stop and req.it is not None):
        try:
            user_n = int(req.n)
        except Exception:
            raise HTTPException(status_code=400, detail="Error: Trapecio requiere que n sea un número entero.")
        if user_n < 1:
            raise HTTPException(status_code=400, detail="Error: Trapecio requiere que n sea mayor o igual a 1.")
        target_n = user_n

    steps = []
    prev_integral = None
    last_x_nodes, last_y_nodes, final_integral, final_h = [], [], 0.0, 0.0
    converged = False
    numeric_errors = []

    limit_iterations = max_it

    for iter_idx in range(1, limit_iterations + 1):
        k = iter_idx  # secuencia n = 1, 2, 3...
        try:
            curr_integral, curr_h, x_nodes, y_nodes = calc_trapecio_raw(f, a, b, k)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error evaluando Trapecio con n={k}: {str(e)}")

        raw_err_pct, error_val = compute_approx_error(curr_integral, prev_integral)
        if raw_err_pct is not None and np.isfinite(raw_err_pct):
            numeric_errors.append({"iter": iter_idx, "error": float(raw_err_pct)})

        steps.append({
            "Iteración": iter_idx,
            "n": k,
            "h": round(curr_h, 6),
            "integral aproximada": round(curr_integral, 6),
            "error aproximado (%)": error_val
        })

        final_integral = curr_integral
        final_h = curr_h
        last_x_nodes = x_nodes
        last_y_nodes = y_nodes

        # Detención por cifras significativas usando el error REAL sin redondear
        if use_error_stop and raw_err_pct is not None and raw_err_pct < target_tol_pct:
            converged = True
            break

        # Si no se usa criterio de parada por error (criterio fijo por iteraciones/subintervalos) y se alcanzó target_n, detenerse
        if not use_error_stop and target_n is not None and k >= target_n:
            converged = True
            break

        prev_integral = curr_integral

    x_curve = np.linspace(min(a, b), max(a, b), 180).tolist()
    y_curve = []
    for x in x_curve:
        try:
            y_curve.append(f(x))
        except Exception:
            y_curve.append(None)

    error_evolution = numeric_errors

    final_error = steps[-1]["error aproximado (%)"] if steps else "N/A"

    if not use_error_stop:
        converged = None
        status_text = "Iteraciones programadas completadas"
        stop_msg = f"Completadas las {len(steps)} iteraciones solicitadas (subintervalo final n = {steps[-1]['n']})."
    else:
        status_text = "Convergencia alcanzada según el criterio establecido" if converged else "Máximo de iteraciones alcanzado sin convergencia"
        stop_msg = (
            f"Convergencia alcanzada en {len(steps)} iteraciones: error ({final_error} %) < tolerancia ({target_tol_pct:.6g} %)."
            if converged
            else f"Máximo de iteraciones alcanzado sin convergencia: se completaron las {max_it} iteraciones sin alcanzar la tolerancia ({target_tol_pct:.6g} %)."
        )

    return NumericalResponse(
        success=True,
        method="Regla del Trapecio",
        converged=converged,
        summary={
            "Valor de la integral": round(final_integral, 6),
            "Subintervalos": steps[-1]["n"],
            "Paso h": round(final_h, 6),
            "Error final (%)": final_error,
            "Estado": status_text
        },
        steps=steps,
        plot_data={
            "x_curve": x_curve,
            "y_curve": y_curve,
            "x_nodes": last_x_nodes,
            "y_nodes": last_y_nodes,
            "h": final_h,
            "area": final_integral,
            "x_label": "x",
            "y_label": "f(x)",
            "error_evolution": error_evolution,
            "error_x_label": "Iteración (subintervalo k)",
            "error_y_label": "Error aproximado (%)"
        },
        details=f"Trapecio ejecutado: {stop_msg} Integral = {final_integral:.6f}."
    )

@router.post("/simpson-13", response_model=NumericalResponse)
def resolver_simpson_13(req: Simpson13Request):
    """
    Método de Simpson 1/3 según rúbrica:
    Columnas: Iteración, n, h, integral aproximada, error aproximado (%)
    Exige n par (n >= 2). Permite parada por cifras significativas o iteraciones fijas.
    Secuencia de subintervalos: n = 2, 4, 6, 8...
    """
    try:
        f, sym = parse_function_1d(req.f)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        a = parse_scalar(req.a, "límite inferior a")
        b = parse_scalar(req.b, "límite superior b")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if a == b:
        raise HTTPException(status_code=400, detail="Los límites de integración a y b deben ser distintos.")

    use_error_stop, target_tol_pct, max_it, crit_desc = get_stop_params(
        req.criterio, req.cifras, req.tol, req.it, default_it=int(req.n // 2) if req.n else 10
    )

    # Validar el n introducido por el usuario
    target_n = None
    if req.n is not None and not (not use_error_stop and req.it is not None):
        try:
            user_n = int(req.n)
        except Exception:
            raise HTTPException(status_code=400, detail="Error: Simpson 1/3 requiere que n sea un número entero.")
        if user_n < 2 or user_n % 2 != 0:
            raise HTTPException(
                status_code=400,
                detail="Error: Simpson 1/3 requiere un número par de subintervalos"
            )
        target_n = user_n
        
        required_iters_for_n = user_n // 2
        if not use_error_stop and req.it is not None and required_iters_for_n > max_it:
            raise HTTPException(
                status_code=400,
                detail=f"Error: El subintervalo objetivo n = {user_n} requiere {required_iters_for_n} iteraciones, pero el máximo de iteraciones configurado es {max_it}. Aumenta el número de iteraciones o reduce n."
            )

    steps = []
    prev_integral = None
    last_x_nodes, last_y_nodes, final_integral, final_h = [], [], 0.0, 0.0
    converged = False
    numeric_errors = []

    limit_iterations = max_it

    for iter_idx in range(1, limit_iterations + 1):
        k = iter_idx * 2  # secuencia n = 2, 4, 6, 8...
        try:
            curr_integral, curr_h, x_nodes, y_nodes = calc_simpson13_raw(f, a, b, k)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error evaluando Simpson 1/3 con n={k}: {str(e)}")

        raw_err_pct, error_val = compute_approx_error(curr_integral, prev_integral)
        if raw_err_pct is not None and np.isfinite(raw_err_pct):
            numeric_errors.append({"iter": iter_idx, "error": float(raw_err_pct)})

        steps.append({
            "Iteración": iter_idx,
            "n": k,
            "h": round(curr_h, 6),
            "integral aproximada": round(curr_integral, 6),
            "error aproximado (%)": error_val
        })

        final_integral = curr_integral
        final_h = curr_h
        last_x_nodes = x_nodes
        last_y_nodes = y_nodes

        # Detención por cifras significativas usando el error REAL sin redondear
        if use_error_stop and raw_err_pct is not None and raw_err_pct < target_tol_pct:
            converged = True
            break

        # Si no se usa criterio de parada por error (criterio fijo por iteraciones/subintervalos) y se alcanzó target_n, detenerse
        if not use_error_stop and target_n is not None and k >= target_n:
            converged = True
            break

        prev_integral = curr_integral

    x_curve = np.linspace(min(a, b), max(a, b), 180).tolist()
    y_curve = []
    for x in x_curve:
        try:
            y_curve.append(f(x))
        except Exception:
            y_curve.append(None)

    error_evolution = numeric_errors

    final_error = steps[-1]["error aproximado (%)"] if steps else "N/A"

    if not use_error_stop:
        converged = None
        status_text = "Iteraciones programadas completadas"
        stop_msg = f"Completadas las {len(steps)} iteraciones solicitadas (subintervalo final n = {steps[-1]['n']})."
    else:
        status_text = "Convergencia alcanzada según el criterio establecido" if converged else "Máximo de iteraciones alcanzado sin convergencia"
        stop_msg = (
            f"Convergencia alcanzada en {len(steps)} iteraciones: error ({final_error} %) < tolerancia ({target_tol_pct:.6g} %)."
            if converged
            else f"Máximo de iteraciones alcanzado sin convergencia: se completaron las {max_it} iteraciones sin alcanzar la tolerancia ({target_tol_pct:.6g} %)."
        )

    return NumericalResponse(
        success=True,
        method="Simpson 1/3",
        converged=converged,
        summary={
            "Valor de la integral": round(final_integral, 6),
            "Subintervalos": steps[-1]["n"],
            "Paso h": round(final_h, 6),
            "Error final (%)": final_error,
            "Estado": status_text
        },
        steps=steps,
        plot_data={
            "x_curve": x_curve,
            "y_curve": y_curve,
            "x_nodes": last_x_nodes,
            "y_nodes": last_y_nodes,
            "h": final_h,
            "area": final_integral,
            "x_label": "x",
            "y_label": "f(x)",
            "error_evolution": error_evolution,
            "error_x_label": "Iteración (partición par k)",
            "error_y_label": "Error aproximado (%)"
        },
        details=f"Simpson 1/3 ejecutado: {stop_msg} Integral = {final_integral:.6f}."
    )

@router.post("/simpson-38", response_model=NumericalResponse)
def resolver_simpson_38(req: Simpson38Request):
    """
    Método de Simpson 3/8 según rúbrica:
    Columnas: Iteración, n, h, integral aproximada, error aproximado (%)
    Exige n múltiplo de 3 (n >= 3). Permite parada por cifras significativas o iteraciones fijas.
    Secuencia de subintervalos: n = 3, 6, 9, 12...
    """
    try:
        f, sym = parse_function_1d(req.f)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        a = parse_scalar(req.a, "límite inferior a")
        b = parse_scalar(req.b, "límite superior b")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if a == b:
        raise HTTPException(status_code=400, detail="Los límites de integración a y b deben ser distintos.")

    use_error_stop, target_tol_pct, max_it, crit_desc = get_stop_params(
        req.criterio, req.cifras, req.tol, req.it, default_it=int(req.n // 3) if req.n else 9
    )

    # Validar el n introducido por el usuario
    target_n = None
    if req.n is not None and not (not use_error_stop and req.it is not None):
        try:
            user_n = int(req.n)
        except Exception:
            raise HTTPException(status_code=400, detail="Error: Simpson 3/8 requiere que n sea un número entero.")
        if user_n < 3 or user_n % 3 != 0:
            raise HTTPException(
                status_code=400,
                detail="Error: Simpson 3/8 requiere un número de subintervalos múltiplo de 3"
            )
        target_n = user_n
        
        required_iters_for_n = user_n // 3
        if not use_error_stop and req.it is not None and required_iters_for_n > max_it:
            raise HTTPException(
                status_code=400,
                detail=f"Error: El subintervalo objetivo n = {user_n} requiere {required_iters_for_n} iteraciones, pero el máximo de iteraciones configurado es {max_it}. Aumenta el número de iteraciones o reduce n."
            )

    steps = []
    prev_integral = None
    last_x_nodes, last_y_nodes, final_integral, final_h = [], [], 0.0, 0.0
    converged = False
    numeric_errors = []

    limit_iterations = max_it

    for iter_idx in range(1, limit_iterations + 1):
        k = iter_idx * 3  # secuencia n = 3, 6, 9, 12...
        try:
            curr_integral, curr_h, x_nodes, y_nodes = calc_simpson38_raw(f, a, b, k)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error evaluando Simpson 3/8 con n={k}: {str(e)}")

        raw_err_pct, error_val = compute_approx_error(curr_integral, prev_integral)
        if raw_err_pct is not None and np.isfinite(raw_err_pct):
            numeric_errors.append({"iter": iter_idx, "error": float(raw_err_pct)})

        steps.append({
            "Iteración": iter_idx,
            "n": k,
            "h": round(curr_h, 6),
            "integral aproximada": round(curr_integral, 6),
            "error aproximado (%)": error_val
        })

        final_integral = curr_integral
        final_h = curr_h
        last_x_nodes = x_nodes
        last_y_nodes = y_nodes

        # Detención por cifras significativas usando el error REAL sin redondear
        if use_error_stop and raw_err_pct is not None and raw_err_pct < target_tol_pct:
            converged = True
            break

        # Si no se usa criterio de parada por error (criterio fijo por iteraciones/subintervalos) y se alcanzó target_n, detenerse
        if not use_error_stop and target_n is not None and k >= target_n:
            converged = True
            break

        prev_integral = curr_integral

    x_curve = np.linspace(min(a, b), max(a, b), 180).tolist()
    y_curve = []
    for x in x_curve:
        try:
            y_curve.append(f(x))
        except Exception:
            y_curve.append(None)

    error_evolution = numeric_errors

    final_error = steps[-1]["error aproximado (%)"] if steps else "N/A"

    if not use_error_stop:
        converged = None
        status_text = "Iteraciones programadas completadas"
        stop_msg = f"Completadas las {len(steps)} iteraciones solicitadas (subintervalo final n = {steps[-1]['n']})."
    else:
        status_text = "Convergencia alcanzada según el criterio establecido" if converged else "Máximo de iteraciones alcanzado sin convergencia"
        stop_msg = (
            f"Convergencia alcanzada en {len(steps)} iteraciones: error ({final_error} %) < tolerancia ({target_tol_pct:.6g} %)."
            if converged
            else f"Máximo de iteraciones alcanzado sin convergencia: se completaron las {max_it} iteraciones sin alcanzar la tolerancia ({target_tol_pct:.6g} %)."
        )

    return NumericalResponse(
        success=True,
        method="Simpson 3/8",
        converged=converged,
        summary={
            "Valor de la integral": round(final_integral, 6),
            "Subintervalos": steps[-1]["n"],
            "Paso h": round(final_h, 6),
            "Error final (%)": final_error,
            "Estado": status_text
        },
        steps=steps,
        plot_data={
            "x_curve": x_curve,
            "y_curve": y_curve,
            "x_nodes": last_x_nodes,
            "y_nodes": last_y_nodes,
            "h": final_h,
            "area": final_integral,
            "x_label": "x",
            "y_label": "f(x)",
            "error_evolution": error_evolution,
            "error_x_label": "Iteración (partición múltiplo de 3 k)",
            "error_y_label": "Error aproximado (%)"
        },
        details=f"Simpson 3/8 ejecutado: {stop_msg} Integral = {final_integral:.6f}."
    )
