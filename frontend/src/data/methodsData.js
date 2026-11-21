const F = {
  fx: { t: 'fx', k: 'f', l: 'Función f(x)', ph: 'x^3 - x - 2', hint: 'Usa x, ^, sin(x), cos(x), exp(x), log(x), sqrt(x), etc.' },
  a: { t: 'num', k: 'a', l: 'Límite inferior (xl / a)', v: '1' },
  b: { t: 'num', k: 'b', l: 'Límite superior (xu / b)', v: '2' },
  cifras: { t: 'num', k: 'cifras', l: 'Cifras significativas (m)', v: '4', hint: 'Tolerancia: εs = 0.5 × 10^(2-m) %' },
  tol: { t: 'num', k: 'tol', l: 'Tolerancia porcentual directa (%)', v: '0.005', opt: 1 },
  it: { t: 'num', k: 'it', l: 'Iteraciones máximas (N)', v: '50' }
};

function cloneField(field, overrides) {
  return { ...field, ...overrides };
}

const raizBase = [F.fx, F.a, F.b, F.cifras, F.it];

export const METHODS_DATA = {
  raices: {
    n: 'Raíces',
    s: 'f(x) = 0',
    m: [
      {
        id: 'bis',
        n: 'Bisección',
        d: 'Divide el intervalo [xl, xu] a la mitad en cada paso verificando f(xl)·f(xr) < 0.',
        f: raizBase,
        r: 'bis'
      },
      {
        id: 'fal',
        n: 'Falsa posición',
        d: 'Usa la recta secante entre (xl, f(xl)) y (xu, f(xu)) para estimar la raíz.',
        f: raizBase,
        r: 'fal'
      },
      {
        id: 'sec',
        n: 'Secante',
        d: 'Aproxima la raíz utilizando dos puntos iniciales x_(i-1) y x_i sin requerir derivada.',
        f: [
          F.fx,
          cloneField(F.a, { k: 'x0', l: 'Punto inicial x_(i−1)', v: '1' }),
          cloneField(F.b, { k: 'x1', l: 'Punto inicial x_i', v: '2' }),
          F.cifras,
          F.it
        ],
        r: 'sec'
      },
      {
        id: 'new',
        n: 'Newton-Raphson',
        d: 'Utiliza la derivada f′(x) para acercarse rápidamente a la raíz desde un valor inicial x0.',
        f: [
          F.fx,
          { t: 'fx', k: 'df', l: 'Derivada f′(x) (opcional)', ph: '3*x^2 - 1', hint: 'Si se omite, se calcula simbólicamente de forma automática' },
          cloneField(F.a, { k: 'x0', l: 'Punto inicial x0', v: '1.5' }),
          F.cifras,
          F.it
        ],
        r: 'new'
      }
    ]
  },
  integ: {
    n: 'Integración',
    s: '∫ f(x) dx',
    m: [
      {
        id: 'tra',
        n: 'Trapecio',
        d: 'Aproxima el área bajo la curva mediante trapecios para n subintervalos.',
        f: [
          cloneField(F.fx, { ph: 'sin(x)', v: 'sin(x)' }),
          cloneField(F.a, { l: 'Límite inferior a', v: '0' }),
          cloneField(F.b, { l: 'Límite superior b', v: 'pi' }),
          { t: 'num', k: 'n', l: 'Subintervalos objetivo (n ≥ 1, opcional)', v: '6', opt: 1 },
          F.cifras,
          F.it
        ],
        r: 'tra'
      },
      {
        id: 's13',
        n: 'Simpson 1/3',
        d: 'Aproxima la integral con parábolas. Exige que n sea par (n ≥ 2).',
        f: [
          cloneField(F.fx, { ph: 'sin(x)', v: 'sin(x)' }),
          cloneField(F.a, { l: 'Límite inferior a', v: '0' }),
          cloneField(F.b, { l: 'Límite superior b', v: 'pi' }),
          { t: 'num', k: 'n', l: 'Subintervalos objetivo (n par, opcional)', v: '6', opt: 1 },
          F.cifras,
          F.it
        ],
        r: 's13'
      },
      {
        id: 's38',
        n: 'Simpson 3/8',
        d: 'Aproxima con polinomios cúbicos. Exige que n sea múltiplo de 3 (n ≥ 3).',
        f: [
          cloneField(F.fx, { ph: 'sin(x)', v: 'sin(x)' }),
          cloneField(F.a, { l: 'Límite inferior a', v: '0' }),
          cloneField(F.b, { l: 'Límite superior b', v: 'pi' }),
          { t: 'num', k: 'n', l: 'Subintervalos objetivo (n múltiplo de 3, opcional)', v: '9', opt: 1 },
          F.cifras,
          F.it
        ],
        r: 's38'
      }
    ]
  },
  interp: {
    n: 'Interpolación y Ajuste',
    s: 'Datos y curvas',
    m: [
      {
        id: 'dir',
        n: 'Interpolación directa',
        d: 'Calcula el polinomio único de grado n que pasa por n+1 puntos resolviendo el sistema.',
        f: [
          { t: 'list', k: 'x', l: 'Valores de x', ph: '1, 2, 3', v: '1, 2, 3', hint: 'Separados por comas o carga un archivo' },
          { t: 'list', k: 'y', l: 'Valores de y (f(x))', ph: '1, 8, 27', v: '1, 8, 27', hint: 'Misma cantidad que x' },
          { t: 'num', k: 'xe', l: 'Evaluar en x =', v: '2.5', hint: 'Punto donde se evaluará el polinomio resultante' }
        ],
        r: 'dir'
      },
      {
        id: 'reg',
        n: 'Regresión por mínimos cuadrados',
        d: 'Ajuste de curvas por mínimos cuadrados. Admite modelo Lineal, Polinomial, Exponencial y Potencia.',
        f: [
          { t: 'list', k: 'x', l: 'Valores de x', ph: '1, 2, 3, 4', v: '1, 2, 3, 4', hint: 'Separados por comas o carga un archivo' },
          { t: 'list', k: 'y', l: 'Valores de y (f(x))', ph: '2, 4.1, 5.9, 8.2', v: '2, 4.1, 5.9, 8.2', hint: 'Misma cantidad que x' },
          { t: 'sel', k: 'mod', l: 'Modelo de regresión', o: ['Lineal', 'Polinomial', 'Exponencial', 'Potencia'] },
          { t: 'num', k: 'g', l: 'Grado del polinomio (solo Polinomial)', v: '2', opt: 1 },
          { t: 'num', k: 'xe', l: 'Evaluar en x = (opcional)', v: '2.5', opt: 1, hint: 'Evalúa la ecuación del modelo en este punto' }
        ],
        r: 'reg'
      }
    ]
  },
  opt: {
    n: 'Optimización',
    s: 'Máximos y mínimos',
    m: [
      {
        id: 'sd',
        n: 'Sección Áurea',
        d: 'Búsqueda del óptimo (mínimo o máximo) mediante la razón áurea con reutilización de puntos interiores.',
        sel: { k: 'tipo', l: 'Tipo de problema', o: ['Univariada', 'Multivariada'] },
        f: [
          { t: 'sel', k: 'obj', l: 'Objetivo', o: ['Máximo', 'Mínimo'] },
          cloneField(F.fx, { ph: '2*sin(x) - x^2/10', v: '2*sin(x) - x^2/10', w: 'Univariada' }),
          cloneField(F.a, { l: 'Límite inferior xl (a)', v: '0', w: 'Univariada' }),
          cloneField(F.b, { l: 'Límite superior xu (b)', v: '4', w: 'Univariada' }),
          cloneField(F.fx, {
            k: 'fm',
            l: 'Función f(x, y)',
            ph: '(x-1)^2 + (y+2)^2',
            v: '(x-1)^2 + (y+2)^2',
            w: 'Multivariada',
            hint: 'Función con variables x, y, z... declaradas abajo'
          }),
          { t: 'list', k: 'vars', l: 'Variables', ph: 'x, y', v: 'x, y', w: 'Multivariada' },
          { t: 'list', k: 'lo', l: 'Límites inferiores', ph: '-5, -5', v: '-5, -5', w: 'Multivariada' },
          { t: 'list', k: 'hi', l: 'Límites superiores', ph: '5, 5', v: '5, 5', w: 'Multivariada' },
          F.cifras,
          F.it
        ],
        r: 'sd'
      }
    ]
  }
};

