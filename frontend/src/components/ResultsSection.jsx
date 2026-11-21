import React, { useState, useEffect } from 'react';
import { STAT_CONFIG, PLOT_TITLES, TABLE_COLUMNS } from '../data/methodsData';

export default function ResultsSection({ methodResultType, isCalculated, resultData, loading, error }) {
  const [activePlotTab, setActivePlotTab] = useState('curve'); // 'curve' o 'error'

  // Reiniciar la pestaña de gráfica a 'curve' cada vez que cambie el método
  useEffect(() => {
    setActivePlotTab('curve');
  }, [methodResultType]);

  const plotTitle = PLOT_TITLES[methodResultType] || 'Gráfica';
  const summary = resultData?.summary || {};
  const steps = resultData?.steps || [];
  const plotData = resultData?.plot_data || null;

  // Determinar columnas dinámicamente según la rúbrica
  let columns = TABLE_COLUMNS[methodResultType] || [];
  if (methodResultType === 'sd' && steps.length > 0 && steps[0]['coordenada activa']) {
    columns = TABLE_COLUMNS.sd_multi;
  } else if (steps.length > 0 && columns.length === 0) {
    columns = Object.keys(steps[0]);
  }

  const stats = STAT_CONFIG[methodResultType] || [];

  // Función auxiliar para formatear valores respetando la precisión calculada
  const formatCellVal = (val) => {
    if (val === undefined || val === null) return '—';
    if (typeof val === 'number') {
      if (Number.isInteger(val)) return String(val);
      // Para números con decimales, mostrar sin truncar a 5 decimales si tiene más precisión
      const strVal = String(val);
      if (strVal.includes('.') && strVal.split('.')[1].length > 5) {
        return strVal;
      }
      return val.toFixed(5);
    }
    return String(val);
  };

  // --- Renderizador de Gráficas SVG con Ejes Rotulados ---
  const renderSvgContent = () => {
    if (!plotData) {
      return (
        <text x={300} y={110} textAnchor="middle" fill="var(--mute)" fontSize="14">
          {loading ? 'Calculando resultados en el backend...' : 'Calcula para ver la gráfica y evolución del error'}
        </text>
      );
    }

    const W = 500;
    const H = 145;
    const padX = 65;
    const padY = 25;

    // --- MODO 1: GRÁFICA DE EVOLUCIÓN DEL ERROR (%) ---
    if (activePlotTab === 'error') {
      const rawEvolution = plotData.error_evolution || [];
      const errPoints = rawEvolution
        .map(p => {
          const num = typeof p.error === 'number' ? p.error : parseFloat(p.error);
          return { iter: p.iter, error: num };
        })
        .filter(p => !isNaN(p.error) && isFinite(p.error));

      if (errPoints.length === 0) {
        return (
          <text x={300} y={110} textAnchor="middle" fill="var(--mute)" fontSize="13">
            No hay errores relativos finitos para graficar (integral evaluada en o cerca de 0)
          </text>
        );
      }

      const minIter = errPoints[0].iter;
      const maxIter = errPoints[errPoints.length - 1].iter || minIter;
      const minErr = 0;
      const maxErr = Math.max(...errPoints.map(p => p.error), 1.0);

      const toSvgX = (it) => padX + (maxIter === minIter ? W / 2 : ((it - minIter) / (maxIter - minIter)) * W);
      const toSvgY = (err) => padY + H - ((err - minErr) / (maxErr - minErr || 1)) * H;

      const dPath = errPoints.reduce((acc, p, idx) => {
        const sx = toSvgX(p.iter);
        const sy = toSvgY(p.error);
        return idx === 0 ? `M ${sx} ${sy}` : `${acc} L ${sx} ${sy}`;
      }, '');

      return (
        <g>
          {/* Ejes X e Y */}
          <line x1={padX} y1={padY + H} x2={padX + W} y2={padY + H} stroke="var(--ink)" strokeWidth="1.5" />
          <line x1={padX} y1={padY} x2={padX} y2={padY + H} stroke="var(--ink)" strokeWidth="1.5" />

          {/* Curva de error */}
          <path d={dPath} fill="none" stroke="#dc2626" strokeWidth="2.5" />

          {/* Puntos en cada iteración */}
          {errPoints.map((p, idx) => (
            <circle
              key={idx}
              cx={toSvgX(p.iter)}
              cy={toSvgY(p.error)}
              r="4"
              fill="#dc2626"
            />
          ))}

          {/* Rótulos de ejes según Rúbrica */}
          <text x={padX + W / 2} y={padY + H + 34} textAnchor="middle" fill="var(--ink)" fontSize="12" fontWeight="600">
            {plotData.error_x_label || 'Iteración (i)'}
          </text>
          <text
            x={18}
            y={padY + H / 2}
            textAnchor="middle"
            fill="var(--ink)"
            fontSize="12"
            fontWeight="600"
            transform={`rotate(-90 18 ${padY + H / 2})`}
          >
            {plotData.error_y_label || 'Error aprox (%)'}
          </text>

          {/* Marcas de valor en los extremos */}
          <text x={padX} y={padY + H + 16} fill="var(--mute)" fontSize="10">{minIter}</text>
          <text x={padX + W} y={padY + H + 16} textAnchor="end" fill="var(--mute)" fontSize="10">{maxIter}</text>
          <text x={padX - 8} y={padY + H} textAnchor="end" fill="var(--mute)" fontSize="10">{minErr.toFixed(1)}%</text>
          <text x={padX - 8} y={padY + 10} textAnchor="end" fill="var(--mute)" fontSize="10">{maxErr.toFixed(2)}%</text>
        </g>
      );
    }

    // --- MODO 2: GRÁFICA DE LA FUNCIÓN O CURVA AJUSTADA ---
    if (plotData.x_curve && plotData.y_curve && plotData.x_curve.length > 0) {
      const validPoints = [];
      plotData.x_curve.forEach((x, i) => {
        const y = plotData.y_curve[i];
        if (y !== null && !isNaN(y) && isFinite(y)) {
          validPoints.push({ x, y });
        }
      });

      if (validPoints.length > 1) {
        let minX = Math.min(...validPoints.map(p => p.x));
        let maxX = Math.max(...validPoints.map(p => p.x));
        let minY = Math.min(...validPoints.map(p => p.y));
        let maxY = Math.max(...validPoints.map(p => p.y));

        if (minY === maxY) {
          minY -= 1;
          maxY += 1;
        }

        const toSvgX = (x) => padX + ((x - minX) / (maxX - minX || 1)) * W;
        const toSvgY = (y) => padY + H - ((y - minY) / (maxY - minY || 1)) * H;

        const dCurve = validPoints.reduce((acc, p, idx) => {
          const sx = toSvgX(p.x);
          const sy = toSvgY(p.y);
          return idx === 0 ? `M ${sx} ${sy}` : `${acc} L ${sx} ${sy}`;
        }, '');

        const zeroY = (minY <= 0 && maxY >= 0) ? toSvgY(0) : null;
        const zeroX = (minX <= 0 && maxX >= 0) ? toSvgX(0) : null;

        return (
          <g>
            {/* Ejes coordenados principales */}
            <line x1={padX} y1={padY + H} x2={padX + W} y2={padY + H} stroke="var(--ink)" strokeWidth="1.5" />
            <line x1={padX} y1={padY} x2={padX} y2={padY + H} stroke="var(--ink)" strokeWidth="1.5" />

            {/* Eje horizontal y = 0 si está visible */}
            {zeroY !== null && (
              <line x1={padX} y1={zeroY} x2={padX + W} y2={zeroY} stroke="var(--line)" strokeDasharray="4 4" strokeWidth="1.5" />
            )}
            {zeroX !== null && (
              <line x1={zeroX} y1={padY} x2={zeroX} y2={padY + H} stroke="var(--line)" strokeDasharray="4 4" strokeWidth="1.5" />
            )}

            {/* Área bajo la curva para integración */}
            {plotData.area !== undefined && (
              <path
                d={`${dCurve} L ${toSvgX(validPoints[validPoints.length - 1].x)} ${toSvgY(0)} L ${toSvgX(validPoints[0].x)} ${toSvgY(0)} Z`}
                fill="rgba(37, 99, 235, 0.15)"
              />
            )}

            {/* Curva matemática continua */}
            <path d={dCurve} fill="none" stroke="var(--acc)" strokeWidth="2.5" />

            {/* Puntos de datos cargados (Interpolación / Regresión) */}
            {plotData.x_points && plotData.y_points && (
              plotData.x_points.map((xp, idx) => (
                <circle
                  key={idx}
                  cx={toSvgX(xp)}
                  cy={toSvgY(plotData.y_points[idx])}
                  r="5"
                  fill="#ef4444"
                  stroke="#fff"
                  strokeWidth="1.5"
                />
              ))
            )}

            {/* Punto evaluado en interpolación o regresión */}
            {plotData.x_eval !== undefined && plotData.y_eval !== undefined && plotData.y_eval !== null && (
              <g>
                <circle
                  cx={toSvgX(plotData.x_eval)}
                  cy={toSvgY(plotData.y_eval)}
                  r="6"
                  fill="#8b5cf6"
                  stroke="#fff"
                  strokeWidth="2"
                />
                <text
                  x={toSvgX(plotData.x_eval)}
                  y={toSvgY(plotData.y_eval) - 10}
                  textAnchor="middle"
                  fill="var(--ink)"
                  fontSize="11"
                  fontWeight="600"
                >
                  P({plotData.x_eval}, {plotData.y_eval.toFixed(2)})
                </text>
              </g>
            )}

            {/* Raíz encontrada (Raíces) */}
            {plotData.root !== undefined && (
              <g>
                <circle
                  cx={toSvgX(plotData.root)}
                  cy={toSvgY(0)}
                  r="6.5"
                  fill="#10b981"
                  stroke="#fff"
                  strokeWidth="2"
                />
                <text
                  x={toSvgX(plotData.root)}
                  y={toSvgY(0) + 16}
                  textAnchor="middle"
                  fill="#10b981"
                  fontSize="11"
                  fontWeight="bold"
                >
                  x* ≈ {plotData.root.toFixed(4)}
                </text>
              </g>
            )}

            {/* Punto óptimo (Optimización) */}
            {plotData.opt_x !== undefined && plotData.opt_f !== undefined && (
              <g>
                <circle
                  cx={toSvgX(plotData.opt_x)}
                  cy={toSvgY(plotData.opt_f)}
                  r="6.5"
                  fill="#10b981"
                  stroke="#fff"
                  strokeWidth="2"
                />
                <text
                  x={toSvgX(plotData.opt_x)}
                  y={toSvgY(plotData.opt_f) - 10}
                  textAnchor="middle"
                  fill="#10b981"
                  fontSize="11"
                  fontWeight="bold"
                >
                  Óptimo ({plotData.opt_x.toFixed(4)}, {plotData.opt_f.toFixed(4)})
                </text>
              </g>
            )}

            {/* Rótulos de ejes según Rúbrica */}
            <text x={padX + W / 2} y={padY + H + 34} textAnchor="middle" fill="var(--ink)" fontSize="12" fontWeight="600">
              {plotData.x_label || 'Eje x'}
            </text>
            <text
              x={20}
              y={padY + H / 2}
              textAnchor="middle"
              fill="var(--ink)"
              fontSize="12"
              fontWeight="600"
              transform={`rotate(-90 20 ${padY + H / 2})`}
            >
              {plotData.y_label || 'Eje y = f(x)'}
            </text>

            {/* Marcas de rango numérico en los extremos */}
            <text x={padX} y={padY + H + 16} fill="var(--mute)" fontSize="10">{minX.toFixed(2)}</text>
            <text x={padX + W} y={padY + H + 16} textAnchor="end" fill="var(--mute)" fontSize="10">{maxX.toFixed(2)}</text>
            <text x={padX - 8} y={padY + H} textAnchor="end" fill="var(--mute)" fontSize="10">{minY.toFixed(1)}</text>
            <text x={padX - 8} y={padY + 10} textAnchor="end" fill="var(--mute)" fontSize="10">{maxY.toFixed(1)}</text>
          </g>
        );
      }
    }

    return (
      <text x={300} y={110} textAnchor="middle" fill="#10b981" fontSize="15" fontWeight="600">
        ✓ Cálculo completado con éxito
      </text>
    );
  };

  const hasErrorPlot = plotData?.error_evolution && plotData.error_evolution.length > 0;

  return (
    <section className="card" id="res" aria-live="polite">
      <h2>Resultados</h2>

      {error && (
        <div style={{ padding: '0.8rem', background: '#fef2f2', border: '1px solid #f87171', borderRadius: '8px', color: '#b91c1c', marginBottom: '1rem', fontWeight: 500 }}>
          <strong>Error en el cálculo:</strong> {error}
        </div>
      )}

      {loading && (
        <div style={{ padding: '0.8rem', background: '#eff6ff', borderRadius: '8px', color: '#1d4ed8', marginBottom: '1rem', fontWeight: 500 }}>
          Procesando método en el backend...
        </div>
      )}

      {/* RÚBRICA 1: Tarjetas de estadísticas y resultados destacados */}
      <div className="stats">
        {stats.map(([label, symbol], index) => {
          let val = summary[label];
          val = formatCellVal(val);
          return (
            <div key={index} className="stat">
              <small>{label}</small>
              <b title={String(val)}>{val}</b>
            </div>
          );
        })}
      </div>

      {/* RÚBRICA 1: Gráfica de la función y Gráfica de la evolución del error con ejes rotulados */}
      <div className="plot">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px 4px' }}>
          <h3 style={{ margin: 0 }}>
            {activePlotTab === 'error' ? 'Evolución del error aproximado (%)' : plotTitle}
          </h3>
          {hasErrorPlot && (
            <div style={{ display: 'flex', gap: '6px' }}>
              <button
                type="button"
                className="clr"
                onClick={() => setActivePlotTab('curve')}
                style={{
                  fontSize: '0.78rem',
                  padding: '4px 9px',
                  background: activePlotTab === 'curve' ? 'var(--acc)' : 'none',
                  color: activePlotTab === 'curve' ? 'var(--acc-ink)' : 'inherit',
                  borderColor: activePlotTab === 'curve' ? 'var(--acc)' : 'var(--line)'
                }}
              >
                Curva f(x)
              </button>
              <button
                type="button"
                className="clr"
                onClick={() => setActivePlotTab('error')}
                style={{
                  fontSize: '0.78rem',
                  padding: '4px 9px',
                  background: activePlotTab === 'error' ? 'var(--acc)' : 'none',
                  color: activePlotTab === 'error' ? 'var(--acc-ink)' : 'inherit',
                  borderColor: activePlotTab === 'error' ? 'var(--acc)' : 'var(--line)'
                }}
              >
                Evolución del Error (%)
              </button>
            </div>
          )}
        </div>

        <svg
          viewBox="0 0 600 230"
          width="100%"
          role="img"
          aria-label="Espacio para la gráfica interactiva con ejes rotulados"
        >
          {/* Cuadrícula de fondo */}
          <g stroke="var(--grid)" strokeWidth="0.8">
            {[1, 2, 3, 4, 5].map((i) => (
              <line key={`v-${i}`} x1={i * 100} y1={10} x2={i * 100} y2={185} />
            ))}
            {[1, 2, 3, 4].map((i) => (
              <line key={`h-${i}`} x1={40} y1={i * 35 + 15} x2={580} y2={i * 35 + 15} />
            ))}
          </g>

          {renderSvgContent()}
        </svg>
      </div>

      {/* RÚBRICA 1: Tabla de iteraciones con las columnas mínimas exactas */}
      <div className="tbl">
        <h3>Tabla de iteraciones ({steps.length} registros)</h3>
        <div className="sc" style={{ maxHeight: '280px', overflowY: 'auto' }}>
          <table>
            <thead>
              <tr>
                {columns.map((col, idx) => (
                  <th key={idx}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {steps.length > 0 ? (
                steps.map((step, sIdx) => (
                  <tr key={sIdx}>
                    {columns.map((col, cIdx) => {
                      const val = step[col] ?? step[Object.keys(step)[cIdx]];
                      return (
                        <td key={cIdx}>
                          {formatCellVal(val)}
                        </td>
                      );
                    })}
                  </tr>
                ))
              ) : (
                <tr>
                  {columns.map((_, idx) => (
                    <td key={idx}>—</td>
                  ))}
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Indicador de Estado y Resumen */}
      {resultData?.summary?.Estado && (
        <div style={{
          marginTop: '1rem',
          padding: '0.65rem 0.95rem',
          borderRadius: '8px',
          backgroundColor: resultData?.converged === false
            ? 'rgba(239, 68, 68, 0.12)'
            : (resultData?.converged === true ? 'rgba(16, 185, 129, 0.12)' : 'rgba(59, 130, 246, 0.12)'),
          border: `1px solid ${resultData?.converged === false ? '#ef4444' : (resultData?.converged === true ? '#10b981' : '#3b82f6')}`,
          color: resultData?.converged === false ? '#dc2626' : (resultData?.converged === true ? '#047857' : '#1d4ed8'),
          fontWeight: 600,
          fontSize: '0.92rem'
        }}>
          {resultData?.converged === false ? '⚠️ ' : (resultData?.converged === true ? '✅ ' : 'ℹ️ ')}
          {resultData.summary.Estado}: {resultData.details}
        </div>
      )}

      {resultData?.details && !resultData?.summary?.Estado && (
        <p className="note" style={{ marginTop: '1rem', color: '#047857', fontWeight: 500 }}>
          {resultData.details}
        </p>
      )}
    </section>
  );
}
