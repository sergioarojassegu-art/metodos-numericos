import numpy as np
from fastapi import APIRouter, HTTPException
from models.schemas import (
    BiseccionRequest,
    FalsaPosicionRequest,
    SecanteRequest,
    NewtonRaphsonRequest,
    NumericalResponse
)
from utils.math_parser import parse_function_1d, parse_derivative_1d, parse_scalar

router = APIRouter(prefix="/raices", tags=["Métodos de Raíces"])

def format_val_prec(val: float | None, prec_digits: int = 6):
    if val is None or isinstance(val, str):
        return val
    return round(val, max(6, prec_digits))

def get_stop_params(criterio: str | None, cifras: int | None, tol: float | None, it: int | None):
    """
    Determina los parámetros de parada según la rúbrica:
    - Selector entre número de iteraciones y cifras significativas (criterio de Scarborough: es = 0.5 * 10^(2-m) %).
    - Soporta también tolerancia porcentual directa.
    - Respeta 'it' como número máximo de iteraciones.
    """
    if it is not None and int(it) < 1:
        raise HTTPException(
            status_code=400,
            detail="El número de iteraciones 'it' debe ser un entero mayor o igual a 1."
        )

    # Determinar si se usa criterio de parada por error o por iteraciones fijas
    crit = (criterio or "").lower()
    
    if cifras is not None or crit == "cifras":
        m = int(cifras) if cifras is not None else 4
        if m < 1:
            raise HTTPException(status_code=400, detail="El número de cifras significativas debe ser al menos 1.")
        # Criterio de Scarborough para error porcentual relativo:
        target_tol_pct = 0.5 * (10.0 ** (2 - m))
        use_error_stop = True
        crit_desc = f"{m} cifras significativas (tolerancia = {target_tol_pct:.6g} %)"
    elif tol is not None or crit == "tol":
        t = float(tol) if tol is not None else 0.0001
        if t <= 0:
            raise HTTPException(status_code=400, detail="La tolerancia debe ser estrictamente positiva (> 0).")
        target_tol_pct = t
        use_error_stop = True
        crit_desc = f"tolerancia de error = {target_tol_pct:.6g} %"
    else:
        # Criterio exclusivo por iteraciones
        target_tol_pct = 0.0
        use_error_stop = False
        crit_desc = "número fijo de iteraciones"

    # Límite máximo de iteraciones
    if it is not None:
        max_it = int(it)
    else:
        max_it = 50 if crit == "it" else 100

    return use_error_stop, target_tol_pct, max_it, crit_desc

def generate_plot_data(f, min_val: float, max_val: float, root_val: float, steps: list):
    """Genera datos de curva y de evolución del error coherentes con la tabla."""
    margin = abs(max_val - min_val) * 0.25 if max_val != min_val else 1.0
    x_min = min(min_val, max_val, root_val) - margin
    x_max = max(min_val, max_val, root_val) + margin
    x_vals = np.linspace(x_min, x_max, 160).tolist()
    y_vals = []
    for xv in x_vals:
        try:
            y_vals.append(f(xv))
        except Exception:
            y_vals.append(None)

    error_evolution = []
    for s in steps:
        err = s.get("error aproximado (%)")
        if err is not None:
            try:
                num_err = float(err)
                if np.isfinite(num_err):
                    error_evolution.append({"iter": s.get("i", 0), "error": num_err})
            except (ValueError, TypeError):
                pass

    return {
        "x_curve": x_vals,
        "y_curve": y_vals,
        "root": root_val,
        "x_label": "x",
        "y_label": "f(x)",
        "error_evolution": error_evolution,
        "error_x_label": "Iteración (i)",
        "error_y_label": "Error aproximado (%)",
        "iterations": [s.get("i", 0) for s in steps],
        "errors": [s.get("error aproximado (%)", 0.0) for s in steps]
    }

