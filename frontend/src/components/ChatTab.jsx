import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { Send, RefreshCw, AlertTriangle, ChevronDown, ChevronUp, GraduationCap, User } from 'lucide-react'
import API_BASE from '../api'

const PERFILES = [
  { value: 'pregrado',       label: 'Estudiante Pregrado' },
  { value: 'posgrado',       label: 'Estudiante Posgrado' },
  { value: 'docente',        label: 'Docente' },
  { value: 'administrativo', label: 'Personal Administrativo' },
]

const SUGERENCIAS = [
  '¿Cuántas materias puedo cancelar sin perder el cupo?',
  '¿Qué documentos necesito para inscribir trabajo de grado?',
  'Quedé en prueba académica, ¿qué hago?',
  '¿Cuál es la fecha límite de matrícula este semestre?',
  '¿Cómo solicito una transferencia interna?',
  '¿Cómo solicito un certificado de notas?',
  '¿Cuáles son los requisitos para una beca socioeconómica?',
  '¿Cómo interpongo un recurso de reposición?',
]

const C = {
  petroleo: '#006065',
  turquesa: '#069A7E',
  verde:    '#C5E1A5',
  oscuro:   '#004548',
}

// Componentes Markdown personalizados para cada tipo de elemento
const MD_COMPONENTS = {
  // Títulos de sección (## 📌 Respuesta, etc.)
  h2: ({ children }) => (
    <div className="flex items-center gap-2 mt-4 mb-2 first:mt-0">
      <span className="text-sm font-bold text-gray-700">{children}</span>
      <div className="flex-1 h-px bg-gray-100" />
    </div>
  ),
  h3: ({ children }) => (
    <p className="font-semibold text-gray-700 mt-3 mb-1 text-sm">{children}</p>
  ),
  // Párrafos normales
  p: ({ children }) => (
    <p className="text-sm text-gray-800 leading-relaxed mb-2">{children}</p>
  ),
  // Listas con bullet
  ul: ({ children }) => (
    <ul className="space-y-1 mb-2 ml-1">{children}</ul>
  ),
  li: ({ children }) => (
    <li className="flex items-start gap-2 text-sm text-gray-700">
      <span className="mt-1.5 w-1.5 h-1.5 rounded-full shrink-0" style={{ background: C.turquesa }} />
      <span className="leading-relaxed">{children}</span>
    </li>
  ),
  // Listas numeradas (pasos)
  ol: ({ children }) => (
    <ol className="space-y-1.5 mb-2 ml-1 counter-reset-item">{children}</ol>
  ),
  // Código inline (para citas de fuentes)
  code: ({ children }) => (
    <code className="text-xs px-1.5 py-0.5 rounded font-mono"
      style={{ background: '#E0EDEB', color: C.oscuro }}>
      {children}
    </code>
  ),
  // Texto en negrita
  strong: ({ children }) => (
    <strong className="font-semibold" style={{ color: C.petroleo }}>{children}</strong>
  ),
  // Texto en cursiva
  em: ({ children }) => (
    <em className="text-gray-500 not-italic text-xs">{children}</em>
  ),
  // Línea horizontal separadora
  hr: () => (
    <div className="my-3 h-px w-full" style={{ background: C.verde }} />
  ),
  // Blockquote (advertencias)
  blockquote: ({ children }) => (
    <div className="border-l-2 pl-3 my-2 text-sm italic text-gray-500"
      style={{ borderColor: C.turquesa }}>
      {children}
    </div>
  ),
}

