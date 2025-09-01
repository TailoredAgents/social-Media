import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// Use the main app with safer Auth0 handling
const AppComponent = App

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AppComponent />
  </StrictMode>,
)