@router.post("/biseccion", response_model=NumericalResponse)
def resolver_biseccion(req: BiseccionRequest):
    """
    Método de Bisección según rúbrica:
    Columnas: i, xl, xu, xr, f(xl), f(xr), f(xl)·f(xr), error aproximado (%)
    Valida cambio de signo f(xl)*f(xu) < 0 y raíces en los extremos.
    """
    try:
        f, _ = parse_function_1d(req.f)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        xl = parse_scalar(req.a, "límite inferior xl (a)")
        xu = parse_scalar(req.b, "límite superior xu (b)")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if xl == xu:
        raise HTTPException(status_code=400, detail="Los extremos del intervalo no pueden ser iguales: xl y xu deben ser distintos.")

    try:
        fxl = f(xl)
        fxu = f(xu)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error evaluando f(x) en los extremos: {str(e)}")

    use_error_stop, target_tol_pct, max_it, crit_desc = get_stop_params(req.criterio, req.cifras, req.tol, req.it)
    prec = max(6, int(req.cifras)) if req.cifras is not None else 6

    # Verificación de raíces en los extremos antes de iterar
    TOL_ZERO = 1e-12
    if abs(fxl) < TOL_ZERO:
        step = {
            "i": 1,
            "xl": round(xl, 6),
            "xu": round(xu, 6),
            "xr": round(xl, 6),
            "f(xl)": round(fxl, 6),
            "f(xr)": round(fxl, 6),
            "f(xl)·f(xr)": 0.0,
            "error aproximado (%)": 0.0
        }
        plot_data = generate_plot_data(f, xl, xu, xl, [step])
        return NumericalResponse(
            success=True,
            method="Bisección",
            converged=True,
            summary={
                "Raíz aproximada": round(xl, 6),
                "Iteraciones": 1,
                "Error aproximado (%)": 0.0,
                "Estado": "Convergencia exitosa (raíz exacta en xl)"
            },
            steps=[step],
            plot_data=plot_data,
            details=f"Convergencia inmediata: x = {xl} es raíz exacta en el extremo inferior del intervalo (f({xl}) = 0)."
        )

    if abs(fxu) < TOL_ZERO:
        step = {
            "i": 1,
            "xl": round(xl, 6),
            "xu": round(xu, 6),
            "xr": round(xu, 6),
            "f(xl)": round(fxl, 6),
            "f(xr)": round(fxu, 6),
            "f(xl)·f(xr)": 0.0,
            "error aproximado (%)": 0.0
        }
        plot_data = generate_plot_data(f, xl, xu, xu, [step])
        return NumericalResponse(
            success=True,
            method="Bisección",
            converged=True,
            summary={
                "Raíz aproximada": round(xu, 6),
                "Iteraciones": 1,
                "Error aproximado (%)": 0.0,
                "Estado": "Convergencia exitosa (raíz exacta en xu)"
            },
            steps=[step],
            plot_data=plot_data,
            details=f"Convergencia inmediata: x = {xu} es raíz exacta en el extremo superior del intervalo (f({xu}) = 0)."
        )

    if fxl * fxu > 0:
        raise HTTPException(
            status_code=400,
            detail=f"f(xl) y f(xu) deben tener signos opuestos (f(a)·f(b) < 0). f({xl}) = {fxl:.6f}, f({xu}) = {fxu:.6f}"
        )

    steps = []
    lista_xr = []
    converged = False
    stop_reason = ""

    for i in range(1, max_it + 1):
        xr = (xl + xu) / 2.0
        lista_xr.append(xr)

        try:
            f_xl = f(xl)
            f_xr = f(xr)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error evaluando la función en iteración {i}: {str(e)}")

        prod = f_xl * f_xr

        # Error porcentual aproximado: |(xr_actual - xr_anterior) / xr_actual| * 100 %
        if len(lista_xr) > 1:
            error_pct = abs((lista_xr[-1] - lista_xr[-2]) / lista_xr[-1]) * 100.0 if lista_xr[-1] != 0 else abs(lista_xr[-1] - lista_xr[-2]) * 100.0
        else:
            error_pct = abs((xu - xl) / xr) * 100.0 if xr != 0 else abs(xu - xl) * 100.0

        step_record = {
            "i": i,
            "xl": round(xl, prec),
            "xu": round(xu, prec),
            "xr": round(xr, prec),
            "f(xl)": round(f_xl, prec),
            "f(xr)": round(f_xr, prec),
            "f(xl)·f(xr)": round(prod, prec),
            "error aproximado (%)": round(error_pct, prec) if error_pct >= 1e-4 else f"{error_pct:.6e}"
        }
        steps.append(step_record)

        if abs(f_xr) < TOL_ZERO:
            converged = True
            stop_reason = f"Convergencia exitosa: se encontró la raíz exacta (|f(xr)| < 1e-12) en iteración {i}."
            break

        if use_error_stop and len(lista_xr) > 1 and error_pct < target_tol_pct:
            converged = True
            stop_reason = f"Convergencia exitosa alcanzada en {i} iteraciones: error ({error_pct:.6e} %) < criterio ({target_tol_pct:.6e} %)."
            break

        if prod < 0:
            xu = xr
        else:
            xl = xr

    if not converged:
        if use_error_stop:
            status_text = "Número máximo de iteraciones alcanzado sin convergencia"
            stop_reason = (
                f"Límite de iteraciones alcanzado ({len(steps)} de {max_it} iteraciones). "
                f"No se alcanzó la tolerancia deseada ({target_tol_pct:.6g} %). Error final = {steps[-1]['error aproximado (%)']} %."
            )
        else:
            converged = None
            status_text = "Iteraciones programadas completadas"
            stop_reason = f"Finalizadas las {max_it} iteraciones programadas por criterio de iteración fija."
    else:
        status_text = "Convergencia alcanzada según el criterio establecido"

    best_root = lista_xr[-1] if lista_xr else xl
    plot_data = generate_plot_data(f, xl, xu, best_root, steps)

    display_digits = int(req.cifras) if req.cifras is not None else 6
    prec = max(6, display_digits)

    return NumericalResponse(
        success=True,
        method="Bisección",
        converged=converged,
        summary={
            "Raíz aproximada": format_val_prec(best_root, display_digits),
            "Iteraciones": len(steps),
            "Error final (%)": steps[-1]["error aproximado (%)"] if steps else 0.0,
            "Estado": status_text
        },
        steps=steps,
        plot_data=plot_data,
        details=stop_reason
    )

