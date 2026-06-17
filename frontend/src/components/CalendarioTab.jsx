import { useState, useEffect } from 'react'
import axios from 'axios'
import { Calendar, AlertCircle } from 'lucide-react'

const C = { petroleo: '#006065', turquesa: '#069A7E', verde: '#C5E1A5' }

export default function CalendarioTab() {
  const [eventos, setEventos] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('/api/calendario')
      .then(r => setEventos(r.data.eventos || []))
      .catch(() => setEventos([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="p-6" style={{ background: '#F4F8F7', minHeight: '100vh' }}>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <img src="/parceru.png" alt="UdeA" className="h-12 w-auto object-contain" />
            <div className="h-8 w-px bg-gray-200" />
            <h1 className="text-2xl font-bold" style={{ color: C.petroleo }}>Calendario Académico</h1>
          </div>
          <p className="text-gray-500 text-sm">Semestre 2026-1 — Universidad de Antioquia</p>
          <div className="mt-2 h-0.5 w-16 rounded-full" style={{ background: C.turquesa }} />
        </div>
        <div className="flex items-center gap-2 rounded-xl px-4 py-2 border"
          style={{ background: '#E0EDEB', borderColor: C.verde }}>
          <Calendar className="w-4 h-4" style={{ color: C.petroleo }} />
          <span className="text-sm font-semibold" style={{ color: C.petroleo }}>2026-1</span>
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[...Array(8)].map((_, i) => <div key={i} className="bg-white rounded-xl h-14 animate-pulse" />)}
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden border border-gray-100">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ background: C.petroleo }}>
                {['Evento', 'Fecha inicio', 'Fecha fin', 'Notas'].map(h => (
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
                  <td className="px-5 py-3.5 text-gray-600">{ev.inicio || '—'}</td>
                  <td className="px-5 py-3.5 text-gray-600">{ev.fin || '—'}</td>
                  <td className="px-5 py-3.5 text-gray-500 text-xs">{ev.notas || ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
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
