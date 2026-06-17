import { useState, useEffect } from 'react'
import axios from 'axios'
import { RefreshCw, MessageSquare, AlertTriangle, CheckCircle, Bot } from 'lucide-react'

const C = { petroleo: '#006065', turquesa: '#069A7E', verde: '#C5E1A5', oscuro: '#004548' }

function KPICard({ icon: Icon, label, value, color }) {
  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
      <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-3" style={{ background: color }}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <p className="text-2xl font-bold text-gray-800">{value}</p>
      <p className="text-sm text-gray-500 mt-0.5">{label}</p>
    </div>
  )
}

export default function AnalyticsTab() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)

  const cargar = () => {
    setLoading(true)
    axios.get('/api/analytics')
      .then(r => setData(r.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }

  useEffect(() => { cargar() }, [])

  return (
    <div className="p-6" style={{ background: '#F4F8F7', minHeight: '100vh' }}>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <img src="/parceru.png" alt="UdeA" className="h-12 w-auto object-contain" />
            <div className="h-8 w-px bg-gray-200" />
            <h1 className="text-2xl font-bold" style={{ color: C.petroleo }}>Analytics del Sistema</h1>
          </div>
          <p className="text-gray-500 text-sm">Estadísticas de uso de la sesión actual</p>
          <div className="mt-2 h-0.5 w-16 rounded-full" style={{ background: C.turquesa }} />
        </div>
        <button onClick={cargar} disabled={loading}
          className="flex items-center gap-2 text-sm border border-gray-200 rounded-xl px-4 py-2 text-gray-600 transition-all"
          onMouseEnter={e => { e.currentTarget.style.background = C.turquesa; e.currentTarget.style.color = '#fff'; e.currentTarget.style.borderColor = C.turquesa }}
          onMouseLeave={e => { e.currentTarget.style.background = ''; e.currentTarget.style.color = '#4b5563'; e.currentTarget.style.borderColor = '#e5e7eb' }}>
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </button>
      </div>

      {data ? (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <KPICard icon={MessageSquare} label="Total consultas"   value={data.total ?? 0}               color={C.petroleo} />
            <KPICard icon={AlertTriangle} label="Casos urgentes"    value={data.urgentes ?? 0}            color="#E65100" />
            <KPICard icon={CheckCircle}   label="Calidad aceptable" value={`${data.tasa_aceptable ?? 0}%`} color={C.turquesa} />
            <KPICard icon={Bot}           label="Agentes activos"   value={Object.keys(data.por_agente ?? {}).length} color="#7B1FA2" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.por_intencion && Object.keys(data.por_intencion).length > 0 && (
              <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                <h3 className="font-semibold text-gray-800 mb-4">Consultas por intención</h3>
                <div className="space-y-2.5">
                  {Object.entries(data.por_intencion).sort((a, b) => b[1] - a[1]).map(([k, v]) => {
                    const total = Object.values(data.por_intencion).reduce((a, b) => a + b, 0)
                    const pct = total ? Math.round(v / total * 100) : 0
                    return (
                      <div key={k}>
                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                          <span className="capitalize">{k}</span>
                          <span className="font-medium">{v} ({pct}%)</span>
                        </div>
                        <div className="rounded-full h-2" style={{ background: '#E0EDEB' }}>
                          <div className="rounded-full h-2 transition-all" style={{ width: `${pct}%`, background: C.petroleo }} />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
            {data.por_perfil && Object.keys(data.por_perfil).length > 0 && (
              <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                <h3 className="font-semibold text-gray-800 mb-4">Consultas por perfil</h3>
                <div className="space-y-2.5">
                  {Object.entries(data.por_perfil).sort((a, b) => b[1] - a[1]).map(([k, v]) => {
                    const total = Object.values(data.por_perfil).reduce((a, b) => a + b, 0)
                    const pct = total ? Math.round(v / total * 100) : 0
                    return (
                      <div key={k}>
                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                          <span className="capitalize">{k}</span>
                          <span className="font-medium">{v} ({pct}%)</span>
                        </div>
                        <div className="rounded-full h-2" style={{ background: '#E0EDEB' }}>
                          <div className="rounded-full h-2 transition-all" style={{ width: `${pct}%`, background: C.turquesa }} />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="bg-white rounded-2xl p-10 text-center border border-gray-100">
          <MessageSquare className="w-12 h-12 mx-auto mb-3" style={{ color: C.verde }} />
          <p className="text-gray-500">Sin datos aún. Realiza consultas en el chat primero.</p>
          <button onClick={cargar} className="mt-4 text-sm underline" style={{ color: C.turquesa }}>
            Intentar cargar datos
          </button>
        </div>
      )}

      <p className="mt-4 text-xs text-gray-400 text-center">
        🔒 Solo metadatos anónimos · Sin texto de consultas ni datos personales
      </p>
    </div>
  )
}
