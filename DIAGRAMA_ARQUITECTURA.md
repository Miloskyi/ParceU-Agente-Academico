# 🏗️ DIAGRAMA DE ARQUITECTURA PARCERU - PARA PRESENTACIÓN

## Arquitectura Visual Completa

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            👥 USUARIOS FINALES                                  │
│          45,000+ Estudiantes | Docentes | Administrativos UdeA                  │
└──────────────────────────┬──────────────────────────────────────────────────────┘
                           │ HTTPS/WSS
┌──────────────────────────▼──────────────────────────────────────────────────────┐
│                     🌐 FRONTEND REACT + VITE                                    │
│  ┌─────────────────┬─────────────────┬─────────────────┬─────────────────────┐  │
│  │   💬 Chat       │   📋 Trámites   │   📅 Calendar   │   📊 Analytics      │  │
│  │   Componente    │   Catálogo      │   Multi-Sem.    │   Dashboard         │  │
│  └─────────────────┴─────────────────┴─────────────────┴─────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────────────────────┘
                           │ REST API (JSON)
┌──────────────────────────▼──────────────────────────────────────────────────────┐
│                        ⚡ FASTAPI BACKEND                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │  /api/chat | /api/tramites | /api/calendario | /api/analytics | /api/sia   │ │
│  │              📋 Pydantic Validation + CORS + Rate Limiting                  │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────────────────────┘
                           │ invoke()
┌──────────────────────────▼──────────────────────────────────────────────────────┐
│                    🧠 LANGGRAPH MULTI-AGENT SYSTEM                              │
│                                                                                  │
│  ┌─ CONTROL LAYER ──────────────────────────────────────────────────────────┐   │
│  │  🎯 Supervisor    💾 Memoria Agent    🎯 Router                          │   │
│  │      │                  │                │                              │   │
│  │      ▼                  ▼                ▼                              │   │
│  │  Analiza             Mantiene        Clasifica                          │   │
│  │  Complejidad         Contexto        Intención                          │   │
│  └──────────────────────────────────────────┬───────────────────────────────┘   │
│                                             │                                   │
│  ┌─ RETRIEVAL LAYER ──────────────────────────▼───────────────────────────────┐ │
│  │  📚 RAG Agent ──→ 🔍 Search Agent ──→ ⚡ Runtime Extractor              │ │
│  │      │                  │                      │                        │ │
│  │      ▼                  ▼                      ▼                        │ │
│  │  ChromaDB           Portal UdeA            PDF Download                 │ │
│  │  Local              Web Scraping           On-Demand                    │ │
│  └──────────────────────────────────────────────┬───────────────────────────┘ │
│                                                 │                             │
│  ┌─ SPECIALIZED LAYER ─────────────────────────────▼─────────────────────────┐ │
│  │  📋 Tramite Agent    📅 Calendario Agent    🚨 Urgency Agent            │ │
│  │  🎓 SIA Scraper      🚫 Out-of-Scope                                    │ │
│  └──────────────────────────────────────────────┬───────────────────────────┘ │
│                                                 │                             │
│  ┌─ GENERATION LAYER ──────────────────────────────▼─────────────────────────┐ │
│  │  💬 Answerer Agent ──→ ✅ Verificador ──→ ⭐ Grader                     │ │
│  │       │                     │                   │                       │ │
│  │       ▼                     ▼                   ▼                       │ │
│  │  Groq LLM              Anti-Hallucination   Quality Control             │ │
│  │  Generation             Evidence Check      Auto-Retry Loop              │ │
│  └──────────────────────────────────────────────┬───────────────────────────┘ │
│                                                 │                             │
│  ┌─ SUPPORT MODULES ───────────────────────────────▼─────────────────────────┐ │
│  │  📁 DocWatcher: Auto-Monitor (APScheduler + SHA-256 Hash)               │ │
│  │  📋 Estado: Shared TypedDict State (17 campos sincronizados)            │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
                           │ Query/Update
┌──────────────────────────▼──────────────────────────────────────────────────────┐
│                      🗄️ DATA LAYER HÍBRIDA                                     │
│                                                                                  │
│  ┌─ LOCAL STORAGE ────────┬─ WEB SOURCES ─────────┬─ LIVE DATA ──────────────┐  │
│  │                        │                       │                          │  │
│  │  🗄️ ChromaDB           │  🌐 Portal Normativo   │  🎓 SIA Universidad      │  │
│  │   • Vectorial DB       │   • Web Scraping       │   • Cupos en Tiempo Real │  │
│  │   • Embeddings         │   • Docs Actualizados  │   • Horarios Actuales    │  │
│  │   • Búsqueda Semántica │   • Runtime Download    │   • Oferta Académica     │  │
│  │                        │                       │                          │  │
│  │  📄 Trámites JSON      │  📊 Analytics Store    │  🔄 DocWatcher State     │  │
│  │   • 20+ Procesos       │   • Métricas Anónimas  │   • Hash Monitoring      │  │
│  │   • Pasos Detallados   │   • KPIs de Uso        │   • Update Timestamps    │  │
│  └────────────────────────┴─────────────────────────┴──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Flujo de Datos Detallado

