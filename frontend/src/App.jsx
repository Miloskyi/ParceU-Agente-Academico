import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatTab from './components/ChatTab'
import TramitesTab from './components/TramitesTab'
import CalendarioTab from './components/CalendarioTab'
import AnalyticsTab from './components/AnalyticsTab'
import LandingPage from './components/LandingPage'

const MENSAJE_BIENVENIDA = {
  role: 'assistant',
  content: '¡Hola! Soy el **Copiloto Administrativo** de la Facultad de Ingeniería UdeA. Puedo ayudarte con preguntas sobre reglamentos, trámites, fechas académicas y más. ¿En qué te puedo ayudar hoy?',
  time: new Date().toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' }),
  fuentes: [],
  es_urgente: false,
}

export default function App() {
  const [view, setView] = useState('landing')
  const [activeTab, setActiveTab] = useState('chat')

  // Estado del chat elevado aquí para que persista al cambiar de pestaña
  const [messages, setMessages] = useState([MENSAJE_BIENVENIDA])
  const [perfil, setPerfil] = useState('pregrado')

  if (view === 'landing') {
    return <LandingPage onEnter={() => setView('app')} />
  }

  return (
    <div className="flex h-screen overflow-hidden bg-udea-gris">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="flex-1 overflow-auto">
        {activeTab === 'chat' && (
          <ChatTab
            messages={messages}
            setMessages={setMessages}
            perfil={perfil}
            setPerfil={setPerfil}
          />
        )}
        {activeTab === 'tramites' && <TramitesTab />}
        {activeTab === 'calendario' && <CalendarioTab />}
        {activeTab === 'analytics' && <AnalyticsTab />}
      </main>
    </div>
  )
}
