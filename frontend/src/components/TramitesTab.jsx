import { useState, useEffect } from 'react'
import axios from 'axios'
import { Clock, Building2, ExternalLink, ChevronRight, X, AlertCircle, FileText, CheckCircle } from 'lucide-react'

const C = { petroleo: '#006065', turquesa: '#069A7E', verde: '#C5E1A5', oscuro: '#004548' }
const ICONOS = ['📄', '❌', '🎓', '💰', '📝', '🏛️', '✅', '🔄']

function TramiteModal({ tramite, onClose }) {
  if (!tramite) return null
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto shadow-2xl"
        onClick={e => e.stopPropagation()}>
        <div className="px-6 py-5 rounded-t-2xl flex items-start justify-between"
          style={{ background: C.petroleo }}>
          <div>
            <h2 className="text-white font-bold text-lg">{tramite.nombre}</h2>
            <p className="text-white/70 text-sm mt-1">{tramite.descripcion}</p>
          </div>
          <button onClick={onClose} className="text-white/70 hover:text-white ml-4 shrink-0 mt-0.5">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Franja turquesa */}
        <div className="h-1" style={{ background: C.turquesa }} />

        <div className="p-6 space-y-6">
          <div className="grid grid-cols-2 gap-3">
            {[
              { icon: Clock,     label: 'Tiempo estimado', value: tramite.tiempo_estimado },
              { icon: Building2, label: 'Oficina',         value: tramite.oficina },
            ].map(({ icon: Icon, label, value }) => (
              <div key={label} className="flex items-start gap-2.5 rounded-xl p-3"
                style={{ background: '#F4F8F7' }}>
                <Icon className="w-4 h-4 shrink-0 mt-0.5" style={{ color: C.turquesa }} />
                <div>
                  <p className="text-xs text-gray-500">{label}</p>
                  <p className="text-sm font-medium text-gray-800">{value}</p>
                </div>
              </div>
            ))}
          </div>

          <div>
            <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <CheckCircle className="w-4 h-4" style={{ color: C.turquesa }} />
              Pasos a seguir
            </h3>
            <ol className="space-y-2">
              {tramite.pasos.map((paso, i) => (
                <li key={i} className="flex items-start gap-3">
                  <span className="w-6 h-6 rounded-full text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5"
                    style={{ background: C.turquesa }}>
                    {i + 1}
                  </span>
                  <p className="text-sm text-gray-700 leading-relaxed">{paso.replace(/^\d+\.\s*/, '')}</p>
                </li>
              ))}
            </ol>
          </div>

          {tramite.documentos_requeridos?.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <FileText className="w-4 h-4" style={{ color: C.petroleo }} />
                Documentos requeridos
              </h3>
              <ul className="space-y-1.5">
                {tramite.documentos_requeridos.map((doc, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                    <span className="font-bold mt-0.5" style={{ color: C.turquesa }}>•</span>
                    {doc}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {tramite.advertencias?.length > 0 && (
            <div className="rounded-xl p-4" style={{ background: '#FFFDE7', border: '1px solid #FFF176' }}>
              <h3 className="font-semibold mb-2 flex items-center gap-2 text-sm text-amber-800">
                <AlertCircle className="w-4 h-4" /> Advertencias importantes
              </h3>
              <ul className="space-y-1">
                {tramite.advertencias.map((adv, i) => (
                  <li key={i} className="text-xs text-amber-700 flex items-start gap-1.5">
                    <span className="shrink-0 mt-0.5">⚠️</span>{adv}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {tramite.url_oficial && (
            <a href={tramite.url_oficial} target="_blank" rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 text-white rounded-xl py-3 text-sm font-medium transition-all"
              style={{ background: C.petroleo }}>
              <ExternalLink className="w-4 h-4" /> Ver en Portal Oficial UdeA
            </a>
          )}
        </div>
      </div>
    </div>
  )
}

export default function TramitesTab() {
  const [tramites, setTramites] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('/api/tramites')
      .then(r => setTramites(r.data.tramites || []))
      .catch(() => setTramites([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="p-6" style={{ background: '#F4F8F7', minHeight: '100vh' }}>
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <img src="/parceru.png" alt="UdeA" className="h-12 w-auto object-contain" />
          <div className="h-8 w-px bg-gray-200" />
          <h1 className="text-2xl font-bold" style={{ color: C.petroleo }}>Guía de Trámites</h1>
        </div>
        <p className="text-gray-500 text-sm">Procesos administrativos paso a paso</p>
        <div className="mt-2 h-0.5 w-16 rounded-full" style={{ background: C.turquesa }} />
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(5)].map((_, i) => <div key={i} className="bg-white rounded-2xl h-40 animate-pulse" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tramites.map((t, i) => (
            <button key={i} onClick={() => setSelected(t)}
              className="bg-white rounded-2xl p-5 text-left hover:shadow-md transition-all duration-200 group border border-transparent"
              onMouseEnter={e => e.currentTarget.style.borderColor = C.verde}
              onMouseLeave={e => e.currentTarget.style.borderColor = 'transparent'}>
              <div className="text-3xl mb-3">{ICONOS[i % ICONOS.length]}</div>
              <h3 className="font-semibold text-gray-800 text-sm leading-tight mb-2 group-hover:transition-colors"
                style={{}}>
                {t.nombre}
              </h3>
              <p className="text-xs text-gray-500 line-clamp-2 mb-3">{t.descripcion}</p>
              <div className="flex items-center justify-between">
                <span className="text-xs px-2 py-1 rounded-full flex items-center gap-1"
                  style={{ background: '#E0EDEB', color: C.petroleo }}>
                  <Clock className="w-3 h-3" /> {t.tiempo_estimado}
                </span>
                <ChevronRight className="w-4 h-4 text-gray-300 group-hover:transition-colors"
                  style={{}} />
              </div>
            </button>
          ))}
        </div>
      )}

      <TramiteModal tramite={selected} onClose={() => setSelected(null)} />
    </div>
  )
}
