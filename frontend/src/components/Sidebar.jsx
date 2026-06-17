import { MessageCircle, ClipboardList, Calendar, BarChart3 } from 'lucide-react'

const NAV = [
  { id: 'chat',       label: 'Consulta',   icon: MessageCircle },
  { id: 'tramites',   label: 'Trámites',   icon: ClipboardList },
  { id: 'calendario', label: 'Calendario', icon: Calendar },
  { id: 'analytics',  label: 'Analytics',  icon: BarChart3 },
]

export default function Sidebar({ activeTab, onTabChange }) {
  return (
    <aside
      className="w-64 flex flex-col h-screen shrink-0"
      style={{ background: 'linear-gradient(180deg, #006065 0%, #004548 100%)' }}
    >
      {/* Logo UdeA */}
      <div className="px-4 pt-7 pb-5 border-b border-white/10">
        <div className="flex flex-col items-center gap-3">
          {/* Logo 2 — versión blanca, visible sobre fondo oscuro, tamaño grande */}
          <img
            src="/parceru.png"
            alt="Universidad de Antioquia"
            className="w-44 h-auto object-contain drop-shadow-md"
          />
          {/* Franja turquesa separadora */}
          <div className="w-full h-0.5 rounded-full" style={{ background: '#069A7E' }} />
          <div className="text-center">
            <p className="text-white font-bold text-sm tracking-wider uppercase">
              Copiloto Administrativo
            </p>
            <p className="text-white/55 text-xs mt-0.5">Facultad de Ingeniería</p>
          </div>
        </div>
      </div>

      {/* Navegación */}
      <nav className="flex-1 px-3 py-5 space-y-1">
        {NAV.map(({ id, label, icon: Icon }) => {
          const active = activeTab === id
          return (
            <button
              key={id}
              onClick={() => onTabChange(id)}
              className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-150"
              style={
                active
                  ? { background: 'rgba(6,154,126,0.25)', color: '#ffffff', borderLeft: '3px solid #C5E1A5' }
                  : { color: 'rgba(255,255,255,0.55)' }
              }
              onMouseEnter={e => { if (!active) e.currentTarget.style.background = 'rgba(255,255,255,0.07)' }}
              onMouseLeave={e => { if (!active) e.currentTarget.style.background = 'transparent' }}
            >
              <Icon
                className="w-4 h-4 shrink-0"
                style={{ color: active ? '#C5E1A5' : undefined }}
              />
              {label}
            </button>
          )
        })}
      </nav>

      {/* Franja turquesa inferior + disclaimer */}
      <div style={{ borderTop: '3px solid #069A7E' }} className="px-4 py-3">
        <p className="text-white/30 text-xs text-center leading-relaxed">
          Solo orientativo · Consulta las oficinas para decisiones definitivas
        </p>
      </div>
    </aside>
  )
}
