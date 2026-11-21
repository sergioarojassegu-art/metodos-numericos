import React, { useState, useEffect, useRef } from 'react';

export default function MethodForm({ currentMethod, onCalculate, onResetResults }) {
  const [formData, setFormData] = useState({});
  const [badFields, setBadFields] = useState({});
  const [errorMessage, setErrorMessage] = useState('');
  
  // Selector claro de criterio de parada: 'cifras' (Cifras significativas) o 'it' (Número de iteraciones)
  const [criterio, setCriterio] = useState('cifras');
  const [cifrasVal, setCifrasVal] = useState('4');

  // Estado para la carga de archivos en Interpolación y Regresión
  const [fileColumns, setFileColumns] = useState([]);
  const [fileRawData, setFileRawData] = useState([]);
  const [selectedColX, setSelectedColX] = useState('');
  const [selectedColY, setSelectedColY] = useState('');
  const [uploadedFileName, setUploadedFileName] = useState('');
  const fileInputRef = useRef(null);

  const isDataMethod = currentMethod.id === 'dir' || currentMethod.id === 'reg';
  const hasStoppingCriteria = currentMethod.f.some(
    (f) => f.k === 'cifras' || f.k === 'tol' || f.k === 'it'
  );

  // Reiniciar estado cuando cambia de método
  useEffect(() => {
    const initialData = {};
    if (currentMethod.sel) {
      initialData[currentMethod.sel.k] = currentMethod.sel.o[0];
    }
    currentMethod.f.forEach((field) => {
      if (field.v !== undefined) {
        initialData[field.k] = field.v;
      } else if (field.t === 'sel' && field.o && field.o.length > 0) {
        initialData[field.k] = field.o[0];
      } else {
        initialData[field.k] = '';
      }
    });

    initialData.criterio = 'cifras';
    initialData.cifras = '4';
    setCriterio('cifras');
    setCifrasVal('4');
    setFormData(initialData);
    setBadFields({});
    setErrorMessage('');
    setFileColumns([]);
    setFileRawData([]);
    setUploadedFileName('');
    onResetResults();
  }, [currentMethod]);

  const currentTipo = formData[currentMethod.sel?.k] || (currentMethod.sel ? currentMethod.sel.o[0] : null);

  const isFieldVisible = (field) => {
    if (field.w && field.w !== currentTipo) return false;
    // Ocultar grado g si el modelo no es Polinomial
    if (field.k === 'g' && formData.mod && formData.mod !== 'Polinomial') {
      return false;
    }
    // Criterios de parada gestionados en el bloque especial
    if (field.k === 'cifras' || field.k === 'tol' || (field.k === 'it' && hasStoppingCriteria)) {
      return false;
    }
    return true;
  };

  const handleInputChange = (key, value) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
    if (badFields[key]) {
      setBadFields((prev) => ({ ...prev, [key]: false }));
    }
  };

  const handleCriterioChange = (nuevoCriterio) => {
    setCriterio(nuevoCriterio);
    setFormData((prev) => ({
      ...prev,
      criterio: nuevoCriterio
    }));
  };

  // --- Manejo de Carga de Archivos (CSV, TXT, JSON) ---
  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadedFileName(file.name);
    const reader = new FileReader();

    reader.onload = (event) => {
      try {
        const text = event.target?.result;
        if (typeof text !== 'string') return;

        // Detectar separador (coma, punto y coma, tabulación o espacio)
        const lines = text.trim().split(/\r?\n/).filter(line => line.trim().length > 0);
        if (lines.length < 2) {
          setErrorMessage('El archivo debe tener al menos una fila de encabezados y una de datos.');
          return;
        }

        const firstLine = lines[0];
        let sep = ',';
        if (firstLine.includes(';')) sep = ';';
        else if (firstLine.includes('\t')) sep = '\t';

        const headers = lines[0].split(sep).map(h => h.trim().replace(/^["']|["']$/g, ''));
        const dataRows = [];

        for (let i = 1; i < lines.length; i++) {
          const cells = lines[i].split(sep).map(c => c.trim());
          if (cells.length >= headers.length) {
            const rowObj = {};
            headers.forEach((h, idx) => {
              const num = parseFloat(cells[idx]);
              rowObj[h] = isNaN(num) ? cells[idx] : num;
            });
            dataRows.push(rowObj);
          }
        }

        setFileColumns(headers);
        setFileRawData(dataRows);

        // Preseleccionar columna x e y automáticamente
        const colX = headers[0];
        const colY = headers.length > 1 ? headers[1] : headers[0];
        setSelectedColX(colX);
        setSelectedColY(colY);

        // Extraer valores
        applyColumnSelection(colX, colY, dataRows);
      } catch (err) {
        setErrorMessage('Error al procesar el archivo: ' + err.message);
      }
    };

    reader.readAsText(file);
  };

  const applyColumnSelection = (colX, colY, dataRows) => {
    if (!colX || !colY || !dataRows || dataRows.length === 0) {
      setErrorMessage('Selecciona columnas válidas del archivo.');
      return;
    }

    const validPairs = [];
    let discardedRows = 0;

    dataRows.forEach((r, idx) => {
      const valX = r[colX];
      const valY = r[colY];
      const numX = typeof valX === 'number' ? valX : parseFloat(valX);
      const numY = typeof valY === 'number' ? valY : parseFloat(valY);

      if (!isNaN(numX) && isFinite(numX) && !isNaN(numY) && isFinite(numY)) {
        validPairs.push({ x: numX, y: numY });
      } else {
        discardedRows++;
      }
    });

    if (validPairs.length === 0) {
      setErrorMessage(`No se encontraron pares (x, y) numéricos válidos en las columnas seleccionadas.`);
      return;
    }

    const listX = validPairs.map(p => p.x);
    const listY = validPairs.map(p => p.y);

    setFormData(prev => ({
      ...prev,
      x: listX.join(', '),
      y: listY.join(', ')
    }));

    if (discardedRows > 0) {
      setErrorMessage(`Archivo cargado: ${validPairs.length} pares válidos extraídos. Se descartaron ${discardedRows} fila(s) incompletas o no numéricas.`);
    } else {
      setErrorMessage('');
    }
  };

  const handleSelectColX = (col) => {
    setSelectedColX(col);
    applyColumnSelection(col, selectedColY, fileRawData);
  };

  const handleSelectColY = (col) => {
    setSelectedColY(col);
    applyColumnSelection(selectedColX, col, fileRawData);
  };

  // Validación y envío
  const handleSubmit = (e) => {
    e.preventDefault();
    const newBad = {};
    let badCount = 0;
    let customErr = '';

    currentMethod.f.forEach((field) => {
      if (!isFieldVisible(field)) return;

      const isOptional = field.opt || field.k === 'df' || field.k === 'xe';
      const val = formData[field.k] !== undefined ? String(formData[field.k]).trim() : '';

      if (!isOptional && val === '') {
        newBad[field.k] = true;
        badCount++;
      }
    });

    // Validaciones específicas para Simpson 1/3 y Simpson 3/8 si se proporciona n
    const isIntegrationMethod = currentMethod.id === 'tra' || currentMethod.id === 's13' || currentMethod.id === 's38';
    const itVal = formData.it !== undefined ? String(formData.it).trim() : '50';
    const intIt = parseInt(itVal, 10);

    if (currentMethod.id === 's13' && formData.n !== undefined && String(formData.n).trim() !== '') {
      const nVal = String(formData.n).trim();
      const intN = parseInt(nVal, 10);
      if (isNaN(intN) || intN < 2 || intN % 2 !== 0) {
        newBad['n'] = true;
        badCount++;
        customErr = 'Error: Simpson 1/3 requiere un número par de subintervalos';
      } else if (criterio === 'it' && !isNaN(intIt) && intIt > 0) {
        const requiredIters = Math.floor(intN / 2);
        if (requiredIters > intIt) {
          newBad['n'] = true;
          badCount++;
          customErr = `Error: El subintervalo objetivo n = ${intN} requiere ${requiredIters} iteraciones, pero el máximo configurado es ${intIt}.`;
        }
      }
    } else if (currentMethod.id === 's38' && formData.n !== undefined && String(formData.n).trim() !== '') {
      const nVal = String(formData.n).trim();
      const intN = parseInt(nVal, 10);
      if (isNaN(intN) || intN < 3 || intN % 3 !== 0) {
        newBad['n'] = true;
        badCount++;
        customErr = 'Error: Simpson 3/8 requiere un número de subintervalos múltiplo de 3';
      } else if (criterio === 'it' && !isNaN(intIt) && intIt > 0) {
        const requiredIters = Math.floor(intN / 3);
        if (requiredIters > intIt) {
          newBad['n'] = true;
          badCount++;
          customErr = `Error: El subintervalo objetivo n = ${intN} requiere ${requiredIters} iteraciones, pero el máximo configurado es ${intIt}.`;
        }
      }
    } else if (currentMethod.id === 'tra' && formData.n !== undefined && String(formData.n).trim() !== '') {
      const nVal = String(formData.n).trim();
      const intN = parseInt(nVal, 10);
      if (isNaN(intN) || intN < 1) {
        newBad['n'] = true;
        badCount++;
        customErr = 'Error: Trapecio requiere que n sea mayor o igual a 1';
      } else if (criterio === 'it' && !isNaN(intIt) && intIt > 0 && intN > intIt) {
        newBad['n'] = true;
        badCount++;
        customErr = `Error: El subintervalo objetivo n = ${intN} requiere ${intN} iteraciones, pero el máximo configurado es ${intIt}.`;
      }
    }

    // Validaciones de pares (X, Y) para Interpolación Directa y Regresión
    if (isDataMethod && !customErr) {
      const rawX = formData.x !== undefined ? String(formData.x).trim() : '';
      const rawY = formData.y !== undefined ? String(formData.y).trim() : '';

      const tokensX = rawX ? rawX.split(',').map((t) => t.trim()).filter((t) => t.length > 0) : [];
      const tokensY = rawY ? rawY.split(',').map((t) => t.trim()).filter((t) => t.length > 0) : [];

      if (tokensX.length !== tokensY.length) {
        newBad['x'] = true;
        newBad['y'] = true;
        badCount++;
        customErr = `Error en datos: X tiene ${tokensX.length} elementos e Y tiene ${tokensY.length} elementos. Deben tener exactamente la misma cantidad.`;
      } else if (tokensX.length < 2) {
        newBad['x'] = true;
        newBad['y'] = true;
        badCount++;
        customErr = 'Error: Se requieren al menos 2 puntos (pares x, y) para realizar el cálculo.';
      } else {
        const strictNumRegex = /^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/;
        const invalidX = [];
        const invalidY = [];
        tokensX.forEach((tok, idx) => {
          if (!strictNumRegex.test(tok)) {
            invalidX.push(`X[${idx + 1}]='${tok}'`);
          } else {
            const num = parseFloat(tok);
            if (isNaN(num) || !isFinite(num)) invalidX.push(`X[${idx + 1}]='${tok}'`);
          }
        });
        tokensY.forEach((tok, idx) => {
          if (!strictNumRegex.test(tok)) {
            invalidY.push(`Y[${idx + 1}]='${tok}'`);
          } else {
            const num = parseFloat(tok);
            if (isNaN(num) || !isFinite(num)) invalidY.push(`Y[${idx + 1}]='${tok}'`);
          }
        });

        if (invalidX.length > 0 || invalidY.length > 0) {
          newBad['x'] = invalidX.length > 0;
          newBad['y'] = invalidY.length > 0;
          badCount++;
          const allInvalids = [...invalidX, ...invalidY].join(', ');
          customErr = `Error: Se encontraron valores no numéricos en los datos: ${allInvalids}.`;
        }
      }
    }

    // Validar criterio de parada
    if (hasStoppingCriteria && !customErr) {
      if (criterio === 'it') {
        const itVal = formData.it !== undefined ? String(formData.it).trim() : '50';
        const intIt = parseInt(itVal, 10);
        if (isNaN(intIt) || intIt < 1) {
          newBad['it'] = true;
          badCount++;
          customErr = 'El número de iteraciones debe ser un entero mayor o igual a 1.';
        }
      } else if (criterio === 'cifras') {
        const mVal = parseInt(cifrasVal, 10);
        if (isNaN(mVal) || mVal < 1) {
          newBad['cifras'] = true;
          badCount++;
          customErr = 'Las cifras significativas deben ser un entero mayor o igual a 1.';
        }
      }
    }

    setBadFields(newBad);

    if (badCount > 0) {
      setErrorMessage(customErr || `Completa los ${badCount} campo(s) requeridos antes de calcular.`);
    } else {
      setErrorMessage('');
      const payload = {
        ...formData,
        criterio,
        cifras: criterio === 'cifras' ? parseInt(cifrasVal, 10) : undefined,
        n: formData.n ? parseInt(formData.n, 10) : undefined,
        it: formData.it ? parseInt(formData.it, 10) : (criterio === 'cifras' ? 200 : 50)
      };
      onCalculate(payload);
    }
  };

  const handleReset = () => {
    const resetData = {};
    if (currentMethod.sel) {
      resetData[currentMethod.sel.k] = currentMethod.sel.o[0];
    }
    currentMethod.f.forEach((field) => {
      resetData[field.k] = field.v || (field.t === 'sel' ? field.o[0] : '');
    });
    resetData.criterio = 'cifras';
    resetData.cifras = '4';
    setCriterio('cifras');
    setCifrasVal('4');
    setFormData(resetData);
    setBadFields({});
    setErrorMessage('');
    setFileColumns([]);
    setFileRawData([]);
    setUploadedFileName('');
    if (fileInputRef.current) fileInputRef.current.value = '';
    onResetResults();
  };

  const renderField = (field) => {
    const id = `f_${field.k}`;
    const isBad = !!badFields[field.k];
    const value = formData[field.k] ?? '';

    return (
      <div key={field.k} style={{ marginBottom: '0.85rem' }}>
        <label htmlFor={id} style={{ display: 'block', fontWeight: '600', marginBottom: '0.25rem' }}>
          {field.l}
        </label>
        {field.t === 'sel' ? (
          <select
            id={id}
            value={value}
            onChange={(e) => handleInputChange(field.k, e.target.value)}
          >
            {field.o.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        ) : field.t === 'list' ? (
          <textarea
            id={id}
            className={`fx ${isBad ? 'bad' : ''}`}
            placeholder={field.ph || ''}
            value={value}
            onChange={(e) => handleInputChange(field.k, e.target.value)}
          />
        ) : field.t === 'num' ? (
          <input
            id={id}
            type="text"
            className={isBad ? 'bad' : ''}
            placeholder={field.ph || ''}
            value={value}
            onChange={(e) => handleInputChange(field.k, e.target.value)}
          />
        ) : (
          <input
            id={id}
            type="text"
            className={`fx ${isBad ? 'bad' : ''}`}
            autoComplete="off"
            spellCheck="false"
            placeholder={field.ph || ''}
            value={value}
            onChange={(e) => handleInputChange(field.k, e.target.value)}
          />
        )}
        {field.hint && (
          <div className="hint" style={{ fontSize: '0.8rem', opacity: 0.8, marginTop: '0.2rem' }}>
            {field.hint}
          </div>
        )}
      </div>
    );
  };

  // Tolerancia de Scarborough calculada en tiempo real: es = 0.5 * 10^(2 - m) %
  const mVal = parseInt(cifrasVal, 10) || 4;
  const tolValRaw = 0.5 * Math.pow(10, 2 - mVal);
  const scarboroughTol = tolValRaw < 1e-4 ? tolValRaw.toExponential(4) : tolValRaw.toFixed(6).replace(/\.?0+$/, '');

  return (
    <form className="card" onSubmit={handleSubmit} onReset={handleReset} noValidate>
      <h2>{currentMethod.n}</h2>
      <p className="desc">{currentMethod.d}</p>

      {/* Selector de tipo para Sección Áurea (Univariada / Multivariada) */}
      {currentMethod.sel && (
        <div key={currentMethod.sel.k} style={{ marginBottom: '0.85rem' }}>
          <label htmlFor={`f_${currentMethod.sel.k}`} style={{ display: 'block', fontWeight: '600', marginBottom: '0.25rem' }}>
            {currentMethod.sel.l}
          </label>
          <select
            id={`f_${currentMethod.sel.k}`}
            value={currentTipo}
            onChange={(e) => handleInputChange(currentMethod.sel.k, e.target.value)}
          >
            {currentMethod.sel.o.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* RÚBRICA 3: Módulo de Carga de Archivos y Elección de Columnas para Interpolación y Regresión */}
      {isDataMethod && (
        <div style={{
          background: 'var(--soft)',
          border: '1px dashed var(--acc)',
          borderRadius: '10px',
          padding: '1rem',
          marginBottom: '1.2rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
            <span style={{ fontWeight: '700', fontSize: '0.92rem', color: 'var(--acc)' }}>
              📁 Cargar datos desde archivo (CSV / TXT)
            </span>
            <input
              type="file"
              ref={fileInputRef}
              accept=".csv,.txt,.tsv"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
              id="file_upload_input"
            />
            <label
              htmlFor="file_upload_input"
              className="clr"
              style={{
                fontSize: '0.82rem',
                padding: '6px 12px',
                cursor: 'pointer',
                borderColor: 'var(--acc)',
                color: 'var(--acc)',
                fontWeight: 600
              }}
            >
              Seleccionar archivo
            </label>
          </div>

          {uploadedFileName && (
            <div style={{ fontSize: '0.82rem', marginBottom: '0.6rem', color: 'var(--mute)' }}>
              Archivo cargado: <strong>{uploadedFileName}</strong> ({fileRawData.length} filas detectadas)
            </div>
          )}

          {/* RÚBRICA 3: Elección de la columna x y de f(x) */}
          {fileColumns.length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '0.5rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Columna X:</label>
                <select
                  value={selectedColX}
                  onChange={(e) => handleSelectColX(e.target.value)}
                  style={{ padding: '6px 8px', fontSize: '0.85rem' }}
                >
                  {fileColumns.map((col) => (
                    <option key={col} value={col}>
                      {col}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Columna Y / f(x):</label>
                <select
                  value={selectedColY}
                  onChange={(e) => handleSelectColY(e.target.value)}
                  style={{ padding: '6px 8px', fontSize: '0.85rem' }}
                >
                  {fileColumns.map((col) => (
                    <option key={col} value={col}>
                      {col}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>
      )}

      {/* RÚBRICA 3: Selector claro entre número de iteraciones y cifras significativas */}
      {hasStoppingCriteria && (
        <div style={{
          background: 'var(--soft)',
          border: '1px solid var(--line)',
          borderRadius: '10px',
          padding: '1rem',
          marginBottom: '1.2rem'
        }}>
          <label style={{ display: 'block', fontWeight: '700', marginBottom: '0.6rem', color: 'var(--ink)' }}>
            🎯 Criterio de parada del algoritmo:
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.8rem', alignItems: 'center', marginBottom: '0.85rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer', margin: 0, fontWeight: 500 }}>
              <input
                type="radio"
                name="criterio_parada"
                value="cifras"
                checked={criterio === 'cifras'}
                onChange={() => handleCriterioChange('cifras')}
              />
              <span>Cifras significativas</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer', margin: 0, fontWeight: 500 }}>
              <input
                type="radio"
                name="criterio_parada"
                value="it"
                checked={criterio === 'it'}
                onChange={() => handleCriterioChange('it')}
              />
              <span>Número fijo de iteraciones</span>
            </label>
          </div>

          {criterio === 'cifras' ? (
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 600 }}>Cifras significativas (m):</label>
              <input
                type="number"
                min="1"
                max="16"
                step="1"
                value={cifrasVal}
                onChange={(e) => setCifrasVal(e.target.value)}
                style={{ padding: '7px 9px' }}
              />
              <div style={{ fontSize: '0.78rem', color: 'var(--mute)', marginTop: '3px' }}>
                εs = 0.5 × 10<sup>{2 - (parseInt(cifrasVal, 10) || 4)}</sup> % = <strong>{scarboroughTol} %</strong>
              </div>
              <div style={{ marginTop: '0.6rem' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--mute)' }}>
                  Límite máximo de seguridad de iteraciones (opcional):
                </label>
                <input
                  type="number"
                  min="1"
                  step="1"
                  placeholder="Por defecto: 200"
                  value={formData.it ?? ''}
                  onChange={(e) => handleInputChange('it', e.target.value)}
                  style={{ padding: '5px 8px', fontSize: '0.85rem' }}
                />
              </div>
            </div>
          ) : (
            <div>
              <label style={{ fontSize: '0.82rem', fontWeight: 600 }}>Número de iteraciones a ejecutar (N):</label>
              <input
                type="number"
                min="1"
                step="1"
                value={formData.it ?? '50'}
                onChange={(e) => handleInputChange('it', e.target.value)}
                style={{ padding: '7px 9px' }}
              />
              <div style={{ fontSize: '0.78rem', color: 'var(--mute)', marginTop: '3px' }}>
                Cantidad exacta de iteraciones
              </div>
            </div>
          )}
        </div>
      )}

      {/* Renderizar resto de campos del método */}
      {currentMethod.f.map((field) => {
        if (!isFieldVisible(field)) return null;
        return renderField(field);
      })}

      {errorMessage && (
        <div className="err" id="err" style={{ color: 'var(--warn)', marginBottom: '0.85rem', fontWeight: 'bold' }}>
          {errorMessage}
        </div>
      )}

      <div className="btns">
        <button className="go" type="submit">
          Calcular
        </button>
        <button className="clr" type="reset">
          Limpiar
        </button>
      </div>
    </form>
  );
}
