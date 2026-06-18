# 🎓 PARCERU - Copiloto Administrativo Inteligente UdeA

**Sistema multi-agente híbrido** con 12 agentes especializados + 4 módulos de soporte para asistencia académica y administrativa 24/7 de la Universidad de Antioquia.

Construido con LangGraph + React + FastAPI para el Hackathon 24h · Equipo Softserve.

---

## ⚡ Arranque en 5 pasos

```bash
# 1. Clonar e instalar dependencias
git clone <repositorio>
cd Hackathon-UdeA-Softserve
pip install -r requirements.txt

# 2. Configurar API keys
cp .env.example .env
# Editar .env y agregar GROQ_API_KEY (gratuita en console.groq.com)
# OPENAI_API_KEY es opcional — sin ella se usan embeddings locales gratuitos

# 3. Indexar documentos (PDFs normativos)
# Colocar PDFs en data/raw/ y ejecutar:
python run_ingesta.py

# 4A. Lanzar backend FastAPI (para frontend React)
python -m uvicorn backend.main:app --reload --port 8000

# 4B. Lanzar frontend React (en terminal separado)
cd frontend
npm install
npm run dev

# 5. Abrir en el navegador
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

> **Nota:** El sistema funciona sin PDFs (responde con información de trámites estructurada).
> Para respuestas normativas completas, coloca los PDFs descargados de
> [normativa.udea.edu.co](https://normativa.udea.edu.co/Documentos/Consultar) en `data/raw/`.

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│               REACT + VITE — Frontend                    │
│  💬 Chat │ 📋 Trámites │ 📅 Calendario │ 📊 Analytics     │
└──────────────────────────┬──────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────┐
│                 FASTAPI — Backend                        │
│  /chat │ /tramites │ /calendario │ /analytics │ /sia     │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│              LANGGRAPH — 12 Agentes + 4 Módulos         │
│                                                          │
│  🧠 [Supervisor] → 💾 [Memoria] → 🎯 [Router]           │
│         │                               │                │
│         ▼                               ▼                │
│  📚 [RAG] → 🔍 [Search] → 📅 [Calendario] → 💬 [Answer] │
│  📋 [Tramite] ────────────────────────────┘             │
│  🚨 [Urgency] ────────────────────────────┘             │
│  🚫 [Out-Scope] → END                                   │
│                                           │              │
│                    💬 [Answer] → ✅ [Verificador]       │
│                                           │              │
│                    ⭐ [Grader] ← ✅ [Verificador]       │
│                         │                               │
│                    ┌────▼─────┐                        │
│                    │ Calidad? │                        │
│                    └─┬──────┬─┘                        │
│                   OK │      │ Mejorar                  │
│                    END      └──→ 🔍 [Search] (retry)    │
│                                                          │
│  ── MÓDULOS DE SOPORTE ──                               │
│  📁 DocWatcher: Monitoreo automático docs               │
│  ⚡ RuntimeExtractor: Descarga PDFs on-demand          │
│  🎓 SIA Scraper: Horarios/cupos en tiempo real         │
│  📋 Estado: TypedDict compartido entre agentes          │
└──────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                  CAPA DE DATOS HÍBRIDA                   │
│  🗄️ ChromaDB │ 🌐 Portal Normativo │ 🎓 SIA │ 📄 JSON   │
│    (Local)     │    (Web Scraping)   │ (API) │ (Trámites)│
└──────────────────────────────────────────────────────────┘
```

---

## 📦 Módulos del Sistema

### 🤖 12 Agentes Principales (Grafo LangGraph)

| Agente | Descripción |
|--------|-------------|
| `agentes/supervisor.py` | Analiza complejidad de consultas y planifica ejecución de agentes |
| `agentes/memoria_agent.py` | Mantiene contexto conversacional y resumen de sesión |
| `agentes/router.py` | Clasifica intención del usuario y detecta urgencias (pre-check + LLM) |
| `agentes/rag_agent.py` | Recupera fragmentos normativos desde ChromaDB con filtro por categoría |
| `agentes/search_agent.py` | Busca documentos en portal normativo en tiempo real (web scraping) |
| `agentes/tramite_agent.py` | Guía paso a paso en trámites administrativos desde `tramites.json` |
| `agentes/calendario_agent.py` | Extrae fechas académicas de documentos recuperados |
| `agentes/urgency_agent.py` | Detecta emergencias y escala con contactos institucionales |
| `agentes/answerer.py` | Genera respuesta final con Groq, citas y adaptación al perfil |
| `agentes/verificador.py` | Control anti-alucinación verificando evidencia documental |
| `agentes/grader.py` | Auto-evalúa calidad de respuesta; reintenta si es insuficiente |
| `agentes/out_of_scope.py` | Filtra consultas fuera del dominio UdeA sin consumir LLM |

