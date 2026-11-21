const BASE_URL = (import.meta.env.VITE_API_URL || (window.location.port === '8000' ? '' : 'http://127.0.0.1:8000')).replace(/\/+$/, '');

// Mapeo entre el ID del método en frontend y el endpoint en FastAPI
const ENDPOINT_MAP = {
  // Raíces
  bis: '/raices/biseccion',
  fal: '/raices/falsa-posicion',
  sec: '/raices/secante',
  new: '/raices/newton-raphson',

  // Integración
  tra: '/integracion/trapecio',
  s13: '/integracion/simpson-13',
  s38: '/integracion/simpson-38',

  // Interpolación y Ajuste
  dir: '/interpolacion/directa',
  reg: '/interpolacion/regresion',

  // Optimización
  sd: '/optimizacion/seccion-dorada'
};

export async function executeNumericalMethod(methodId, formData) {
  const endpoint = ENDPOINT_MAP[methodId];
  if (!endpoint) {
    throw new Error(`Endpoint no configurado para el método: ${methodId}`);
  }

  // Clonar y transformar datos según tipo de campo
  const payload = {};

  for (const [key, rawVal] of Object.entries(formData)) {
    if (rawVal === undefined || rawVal === null || rawVal === '') continue;

    // Campos de listas (ej. x, y, vars, lo, hi)
    if (['x', 'y'].includes(key)) {
      if (typeof rawVal === 'string') {
        const strictNumberRegex = /^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/;
        payload[key] = rawVal
          .split(',')
          .map((v) => v.trim())
          .filter((v) => v.length > 0)
          .map((v) => {
            if (!strictNumberRegex.test(v)) {
              throw new Error(`El valor '${v}' en la lista ${key} no es un número válido.`);
            }
            const num = parseFloat(v);
            if (isNaN(num) || !isFinite(num)) {
              throw new Error(`El valor '${v}' en la lista ${key} no es un número válido.`);
            }
            return num;
          });
      } else {
        payload[key] = rawVal;
      }
    } else if (['lo', 'hi'].includes(key)) {
      if (typeof rawVal === 'string') {
        const strictNumberRegex = /^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/;
        payload[key] = rawVal
          .split(',')
          .map((v) => v.trim())
          .filter((v) => v.length > 0)
          .map((v) => {
            if (strictNumberRegex.test(v)) {
              const num = parseFloat(v);
              return (!isNaN(num) && isFinite(num)) ? num : v;
            }
            // Si es una expresión matemática como "pi", "-pi", "pi/2", enviar el string
            return v;
          });
      } else {
        payload[key] = rawVal;
      }
    } else if (key === 'vars') {
      if (typeof rawVal === 'string') {
        payload[key] = rawVal.split(',').map((v) => v.trim()).filter((v) => v.length > 0);
      } else {
        payload[key] = rawVal;
      }
    } else if (['a', 'b', 'x0', 'x1'].includes(key)) {
      if (typeof rawVal === 'string') {
        const trimmed = rawVal.trim();
        const num = parseFloat(trimmed);
        // Si es un número puro ("1", "2.5", "-3"), usar el float; si contiene símbolos como "pi", "e", enviar el string
        payload[key] = (!isNaN(num) && isFinite(num) && /^-?\d+(\.\d+)?([eE][+-]?\d+)?$/.test(trimmed)) ? num : trimmed;
      } else {
        payload[key] = rawVal;
      }
    } else if (['tol', 'xe'].includes(key)) {
      payload[key] = parseFloat(rawVal);
    } else if (['it', 'n', 'g', 'cifras'].includes(key)) {
      payload[key] = parseInt(rawVal, 10);
    } else {
      payload[key] = rawVal;
    }
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  const data = await response.json();

  if (!response.ok) {
    const errorDetail = data?.detail || 'Error procesando la solicitud en el servidor.';
    throw new Error(typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail));
  }

  return data;
}
