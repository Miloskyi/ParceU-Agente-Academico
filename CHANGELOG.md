# Changelog - PARCERU

Todos los cambios notables del proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-18 (Hackathon Release)

### 🎉 Added - Funcionalidades Principales

#### Sistema Multi-Agente (12 Agentes)
- **Supervisor**: Análisis de complejidad y planificación de agentes
- **Memoria Agent**: Contexto conversacional persistente  
- **Router**: Clasificación de intención + detección de urgencias
- **RAG Agent**: Búsqueda semántica en ChromaDB local
- **Search Agent**: Web scraping portal normativo UdeA en tiempo real
- **Tramite Agent**: Guías paso a paso para 20+ trámites estructurados
- **Calendario Agent**: Extracción inteligente de fechas académicas
- **Urgency Agent**: Escalamiento automático de emergencias estudiantiles
- **Answerer**: Generación de respuesta con Groq LLM + adaptación por perfil
- **Verificador**: Control anti-alucinación con validación documental
- **Grader**: Evaluación de calidad con ciclo de auto-mejora
- **Out-of-Scope**: Filtro eficiente de consultas fuera del dominio UdeA

#### Módulos de Soporte (4 Módulos)
- **DocWatcher**: Monitoreo automático de documentos normativos (APScheduler + SHA-256)
- **Runtime Extractor**: Descarga y procesamiento de PDFs on-demand
- **SIA Scraper**: Consulta en tiempo real de horarios, cupos y oferta académica
- **Estado**: TypedDict compartido con 17 campos sincronizados entre agentes

#### Frontend React Moderno
- **Arquitectura**: React 18 + Vite + TailwindCSS
- **Chat Component**: Interfaz conversacional con selector de perfil
- **Tramites Component**: Catálogo interactivo de trámites con guías
- **Calendario Component**: Vista multi-semestre (2025-1 a 2026-2)
- **Analytics Component**: Dashboard de métricas y KPIs de uso

#### Backend FastAPI Robusto
- **API REST**: Endpoints /api/chat, /api/tramites, /api/calendario, /api/analytics
- **CORS**: Configuración para desarrollo local y producción
- **Validación**: Modelos Pydantic para request/response
- **Error Handling**: Manejo graceful de timeouts y fallos

#### Sistema de Datos Híbrido
- **ChromaDB Local**: Base vectorial para búsqueda semántica rápida (< 2s)
- **Portal Normativo**: Web scraping en tiempo real para documentos actualizados
- **SIA Integration**: Consulta de cupos y horarios académicos en vivo
- **Trámites JSON**: 20+ procesos estructurados con pasos detallados

### 🔧 Technical Features

#### Recuperación Multi-Nivel
- **Nivel 1**: ChromaDB local (300ms) - Documentos pre-indexados
- **Nivel 2**: Portal normativo (2-3s) - Web scraping tiempo real  
- **Nivel 3**: Runtime download (3-5s) - PDFs on-demand
- **Nivel 4**: SIA live data (1-2s) - Horarios y cupos actuales

#### Auto-Mejora Continua
- **Ciclo Grader**: Evaluación automática de calidad de respuesta
- **Reintentos Inteligentes**: Búsqueda adicional si calidad insuficiente
- **Verificación Anti-Alucinación**: Validación de afirmaciones contra evidencia
- **Límites de Seguridad**: Máximo 2 reintentos para evitar loops infinitos

#### Monitoreo Proactivo  
- **DocWatcher Automático**: Verificación cada 6 horas de cambios en documentos
- **Hash SHA-256**: Detección precisa de modificaciones en PDFs
- **Re-indexación**: Actualización automática de ChromaDB cuando hay cambios
- **Logs Estructurados**: Registro de eventos para auditoría y debugging

#### Adaptación Multi-Perfil
- **Pregrado**: Tono casual y explicativo con ejemplos prácticos
- **Posgrado**: Lenguaje técnico y referencias a investigación  
- **Docente**: Enfoque en procesos administrativos y normativa
- **Administrativo**: Información precisa sobre reglamentos internos

### 🧪 Testing y Calidad

#### Testing Backend (Python)
- **36 tests unitarios**: Cobertura completa de agentes críticos
- **Property-based testing**: Validación con Hypothesis para edge cases
- **Tests sin API keys**: Funcionan offline para CI/CD
- **Mock integrations**: Tests de integración sin dependencias externas

