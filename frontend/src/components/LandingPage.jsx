import {
  MessageCircle,
  Calendar,
  BookOpen,
  BarChart3,
  ClipboardList,
  Heart,
  Users,
} from 'lucide-react'

// ---------------------------------------------------------------------------
// Datos estáticos de módulo — editables sin tocar el JSX
// ---------------------------------------------------------------------------

const DATA_FUNCIONALIDADES = [
  {
    icon: MessageCircle,
    titulo: 'Consulta de trámites',
    descripcion: 'Conoce los pasos y requisitos de los trámites académicos más frecuentes.',
  },
  {
    icon: Calendar,
    titulo: 'Calendario académico',
    descripcion: 'Consulta fechas clave de matrículas, exámenes y eventos del semestre.',
  },
  {
    icon: BookOpen,
    titulo: 'Reglamento estudiantil',
    descripcion: 'Resuelve dudas sobre derechos, deberes y normativas de la UdeA.',
  },
  {
    icon: BarChart3,
    titulo: 'Analíticas de uso',
    descripcion: 'Visualiza las preguntas más frecuentes y tendencias de consulta.',
  },
]

const DATA_PASOS = [
  {
    numero: 1,
    titulo: 'Escribe tu pregunta',
    descripcion: 'Redacta en lenguaje natural lo que necesitas saber sobre tu vida académica.',
  },
  {
    numero: 2,
    titulo: 'ParcerU consulta los documentos',
    descripcion: 'El sistema busca en los documentos oficiales de la UdeA la información más relevante.',
  },
  {
    numero: 3,
    titulo: 'Recibe una respuesta orientativa',
    descripcion: 'Obtienes la respuesta con la fuente del documento institucional como referencia.',
  },
]

const DATA_CATEGORIAS = [
  {
    nombre: 'Reglamento Estudiantil',
    icon: BookOpen,
    ejemplos: [
      'Mínimo de créditos para conservar el cupo',
      'Causales de cancelación de matrícula',
      'Proceso de apelación de notas',
      'Normas sobre monitorías académicas',
    ],
  },
  {
    nombre: 'Trámites y Procedimientos',
    icon: ClipboardList,
    ejemplos: [
      'Liquidación y pago de matrícula',
      'Matrícula de estudiantes en intercambio',
      'Solicitud de certificados y constancias',
      'Trámites para estudiantes indígenas y NARP',
    ],
  },
  {
    nombre: 'Calendario Académico',
    icon: Calendar,
    ejemplos: [
      'Fechas de inicio y cierre del semestre',
      'Periodos de adición y cancelación de materias',
      'Semana de exámenes finales',
      'Días festivos y vacaciones institucionales',
    ],
  },
  {
    nombre: 'Bienestar Universitario',
    icon: Heart,
    ejemplos: [
      'Servicios del Sistema de Bienestar UdeA',
      'Beneficios de alimentación y transporte',
      'Apoyos económicos y becas disponibles',
      'Actividades culturales y deportivas',
    ],
  },
  {
    nombre: 'Admisiones',
    icon: Users,
    ejemplos: [
      'Proceso de admisión para aspirantes nuevos',
      'Exentos de pago de derechos de matrícula',
      'Guía para aspirantes con pruebas especiales',
      'Requisitos para programas de arte y música',
    ],
  },
]

// ---------------------------------------------------------------------------
// HeroSection — sección principal visible sin scroll
// ---------------------------------------------------------------------------

function HeroSection({ onEnter }) {
  return (
    <section
      className="flex flex-col items-center justify-center text-center text-white min-h-screen px-4"
      style={{ background: 'linear-gradient(180deg, #006065 0%, #004548 100%)' }}
    >
      <img
        src="/parceru.png"
        alt="Logo ParcerU"
        className="w-32 sm:w-48 mb-6"
      />
      <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold mb-4">
        ParcerU
      </h1>
      <p className="text-base sm:text-lg md:text-xl max-w-xl mb-8 text-white/90">
        Tu copiloto administrativo en la Universidad de Antioquia
      </p>
      <button
        type="button"
        onClick={() => onEnter?.()}
        className="bg-udea-turquesa hover:bg-udea-oscuro text-white font-semibold px-8 py-3 rounded-lg text-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-udea-verde focus:ring-offset-2 focus:ring-offset-udea-petroleo"
      >
        Empezar ahora
      </button>
    </section>
  )
}

// ---------------------------------------------------------------------------
// Sub-componente: FuncionalidadesSection
// ---------------------------------------------------------------------------