@router.post("/falsa-posicion", response_model=NumericalResponse)
def resolver_falsa_posicion(req: FalsaPosicionRequest):
    """
    Método de Regula Falsi (Falsa Posición) según rúbrica:
    Columnas: i, xl, xu, xr, f(xl), f(xu), f(xr), error aproximado (%)
    Valida cambio de signo f(xl)*f(xu) < 0 y raíces en extremos.
    """
    try:
        f, _ = parse_function_1d(req.f)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        xl = parse_scalar(req.a, "límite inferior xl (a)")
        xu = parse_scalar(req.b, "límite superior xu (b)")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if xl == xu:
        raise HTTPException(status_code=400, detail="Los extremos del intervalo no pueden ser iguales: xl y xu deben ser distintos.")

    try:
        fxl = f(xl)
        fxu = f(xu)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error evaluando f(x) en los extremos: {str(e)}")

    use_error_stop, target_tol_pct, max_it, crit_desc = get_stop_params(req.criterio, req.cifras, req.tol, req.it)
    prec = max(6, int(req.cifras)) if req.cifras is not None else 6

    TOL_ZERO = 1e-12
    if abs(fxl) < TOL_ZERO:
        step = {"i": 1, "xl": round(xl, 6), "xu": round(xu, 6), "xr": round(xl, 6), "f(xl)": round(fxl, 6), "f(xu)": round(fxu, 6), "f(xr)": round(fxl, 6), "error aproximado (%)": 0.0}
        plot_data = generate_plot_data(f, xl, xu, xl, [step])
        return NumericalResponse(
            success=True, method="Falsa Posición", converged=True,
            summary={"Raíz aproximada": round(xl, 6), "Iteraciones": 1, "Error final (%)": 0.0, "Estado": "Convergencia exitosa (raíz en xl)"},
            steps=[step], plot_data=plot_data, details=f"Convergencia inmediata: x = {xl} es raíz exacta."
        )

    if abs(fxu) < TOL_ZERO:
        step = {"i": 1, "xl": round(xl, 6), "xu": round(xu, 6), "xr": round(xu, 6), "f(xl)": round(fxl, 6), "f(xu)": round(fxu, 6), "f(xr)": round(fxu, 6), "error aproximado (%)": 0.0}
        plot_data = generate_plot_data(f, xl, xu, xu, [step])
        return NumericalResponse(
            success=True, method="Falsa Posición", converged=True,
            summary={"Raíz aproximada": round(xu, 6), "Iteraciones": 1, "Error final (%)": 0.0, "Estado": "Convergencia exitosa (raíz en xu)"},
            steps=[step], plot_data=plot_data, details=f"Convergencia inmediata: x = {xu} es raíz exacta."
        )

    if fxl * fxu > 0:
        raise HTTPException(
            status_code=400,
            detail=f"f(xl) y f(xu) deben tener signos opuestos (f(a)·f(b) < 0). f({xl}) = {fxl:.6f}, f({xu}) = {fxu:.6f}"
        )

    steps = []
    xr_ant = None
    xr = xl
    converged = False
    stop_reason = ""

    for i in range(1, max_it + 1):
        den = (fxu - fxl)
        if abs(den) < 1e-15:
            raise HTTPException(status_code=400, detail="División por cero en el denominador de Falsa Posición (f(xu) ≈ f(xl)).")

        xr = (xl * fxu - xu * fxl) / den
        try:
            fxr = f(xr)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error evaluando f(xr) en iteración {i}: {str(e)}")

        if xr_ant is not None:
            error_pct = abs((xr - xr_ant) / xr) * 100.0 if xr != 0 else abs(xr - xr_ant) * 100.0
        else:
            error_pct = abs((xu - xl) / xr) * 100.0 if xr != 0 else abs(xu - xl) * 100.0

        step_record = {
            "i": i,
            "xl": round(xl, prec),
            "xu": round(xu, prec),
            "xr": round(xr, prec),
            "f(xl)": round(fxl, prec),
            "f(xu)": round(fxu, prec),
            "f(xr)": round(fxr, prec),
            "error aproximado (%)": round(error_pct, prec) if error_pct >= 1e-4 else f"{error_pct:.6e}"
        }
        steps.append(step_record)

        if abs(fxr) < TOL_ZERO:
            converged = True
            stop_reason = f"Convergencia exitosa: se encontró la raíz exacta (|f(xr)| < 1e-12) en iteración {i}."
            break

        if use_error_stop and xr_ant is not None and error_pct < target_tol_pct:
            converged = True
            stop_reason = f"Convergencia exitosa alcanzada en {i} iteraciones: error ({error_pct:.6e} %) < criterio ({target_tol_pct:.6e} %)."
            break

        if fxl * fxr < 0:
            xu = xr
            fxu = fxr
        else:
            xl = xr
            fxl = fxr

        xr_ant = xr

    if not converged:
        if use_error_stop:
            status_text = "Número máximo de iteraciones alcanzado sin convergencia"
            stop_reason = (
                f"Límite de iteraciones alcanzado ({len(steps)} de {max_it} iteraciones). "
                f"No se alcanzó la tolerancia deseada ({target_tol_pct:.6g} %). Error final = {steps[-1]['error aproximado (%)']} %."
            )
        else:
            converged = None
            status_text = "Iteraciones programadas completadas"
            stop_reason = f"Finalizadas las {max_it} iteraciones programadas por criterio de iteración fija."
    else:
        status_text = "Convergencia alcanzada según el criterio establecido"

    plot_data = generate_plot_data(f, xl, xu, xr, steps)

    display_digits = int(req.cifras) if req.cifras is not None else 6
    prec = max(6, display_digits)

    return NumericalResponse(
        success=True,
        method="Falsa Posición",
        converged=converged,
        summary={
            "Raíz aproximada": format_val_prec(xr, display_digits),
            "Iteraciones": len(steps),
            "Error final (%)": steps[-1]["error aproximado (%)"] if steps else 0.0,
            "Estado": status_text
        },
        steps=steps,
        plot_data=plot_data,
        details=stop_reason
    )

