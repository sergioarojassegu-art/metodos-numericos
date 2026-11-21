import React from 'react';

export default function Hero({ onStartCalculating, onScrollToMethods }) {
  return (
    <section className="hero">
      <div>
        <h1>Resuelve métodos numéricos paso a paso</h1>
        <p>
          Escribe tu función o tu lista de datos, elige el método y revisa las iteraciones,
          el error y la gráfica en un solo lugar.
        </p>
        <div className="hbtn">
          <button className="go" type="button" onClick={onStartCalculating}>
            Empezar a calcular
          </button>
          <button className="clr" type="button" onClick={onScrollToMethods}>
            Ver métodos
          </button>
        </div>
      </div>
      <div className="panel">
        <svg
          viewBox="0 0 520 240"
          width="100%"
          role="img"
          aria-label="Curva con una recta tangente que se acerca a la raíz"
        >
          <g stroke="var(--line)">
            <line x1="20" y1="150" x2="500" y2="150" />
            <line x1="20" y1="20" x2="20" y2="220" />
          </g>
          <path
            d="M30,215 Q250,215 480,20"
            fill="none"
            stroke="var(--acc)"
            strokeWidth="3"
          />
          <line
            x1="430"
            y1="61"
            x2="300"
            y2="150"
            stroke="var(--ink)"
            strokeWidth="1.5"
          />
          <line
            x1="388"
            y1="150"
            x2="388"
            y2="90"
            stroke="var(--mute)"
            strokeDasharray="4 4"
          />
          <circle cx="388" cy="90" r="5" fill="var(--ink)" />
          <circle cx="300" cy="150" r="5" fill="var(--ink)" />
          <circle cx="287" cy="150" r="7" fill="var(--acc)" />
          <text x="287" y="175" textAnchor="middle" fill="var(--ink)" fontSize="14">
            raíz
          </text>
          <text x="440" y="52" fill="var(--mute)" fontSize="14">
            f(x)
          </text>
        </svg>
      </div>
    </section>
  );
}
