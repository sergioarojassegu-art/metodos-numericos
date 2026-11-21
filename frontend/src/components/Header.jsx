import React from 'react';

export default function Header({ currentView, onNavigate }) {
  return (
    <header className="top">
      <button 
        className="brand" 
        type="button" 
        onClick={() => onNavigate('home')}
      >
        Métodos numéricos : Sergio Rojas y Brayan Murcia
      </button>
      <nav className="nav" id="nav">
        <button 
          type="button" 
          aria-current={currentView === 'home' ? 'page' : 'false'}
          onClick={() => onNavigate('home')}
        >
          Inicio
        </button>
        <button 
          type="button" 
          aria-current={currentView === 'app' ? 'page' : 'false'}
          onClick={() => onNavigate('app')}
        >
          Calculadora
        </button>
      </nav>
    </header>
  );
}
