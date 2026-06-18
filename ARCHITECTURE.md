# 🏗️ Arquitectura PARCERU - Documentación Técnica

## Visión General del Sistema

PARCERU es un sistema multi-agente híbrido que combina 12 agentes especializados con 4 módulos de soporte para crear un copiloto administrativo inteligente para la Universidad de Antioquia.

## Stack Tecnológico

### Backend
- **Python 3.11+**
- **LangGraph 0.2+**: Orquestación de agentes con grafo de estados
- **FastAPI**: API REST moderna con validación automática
- **ChromaDB 0.5+**: Base de datos vectorial para búsqueda semántica
- **Groq API**: LLM gratuito (Llama-3.3-70b) para generación
- **APScheduler**: Tareas programadas para monitoreo automático

### Frontend
- **React 18**: Framework declarativo con hooks
- **Vite**: Build tool moderno y rápido
- **TailwindCSS**: Utility-first CSS framework
- **Axios**: Cliente HTTP con interceptors

### Datos y ML
- **sentence-transformers**: Embeddings gratuitos offline
- **PyMuPDF + pdfplumber**: Procesamiento robusto de PDFs
- **BeautifulSoup4**: Web scraping inteligente

## Arquitectura de 3 Capas

### 1. Capa de Presentación (Frontend React)
```
┌─────────────────────────────────────┐
│            React App                │
├─────────────────────────────────────┤
│ Chat.jsx     │ Tramites.jsx        │
│ Calendario.jsx │ Analytics.jsx     │
└─────────────────────────────────────┘
```

**Responsabilidades:**
- Interfaz de usuario responsiva con 4 pestañas
- Manejo de estado local con React hooks
- Comunicación con backend via REST API
- Renderizado de respuestas con markdown

### 2. Capa de Aplicación (FastAPI Backend)
```
┌─────────────────────────────────────┐
│           FastAPI Router            │
├─────────────────────────────────────┤
│ /api/chat    │ /api/tramites       │
│ /api/calendario │ /api/analytics   │
│ /api/sia     │ /api/documentos     │
└─────────────────────────────────────┘
```

**Responsabilidades:**
- Exposición de endpoints REST con validación Pydantic
- Manejo de CORS para desarrollo local
- Integración con sistema de agentes LangGraph
- Gestión de errores y timeouts

### 3. Capa de Lógica de Negocio (Sistema Multi-Agente)
```
┌─────────────────────────────────────┐
│        LangGraph StateGraph         │
├─────────────────────────────────────┤
│  12 Agentes + 4 Módulos Soporte     │
│  Estado Compartido (17 campos)      │
│  Flujo Condicional Inteligente      │
└─────────────────────────────────────┘
```

## Los 12 Agentes del Grafo LangGraph

### Agentes de Control y Planificación
1. **Supervisor**: Analiza complejidad y planifica ejecución
2. **Memoria Agent**: Mantiene contexto conversacional
3. **Router**: Clasifica intención y detecta urgencias

### Agentes de Recuperación de Información
4. **RAG Agent**: Búsqueda semántica en ChromaDB local
5. **Search Agent**: Web scraping portal normativo UdeA
6. **Runtime Extractor** (vía módulo): PDFs on-demand

### Agentes Especializados por Dominio
7. **Tramite Agent**: Guías estructuradas paso a paso
8. **Calendario Agent**: Extracción de fechas académicas
9. **Urgency Agent**: Escalamiento de emergencias
10. **Out-of-Scope**: Filtro de consultas irrelevantes

### Agentes de Generación y Calidad
11. **Answerer**: Generación de respuesta con Groq LLM
12. **Verificador**: Control anti-alucinación
13. **Grader**: Evaluación de calidad y reintento

## Los 4 Módulos de Soporte

### 1. DocWatcher (Monitoreo Automático)
```python
# Cada 6 horas verifica cambios con SHA-256
scheduler = APScheduler()
@scheduler.interval_job(hours=6)
def verificar_documentos():
    for doc in documentos_monitoreados:
        if hash_cambio(doc.url):
            re_indexar(doc)
```

**Funcionalidades:**
- Hash SHA-256 para detectar cambios
- Re-indexación automática en ChromaDB
- Registro de eventos con timestamps
- API para forzar actualización manual

### 2. Runtime Extractor (PDFs On-Demand)
```python
def extraer_runtime(query):
    # 1. Buscar en portal normativo
    resultados = buscar_portal(query)
    
    # 2. Descargar PDFs en memoria
    for url in resultados[:3]:  # Máximo 3 PDFs
        pdf_bytes = httpx.get(url).content
        
        # 3. Procesar inmediatamente
        chunks = procesar_pdf(pdf_bytes)
        yield chunks
```

**Ventajas:**
- Acceso a CUALQUIER documento sin pre-indexación
- No consume espacio en disco
- Información siempre actualizada

### 3. SIA Scraper (Datos Académicos en Vivo)
```python
def consultar_sia(materia):
    url = f"https://sia.udea.edu.co/Catalogo/Cursos?q={materia}"
    response = httpx.get(url, timeout=15)
    
    # Cache 1 hora para evitar spam
    return parse_horarios_cupos(response.html)
```

**Datos extraídos:**
- Cupos disponibles por grupo
- Horarios y aulas
- Docentes asignados
- Prerrequisitos

### 4. Estado (Memoria Compartida)
```python
class EstadoCopiloto(TypedDict):
    # 17 campos sincronizados entre agentes
    mensajes: List[Message]
    documentos_rag: List[Dict]
    calidad: str
    # ... otros campos
```

