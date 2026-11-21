import math
import re
import numpy as np
import sympy as sp

# Diccionario seguro de funciones y constantes matemáticas para numpy/eval
MATH_NAMES = {
    'sin': np.sin,
    'cos': np.cos,
    'tan': np.tan,
    'asin': np.arcsin,
    'acos': np.arccos,
    'atan': np.arctan,
    'arcsin': np.arcsin,
    'arccos': np.arccos,
    'arctan': np.arctan,
    'sinh': np.sinh,
    'cosh': np.cosh,
    'tanh': np.tanh,
    'exp': np.exp,
    'log': np.log,
    'ln': np.log,
    'log10': np.log10,
    'sqrt': np.sqrt,
    'abs': np.abs,
    'pi': np.pi,
    'e': np.e,
}

ALLOWED_FUNCS = {
    'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'arcsin', 'arccos', 'arctan',
    'sinh', 'cosh', 'tanh', 'exp', 'log', 'ln', 'log10', 'sqrt', 'abs', 'Abs'
}

SYMPY_LOCALS = {
    'e': sp.E,
    'E': sp.E,
    'pi': sp.pi,
    'ln': sp.log,
    'log': sp.log,
    'log10': lambda arg: sp.log(arg, 10),
    'exp': sp.exp,
    'sin': sp.sin,
    'cos': sp.cos,
    'tan': sp.tan,
    'asin': sp.asin,
    'acos': sp.acos,
    'atan': sp.atan,
    'arcsin': sp.asin,
    'arccos': sp.acos,
    'arctan': sp.atan,
    'sinh': sp.sinh,
    'cosh': sp.cosh,
    'tanh': sp.tanh,
    'sqrt': sp.sqrt,
    'abs': sp.Abs,
}

def clean_expr_string(expr: str) -> str:
    """Reemplaza notaciones comunes como ^ por ** y normaliza espacios."""
    if not expr or not expr.strip():
        raise ValueError("La expresión matemática no puede estar vacía.")
    expr = expr.strip()
    expr = expr.replace('^', '**')
    expr = re.sub(r'\bln\b', 'log', expr)
    # Soportar multiplicación implícita con constantes o funciones comunes: ej. 2pi -> 2*pi, 2e -> 2*e
    expr = re.sub(r'(\d+)\s*([a-zA-Z(])', r'\1*\2', expr)
    return expr

def validate_sympy_expr_1d(sym_expr: sp.Expr, expr_str: str):
    """Verifica que la expresión solo use la variable x y funciones permitidas."""
    # Verificar funciones
    for fn in sym_expr.atoms(sp.Function):
        fn_name = fn.func.__name__
        if fn_name not in ALLOWED_FUNCS:
            raise ValueError(
                f"Función no reconocida o no permitida: '{fn_name}'. "
                f"Funciones matemáticas válidas: sin, cos, tan, exp, log, ln, sqrt, abs, etc."
            )
    
    # Verificar variables / símbolos
    for s in sym_expr.free_symbols:
        if s.name != 'x' and s.name not in ('e', 'pi'):
            raise ValueError(
                f"Símbolo o variable no reconocida: '{s.name}'. "
                f"Para este método únicamente se permite la variable independiente 'x'."
            )

def parse_function_1d(expr_str: str):
    """
    Retorna una función f(x) evaluable numéricamente usando numpy/math de forma segura.
    Valida sintaxis, variables y funciones matemáticas permitidas.
    """
    clean_expr = clean_expr_string(expr_str)
    
    # Comprobar sintaxis con sympy
    x = sp.Symbol('x')
    try:
        sym_expr = sp.sympify(clean_expr, locals=SYMPY_LOCALS)
    except Exception as e:
        raise ValueError(f"Expresión matemática inválida '{expr_str}': {str(e)}")
    
    # Validar que no contenga funciones o símbolos no permitidos (ej. foo(x))
    validate_sympy_expr_1d(sym_expr, expr_str)

    def f(val):
        env = dict(MATH_NAMES)
        env['x'] = float(val) if not isinstance(val, np.ndarray) else val
        try:
            res = eval(clean_expr, {"__builtins__": {}}, env)
            float_res = float(res)
            if math.isnan(float_res) or math.isinf(float_res):
                raise ValueError(f"La función produce un valor no finito ({float_res}) en x = {val}")
            return float_res
        except ZeroDivisionError:
            raise ValueError(f"División por cero evaluando la función en x = {val}")
        except ValueError as ve:
            raise ve
        except Exception as e:
            raise ValueError(f"Error evaluando la función en x = {val}: {str(e)}")

    # Comprobación preliminar de evaluación segura en un valor de prueba (ej. x = 1.0)
    # Si falla por dominio (ej. log(x-5)), se ignora aquí y se evaluará en el rango real
    try:
        f(1.0)
    except (ZeroDivisionError, ValueError):
        pass
    except Exception as e:
        raise ValueError(f"Error en la estructura de la función: {str(e)}")

    return f, sym_expr

