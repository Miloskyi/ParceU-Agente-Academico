import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatTab from './components/ChatTab'
import TramitesTab from './components/TramitesTab'
import CalendarioTab from './components/CalendarioTab'
import AnalyticsTab from './components/AnalyticsTab'
import LandingPage from './components/LandingPage'

export default function App() {
  const [view, setView] = useState('landing')
  const [activeTab, setActiveTab] = useState('chat')

  if (view === 'landing') {
    return <LandingPage onEnter={() => setView('app')} />
  }

  const tabs = {
    chat: <ChatTab />,
    tramites: <TramitesTab />,
    calendario: <CalendarioTab />,
    analytics: <AnalyticsTab />,
  }

  return (
    <div className="flex h-screen overflow-hidden bg-udea-gris">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="flex-1 overflow-auto">
        {tabs[activeTab]}
      </main>
    </div>
  )
}