export const STAT_CONFIG = {
  bis: [
    ['Raíz aproximada', 'xr'],
    ['Iteraciones', 'n'],
    ['Error final (%)', 'εa%']
  ],
  fal: [
    ['Raíz aproximada', 'xr'],
    ['Iteraciones', 'n'],
    ['Error final (%)', 'εa%']
  ],
  new: [
    ['Raíz aproximada', 'x*'],
    ['Iteraciones', 'n'],
    ['Error final (%)', 'εa%']
  ],
  sec: [
    ['Raíz aproximada', 'x*'],
    ['Iteraciones', 'n'],
    ['Error final (%)', 'εa%']
  ],
  tra: [
    ['Valor de la integral', 'I'],
    ['Subintervalos', 'n'],
    ['Error final (%)', 'ε%']
  ],
  s13: [
    ['Valor de la integral', 'I'],
    ['Subintervalos', 'n'],
    ['Error final (%)', 'ε%']
  ],
  s38: [
    ['Valor de la integral', 'I'],
    ['Subintervalos', 'n'],
    ['Error final (%)', 'ε%']
  ],
  dir: [
    ['Valor interpolado p(x)', 'p(xe)'],
    ['Grado del polinomio', 'n'],
    ['Puntos cargados', 'pts']
  ],
  reg: [
    ['Ecuación del modelo', 'y(x)'],
    ['Coeficiente R²', 'R²'],
    ['Error cuadrático (Σe²)', 'Σe²']
  ],
  sd: [
    ['Punto óptimo', 'x*'],
    ['Valor f(x*)', 'f(x*)'],
    ['Error final (%)', 'εa%'],
    ['Iteraciones', 'n']
  ]
};

