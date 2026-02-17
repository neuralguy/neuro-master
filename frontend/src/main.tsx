import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// CRITICAL: Cache uid/token from URL BEFORE React Router mounts
// and changes the URL (losing query params).
import { initTokenAuth } from '@/utils/telegram';
initTokenAuth();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