## Flujo de Datos Detallado

### Ejemplo: "¿Cuándo son las matrículas 2026-2?"

1. **Frontend → Backend**
```javascript
POST /api/chat
{
  "mensaje": "¿Cuándo son las matrículas 2026-2?",
  "perfil": "pregrado"
}
```

2. **Supervisor** (200ms)
```python
# Análisis sin LLM
complejidad = detectar_complejidad(mensaje)  # "media"
plan = ["router", "rag_agent", "search_agent", "answerer"]
```

3. **Router** (1.5s)
```python
# Pre-checks rápidos
es_urgente = check_keywords_urgencia(mensaje)  # False
es_udea = check_keywords_udea(mensaje)        # True

# Clasificación LLM
intencion = groq_llm.classify(mensaje)        # "calendario"
```

4. **RAG Agent** (300ms)
```python
query_vector = embeddings.encode("matricula 2026-2")
docs = chromadb.query(query_vector, n_results=5)
```

5. **Search Agent** (2s)
```python
results = scrape_portal_normativo("calendario 2026-2")
```

6. **Answerer** (2s)
```python
context = combine(docs_rag, docs_web)
response = groq_llm.generate(context, perfil="pregrado")
```

7. **Grader** (700ms)
```python
quality = evaluate_response(response, criteria)
if quality == "aceptable":
    return response
else:
    retry_search_agent()
```

## Patrones de Diseño Implementados

### 1. Multi-Agent Orchestration (LangGraph)
- **Estado compartido**: TypedDict sincronizado
- **Flujo condicional**: Decisiones basadas en clasificación
- **Error handling**: Reintentos automáticos con límites

### 2. Hybrid RAG (Retrieval-Augmented Generation)
- **Nivel 1**: ChromaDB local (< 2s)
- **Nivel 2**: Web scraping (< 5s)
- **Nivel 3**: Runtime download (< 10s)
- **Nivel 4**: SIA en vivo (< 3s)

### 3. Auto-Improvement Loop
```
Answerer → Verificador → Grader
    ↑                       ↓
    └── Retry Search ←──────┘
```

### 4. Event-Driven Updates
- **DocWatcher**: Scheduler basado en eventos
- **Webhooks**: Actualizaciones push desde UdeA (futuro)
- **Cache invalidation**: TTL dinámico por tipo de documento

## Métricas de Rendimiento

### Tiempos de Respuesta Objetivo
| Tipo Consulta | Agentes Activos | Tiempo Objetivo |
|---------------|-----------------|-----------------|
| Simple (trámite) | 4 agentes | < 3s |
| Media (fechas) | 6 agentes | < 6s |
| Compleja (normativa) | 8+ agentes | < 10s |

### Escalabilidad
| Métrica | Valor Actual | Valor Objetivo |
|---------|--------------|----------------|
| Usuarios concurrentes | 50 | 500 |
| Consultas/minuto | 100 | 1000 |
| Documentos indexados | 50 | 500 |
| Tiempo de indexación | 30s/PDF | 10s/PDF |

## Seguridad y Privacidad

### Datos No Almacenados (Privacy by Design)
- ❌ Texto completo de consultas de usuarios
- ❌ Información personal identificable (PII)
- ❌ Historial de conversaciones completo

### Datos Almacenados (Solo Metadatos)
- ✅ Intención clasificada (anonimizada)
- ✅ Calidad de respuesta (métricas)
- ✅ Perfil de usuario (sin identificación)
- ✅ Timestamps y contadores

### Validación de Entrada
```python
# Sanitización automática
mensaje = sanitize_input(request.mensaje)
perfil = validate_perfil(request.perfil)

# Rate limiting por IP
@limiter.limit("60/minute")
def chat_endpoint():
    pass
```

## Deployment y DevOps

### Containerización
```dockerfile
# Multi-stage build para optimización
FROM python:3.11-slim as backend
FROM node:18-alpine as frontend
FROM nginx:alpine as proxy
```

### CI/CD Pipeline
1. **Tests**: pytest + vitest
2. **Build**: Docker multi-stage
3. **Deploy**: Railway/Vercel/AWS
4. **Monitor**: Logs + métricas

### Variables de Entorno por Ambiente
```bash
# Development
GROQ_API_KEY=dev_key
DEBUG=True
LOG_LEVEL=DEBUG

# Production  
GROQ_API_KEY=prod_key
DEBUG=False
LOG_LEVEL=INFO
RATE_LIMIT=1000/hour
```

## Roadmap Técnico

### Fase 1: Hackathon (Actual)
- ✅ 12 agentes + 4 módulos
- ✅ Frontend React completo
- ✅ API FastAPI con CORS
- ✅ Documentación técnica

### Fase 2: Piloto UdeA (Q2 2026)
- 🔄 Integración SSO UdeA
- 🔄 Webhook actualizaciones automáticas
- 🔄 Dashboard administrativo
- 🔄 Métricas avanzadas

### Fase 3: Escalamiento (Q3 2026)
- 📋 Microservicios independientes
- 📋 Base de datos PostgreSQL
- 📋 Cache distribuido (Redis)
- 📋 Load balancer (NGINX)

### Fase 4: Inteligencia Avanzada (Q4 2026)
- 📋 Fine-tuning modelo específico UdeA
- 📋 Embeddings especializados normativa
- 📋 Agentes predictivos (renovaciones, alertas)
- 📋 Integración con otros sistemas universitarios

---

Esta arquitectura garantiza escalabilidad, mantenibilidad y evolución continua del sistema PARCERU.