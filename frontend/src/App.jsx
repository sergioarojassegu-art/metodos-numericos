import React, { useState } from 'react';
import Header from './components/Header';
import HomeView from './components/HomeView';
import CalculatorView from './components/CalculatorView';
import { METHODS_DATA } from './data/methodsData';
import { executeNumericalMethod } from './services/api';

export default function App() {
  const [currentView, setCurrentView] = useState('home');
  const [selectedCategory, setSelectedCategory] = useState('raices');
  const [selectedMethodId, setSelectedMethodId] = useState('bis');
  const [isCalculated, setIsCalculated] = useState(false);
  const [resultData, setResultData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleNavigate = (view) => {
    setCurrentView(view);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSelectCategory = (catKey) => {
    setSelectedCategory(catKey);
    const firstMethodId = METHODS_DATA[catKey]?.m[0]?.id || 'bis';
    setSelectedMethodId(firstMethodId);
    setIsCalculated(false);
    setResultData(null);
    setError(null);
  };

  const handleSelectCategoryAndOpen = (catKey, methodId) => {
    setSelectedCategory(catKey);
    setSelectedMethodId(methodId || METHODS_DATA[catKey]?.m[0]?.id || 'bis');
    setIsCalculated(false);
    setResultData(null);
    setError(null);
    setCurrentView('app');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSelectMethod = (methodId) => {
    setSelectedMethodId(methodId);
    setIsCalculated(false);
    setResultData(null);
    setError(null);
  };

  const handleCalculate = async (formData) => {
    setLoading(true);
    setError(null);
    try {
      const data = await executeNumericalMethod(selectedMethodId, formData);
      setResultData(data);
      setIsCalculated(true);
    } catch (err) {
      setError(err.message || 'Error al comunicarse con el backend.');
      setIsCalculated(true);
    } finally {
      setLoading(false);
    }
  };

  const handleResetResults = () => {
    setIsCalculated(false);
    setResultData(null);
    setError(null);
  };

  return (
    <div className="wrap">
      <Header
        currentView={currentView}
        onNavigate={handleNavigate}
      />

      {currentView === 'home' ? (
        <HomeView
          onSelectCategoryAndOpen={handleSelectCategoryAndOpen}
          onStartCalculating={() => handleNavigate('app')}
        />
      ) : (
        <CalculatorView
          selectedCategory={selectedCategory}
          selectedMethodId={selectedMethodId}
          onSelectCategory={handleSelectCategory}
          onSelectMethod={handleSelectMethod}
          isCalculated={isCalculated}
          onCalculate={handleCalculate}
          onResetResults={handleResetResults}
          resultData={resultData}
          loading={loading}
          error={error}
        />
      )}
    </div>
  );
}
