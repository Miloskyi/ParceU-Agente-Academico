import { useState, useEffect } from 'react'
import axios from 'axios'
import { Calendar, AlertCircle, AlertTriangle } from 'lucide-react'

const C = { petroleo: '#006065', turquesa: '#069A7E', verde: '#C5E1A5' }

const TIPO_BADGE = {
  matricula:  { bg: '#DBEAFE', text: '#1E40AF', label: 'Matrícula' },
  clases:     { bg: '#DCFCE7', text: '#166534', label: 'Clases' },
  evaluacion: { bg: '#FEF9C3', text: '#854D0E', label: 'Evaluación' },
  receso:     { bg: '#F3F4F6', text: '#374151', label: 'Receso' },
  grado:      { bg: '#EDE9FE', text: '#5B21B6', label: 'Grado' },
  tramite:    { bg: '#CCFBF1', text: '#115E59', label: 'Trámite' },
  otro:       { bg: '#F9FAFB', text: '#6B7280', label: 'Otro' },
}

function TipoBadge({ tipo }) {
  const style = TIPO_BADGE[tipo] || TIPO_BADGE.otro
  return (
    <span
      className="inline-block rounded-full px-2.5 py-0.5 text-xs font-medium"
      style={{ background: style.bg, color: style.text }}
    >
      {style.label}
    </span>
  )
}

export default function CalendarioTab() {
  const [semestres, setSemestres] = useState([])
  const [semestreActual, setSemestreActual] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('/api/calendario')
      .then(r => {
        const lista = r.data.semestres ?? []
        setSemestres(lista)
        // Seleccionar automáticamente el semestre activo, o el primero
        const activo = lista.find(s => s.estado === 'activo') || lista[0] || null
        setSemestreActual(activo)
      })
      .catch(() => {
        setSemestres([])
        setSemestreActual(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const eventos = semestreActual?.eventos ?? []

  return (
    <div className="p-6" style={{ background: '#F4F8F7', minHeight: '100vh' }}>
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <img src="/parceru.png" alt="UdeA" className="h-12 w-auto object-contain" />
            <div className="h-8 w-px bg-gray-200" />
            <h1 className="text-2xl font-bold" style={{ color: C.petroleo }}>Calendario Académico</h1>
          </div>
          <p className="text-gray-500 text-sm">
            {semestreActual?.descripcion ?? 'Universidad de Antioquia'}
          </p>
          <div className="mt-2 h-0.5 w-16 rounded-full" style={{ background: C.turquesa }} />
        </div>
        <div className="flex items-center gap-2 rounded-xl px-4 py-2 border"
          style={{ background: '#E0EDEB', borderColor: C.verde }}>
          <Calendar className="w-4 h-4" style={{ color: C.petroleo }} />
          <span className="text-sm font-semibold" style={{ color: C.petroleo }}>
            {semestreActual?.semestre ?? '—'}
          </span>
        </div>
      </div>

      {/* Selector de semestres */}
      {!loading && semestres.length > 0 && (
        <div className="mb-5 flex flex-wrap gap-2">
          {semestres.map(s => {
            const isActivo = s.estado === 'activo'
            const isSelected = semestreActual?.semestre === s.semestre
            const label = s.semestre + (s.estado === 'futuro' ? ' (provisional)' : '')

            let bg, color, border
            if (isSelected && isActivo) {
              bg = C.petroleo; color = '#fff'; border = C.petroleo
            } else if (isSelected) {
              bg = '#E0EDEB'; color = C.petroleo; border = C.petroleo
            } else {
              bg = '#fff'; color = '#6B7280'; border = '#D1D5DB'
            }

            return (
              <button
                key={s.semestre}
                onClick={() => setSemestreActual(s)}
                className="rounded-lg px-4 py-2 text-sm font-medium transition-colors"
                style={{ background: bg, color, border: `1px solid ${border}` }}
              >
                {label}
              </button>
            )
          })}
        </div>
      )}

      {/* Banner de fechas provisionales */}
      {semestreActual?.estado === 'futuro' && (
        <div className="mb-4 flex items-start gap-2 rounded-xl px-4 py-3"
          style={{ background: '#FEF9C3', border: '1px solid #FDE047' }}>
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-yellow-600" />
          <p className="text-sm text-yellow-800">
            ⚠️ Las fechas de este semestre son provisionales y pueden cambiar.
          </p>
        </div>
      )}

      {loading ? (
        <div className="space-y-3">
          {[...Array(8)].map((_, i) => <div key={i} className="bg-white rounded-xl h-14 animate-pulse" />)}
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden border border-gray-100">
          {eventos.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-gray-400">
              <Calendar className="w-10 h-10 mb-3 opacity-40" />
              <p className="text-sm">No hay eventos registrados para este semestre.</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr style={{ background: C.petroleo }}>
                  {['Evento', 'Tipo', 'Fecha inicio', 'Fecha fin', 'Notas'].map(h => (
                    <th key={h} className="text-left px-5 py-3.5 font-semibold text-white">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {eventos.map((ev, i) => (
                  <tr key={i} className="border-b border-gray-50 hover:transition-colors"
                    style={{ background: i % 2 === 0 ? '#fff' : '#F4F8F7' }}
                    onMouseEnter={e => e.currentTarget.style.background = '#E0EDEB'}
                    onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? '#fff' : '#F4F8F7'}>
                    <td className="px-5 py-3.5 font-medium text-gray-800">{ev.evento}</td>
                    <td className="px-5 py-3.5">
                      <TipoBadge tipo={ev.tipo_evento} />
                    </td>
                    <td className="px-5 py-3.5 text-gray-600">{ev.inicio || '—'}</td>
                    <td className="px-5 py-3.5 text-gray-600">{ev.fin || '—'}</td>
                    <td className="px-5 py-3.5 text-gray-500 text-xs">{ev.notas || ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {/* Franja turquesa inferior */}
          <div className="h-1" style={{ background: C.turquesa }} />
        </div>
      )}

      <div className="mt-4 flex items-start gap-2 rounded-xl px-4 py-3"
        style={{ background: '#E0EDEB', border: `1px solid ${C.verde}` }}>
        <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" style={{ color: C.petroleo }} />
        <p className="text-xs" style={{ color: C.petroleo }}>
          <strong>Importante:</strong> Estas fechas son orientativas. Verifica siempre en el{' '}
          <a href="https://www.udea.edu.co" target="_blank" rel="noopener noreferrer"
            className="underline" style={{ color: C.turquesa }}>
            Portal Universitario
          </a>{' '}
          el calendario oficial aprobado por la Vicerrectoría de Docencia.
        </p>
      </div>
    </div>
  )
}
