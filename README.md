# 🎓 Copiloto Administrativo — Universidad de Antioquia

**Sistema multi-agente** para orientación académica y administrativa de la Facultad de Ingeniería UdeA.
Construido con LangGraph + Gradio para el Hackathon 24h · Equipo Softserve.

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

# 4. Lanzar la interfaz
python interfaz/app.py

# 5. Abrir en el navegador
# La URL aparece en la consola: http://localhost:7860
```

> **Nota:** El sistema funciona sin PDFs (responde con información de trámites estructurada).
> Para respuestas normativas completas, coloca los PDFs descargados de
> [normativa.udea.edu.co](https://normativa.udea.edu.co/Documentos/Consultar) en `data/raw/`.

---

## 🏗️ Arquitectura del Sistema

```
┌──────────────────────────────────────────────────────┐
│            GRADIO — Interfaz Multi-pestaña            │
│  💬 Consulta │ 📋 Trámites │ 📅 Calendario │ 📊 Analytics │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│              LANGGRAPH — Grafo de Agentes             │
│                                                       │
│  [Router] → clasifica intención + detecta urgencias   │
│     ├── [RAG Agent]     → busca en ChromaDB           │
│     │      └── [Search Agent] → portal normativa UdeA │
│     │             └── [Calendario Agent] → fechas     │
│     │                     └── [Answerer] → Claude     │
│     │                            └── [Grader] ──┐     │
│     ├── [Tramite Agent] → guía paso a paso       │     │
│     └── [Urgency Agent] → escala emergencias     │     │
│                                ↑                 │     │
│                          reintento si            │     │
│                          calidad=mejorar ────────┘     │
└──────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│                   CAPA DE DATOS                       │
│  ChromaDB local │ normativa.udea.edu.co │ tramites.json│
└──────────────────────────────────────────────────────┘
```

---

## 📦 Módulos del Sistema

| Módulo | Descripción |
|--------|-------------|
| `agentes/router.py` | Clasifica la intención del usuario y detecta urgencias (pre-check sin LLM + Claude) |
| `agentes/rag_agent.py` | Recupera fragmentos normativos desde ChromaDB con filtro por categoría |
| `agentes/search_agent.py` | Busca documentos en el portal normativo en tiempo real (httpx) |
| `agentes/tramite_agent.py` | Guía paso a paso en trámites administrativos desde `tramites.json` |
| `agentes/calendario_agent.py` | Extrae fechas académicas de los documentos recuperados |
| `agentes/urgency_agent.py` | Detecta emergencias y escala con contactos institucionales |
| `agentes/answerer.py` | Genera respuesta final con Claude, citas y adaptación al perfil |
| `agentes/grader.py` | Auto-evalúa la calidad de la respuesta; reintenta si es insuficiente |
| `agentes/grafo.py` | Ensambla el grafo LangGraph completo |
| `ingesta/` | Pipeline de procesamiento de PDFs (PyMuPDF + pdfplumber + ChromaDB) |
| `interfaz/app.py` | Interfaz Gradio multi-pestaña con paleta UdeA |
| `data/tramites/tramites.json` | 5 trámites estructurados con pasos, documentos y advertencias |

---

## 🗂️ Estructura de Archivos

```
Hackathon-UdeA-Softserve/
├── data/
│   ├── raw/                  ← PDFs normativos (agregar antes del demo)
│   ├── chroma_db/            ← Índice vectorial (generado por run_ingesta.py)
│   └── tramites/
│       └── tramites.json     ← 5 trámites estructurados
├── ingesta/
│   ├── procesador_pdf.py     ← Extracción de texto y tablas de PDFs
│   ├── chunker.py            ← División en chunks (700 chars, overlap 120)
│   └── indexador.py          ← Indexación en ChromaDB
├── agentes/
│   ├── estado.py             ← TypedDict EstadoCopiloto (17 campos)
│   ├── router.py             ← Clasificación de intención + urgencia
│   ├── rag_agent.py          ← Búsqueda semántica en ChromaDB
│   ├── search_agent.py       ← Búsqueda web en tiempo real
│   ├── tramite_agent.py      ← Guía de trámites desde JSON
│   ├── calendario_agent.py   ← Extracción de fechas académicas
│   ├── urgency_agent.py      ← Escalamiento de emergencias
│   ├── answerer.py           ← Generación de respuesta con Claude
│   ├── grader.py             ← Auto-evaluación de calidad
│   └── grafo.py              ← Grafo LangGraph compilado
├── interfaz/
│   ├── app.py                ← Punto de entrada Gradio
│   ├── estilos.py            ← CSS y HTML paleta UdeA
│   └── componentes/
│       ├── chat.py           ← Tab de consulta
│       ├── tramites.py       ← Tab de trámites
│       ├── calendario.py     ← Tab de calendario
│       └── analytics.py     ← Tab de analytics
├── utils/
│   ├── logger.py             ← Logging centralizado
│   ├── formateador.py        ← Formateo de citas, pasos y fechas
│   └── analytics.py         ← Registro en memoria (sin PII)
├── tests/
│   ├── test_tramites.py      ← 11 tests unitarios del tramite_agent
│   ├── test_rag.py           ← 36 tests del grader y router (sin API keys)
│   ├── preguntas_prueba.json ← 5 preguntas del hackathon
│   └── conftest.py           ← Configuración de pytest
├── run_ingesta.py            ← Script único de ingesta de PDFs
├── requirements.txt
├── .env.example
└── README.md
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
# Todos los tests (no requieren API keys ni internet)
pytest tests/ -v

# Solo tests de trámites
pytest tests/test_tramites.py -v

# Solo tests de grader/router
pytest tests/test_rag.py -v
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

- **Doble recuperación**: RAG local (ChromaDB) + búsqueda web en tiempo real en portal normativo
- **Ciclo de calidad**: el Grader evalúa la respuesta y reintenta automáticamente si es insuficiente
- **Detección de urgencias**: pre-check sin LLM para velocidad + escalamiento con contactos institucionales
- **Multi-perfil**: adapta el tono para pregrado, posgrado, docente y administrativo
- **Trámites estructurados**: 5 guías paso a paso funcionan incluso sin PDFs indexados

---

## ⚖️ Ética y Privacidad

- Solo usa fuentes de información pública de la Universidad de Antioquia
- No almacena el texto de las consultas ni datos personales (PII)
- El analytics solo registra metadatos anónimos (intención, perfil, calidad)
- Disclaimer visible en la interfaz: las respuestas son orientativas

---

*Copiloto Administrativo UdeA — Hackathon 24h · Facultad de Ingeniería · Equipo Softserve*