### 🔧 4 Módulos de Soporte

| Módulo | Descripción |
|--------|-------------|
| `agentes/doc_watcher.py` | Monitoreo automático de documentos normativos (APScheduler + SHA-256) |
| `agentes/runtime_extractor.py` | Descarga y procesa PDFs on-demand desde portal normativo |
| `agentes/sia_scraper.py` | Scraper de horarios, cupos y oferta académica en tiempo real |
| `agentes/estado.py` | TypedDict EstadoCopiloto (17 campos) compartido entre agentes |

### 🎨 Frontend React

| Módulo | Descripción |
|--------|-------------|
| `frontend/src/App.jsx` | Aplicación principal con 4 pestañas |
| `frontend/src/components/Chat.jsx` | Interfaz conversacional principal |
| `frontend/src/components/Tramites.jsx` | Catálogo de trámites con guías |
| `frontend/src/components/Calendario.jsx` | Vista calendario multi-semestre |
| `frontend/src/components/Analytics.jsx` | Dashboard de métricas y KPIs |

### ⚙️ Backend FastAPI

| Módulo | Descripción |
|--------|-------------|
| `backend/main.py` | API REST con endpoints para chat, trámites, calendario |
| `ingesta/procesador_pdf.py` | Extracción de texto y tablas de PDFs |
| `ingesta/chunker.py` | División en chunks (700 chars, overlap 120) |
| `ingesta/indexador.py` | Indexación en ChromaDB con metadatos |

### 📊 Datos y Configuración

| Directorio | Descripción |
|------------|-------------|
| `data/raw/` | PDFs normativos para indexar |
| `data/chroma_db/` | Base vectorial local (generada automáticamente) |
| `data/tramites/tramites.json` | 20+ trámites estructurados con pasos |
| `utils/` | Logger, formateador, analytics, helpers |

---

## 🗂️ Estructura de Archivos

```
Hackathon-UdeA-Softserve/
├── backend/
│   ├── main.py               ← API REST FastAPI con CORS y endpoints
│   └── __init__.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx           ← Aplicación React principal
│   │   ├── components/       ← Componentes de las 4 pestañas
│   │   │   ├── Chat.jsx      ← Interfaz conversacional
│   │   │   ├── Tramites.jsx  ← Catálogo de trámites
│   │   │   ├── Calendario.jsx ← Vista multi-semestre
│   │   │   └── Analytics.jsx ← Dashboard KPIs
│   │   └── index.css         ← Estilos TailwindCSS
│   ├── package.json          ← Dependencias React
│   ├── vite.config.js        ← Configuración Vite
│   └── tailwind.config.js    ← Configuración TailwindCSS
├── agentes/                  ← 12 Agentes + 4 Módulos
│   ├── supervisor.py         ← Análisis complejidad y planificación
│   ├── memoria_agent.py      ← Contexto conversacional
│   ├── router.py             ← Clasificación intención + urgencias  
│   ├── rag_agent.py          ← Búsqueda semántica ChromaDB
│   ├── search_agent.py       ← Web scraping portal normativo
│   ├── tramite_agent.py      ← Guías trámites estructurados
│   ├── calendario_agent.py   ← Extracción fechas académicas
│   ├── urgency_agent.py      ← Escalamiento emergencias
│   ├── answerer.py           ← Generación respuesta final
│   ├── verificador.py        ← Control anti-alucinación
│   ├── grader.py             ← Evaluación calidad + reintento
│   ├── out_of_scope.py       ← Filtro dominio UdeA
│   ├── doc_watcher.py        ← Monitoreo automático documentos
│   ├── runtime_extractor.py  ← Descarga PDFs on-demand
│   ├── sia_scraper.py        ← Scraper SIA tiempo real
│   ├── estado.py             ← TypedDict EstadoCopiloto
│   └── grafo.py              ← Grafo LangGraph compilado
├── data/
│   ├── raw/                  ← PDFs normativos (agregar manualmente)
│   ├── chroma_db/            ← Índice vectorial (auto-generado)
│   └── tramites/
│       └── tramites.json     ← 20+ trámites estructurados
├── ingesta/
│   ├── procesador_pdf.py     ← Extracción texto y tablas PDFs
│   ├── chunker.py            ← División chunks (700 chars, overlap 120)
│   ├── indexador.py          ← Indexación ChromaDB con metadatos
│   └── __init__.py
├── utils/
│   ├── logger.py             ← Logging centralizado
│   ├── formateador.py        ← Formateo citas, pasos y fechas
│   ├── analytics.py          ← Registro métricas (sin PII)
│   └── __init__.py
├── tests/
│   ├── test_tramites.py      ← Tests unitarios tramite_agent
│   ├── test_rag.py           ← Tests grader y router (sin API keys)
│   ├── test_frontend.test.js ← Tests React con Vitest
│   ├── preguntas_prueba.json ← Dataset pruebas hackathon
│   └── conftest.py           ← Configuración pytest
├── run_ingesta.py            ← Script indexación PDFs
├── requirements.txt          ← Dependencias Python
├── .env.example              ← Variables entorno template
├── .gitignore
├── Dockerfile                ← Containerización
└── README.md                 ← Esta documentación
```

