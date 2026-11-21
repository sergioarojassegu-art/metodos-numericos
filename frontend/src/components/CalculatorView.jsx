import React from 'react';
import MethodForm from './MethodForm';
import ResultsSection from './ResultsSection';
import { METHODS_DATA } from '../data/methodsData';

export default function CalculatorView({
  selectedCategory,
  selectedMethodId,
  onSelectCategory,
  onSelectMethod,
  isCalculated,
  onCalculate,
  onResetResults,
  resultData,
  loading,
  error
}) {
  const currentCategoryData = METHODS_DATA[selectedCategory] || METHODS_DATA.raices;
  const currentMethod =
    currentCategoryData.m.find((m) => m.id === selectedMethodId) ||
    currentCategoryData.m[0];

  return (
    <div id="app">
      <p className="sub">
        Elige un tema y un método, escribe la función o los datos y pulsa «Calcular».
      </p>

      {/* Categorías */}
      <div className="cats" role="tablist" id="cats">
        {Object.entries(METHODS_DATA).map(([catKey, cat]) => {
          const isSelected = catKey === selectedCategory;
          return (
            <button
              key={catKey}
              type="button"
              role="tab"
              className="cat"
              aria-selected={isSelected}
              onClick={() => onSelectCategory(catKey)}
            >
              <b>{cat.n}</b>
              <span>{cat.s}</span>
            </button>
          );
        })}
      </div>

      {/* Métodos de la categoría seleccionada */}
      <div className="tabs" role="tablist" id="tabs">
        {currentCategoryData.m.map((method) => {
          const isSelected = method.id === currentMethod.id;
          return (
            <button
              key={method.id}
              type="button"
              role="tab"
              className="tab"
              aria-selected={isSelected}
              onClick={() => onSelectMethod(method.id)}
            >
              {method.n}
            </button>
          );
        })}
      </div>

      {/* Formulario y Resultados */}
      <div className="grid">
        <MethodForm
          currentMethod={currentMethod}
          onCalculate={onCalculate}
          onResetResults={onResetResults}
        />
        <ResultsSection
          methodResultType={currentMethod.r}
          isCalculated={isCalculated}
          resultData={resultData}
          loading={loading}
          error={error}
        />
      </div>
    </div>
  );
}
