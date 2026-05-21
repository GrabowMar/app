import './_appBase.js';
import './index.css';
import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { APP_BASE } from './_appBase.js';
import App from './App.jsx';

const root = createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter basename={APP_BASE || '/'}>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