function TypingIndicator() {
  return (
    <div className="flex items-end gap-2 mb-4">
      <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
        style={{ background: C.petroleo }}>
        <GraduationCap className="w-4 h-4 text-white" />
      </div>
      <div className="bg-white rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm border border-gray-100">
        <div className="flex gap-1 items-center h-4">
          {[0, 150, 300].map(delay => (
            <span key={delay} className="w-2 h-2 rounded-full animate-bounce"
              style={{ background: C.turquesa, animationDelay: `${delay}ms` }} />
          ))}
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ msg }) {
  const [showFuentes, setShowFuentes] = useState(false)
  const isUser = msg.role === 'user'

  return (
    <div className={`flex items-end gap-2 mb-5 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
        style={{ background: isUser ? C.turquesa : C.petroleo }}>
        {isUser ? <User className="w-4 h-4 text-white" /> : <GraduationCap className="w-4 h-4 text-white" />}
      </div>

      <div className={`max-w-[78%] flex flex-col gap-1 ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Alerta urgente */}
        {msg.es_urgente && !isUser && (
          <div className="flex items-start gap-2 rounded-xl px-3 py-2 text-sm w-full mb-1"
            style={{ background: '#FFF3E0', border: '1px solid #FFB74D', color: '#E65100' }}>
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <span className="font-medium text-xs">⚠️ Caso urgente — Contacta: secretaria.ingenieria@udea.edu.co | (604) 219 5555 | Línea crisis: 106</span>
          </div>
        )}

        {/* Burbuja */}
        <div
          className="shadow-sm text-sm leading-relaxed"
          style={isUser
            ? {
                background: C.petroleo,
                color: '#fff',
                borderRadius: '18px 18px 4px 18px',
                padding: '10px 16px',
              }
            : {
                background: '#fff',
                border: '1px solid #e8f0ef',
                borderRadius: '18px 18px 18px 4px',
                padding: '12px 16px',
                minWidth: '200px',
              }
          }
        >
          {isUser
            ? <p className="text-sm text-white">{msg.content}</p>
            : <ReactMarkdown components={MD_COMPONENTS}>{msg.content}</ReactMarkdown>
          }
        </div>

        {/* Footer: timestamp + fuentes */}
        <div className={`flex items-center gap-2 px-1 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
          <span className="text-xs text-gray-400">{msg.time}</span>
          {(msg.fuentes?.length > 0 || msg.documentos_info?.length > 0) && !isUser && (
            <button onClick={() => setShowFuentes(v => !v)}
              className="flex items-center gap-1 text-xs font-medium transition-colors"
              style={{ color: C.turquesa }}>
              📄 {msg.documentos_info?.length || msg.fuentes?.length} fuente{(msg.documentos_info?.length || msg.fuentes?.length) > 1 ? 's' : ''}
              {showFuentes ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
          )}
        </div>

        {/* Fuentes expandibles */}
        {showFuentes && (msg.fuentes?.length > 0 || msg.documentos_info?.length > 0) && (
          <div className="rounded-xl px-3 py-2.5 text-xs text-gray-600 space-y-2 w-full"
            style={{ background: '#E8F5E9', border: `1px solid ${C.verde}` }}>

            {/* Documentos con fecha de modificación */}
            {msg.documentos_info?.length > 0 && (
              <div className="space-y-1.5">
                <p className="font-semibold text-xs uppercase tracking-wide mb-1"
                  style={{ color: C.petroleo }}>Documentos consultados</p>
                {msg.documentos_info.map((doc, i) => (
                  <div key={i} className="flex items-start gap-2 bg-white/70 rounded-lg px-2 py-1.5">
                    <span className="text-base leading-none mt-0.5">📄</span>
                    <div>
                      <p className="font-medium text-gray-700">{doc.documento}</p>
                      <p className="text-gray-400 text-xs mt-0.5 flex items-center gap-1">
                        <span>🕒</span>
                        <span>Última modificación: <strong>{doc.fecha_modificacion}</strong></span>
                        {doc.articulo && <span className="ml-1">· {doc.articulo}</span>}
                        {doc.pagina && <span>· pág. {doc.pagina}</span>}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Citas textuales */}
            {msg.fuentes?.length > 0 && (
              <div className="space-y-1 pt-1 border-t border-white/50">
                <p className="font-semibold text-xs uppercase tracking-wide mb-1"
                  style={{ color: C.petroleo }}>Citas</p>
                {msg.fuentes.map((f, i) => (
                  <p key={i} className="flex items-start gap-1.5 leading-relaxed">
                    <span className="font-bold shrink-0" style={{ color: C.turquesa }}>•</span>
                    <span>{f}</span>
                  </p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default function ChatTab({ messages, setMessages, perfil, setPerfil }) {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, loading])

  const sendMessage = async (texto) => {
    const msg = texto || input.trim()
    if (!msg || loading) return
    setInput('')
    setMessages(prev => [...prev, {
      role: 'user', content: msg,
      time: new Date().toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' }),
    }])
    setLoading(true)
    try {
      const { data } = await axios.post(`${API_BASE}/api/chat`, { mensaje: msg, perfil })
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.respuesta,
        fuentes: data.fuentes || [],
        documentos_info: data.documentos_info || [],
        es_urgente: data.es_urgente,
        time: new Date().toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' }),
      }])
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '⚠️ No pude procesar tu consulta. Verifica que el backend esté corriendo.',
        fuentes: [], es_urgente: false,
        time: new Date().toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' }),
      }])
    } finally { setLoading(false) }
  }

  return (
    <div className="flex flex-col h-screen" style={{ background: '#F4F8F7' }}>
      {/* Header */}
      <div className="bg-white px-6 py-4 flex items-center justify-between shrink-0 shadow-sm"
        style={{ borderBottom: `3px solid ${C.verde}` }}>
        <div className="flex items-center gap-3">
          {/* Logo 1 sobre fondo blanco — tamaño mayor */}
          <img src="/parceru.png" alt="UdeA" className="h-12 w-auto object-contain" />
          <div className="h-8 w-px bg-gray-200" />
          <div>
            <h1 className="text-base font-bold" style={{ color: C.petroleo }}>Consulta Normativa</h1>
            <p className="text-xs text-gray-400">Reglamentos · Trámites · Fechas académicas</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <select value={perfil} onChange={e => setPerfil(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-gray-700 focus:outline-none"
            style={{ focusBorderColor: C.turquesa }}>
            {PERFILES.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
          </select>
          <button onClick={() => setMessages([{
            role: 'assistant',
            content: '¡Hola! Soy el **Copiloto Administrativo** de la Facultad de Ingeniería UdeA. Puedo ayudarte con preguntas sobre reglamentos, trámites, fechas académicas y más. ¿En qué te puedo ayudar hoy?',
            time: new Date().toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' }),
            fuentes: [], es_urgente: false,
          }])}
            className="flex items-center gap-1.5 text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-gray-500 hover:text-white transition-all"
            onMouseEnter={e => { e.currentTarget.style.background = C.turquesa; e.currentTarget.style.borderColor = C.turquesa; e.currentTarget.style.color = '#fff' }}
            onMouseLeave={e => { e.currentTarget.style.background = ''; e.currentTarget.style.borderColor = '#e5e7eb'; e.currentTarget.style.color = '#6b7280' }}>
            <RefreshCw className="w-3.5 h-3.5" /> Nueva
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 scrollbar-thin">
        {messages.map((msg, i) => <MessageBubble key={i} msg={msg} />)}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Sugerencias */}
      {messages.length <= 1 && (
        <div className="px-6 pb-3 flex gap-2 flex-wrap shrink-0">
          {SUGERENCIAS.slice(0, 4).map((s, i) => (
            <button key={i} onClick={() => sendMessage(s)}
              className="text-xs bg-white border rounded-full px-3 py-1.5 text-gray-600 transition-all"
              style={{ borderColor: C.verde }}
              onMouseEnter={e => { e.currentTarget.style.background = C.verde; e.currentTarget.style.color = C.oscuro }}
              onMouseLeave={e => { e.currentTarget.style.background = '#fff'; e.currentTarget.style.color = '#4b5563' }}>
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="bg-white border-t border-gray-100 px-6 py-4 shrink-0">
        <div className="flex gap-3 items-end">
          <textarea value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }}}
            placeholder="Escribe tu pregunta aquí... (Enter para enviar)"
            rows={1}
            className="flex-1 resize-none border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none scrollbar-thin max-h-32"
            style={{ minHeight: '44px' }}
            onFocus={e => e.target.style.borderColor = C.turquesa}
            onBlur={e => e.target.style.borderColor = '#e5e7eb'}
          />
          <button onClick={() => sendMessage()} disabled={loading || !input.trim()}
            className="text-white rounded-xl w-11 h-11 flex items-center justify-center shrink-0 transition-all shadow-sm disabled:opacity-40 disabled:cursor-not-allowed"
            style={{ background: C.turquesa }}>
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
