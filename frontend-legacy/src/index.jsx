import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import { ThemeProvider, initializeTheme } from './lib/ThemeProvider.jsx';
import './index.css';
import './lib/dark.css';

// Initialize theme before rendering
initializeTheme();

const container = document.getElementById('root');
const root = createRoot(container);

root.render(
  <React.StrictMode>
    <ThemeProvider>
      <App />
    </ThemeProvider>
  </React.StrictMode>
);