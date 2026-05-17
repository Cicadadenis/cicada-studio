import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { AppDialogProvider } from './dialog/AppDialogProvider.jsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <AppDialogProvider>
    <App />
  </AppDialogProvider>,
);
