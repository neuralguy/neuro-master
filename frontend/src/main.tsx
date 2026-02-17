import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// IMPORTANT: Cache token auth params BEFORE React Router changes the URL
import { initTokenAuth } from '@/utils/telegram';
initTokenAuth();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