@router.post("/secante", response_model=NumericalResponse)
def resolver_secante(req: SecanteRequest):
    """
    Método de la Secante según rúbrica:
    Columnas: i, x_(i−1), x_i, f(x_(i−1)), f(x_i), x_(i+1), error aproximado (%)
    Usa dos valores iniciales, sin derivada.
    """
    try:
        f, _ = parse_function_1d(req.f)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        x_ant = parse_scalar(req.x0, "punto inicial x0")
        x_act = parse_scalar(req.x1, "punto inicial x1")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if x_ant == x_act:
        raise HTTPException(status_code=400, detail="Los puntos iniciales x0 y x1 deben ser distintos.")

    try:
        f_ant = f(x_ant)
        f_act = f(x_act)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error evaluando f(x) en los puntos iniciales: {str(e)}")

    use_error_stop, target_tol_pct, max_it, crit_desc = get_stop_params(req.criterio, req.cifras, req.tol, req.it)
    prec = max(6, int(req.cifras)) if req.cifras is not None else 6

    TOL_ZERO = 1e-12
    if abs(f_ant) < TOL_ZERO:
        step = {"i": 1, "x_(i−1)": round(x_ant, 6), "x_i": round(x_act, 6), "f(x_(i−1))": round(f_ant, 6), "f(x_i)": round(f_act, 6), "x_(i+1)": round(x_ant, 6), "error aproximado (%)": 0.0}
        plot_data = generate_plot_data(f, x_ant, x_act, x_ant, [step])
        return NumericalResponse(
            success=True, method="Secante", converged=True,
            summary={"Raíz aproximada": round(x_ant, 6), "Iteraciones": 1, "Error final (%)": 0.0, "Estado": "Convergencia exitosa (raíz en x0)"},
            steps=[step], plot_data=plot_data, details=f"Convergencia inmediata: x0 = {x_ant} es raíz exacta."
        )

    if abs(f_act) < TOL_ZERO:
        step = {"i": 1, "x_(i−1)": round(x_ant, 6), "x_i": round(x_act, 6), "f(x_(i−1))": round(f_ant, 6), "f(x_i)": round(f_act, 6), "x_(i+1)": round(x_act, 6), "error aproximado (%)": 0.0}
        plot_data = generate_plot_data(f, x_ant, x_act, x_act, [step])
        return NumericalResponse(
            success=True, method="Secante", converged=True,
            summary={"Raíz aproximada": round(x_act, 6), "Iteraciones": 1, "Error final (%)": 0.0, "Estado": "Convergencia exitosa (raíz en x1)"},
            steps=[step], plot_data=plot_data, details=f"Convergencia inmediata: x1 = {x_act} es raíz exacta."
        )

    steps = []
    converged = False
    stop_reason = ""
    last_root = x_act

    for i in range(1, max_it + 1):
        den = (f_act - f_ant)
        if abs(den) < 1e-15:
            raise HTTPException(status_code=400, detail=f"División por cero en iteración {i}: f(x_i) - f(x_(i-1)) ≈ 0.")

        x_sig = x_act - (f_act * (x_act - x_ant)) / den
        try:
            f_sig = f(x_sig)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error evaluando f(x) en iteración {i}: {str(e)}")

        error_pct = abs((x_sig - x_act) / x_sig) * 100.0 if x_sig != 0 else abs(x_sig - x_act) * 100.0
        last_root = x_sig

        step_record = {
            "i": i,
            "x_(i−1)": round(x_ant, prec),
            "x_i": round(x_act, prec),
            "f(x_(i−1))": round(f_ant, prec),
            "f(x_i)": round(f_act, prec),
            "x_(i+1)": round(x_sig, prec),
            "error aproximado (%)": round(error_pct, prec) if error_pct >= 1e-4 else f"{error_pct:.6e}"
        }
        steps.append(step_record)

        if abs(f_sig) < TOL_ZERO:
            converged = True
            stop_reason = f"Convergencia exitosa: se encontró la raíz exacta (|f(x)| < 1e-12) en iteración {i}."
            break

        if use_error_stop and error_pct < target_tol_pct:
            converged = True
            stop_reason = f"Convergencia exitosa alcanzada en {i} iteraciones: error ({error_pct:.6e} %) < criterio ({target_tol_pct:.6e} %)."
            break

        x_ant, f_ant = x_act, f_act
        x_act, f_act = x_sig, f_sig

    if not converged:
        if use_error_stop:
            status_text = "Número máximo de iteraciones alcanzado sin convergencia"
            stop_reason = (
                f"Límite de iteraciones alcanzado ({len(steps)} de {max_it} iteraciones). "
                f"No se alcanzó la tolerancia deseada ({target_tol_pct:.6g} %). Error final = {steps[-1]['error aproximado (%)']} %."
            )
        else:
            converged = None
            status_text = "Iteraciones programadas completadas"
            stop_reason = f"Finalizadas las {max_it} iteraciones programadas por criterio de iteración fija."
    else:
        status_text = "Convergencia alcanzada según el criterio establecido"

    plot_data = generate_plot_data(f, min(x_ant, x_act), max(x_ant, x_act), last_root, steps)

    display_digits = int(req.cifras) if req.cifras is not None else 6
    prec = max(6, display_digits)

    return NumericalResponse(
        success=True,
        method="Secante",
        converged=converged,
        summary={
            "Raíz aproximada": format_val_prec(last_root, display_digits),
            "Iteraciones": len(steps),
            "Error final (%)": steps[-1]["error aproximado (%)"] if steps else 0.0,
            "Estado": status_text
        },
        steps=steps,
        plot_data=plot_data,
        details=stop_reason
    )