export const PLOT_TITLES = {
  bis: 'Bisección: Función y evolución del error',
  fal: 'Falsa Posición: Función y evolución del error',
  new: 'Newton-Raphson: Tangente, función y evolución del error',
  sec: 'Secante: Función y evolución del error',
  tra: 'Regla del Trapecio: Área bajo la curva y convergencia',
  s13: 'Simpson 1/3: Área bajo la curva y convergencia',
  s38: 'Simpson 3/8: Área bajo la curva y convergencia',
  dir: 'Interpolación polinómica: datos y curva',
  reg: 'Regresión: datos y curva ajustada',
  sd: 'Sección Áurea: Función, búsqueda y evolución del error'
};

// Columnas mínimas exactas exigidas por la rúbrica oficial (Páginas 1 y 2)
export const TABLE_COLUMNS = {
  bis: ['i', 'xl', 'xu', 'xr', 'f(xl)', 'f(xr)', 'f(xl)·f(xr)', 'error aproximado (%)'],
  fal: ['i', 'xl', 'xu', 'xr', 'f(xl)', 'f(xu)', 'f(xr)', 'error aproximado (%)'],
  new: ['i', 'x_i', 'f(x_i)', "f'(x_i)", 'x_(i+1)', 'error aproximado (%)'],
  sec: ['i', 'x_(i−1)', 'x_i', 'f(x_(i−1))', 'f(x_i)', 'x_(i+1)', 'error aproximado (%)'],
  tra: ['Iteración', 'n', 'h', 'integral aproximada', 'error aproximado (%)'],
  s13: ['Iteración', 'n', 'h', 'integral aproximada', 'error aproximado (%)'],
  s38: ['Iteración', 'n', 'h', 'integral aproximada', 'error aproximado (%)'],
  dir: ['i', 'xᵢ', 'yᵢ', 'Fila Vandermonde V[i,:]', 'P(xᵢ) calculado'],
  reg: ['i', 'xᵢ', 'yᵢ', 'ŷᵢ (predicho)', 'Residuo eᵢ'],
  sd: ['i', 'xl', 'xu', 'x1', 'x2', 'f(x1)', 'f(x2)', 'error aproximado (%)'],
  sd_multi: ['i', 'xl', 'xu', 'x1', 'x2', 'f(x1)', 'f(x2)', 'error aproximado (%)', 'coordenada activa', 'punto actual']
};