#### Testing Frontend (React)
- **Vitest + React Testing Library**: Framework moderno de testing
- **Property-based testing**: Validación con fast-check
- **Coverage reporting**: Métricas de cobertura automatizadas
- **Component testing**: Tests unitarios de cada componente UI

#### Code Quality
- **Black + isort**: Formateo automático de código Python
- **Flake8**: Linting y style checking backend
- **ESLint + Prettier**: Linting y formateo frontend React
- **Type hints**: Tipado estático en Python con TypedDict

### 📊 Performance y Escalabilidad

#### Tiempos de Respuesta
- **Consultas simples** (trámites): 2-3 segundos
- **Consultas medias** (fechas): 4-6 segundos  
- **Consultas complejas** (normativa): 6-10 segundos
- **Detección urgencias**: < 500ms (pre-check sin LLM)

#### Capacidad del Sistema
- **Usuarios objetivo**: 8,000 estudiantes Ingeniería → 45,000+ UdeA
- **Documentos**: 50+ PDFs normativos indexados
- **Trámites**: 20+ procesos estructurados con guías
- **Calendario**: 4 semestres completos (2025-1 a 2026-2)

### 🛡️ Seguridad y Privacidad

#### Privacy by Design
- **Sin almacenamiento PII**: No guarda datos personales identificables
- **Analytics anónimos**: Solo metadatos (intención, perfil, calidad)
- **Sin historial completo**: No persiste texto de conversaciones
- **Disclaimer visible**: Respuestas son orientativas, no oficiales

#### Validación de Entrada
- **Sanitización**: Limpieza automática de inputs de usuario
- **Rate limiting**: Prevención de spam y abuso (futura implementación)
- **CORS seguro**: Configuración restrictiva para producción

### 🚀 Deployment y DevOps

#### Containerización
- **Dockerfile multi-stage**: Optimización de imagen para producción
- **Docker Compose**: Setup completo con un comando
- **Volume mapping**: Persistencia de datos y configuración

#### Documentación Completa
- **README.md**: Setup rápido en 5 pasos
- **ARCHITECTURE.md**: Documentación técnica detallada
- **DEPLOYMENT.md**: Guías para todos los ambientes
- **CONTRIBUTING.md**: Estándares del equipo y flujo de trabajo

#### Variables de Entorno
- **GROQ_API_KEY**: ✅ Requerida (API gratuita)
- **OPENAI_API_KEY**: ❌ Opcional (embeddings premium)
- **Configuración flexible**: Paths personalizables para datos

### 🎯 Innovaciones Diferenciadoras

#### Primer Copiloto Universitario Multi-Agente LATAM
- **Arquitectura especializada**: 12 agentes + 4 módulos vs chatbots simples
- **Dominio específico**: Optimizado para ecosistema universitario colombiano
- **Escalabilidad probada**: De prototipo a sistema empresarial

#### Sistema Híbrido de Recuperación  
- **Cobertura total**: Acceso a CUALQUIER documento oficial UdeA
- **Información actualizada**: Portal normativo + SIA en tiempo real
- **Fallback inteligente**: Múltiples niveles de búsqueda con degradación graceful

#### Auto-Mejora y Confiabilidad
- **Verificación anti-alucinación**: Validación automática contra evidencia
- **Monitoreo proactivo**: Sistema se actualiza automáticamente
- **Calidad garantizada**: Ciclo de evaluación con reintentos inteligentes

---

## [Unreleased] - Roadmap Futuro

### 🔄 En Desarrollo
- Integración SSO Universidad de Antioquia
- Dashboard administrativo para gestión de contenido
- API webhooks para actualizaciones push desde UdeA
- Métricas avanzadas con Prometheus + Grafana

### 📋 Planned Features
- Fine-tuning modelo LLM específico para normativa UdeA  
- Agentes predictivos (alertas de renovaciones, fechas importantes)
- Integración con más sistemas universitarios (biblioteca, bienestar)
- Soporte multiidioma (español, inglés, lenguas indígenas)
- Mobile app con notificaciones push
- Chatbot voice interface con speech-to-text

### 🏗️ Technical Debt
- Migración a microservicios independientes
- Base de datos PostgreSQL para metadatos
- Cache distribuido con Redis
- Load balancer con NGINX
- Monitoring con APM tools

---

**Nota**: Este proyecto fue desarrollado durante el Hackathon UdeA 2026 por el Equipo Softserve.
Transformando la experiencia estudiantil universitaria con IA conversacional. 🚀