@router.post("/newton-raphson", response_model=NumericalResponse)
def resolver_newton_raphson(req: NewtonRaphsonRequest):
    """
    Método de Newton-Raphson según rúbrica:
    Columnas: i, x_i, f(x_i), f'(x_i), x_(i+1), error aproximado (%)
    Calcula f'(x); avisa si f'(x) = 0.
    """
    try:
        f, _ = parse_function_1d(req.f)
        df, df_symbolic = parse_derivative_1d(req.f, req.df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        x_act = parse_scalar(req.x0, "punto inicial x0")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    use_error_stop, target_tol_pct, max_it, crit_desc = get_stop_params(req.criterio, req.cifras, req.tol, req.it)
    prec = max(6, int(req.cifras)) if req.cifras is not None else 6

    try:
        fx0 = f(x_act)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error evaluando f(x) en el punto inicial x0={x_act}: {str(e)}")

    TOL_ZERO = 1e-12
    if abs(fx0) < TOL_ZERO:
        step = {"i": 1, "x_i": round(x_act, 6), "f(x_i)": round(fx0, 6), "f'(x_i)": round(df(x_act), 6), "x_(i+1)": round(x_act, 6), "error aproximado (%)": 0.0}
        plot_data = generate_plot_data(f, x_act, x_act, x_act, [step])
        plot_data["derivative_used"] = df_symbolic
        return NumericalResponse(
            success=True,
            method="Newton-Raphson",
            converged=True,
            summary={"Raíz aproximada": round(x_act, 6), "Iteraciones": 1, "Error final (%)": 0.0, "Estado": "Convergencia exitosa (raíz en x0)"},
            steps=[step],
            plot_data=plot_data,
            details=f"Convergencia inmediata: x0 = {x_act} es raíz exacta (f({x_act}) = 0)."
        )

    steps = []
    converged = False
    stop_reason = ""
    last_root = x_act

    for i in range(1, max_it + 1):
        try:
            fx = f(x_act)
            dfx = df(x_act)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error evaluando la función o derivada en x = {x_act}: {str(e)}")

        if abs(dfx) < 1e-15:
            raise HTTPException(
                status_code=400,
                detail=f"Derivada f'(x) = 0 (o casi nula: {dfx:.2e}) en x = {x_act}. La recta tangente es horizontal y el método no puede continuar."
            )

        x_sig = x_act - (fx / dfx)
        try:
            fx_sig = f(x_sig)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error evaluando f(x_(i+1)) en x = {x_sig}: {str(e)}")

        error_pct = abs((x_sig - x_act) / x_sig) * 100.0 if x_sig != 0 else abs(x_sig - x_act) * 100.0
        last_root = x_sig

        step_record = {
            "i": i,
            "x_i": round(x_act, prec),
            "f(x_i)": round(fx, prec),
            "f'(x_i)": round(dfx, prec),
            "x_(i+1)": round(x_sig, prec),
            "error aproximado (%)": round(error_pct, prec) if error_pct >= 1e-4 else f"{error_pct:.6e}"
        }
        steps.append(step_record)

        if abs(fx_sig) < TOL_ZERO:
            converged = True
            stop_reason = f"Convergencia exitosa: se encontró la raíz exacta (|f(x)| < 1e-12) en iteración {i}."
            break

        if use_error_stop and error_pct < target_tol_pct:
            converged = True
            stop_reason = f"Convergencia exitosa alcanzada en {i} iteraciones: error ({error_pct:.6e} %) < criterio ({target_tol_pct:.6e} %)."
            break

        x_act = x_sig

    if not converged:
        if use_error_stop:
            status_text = "Número máximo de iteraciones alcanzado sin convergencia"
            stop_reason = (
                f"Límite de iteraciones alcanzado ({len(steps)} de {max_it} iteraciones). "
                f"No se alcanzó la tolerancia deseada ({target_tol_pct:.6g} %). Error final = {steps[-1]['error aproximado (%)']} %."
            )
        else:
            converged = None
            status_text = "Iteraciones programadas completadas"
            stop_reason = f"Finalizadas las {max_it} iteraciones programadas por criterio de iteración fija."
    else:
        status_text = "Convergencia alcanzada según el criterio establecido"

    plot_data = generate_plot_data(f, x_act - 1.0, last_root + 1.0, last_root, steps)
    plot_data["derivative_used"] = df_symbolic

    display_digits = int(req.cifras) if req.cifras is not None else 6
    prec = max(6, display_digits)

    return NumericalResponse(
        success=True,
        method="Newton-Raphson",
        converged=converged,
        summary={
            "Raíz aproximada": format_val_prec(last_root, display_digits),
            "Iteraciones": len(steps),
            "Error final (%)": steps[-1]["error aproximado (%)"] if steps else 0.0,
            "Estado": status_text
        },
        steps=steps,
        plot_data=plot_data,
        details=f"{stop_reason} [Derivada empleada: f'(x) = {df_symbolic}]"
    )