```
👤 Usuario: "¿Cuándo son las matrículas 2026-2?"
    │
    ▼ (HTTP POST)
🌐 Frontend React → /api/chat
    │
    ▼ (FastAPI Router)
⚡ Backend API → grafo.invoke(estado_inicial)
    │
    ▼ (LangGraph StateGraph)
🧠 SUPERVISOR (200ms)
    │ ┌─ Analiza: "cuándo" → complejidad MEDIA
    │ └─ Planifica: [router, rag, search, answerer, grader]
    ▼
💾 MEMORIA AGENT (100ms)
    │ └─ Actualiza contexto conversacional
    ▼
🎯 ROUTER (1.5s)
    │ ┌─ Pre-check urgencia: False
    │ ┌─ Pre-check dominio: True ("matrícula")
    │ └─ LLM clasifica: intención="calendario"
    ▼
📚 RAG AGENT (300ms)
    │ └─ ChromaDB.query("matricula 2026-2") → 5 docs
    ▼
🔍 SEARCH AGENT (2s)
    │ └─ Scraping portal normativo → docs actualizados
    ▼
📅 CALENDARIO AGENT (500ms)
    │ └─ Extrae fechas: "13-24 julio 2026"
    ▼
💬 ANSWERER (2s)
    │ └─ Groq LLM genera respuesta con fuentes
    ▼
✅ VERIFICADOR (800ms)
    │ └─ Valida: fechas tienen respaldo documental ✓
    ▼
⭐ GRADER (700ms)
    │ └─ Evalúa: calidad="aceptable" ✓
    ▼
📤 RESPUESTA FINAL (Total: ~6s)
    └─ "📅 Matrícula 2026-2: Del 13 al 24 de julio..."
```

## Arquitectura Escalable Multi-Modelo

```
                    ┌─ MODELO DEPLOYMENT OPTIONS ─┐
                    │                              │
        ┌─ LOCAL ─────────────┬─ CLOUD ────────────────┐
        │                     │                        │
   🖥️ OLLAMA LOCAL      ☁️ AMAZON BEDROCK        🌐 GROQ API
   • llama3.1:70b        • Claude-3.5 Sonnet      • llama-3.3-70b
   • codellama          • GPT-4 Turbo             • mixtral-8x7b
   • embeddings local   • Titan Embeddings       • Free Tier
   
   ┌─ PROS ─────────────┐  ┌─ PROS ─────────────────┐  ┌─ PROS ─────────────┐
   │ • 100% Privado      │  │ • Modelos Premium       │  │ • Setup Rápido     │
   │ • Sin costos API    │  │ • Escalabilidad Masiva  │  │ • Costo Bajo       │
   │ • Baja latencia     │  │ • Compliance Enterprise │  │ • Alta Disponib.   │
   │ • Control total     │  │ • SLAs Garantizados     │  │ • Fácil Migración  │
   └─────────────────────┘  └─────────────────────────┘  └─────────────────────┘

              ┌─ HYBRID DEPLOYMENT STRATEGY ─┐
              │                              │
              │  🏛️ INSTITUCIONES PÚBLICAS    │
              │                              │
              │  NIVEL 1: Ollama Local      │
              │  • Datos sensibles          │
              │  • Cumplimiento normativo   │
              │                              │
              │  NIVEL 2: Cloud Privado     │
              │  • AWS GovCloud             │
              │  • Azure Government         │
              │                              │
              │  NIVEL 3: API Externa       │
              │  • Groq/OpenAI (datos no   │
              │    sensibles solamente)     │
              └──────────────────────────────┘
```

## Arquitectura de Despliegue por Institución

```
┌─ PEQUEÑA INSTITUCIÓN ─────────────────────────────────────────────────────┐
│ < 5,000 estudiantes                                                       │
│                                                                           │
│ 🖥️ Servidor On-Premise                                                   │
│ • Ubuntu 22.04 LTS                                                       │
│ • Ollama + llama3.1:8b                                                   │
│ • Docker Compose                                                         │
│ • ChromaDB local                                                         │
│ • Backup automático                                                      │
│                                                                           │
│ 💰 Costo: ~$2,000 USD setup + $200/mes mantenimiento                    │
└───────────────────────────────────────────────────────────────────────────┘

┌─ INSTITUCIÓN MEDIA ───────────────────────────────────────────────────────┐
│ 5,000 - 25,000 estudiantes                                               │
│                                                                           │
│ ☁️ Cloud Híbrido                                                         │
│ • Kubernetes cluster (3 nodos)                                          │
│ • Ollama + llama3.1:70b                                                 │
│ • PostgreSQL + Redis                                                     │
│ • Load balancer + CDN                                                    │
│ • Monitoring (Prometheus)                                                │
│                                                                           │
│ 💰 Costo: ~$10,000 USD setup + $1,500/mes operación                     │
└───────────────────────────────────────────────────────────────────────────┘

┌─ INSTITUCIÓN GRANDE ──────────────────────────────────────────────────────┐
│ 25,000+ estudiantes (como UdeA)                                          │
│                                                                           │
│ 🏢 Infraestructura Empresarial                                           │
│ • Microservicios independientes                                          │
│ • Amazon Bedrock + Ollama hybrid                                         │
│ • Multi-región deployment                                                 │
│ • Auto-scaling                                                           │
│ • 99.9% SLA garantizado                                                  │
│                                                                           │
│ 💰 Costo: ~$50,000 USD setup + $8,000/mes operación                     │
└───────────────────────────────────────────────────────────────────────────┘
```