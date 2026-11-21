import math
import numpy as np
from fastapi import APIRouter, HTTPException
from models.schemas import SeccionDoradaRequest, NumericalResponse
from utils.math_parser import parse_function_1d, parse_function_multivar, parse_scalar

router = APIRouter(prefix="/optimizacion", tags=["Métodos de Optimización"])

def get_stop_params(criterio: str | None, cifras: int | None, tol: float | None, it: int | None):
    """
    Determina parámetros de parada según rúbrica:
    - Selector entre cifras significativas (Scarborough) y número de iteraciones.
    - Soporta tolerancia porcentual directa.
    """
    if it is not None and int(it) < 1:
        raise HTTPException(
            status_code=400,
            detail="El número de iteraciones 'it' debe ser un entero mayor o igual a 1."
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
        max_it = 50 if crit == "it" else 100

    return use_error_stop, target_tol_pct, max_it, crit_desc

@router.post("/seccion-dorada", response_model=NumericalResponse)
def resolver_seccion_dorada(req: SeccionDoradaRequest):
    """
    Método de la Sección Áurea (Simple y Multivariada) según rúbrica:
    - Razón áurea phi = (sqrt(5)-1)/2 ≈ 0.6180339887
    - Permite tanto Máximo como Mínimo.
    - Reutiliza el punto interior y su evaluación en cada iteración.
    - Columnas Simple: i, xl, xu, x1, x2, f(x1), f(x2), error aproximado (%)
    - Columnas Multivar: i, xl, xu, x1, x2, f(x1), f(x2), error aproximado (%), coordenada activa, punto actual
    """
    is_multivar = req.tipo and req.tipo.lower().startswith("multi")
    is_max = req.obj and req.obj.lower().replace("á", "a").startswith("max")
    # Para maximizar, multiplicamos por -1 internamente para buscar mínimo de -f
    sign = -1.0 if is_max else 1.0

    use_error_stop, target_tol_pct, max_it, crit_desc = get_stop_params(req.criterio, req.cifras, req.tol, req.it)
    phi = (math.sqrt(5) - 1.0) / 2.0  # ≈ 0.618033988749895

    if not is_multivar:
        # --- CASO UNIVARIADO ---
        if not req.f:
            raise HTTPException(status_code=400, detail="Debe proporcionar la función f(x) para el caso univariado.")
        if req.a is None or req.b is None:
            raise HTTPException(status_code=400, detail="Debe proporcionar los límites xl (a) y xu (b).")

        try:
            raw_f, _ = parse_function_1d(req.f)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        obj_func = lambda x: sign * raw_f(x)
        
        try:
            xl = parse_scalar(req.a, "límite inferior xl (a)")
            xu = parse_scalar(req.b, "límite superior xu (b)")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        if xl == xu:
            raise HTTPException(status_code=400, detail="Los límites xl y xu deben ser distintos.")
        if xl > xu:
            xl, xu = xu, xl

        d = phi * (xu - xl)
        x1 = xu - d
        x2 = xl + d
        try:
            f1 = obj_func(x1)
            f2 = obj_func(x2)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error evaluando la función en los puntos interiores iniciales: {str(e)}")

        steps = []
        converged = False
        prev_x_opt = None

        for i in range(1, max_it + 1):
            curr_opt_x = x1 if f1 < f2 else x2
            
            # Error aproximado porcentual según fórmula estándar de sección áurea:
            # error (%) = (1 - phi) * |(xu - xl) / opt_x| * 100 %
            if curr_opt_x != 0:
                err_pct = (1.0 - phi) * abs((xu - xl) / curr_opt_x) * 100.0
            else:
                err_pct = (1.0 - phi) * abs(xu - xl) * 100.0

            # Guardar valores reales de la función del usuario f(x), no la transformada por el signo
            f_real_x1 = raw_f(x1)
            f_real_x2 = raw_f(x2)

            steps.append({
                "i": i,
                "xl": round(xl, 6),
                "xu": round(xu, 6),
                "x1": round(x1, 6),
                "x2": round(x2, 6),
                "f(x1)": round(f_real_x1, 6),
                "f(x2)": round(f_real_x2, 6),
                "error aproximado (%)": round(err_pct, 6)
            })

            if use_error_stop and err_pct < target_tol_pct:
                converged = True
                break

            # Reutilización estricta del punto interior:
            if f1 < f2:
                # El nuevo intervalo es [xl, x2]
                xu = x2
                x2 = x1
                f2 = f1  # <--- REUTILIZACIÓN: x1 pasa a ser x2 sin reevaluar f
                d = phi * (xu - xl)
                x1 = xu - d
                try:
                    f1 = obj_func(x1)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Error evaluando f(x1) en iteración {i}: {str(e)}")
            else:
                # El nuevo intervalo es [x1, xu]
                xl = x1
                x1 = x2
                f1 = f2  # <--- REUTILIZACIÓN: x2 pasa a ser x1 sin reevaluar f
                d = phi * (xu - xl)
                x2 = xl + d
                try:
                    f2 = obj_func(x2)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Error evaluando f(x2) en iteración {i}: {str(e)}")

            prev_x_opt = curr_opt_x

        final_opt_x = (xl + xu) / 2.0
        try:
            final_opt_f = raw_f(final_opt_x)
        except Exception:
            final_opt_f = raw_f(curr_opt_x)

        margin = abs(xu - xl) * 0.25 if xu != xl else 1.0
        x_min = min(xl, xu, final_opt_x) - margin
        x_max = max(xl, xu, final_opt_x) + margin
        x_curve = np.linspace(x_min, x_max, 180).tolist()
        y_curve = []
        for xv in x_curve:
            try:
                y_curve.append(raw_f(xv))
            except Exception:
                y_curve.append(None)

        error_evolution = [
            {"iter": s["i"], "error": s["error aproximado (%)"]}
            for s in steps
        ]

        if not use_error_stop:
            converged = None
            status_text = "Iteraciones programadas completadas"
            stop_msg = f"Finalizado en {len(steps)} de {max_it} iteraciones programadas."
        else:
            if converged:
                status_text = "Convergencia alcanzada según el criterio establecido"
                stop_msg = f"Convergencia alcanzada en {len(steps)} iteraciones: error ({steps[-1]['error aproximado (%)']:.6g} %) < criterio ({target_tol_pct:.6g} %)."
            else:
                status_text = "Máximo de iteraciones alcanzado sin convergencia"
                stop_msg = f"Límite de iteraciones alcanzado ({len(steps)} de {max_it}) sin alcanzar la tolerancia requerida ({target_tol_pct:.6g} %)."

        display_digits = int(req.cifras) if req.cifras is not None else 6

        return NumericalResponse(
            success=True,
            method=f"Sección Áurea ({req.obj})",
            converged=converged,
            summary={
                "Punto óptimo": round(final_opt_x, max(6, display_digits)),
                "Valor f(x*)": round(final_opt_f, max(6, display_digits)),
                "Iteraciones": len(steps),
                "Error final (%)": steps[-1]["error aproximado (%)"] if steps else 0.0,
                "Estado": status_text
            },
            steps=steps,
            plot_data={
                "x_curve": x_curve,
                "y_curve": y_curve,
                "opt_x": final_opt_x,
                "opt_f": final_opt_f,
                "x_label": "x",
                "y_label": "f(x)",
                "error_evolution": error_evolution,
                "error_x_label": "Iteración (i)",
                "error_y_label": "Error aproximado (%)"
            },
            details=f"Punto óptimo x* ≈ {final_opt_x:.6f} con f(x*) ≈ {final_opt_f:.6f}. {stop_msg}"
        )

    else:
        # --- CASO MULTIVARIADO (Búsqueda por coordenadas con Sección Áurea) ---
        if not req.fm:
            raise HTTPException(status_code=400, detail="Debe proporcionar la función multivariada f(x, y, ...).")
        if not req.vars or len(req.vars) < 2:
            raise HTTPException(status_code=400, detail="Debe especificar al menos 2 variables (ej. ['x', 'y']).")
        if not req.lo or not req.hi or len(req.lo) != len(req.vars) or len(req.hi) != len(req.vars):
            raise HTTPException(status_code=400, detail="Los límites inferiores y superiores deben coincidir con la cantidad de variables.")

        try:
            parsed_lo = [parse_scalar(l, f"límite inferior de {v}") for l, v in zip(req.lo, req.vars)]
            parsed_hi = [parse_scalar(h, f"límite superior de {v}") for h, v in zip(req.hi, req.vars)]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        try:
            raw_f = parse_function_multivar(req.fm, req.vars)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        num_vars = len(req.vars)
        current_point = [0.5 * (l + h) for l, h in zip(parsed_lo, parsed_hi)]
        steps = []
        converged = False

        # Tolerancia interna adaptativa para la optimización 1D a lo largo de cada eje
        inner_tol = min(target_tol_pct * 0.05, 1e-4) if use_error_stop else 1e-6
        point_at_round_start = list(current_point)
        last_round_error = 100.0

        for it_idx in range(1, max_it + 1):
            dim = (it_idx - 1) % num_vars
            var_name = req.vars[dim]

            if dim == 0:
                point_at_round_start = list(current_point)

            xl_dim = float(parsed_lo[dim])
            xu_dim = float(parsed_hi[dim])
            if xl_dim > xu_dim:
                xl_dim, xu_dim = xu_dim, xl_dim

            def f_line(alpha, d_idx=dim):
                pt = list(current_point)
                pt[d_idx] = alpha
                return sign * raw_f(pt)

            d = phi * (xu_dim - xl_dim)
            x1 = xu_dim - d
            x2 = xl_dim + d
            try:
                f1 = f_line(x1)
                f2 = f_line(x2)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error evaluando f multivariada: {str(e)}")

            # Optimizar a lo largo de la coordenada activa reutilizando puntos interiores
            max_inner = 150
            for _ in range(max_inner):
                if f1 < f2:
                    xu_dim = x2
                    x2 = x1
                    f2 = f1  # reutilizado
                    d = phi * (xu_dim - xl_dim)
                    x1 = xu_dim - d
                    f1 = f_line(x1)
                else:
                    xl_dim = x1
                    x1 = x2
                    f1 = f2  # reutilizado
                    d = phi * (xu_dim - xl_dim)
                    x2 = xl_dim + d
                    f2 = f_line(x2)

                x_opt_curr = x1 if f1 < f2 else x2
                denom = abs(x_opt_curr) if abs(x_opt_curr) > 1e-12 else 1.0
                err_inner = (1.0 - phi) * (abs(xu_dim - xl_dim) / denom) * 100.0
                if err_inner < inner_tol:
                    break

            best_dim_val = x1 if f1 < f2 else x2
            old_dim_val = current_point[dim]
            current_point[dim] = best_dim_val

            # Error de la dimensión individual
            denom_dim = abs(best_dim_val) if abs(best_dim_val) > 1e-12 else 1.0
            err_dim_pct = (abs(best_dim_val - old_dim_val) / denom_dim) * 100.0

            # Al completar una ronda completa de todas las coordenadas, evaluamos la convergencia vectorial
            if dim == num_vars - 1:
                diffs = [abs(current_point[d] - point_at_round_start[d]) for d in range(num_vars)]
                denoms = [abs(current_point[d]) if abs(current_point[d]) > 1e-12 else 1.0 for d in range(num_vars)]
                last_round_error = max((diff / den) * 100.0 for diff, den in zip(diffs, denoms))
                step_error = last_round_error
            else:
                step_error = err_dim_pct

            pt_str = f"({', '.join([f'{v}={val:.4f}' for v, val in zip(req.vars, current_point)])})"

            # Rúbrica exige: i, xl, xu, x1, x2, f(x1), f(x2), error aproximado (%); en multivariada: coordenada activa, punto actual
            steps.append({
                "i": it_idx,
                "xl": round(xl_dim, 6),
                "xu": round(xu_dim, 6),
                "x1": round(x1, 6),
                "x2": round(x2, 6),
                "f(x1)": round(sign * f1, 6),
                "f(x2)": round(sign * f2, 6),
                "error aproximado (%)": round(step_error, 6),
                "coordenada activa": var_name,
                "punto actual": pt_str
            })

            # Parada por convergencia sólo después de una ronda completa
            if use_error_stop and (dim == num_vars - 1) and (last_round_error < target_tol_pct) and (it_idx >= num_vars):
                converged = True
                break

        final_f = raw_f(current_point)
        pt_final_str = f"({', '.join([f'{v}={val:.4f}' for v, val in zip(req.vars, current_point)])})"

        error_evolution = [
            {"iter": s["i"], "error": s["error aproximado (%)"]}
            for s in steps
        ]

        if not use_error_stop:
            converged = None
            status_text = "Iteraciones programadas completadas"
        else:
            status_text = "Convergencia alcanzada según el criterio establecido" if converged else "Número máximo de iteraciones alcanzado sin convergencia"

        display_digits = int(req.cifras) if req.cifras is not None else 6
        pt_final_str = f"({', '.join([f'{v}={val:.{display_digits}f}' for v, val in zip(req.vars, current_point)])})"

        return NumericalResponse(
            success=True,
            method=f"Sección Áurea Multivariada ({req.obj})",
            converged=converged,
            summary={
                "Punto óptimo": pt_final_str,
                "Valor f(x*)": round(final_f, max(6, display_digits)),
                "Iteraciones": len(steps),
                "Error final (%)": steps[-1]["error aproximado (%)"] if steps else 0.0,
                "Estado": status_text
            },
            steps=steps,
            plot_data={
                "error_evolution": error_evolution,
                "error_x_label": "Iteración (ciclo por coordenada)",
                "error_y_label": "Error aproximado (%)"
            },
            details=f"Punto óptimo multivariado: {pt_final_str} con f(x*) = {final_f:.6f}. {status_text}."
        )
