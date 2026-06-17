import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatTab from './components/ChatTab'
import TramitesTab from './components/TramitesTab'
import CalendarioTab from './components/CalendarioTab'
import AnalyticsTab from './components/AnalyticsTab'

export default function App() {
  const [activeTab, setActiveTab] = useState('chat')

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