function FuncionalidadesSection() {
  return (
    <section className="bg-udea-gris py-16 px-4">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-udea-oscuro text-center mb-10">
          ¿Qué puede hacer ParcerU?
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {DATA_FUNCIONALIDADES.map((item, index) => {
            const Icon = item.icon
            return (
              <div
                key={index}
                className="bg-white border border-udea-gris2 rounded-xl p-6 flex flex-col items-start gap-3 shadow-sm"
              >
                <Icon className="text-udea-turquesa w-8 h-8" aria-hidden="true" />
                <h3 className="text-udea-oscuro font-semibold text-base leading-snug">
                  {item.titulo}
                </h3>
                <p className="text-udea-oscuro/70 text-sm leading-relaxed">
                  {item.descripcion}
                </p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------------------
// Sección "¿Cómo Funciona?"
// ---------------------------------------------------------------------------

function ComoFuncionaSection() {
  return (
    <section className="bg-white py-16 px-4">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-3xl font-bold text-udea-oscuro text-center mb-12">
          ¿Cómo funciona?
        </h2>

        <div className="flex flex-col gap-8 mb-10">
          {DATA_PASOS.map((paso) => (
            <div
              key={paso.numero}
              className="flex items-start gap-6 bg-white rounded-xl p-6 shadow-sm border border-udea-gris2"
            >
              <span className="text-4xl font-bold text-udea-turquesa shrink-0 w-12 text-center leading-none">
                {paso.numero}
              </span>
              <div>
                <h3 className="text-lg font-semibold text-udea-oscuro mb-1">
                  {paso.titulo}
                </h3>
                <p className="text-udea-oscuro/80 text-base">
                  {paso.descripcion}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-udea-gris rounded-lg px-6 py-4 text-udea-petroleo text-sm text-center">
          ⚠️ Las respuestas son orientativas. Consulta las oficinas para decisiones definitivas.
        </div>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------------------
// ConsultasSection — categorías de temas consultables con ejemplos
// ---------------------------------------------------------------------------

function ConsultasSection() {
  if (!DATA_CATEGORIAS || DATA_CATEGORIAS.length === 0) {
    return (
      <section className="py-16 px-4 bg-udea-gris">
        <p className="text-red-600 text-center py-8 text-base font-medium">
          No se pudieron cargar los temas de consulta. Por favor recarga la página.
        </p>
      </section>
    )
  }

  return (
    <section className="py-16 px-4 bg-udea-gris">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-bold text-udea-oscuro text-center mb-3">
          ¿Sobre qué puedes consultarme?
        </h2>
        <p className="text-center text-udea-petroleo mb-10 text-sm sm:text-base">
          Fuentes: documentos oficiales de la Universidad de Antioquia
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {DATA_CATEGORIAS.map((categoria) => {
            const Icon = categoria.icon
            return (
              <div
                key={categoria.nombre}
                className="bg-white rounded-xl border border-udea-gris2 p-5 flex flex-col gap-3 shadow-sm"
              >
                <div className="flex items-center gap-3">
                  <Icon className="text-udea-turquesa shrink-0" size={22} aria-hidden="true" />
                  <h3 className="text-udea-petroleo font-semibold text-base leading-tight">
                    {categoria.nombre}
                  </h3>
                </div>
                <ul className="space-y-1.5">
                  {categoria.ejemplos.map((ejemplo) => (
                    <li
                      key={ejemplo}
                      className="text-udea-oscuro text-sm pl-2 border-l-2 border-udea-gris2"
                    >
                      {ejemplo}
                    </li>
                  ))}
                </ul>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------------------
// CTAFinalSection — segundo CTA al final de la página
// ---------------------------------------------------------------------------

function CTAFinalSection({ onEnter }) {
  return (
    <section className="bg-udea-petroleo py-20 px-4 text-center text-white">
      <div className="max-w-2xl mx-auto flex flex-col items-center gap-6">
        <h2 className="text-3xl sm:text-4xl font-bold">
          ¿Listo para empezar?
        </h2>
        <p className="text-white/80 text-base sm:text-lg max-w-md">
          Ingresa a ParcerU y resuelve tus dudas académicas en segundos.
        </p>
        <button
          type="button"
          onClick={() => onEnter?.()}
          className="bg-udea-verde text-udea-oscuro font-semibold px-10 py-3 rounded-lg text-lg hover:brightness-95 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-udea-verde focus:ring-offset-2 focus:ring-offset-udea-petroleo"
        >
          Ingresar a ParcerU
        </button>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------------------
// FooterSection — información institucional y aviso orientativo
// ---------------------------------------------------------------------------

function FooterSection({ year }) {
  return (
    <footer className="bg-udea-oscuro border-t-2 border-udea-turquesa px-4 py-10 text-white/70">
      <div className="max-w-4xl mx-auto flex flex-col items-center gap-3 text-center text-sm">
        <p className="font-semibold text-white text-base">ParcerU</p>
        <p>Universidad de Antioquia — Facultad de Ingeniería</p>
        <p className="max-w-xl text-xs leading-relaxed">
          Herramienta orientativa. Las respuestas no reemplazan la orientación oficial de las dependencias universitarias.
        </p>
        <p className="text-xs mt-1">© {year}</p>
      </div>
    </footer>
  )
}

// ---------------------------------------------------------------------------
// Componente principal — LandingPage ensamblado
// ---------------------------------------------------------------------------

export default function LandingPage({ onEnter }) {
  const year = new Date().getFullYear()
  return (
    <div className="w-full min-h-screen overflow-x-hidden">
      <HeroSection onEnter={onEnter} />
      <FuncionalidadesSection />
      <ComoFuncionaSection />
      <ConsultasSection />
      <CTAFinalSection onEnter={onEnter} />
      <FooterSection year={year} />
    </div>
  )
}

// ---------------------------------------------------------------------------
// Exportar las constantes para que las pruebas PBT puedan importarlas
// ---------------------------------------------------------------------------

export { DATA_FUNCIONALIDADES, DATA_PASOS, DATA_CATEGORIAS }
