import React from 'react';
import Hero from './Hero';
import { METHODS_DATA } from '../data/methodsData';

export default function HomeView({ onSelectCategoryAndOpen, onStartCalculating }) {
  const scrollToMethods = () => {
    const el = document.getElementById('metodos');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <main id="home">
      <Hero
        onStartCalculating={onStartCalculating}
        onScrollToMethods={scrollToMethods}
      />

      <h2 className="sec" id="metodos">
        Métodos disponibles
      </h2>
      <div className="mcards" id="mcards">
        {Object.entries(METHODS_DATA).map(([catKey, cat]) => (
          <div key={catKey} className="card mc">
            <h3>{cat.n}</h3>
            <div className="sy">{cat.s}</div>
            <ul>
              {cat.m.map((method) => (
                <li key={method.id}>{method.n}</li>
              ))}
            </ul>
            <button
              type="button"
              className="clr"
              onClick={() => onSelectCategoryAndOpen(catKey, cat.m[0].id)}
            >
              Abrir {cat.n.toLowerCase()}
            </button>
          </div>
        ))}
      </div>

      <h2 className="sec">Cómo funciona</h2>
      <div className="steps">
        <div className="st">
          <b>1. Elige el método</b>
          <span>Raíces, integración, interpolación u optimización.</span>
        </div>
        <div className="st">
          <b>2. Escribe tus datos</b>
          <span>Una función como x^3 - x - 2 o una lista de valores separados por comas.</span>
        </div>
        <div className="st">
          <b>3. Revisa el resultado</b>
          <span>Valor final, número de iteraciones, error y gráfica.</span>
        </div>
      </div>
    </main>
  );
}