---

## 🔑 Variables de Entorno

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `GROQ_API_KEY` | ✅ Sí | API key de Groq (gratuita en console.groq.com) |
| `OPENAI_API_KEY` | ❌ Opcional | Para embeddings OpenAI; sin ella usa sentence-transformers gratis |
| `CHROMA_PATH` | ❌ Opcional | Ruta a ChromaDB (default: `data/chroma_db`) |
| `TRAMITES_PATH` | ❌ Opcional | Ruta a tramites.json (default: `data/tramites/tramites.json`) |

---

## 🧪 Ejecutar Tests

```bash
# Backend - Tests Python con pytest
pytest tests/ -v

# Frontend - Tests React con Vitest  
cd frontend
npm test

# Tests específicos por módulo
pytest tests/test_tramites.py -v          # Solo trámites
pytest tests/test_rag.py -v               # Solo RAG y grader
cd frontend && npm run test:coverage       # Coverage frontend

# Property-based testing (avanzado)
pytest tests/ -v --tb=short -x            # Para con primer fallo
```

---

## 📥 Cómo Conseguir los PDFs Normativos

1. Ir a [normativa.udea.edu.co/Documentos/Consultar](https://normativa.udea.edu.co/Documentos/Consultar)
2. Buscar y descargar manualmente:
   - `Reglamento Estudiantil` (Acuerdo Superior 1 de 1981)
   - `Reglamento Posgrado`
   - `Estatuto General`
   - `Trabajo de Grado Ingeniería`
   - `Calendario Académico 2026`
   - `Bienestar Universitario`
3. Colocar los PDFs en `data/raw/`
4. Ejecutar `python run_ingesta.py`

> Con 5-6 PDFs bien elegidos se cubre el 90% de las consultas estudiantiles.

---

## 👥 Roles del Equipo

| Persona | Rol | Módulos |
|---------|-----|---------|
| **Persona 1** | Data Engineer | `ingesta/`, `data/raw/`, `run_ingesta.py` |
| **Persona 2** | AI Engineer | `agentes/`, `agentes/grafo.py` |
| **Persona 3** | Frontend | `interfaz/`, `interfaz/componentes/` |
| **Persona 4** | Lead / QA | Arquitectura, `tests/`, integración, pitch |

---

## 🚀 Innovaciones Diferenciadoras

- **Sistema híbrido cuádruple**: RAG local (ChromaDB) + web scraping (portal normativo) + descarga runtime (PDFs on-demand) + SIA en tiempo real (cupos/horarios)
- **Monitoreo proactivo**: DocWatcher con APScheduler verifica cambios automáticamente cada 6 horas usando hash SHA-256
- **Cobertura total**: Runtime Extractor puede acceder a CUALQUIER documento de normativa.udea.edu.co sin pre-indexación
- **Ciclo de auto-mejora**: Grader evalúa calidad → Verificador valida evidencia → reintenta automáticamente si es insuficiente
- **Detección de urgencias**: pre-check sin LLM para velocidad + escalamiento con contactos institucionales
- **Adaptación multi-perfil**: tono diferenciado para pregrado, posgrado, docente y administrativo
- **Información en vivo**: SIA Scraper consulta cupos disponibles y horarios actuales durante períodos de matrícula
- **Arquitectura 12+4**: 12 agentes especializados en grafo LangGraph + 4 módulos de soporte para funcionalidades avanzadas

---

## ⚖️ Ética y Privacidad

- Solo usa fuentes de información pública de la Universidad de Antioquia
- No almacena el texto de las consultas ni datos personales (PII)
- El analytics solo registra metadatos anónimos (intención, perfil, calidad)
- Disclaimer visible en la interfaz: las respuestas son orientativas

---

*PARCERU - Copiloto Administrativo Inteligente UdeA — Hackathon 24h · Facultad de Ingeniería · Equipo Softserve*

**"Transformando la experiencia estudiantil universitaria con IA conversacional"**