def parse_scalar(val, param_name: str = "parámetro") -> float:
    """
    Parsea e interpreta de forma segura un número o constante matemática como 'pi', 'e', '2*pi', etc.
    """
    if val is None:
        raise ValueError(f"El valor de {param_name} no puede estar vacío.")
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s:
        raise ValueError(f"El valor de {param_name} no puede estar vacío.")
    try:
        return float(s)
    except ValueError:
        pass
    try:
        clean = clean_expr_string(s)
        locals_dict = {'pi': sp.pi, 'e': sp.E, 'E': sp.E, 'PI': sp.pi}
        expr = sp.sympify(clean, locals=locals_dict)
        res = float(expr.evalf())
        if math.isnan(res) or math.isinf(res):
            raise ValueError(f"El valor de {param_name} evaluó a un número no finito ({res}).")
        return res
    except Exception as e:
        raise ValueError(f"No se pudo interpretar el valor numérico '{val}' para {param_name}: {str(e)}")

def parse_derivative_1d(expr_str: str, df_str: str | None = None):
    """
    Si df_str viene dada, la parsea y valida. Si no, calcula la derivada simbólica analítica usando sympy.
    """
    clean_expr = clean_expr_string(expr_str)
    x = sp.Symbol('x')
    
    try:
        sym_expr = sp.sympify(clean_expr, locals=SYMPY_LOCALS)
    except Exception as e:
        raise ValueError(f"Expresión matemática inválida '{expr_str}': {str(e)}")
    
    validate_sympy_expr_1d(sym_expr, expr_str)

    if df_str and df_str.strip():
        clean_df = clean_expr_string(df_str)
        try:
            sym_df = sp.sympify(clean_df, locals=SYMPY_LOCALS)
        except Exception as e:
            raise ValueError(f"Expresión de derivada inválida '{df_str}': {str(e)}")
        validate_sympy_expr_1d(sym_df, df_str)
    else:
        try:
            sym_df = sp.diff(sym_expr, x)
        except Exception as e:
            raise ValueError(f"No fue posible calcular la derivada analítica de '{expr_str}': {str(e)}")
        
        # Verificar si sympy dejó una derivada sin evaluar
        if sym_df.atoms(sp.Derivative):
            raise ValueError(
                f"No fue posible calcular la derivada de '{expr_str}'. "
                "Por favor proporcione la derivada f'(x) manualmente."
            )

    clean_df_eval = str(sym_df).replace('**', '^')

    def df(val):
        env = dict(MATH_NAMES)
        env['x'] = float(val) if not isinstance(val, np.ndarray) else val
        try:
            res = eval(clean_expr_string(str(sym_df)), {"__builtins__": {}}, env)
            float_res = float(res)
            if math.isnan(float_res) or math.isinf(float_res):
                raise ValueError(f"La derivada produce un valor no finito ({float_res}) en x = {val}")
            return float_res
        except ZeroDivisionError:
            raise ValueError(f"División por cero evaluando la derivada en x = {val}")
        except ValueError as ve:
            raise ve
        except Exception as e:
            raise ValueError(f"Error evaluando la derivada en x = {val}: {str(e)}")

    return df, clean_df_eval

def parse_function_multivar(expr_str: str, var_names: list[str]):
    """
    Parsea funciones multivariadas f(x, y, ...).
    """
    clean_expr = clean_expr_string(expr_str)
    
    try:
        sym_expr = sp.sympify(clean_expr, locals=SYMPY_LOCALS)
    except Exception as e:
        raise ValueError(f"Expresión multivariada inválida '{expr_str}': {str(e)}")

    for fn in sym_expr.atoms(sp.Function):
        fn_name = fn.func.__name__
        if fn_name not in ALLOWED_FUNCS:
            raise ValueError(f"Función no reconocida o no permitida: '{fn_name}'.")

    allowed_vars = set(var_names) | {'e', 'pi'}
    for s in sym_expr.free_symbols:
        if s.name not in allowed_vars:
            raise ValueError(
                f"Variable no reconocida: '{s.name}'. "
                f"Variables declaradas permitidas: {', '.join(var_names)}."
            )

    def f(point: list[float] | np.ndarray):
        env = dict(MATH_NAMES)
        for name, val in zip(var_names, point):
            env[name] = float(val)
        try:
            res = eval(clean_expr, {"__builtins__": {}}, env)
            return float(res)
        except ZeroDivisionError:
            raise ValueError(f"División por cero evaluando la función en {point}")
        except Exception as e:
            raise ValueError(f"Error evaluando la función en {point}: {str(e)}")

    return f
