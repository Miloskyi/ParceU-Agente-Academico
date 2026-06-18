# Implementation Plan: Copiloto Administrativo Agéntico UdeA

## Overview

Implementación incremental del Copiloto siguiendo el orden de prioridades del hackathon:
1. Núcleo del grafo LangGraph (router + rag + answerer + grader)
2. Interfaz Gradio multi-pestaña conectada al grafo
3. tramites.json con 5+ trámites completos
4. Pipeline de ingesta (procesador_pdf + chunker + indexador)
5. README con instrucciones en 5 pasos
6. Tests básicos y de propiedad
7. Innovaciones diferenciadoras (urgency_agent, search_agent, analytics)

Cada tarea construye sobre las anteriores. No hay código huérfano — todo se integra al grafo o la interfaz al final de cada fase.

---

## Tasks

- [x] 1. Configurar estructura del proyecto y dependencias base
  - Crear la estructura de directorios completa según el diseño: `copiloto_udea/data/raw/`, `data/chroma_db/`, `data/tramites/`, `ingesta/`, `agentes/`, `interfaz/componentes/`, `utils/`, `tests/`
  - Crear `requirements.txt` con versiones exactas: `langgraph>=0.2`, `langchain>=0.3`, `langchain-anthropic>=0.3`, `langchain-openai>=0.3`, `chromadb>=0.5`, `gradio>=4.40`, `httpx>=0.27`, `pymupdf>=1.24`, `pdfplumber>=0.11`, `sentence-transformers>=3.0`, `hypothesis>=6.100`, `pytest>=8.0`, `python-dotenv>=1.0`
  - Crear `.env.example` con las variables: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` (opcional), `CHROMA_PATH=data/chroma_db`, `TRAMITES_PATH=data/tramites/tramites.json`
  - Crear `utils/logger.py` con configuración de logging estándar (nivel INFO, formato con timestamp y nombre de módulo)
  - Crear archivos `__init__.py` en todos los paquetes
  - _Requerimientos: 13.1, 13.2_

- [x] 2. Implementar el Estado del Grafo y la estructura de datos central
  - Crear `agentes/estado.py` con `EstadoCopiloto` TypedDict completo según el diseño: campos `mensajes`, `perfil_usuario`, `intencion`, `categoria`, `es_urgente`, `nivel_urgencia`, `pregunta_reformulada`, `documentos_rag`, `documentos_web`, `tramite_guia`, `pasos_tramite`, `fechas_relevantes`, `respuesta_candidata`, `fuentes_citadas`, `agente_usado`, `calidad`, `intentos`
  - Crear función `estado_inicial()` que retorna el Estado con valores por defecto seguros
  - Crear `utils/formateador.py` con funciones auxiliares: `formatear_cita()`, `formatear_pasos()`, `formatear_fechas()`
  - _Requerimientos: 2.4, 8.6, 9.6_

- [x] 3. Implementar el nodo Router con clasificación de intención
  - Crear `agentes/router.py` con la constante `PALABRAS_URGENCIA` (lista de al menos 15 palabras/frases clave críticas)
  - Implementar `router_node(estado)` que ejecuta pre-check de keywords sin llamada a LLM
  - Implementar llamada a Claude con prompt de clasificación en 5 categorías: normativa, trámite, calendario, urgencia, otro
  - Actualizar el Estado con `intencion`, `categoria`, `es_urgente`, `nivel_urgencia`, `pregunta_reformulada`
  - Implementar `decidir_ruta(estado)` como función de enrutamiento condicional del grafo
  - Envolver toda la lógica en try/except que actualiza `calidad=sin_info` si falla
  - _Requerimientos: 2.1, 2.2, 2.3, 2.4, 2.5, 7.4_

  - [ ]* 3.1 Escribir prueba de propiedad P3: Exhaustividad de clasificación del Router
    - **Propiedad 3: Exhaustividad de clasificación del Router**
    - Usar `hypothesis` con `@given(st.text())` y mock de Claude para verificar que la respuesta siempre está en `{normativa, trámite, calendario, urgencia, otro}`
    - **Valida: Requerimiento 2.1**

  - [ ]* 3.2 Escribir prueba de propiedad P4: Sensibilidad al pre-check de urgencia
    - **Propiedad 4: Sensibilidad al pre-check de urgencia**
    - Usar `hypothesis` con `@given(st.text())` inyectando keywords de urgencia y verificar `es_urgente=True`
    - **Valida: Requerimientos 2.2, 7.4**

- [x] 4. Implementar ChromaDB y el RAG Agent
  - Crear `agentes/rag_agent.py` con función `rag_agent_node(estado)` que inicializa ChromaDB PersistentClient
  - Implementar búsqueda semántica con filtro por `categoria` y score mínimo 0.3
  - Retornar top-6 fragmentos con metadatos `{contenido, fuente, articulo, pagina, score}` en `documentos_rag`
  - Si no hay resultados con score >= 0.3, establecer `documentos_rag = []`
  - Envolver en try/except para manejo de ChromaDB no disponible
  - _Requerimientos: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ]* 4.1 Escribir prueba de propiedad P5: Invariante de score mínimo RAG
    - **Propiedad 5: Invariante de score mínimo RAG**
    - Usar ChromaDB en memoria con documentos generados por `hypothesis`; verificar que todos los resultados tienen score >= 0.3
    - **Valida: Requerimiento 3.2**

  - [ ]* 4.2 Escribir prueba de propiedad P6: Invariante de cardinalidad RAG
    - **Propiedad 6: Invariante de cardinalidad RAG**
    - Verificar que `len(documentos_rag) <= 6` para cualquier búsqueda con resultados disponibles
    - **Valida: Requerimiento 3.3**

- [x] 5. Implementar el Tramite Agent y tramites.json
  - Crear `data/tramites/tramites.json` con los 5 trámites mínimos: certificado de notas, cancelación de materias, inscripción de trabajo de grado, beca socioeconómica, recurso de reposición. Cada trámite debe incluir todos los campos del esquema: `nombre`, `descripcion`, `categoria`, `tiempo_estimado`, `costo`, `oficina`, `url_oficial`, `keywords` (lista), `pasos` (lista numerada), `documentos_requeridos` (lista), `advertencias` (lista)
  - Crear `agentes/tramite_agent.py` con función `tramite_agent_node(estado)` que carga `tramites.json`
  - Implementar algoritmo de búsqueda por keywords con puntuación de coincidencia
  - Si puntuación = 0, establecer `tramite_guia = None` para que el grafo delegue al RAG_Agent
  - Almacenar en Estado: `tramite_guia`, `pasos_tramite`
  - _Requerimientos: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 5.1 Escribir prueba de propiedad P8: Búsqueda por keywords de trámites
    - **Propiedad 8: Búsqueda por keywords de trámites**
    - Usar `hypothesis` con `st.sampled_from()` sobre las keywords de `tramites.json`; verificar que cada keyword encuentra su trámite correspondiente
    - **Valida: Requerimiento 5.1**

  - [ ]* 5.2 Escribir prueba de propiedad P9: Integridad del esquema de tramites.json
    - **Propiedad 9: Integridad del esquema de tramites.json**
    - Verificar que todos los trámites del archivo tienen los 11 campos obligatorios con el tipo correcto
    - **Valida: Requerimiento 5.6**

- [x] 6. Implementar el Answerer y conectar los primeros nodos del grafo
  - Crear `agentes/answerer.py` con función `answerer_node(estado)` que llama a Claude con prompt de sistema completo
  - El prompt debe incluir el `perfil_usuario`, instrucciones de citado en formato `(Fuente: X, Artículo Y, pág. Z)`, presentación numerada de pasos de trámite y mensaje de fallback si no hay información
  - Almacenar resultado en `respuesta_candidata` y `fuentes_citadas`
  - Actualizar `agente_usado` con el nombre del agente que proveyó los documentos
  - Crear `agentes/grafo.py` con el StateGraph parcial: router → rag_agent → answerer (sin grader ni search aún)
  - Compilar y exponer `app_grafo` para pruebas tempranas
  - _Requerimientos: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [x] 7. Implementar el Grader y completar el ciclo de calidad
  - Crear `agentes/grader.py` con función `grader_node(estado)` que evalúa `respuesta_candidata`
  - Clasificar en `{aceptable, mejorar, sin_info}` basándose en presencia de citas, longitud de respuesta y palabras indicadoras de no-información
  - Incrementar `intentos` en 1 en cada evaluación
  - Implementar `decidir_post_grader(estado)` que retorna `"fin"` o `"search_agent"` según calidad e intentos
  - Actualizar `agentes/grafo.py` para incluir `grader` con aristas condicionales; agregar `END` para aristas de fin
  - _Requerimientos: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [ ]* 7.1 Escribir prueba de propiedad P10: Exhaustividad de clasificación del Grader
    - **Propiedad 10: Exhaustividad de clasificación del Grader**
    - Usar `@given(st.text())` como `respuesta_candidata`; verificar que resultado siempre está en `{aceptable, mejorar, sin_info}`
    - **Valida: Requerimiento 9.1**

  - [ ]* 7.2 Escribir prueba de propiedad P11: Invariante de incremento de intentos
    - **Propiedad 11: Invariante de incremento de intentos**
    - Usar `@given(st.integers(min_value=0, max_value=10))` como valor inicial de `intentos`; verificar que `intentos_final = intentos_inicial + 1`
    - **Valida: Requerimiento 9.6**

- [x] 8. Checkpoint — Verificar el flujo básico del grafo
  - Asegurar que todas las pruebas de las tareas anteriores pasen. Ejecutar el flujo manualmente con al menos 2 de las 5 preguntas del hackathon. Resolver cualquier problema antes de continuar.

- [x] 9. Implementar el Search Agent y conectarlo al grafo
  - Crear `agentes/search_agent.py` con función `search_agent_node(estado)` usando `httpx` con timeout de 10 segundos
  - URL principal: `normativa.udea.edu.co`; URL fallback predefinida en constante
  - Si el portal es inaccesible, registrar en log y continuar con `documentos_web = []`
  - Almacenar resultados en `documentos_web` con campo `url` de origen
  - Actualizar `agentes/grafo.py` para conectar: `rag_agent → search_agent → answerer` y el ciclo `grader → search_agent`
  - _Requerimientos: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 10. Implementar el Urgency Agent y el Calendario Agent
  - Crear `agentes/urgency_agent.py` con mapeo de tipos de urgencia a contactos institucionales (Bienestar Universitario, Línea de Crisis, Defensoría Estudiantil, etc.)
  - La función `urgency_agent_node(estado)` debe agregar contactos al contexto para el Answerer y establecer bandera de urgencia
  - Crear `agentes/calendario_agent.py` que extrae fechas desde `documentos_rag` o `documentos_web` y las almacena en `fechas_relevantes`
  - Conectar ambos nodos al grafo en `agentes/grafo.py`
  - _Requerimientos: 6.1, 6.2, 6.3, 6.4, 7.1, 7.2, 7.3, 7.5_

- [x] 11. Implementar la interfaz Gradio multi-pestaña
  - Crear `interfaz/componentes/chat.py` con el tab de Chat Principal: `gr.Chatbot`, `gr.Textbox` para entrada, `gr.Dropdown` para selector de perfil (pregrado/posgrado/docente/administrativo), `gr.Examples` con las 8 preguntas predefinidas, `gr.HTML` para alerta de urgencia
  - Crear `interfaz/componentes/tramites.py` con el tab de Trámites: `gr.Accordion` por cada trámite de `tramites.json` con pasos y documentos requeridos
  - Crear `interfaz/componentes/calendario.py` con el tab de Calendario: campo de consulta y presentación de fechas
  - Crear `interfaz/componentes/analytics.py` con el tab de Analytics: gráfico de distribución de intenciones, top-5 preguntas, tasa de calidad aceptable
  - Crear `interfaz/app.py` que ensambla los 4 tabs en `gr.TabbedInterface` con CSS de paleta UdeA y disclaimer de privacidad visible
  - Conectar el submit del chat al grafo compilado: llamar a `app_grafo.invoke(estado_inicial())` y actualizar el chatbot con la respuesta
  - Mostrar alerta visual si `es_urgente=True` en la respuesta del grafo
  - _Requerimientos: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 12.1_

- [x] 12. Implementar el sistema de analytics y registro de sesión
  - Crear módulo de analytics en `interfaz/componentes/analytics.py` con almacenamiento en memoria (lista de dicts por sesión)
  - Registrar por cada consulta: `timestamp`, `intencion`, `perfil_usuario`, `calidad_final`, `agente_usado`, `es_urgente` — SIN almacenar la consulta textual ni PII
  - Conectar el registro al callback post-respuesta del chat
  - Implementar cálculo de distribución de intenciones, top-5 consultas por tipo y tasa de calidad
  - _Requerimientos: 11.1, 11.2, 11.3, 11.4, 11.5, 12.2_

- [x] 13. Implementar el pipeline de ingesta de PDFs
  - Crear `ingesta/procesador_pdf.py` con función `procesar_pdf(ruta)` que usa `fitz` para texto por bloques y `pdfplumber` para tablas, preservando marcadores de artículos
  - Crear `ingesta/chunker.py` con `RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=120, separators=["Artículo", "\n\n", "\n", ". ", " "])`
  - Crear `ingesta/indexador.py` que intenta `OpenAIEmbeddings`, con fallback a `HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")`, y persiste en `ChromaDB.PersistentClient`
  - Implementar verificación de duplicados por ID antes de insertar (idempotencia)
  - Crear `run_ingesta.py` en la raíz que orquesta: listar PDFs en `data/raw/` → procesar → chunkear → indexar → reportar resumen
  - _Requerimientos: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 13.4_

  - [ ]* 13.1 Escribir prueba de propiedad P1: Invariante de tamaño de chunks
    - **Propiedad 1: Invariante de tamaño de chunks**
    - Usar `@given(st.text(min_size=1, max_size=5000))` y verificar que `all(len(c) <= 700 for c in chunks)`
    - **Valida: Requerimiento 1.2**

  - [ ]* 13.2 Escribir prueba de propiedad P7: Idempotencia de la ingesta
    - **Propiedad 7: Idempotencia de la ingesta**
    - Crear ChromaDB en memoria; ejecutar indexación dos veces; verificar `count_after_1 == count_after_2`
    - **Valida: Requerimiento 1.5**

  - [ ]* 13.3 Escribir prueba de propiedad P2: Round-trip de indexación
    - **Propiedad 2: Round-trip de indexación**
    - Indexar documentos generados; verificar que una query semánticamente relacionada recupera al menos uno de los documentos indexados
    - **Valida: Requerimiento 1.4**

- [x] 14. Escribir las pruebas de integración end-to-end
  - Crear `tests/preguntas_prueba.json` con las 5 preguntas del hackathon y sus respuestas esperadas mínimas (palabras clave que deben aparecer en la respuesta)
  - Crear `tests/test_rag.py` con pruebas que verifican que el RAG_Agent retorna resultados para las 5 preguntas del hackathon usando ChromaDB en memoria con documentos de muestra
  - Crear `tests/test_tramites.py` con pruebas que verifican que el Tramite_Agent encuentra el trámite correcto para los 5 trámites de `tramites.json`
  - Agregar prueba end-to-end en `tests/test_rag.py` que ejecuta el grafo completo con mock de Claude y verifica que la respuesta no está vacía y tiene citas
  - Verificar que el ciclo Grader→Search no supera 2 iteraciones en ningún caso
  - _Requerimientos: 14.1, 14.2, 14.3, 14.4, 14.5_

- [x] 15. Checkpoint final — Garantizar que el sistema pasa las 5 preguntas del hackathon
  - Ejecutar la suite completa de tests: `pytest tests/ -v`
  - Verificar las 5 preguntas del hackathon con el sistema funcionando end-to-end
  - Confirmar que la interfaz Gradio inicia con `python interfaz/app.py`
  - Resolver cualquier error antes de continuar.

- [x] 16. Crear README y documentación final
  - Crear `README.md` con instrucciones en exactamente 5 pasos: (1) clonar e instalar dependencias, (2) copiar `.env.example` a `.env` y configurar API keys, (3) colocar PDFs en `data/raw/` y ejecutar `python run_ingesta.py`, (4) ejecutar la interfaz con `python interfaz/app.py`, (5) abrir la URL indicada en consola
  - Incluir diagrama de arquitectura en ASCII o imagen en el README
  - Incluir tabla de módulos con descripción breve
  - Documentar los 4 roles del equipo en el README
  - _Requerimientos: 13.3_

- [x] 17. Implementar Runtime Extractor — descarga y procesamiento de PDFs en tiempo real
  - Crear `agentes/runtime_extractor.py` con función `extraer_documentos_runtime(query)` que orquesta el pipeline completo
  - Implementar `_buscar_en_portal(query)` que consulta `normativa.udea.edu.co/Documentos/Consultar?search=TÉRMINO` y extrae hasta 3 URLs de PDFs con sus títulos y fechas
  - Implementar `_descargar_pdf_en_memoria(url)` que descarga el PDF como bytes con timeout=20s sin guardarlo en disco
  - Implementar `_extraer_texto_pdf(pdf_bytes)` usando PyMuPDF (fitz) con fallback a pypdf si no está disponible
  - Implementar `_chunkear_texto(texto, fuente)` con chunk_size=700, overlap=120
  - Cada chunk retornado debe incluir metadatos: {contenido, fuente, url_origen, fecha_publicacion, tipo: "runtime_pdf"}
  - _Requerimientos: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7_

  - [ ]* 17.1 Escribir prueba de propiedad P12: Pipeline runtime no bloquea si portal cae
    - **Propiedad 12: Resiliencia del Runtime Extractor**
    - Mockear `httpx.get` para que lance `TimeoutException`; verificar que `extraer_documentos_runtime()` retorna `[]` sin lanzar excepción
    - **Valida: Requerimiento 15.6**

- [x] 18. Implementar DocWatcher — monitoreo y actualización automática de documentos
  - Crear `agentes/doc_watcher.py` con `RegistroDocumento` TypedDict: {url, titulo, hash_sha256, ultima_revision, ultima_actualizacion, estado}
  - Implementar `registrar_documento(url, titulo)` que calcula hash SHA-256 inicial y persiste en `data/doc_watcher_state.json`
  - Implementar `verificar_documento(url)` que descarga y compara hash; si cambió, llama a `_reindexar_documento()`
  - Implementar `_reindexar_documento(url, titulo, contenido_bytes)` que borra chunks viejos de ChromaDB e inserta los nuevos
  - Implementar `forzar_actualizacion(url)` que re-indexa sin importar si el hash cambió
  - Implementar `obtener_estado_documentos()` que retorna lista de estado para el frontend
  - Implementar `iniciar_scheduler()` y `detener_scheduler()` que controlan el hilo daemon de polling
  - El hilo daemon debe verificar documentos normativos cada 6 horas y ser detenible con flag `_scheduler_activo`
  - _Requerimientos: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8_

  - [ ]* 18.1 Escribir prueba de propiedad P13: Idempotencia de re-indexación
    - **Propiedad 13: Idempotencia del DocWatcher**
    - Mockear ChromaDB; ejecutar `_reindexar_documento()` dos veces con el mismo contenido; verificar que el count final es igual al count después de la primera ejecución
    - **Valida: Requerimiento 16.3**

- [x] 19. Implementar SIA Scraper — consulta de oferta académica en tiempo real
  - Crear `agentes/sia_scraper.py` con función `consultar_sia(query, forzar_actualizacion=False)` como función principal
  - Implementar `_obtener_del_cache(query)` y `_guardar_en_cache(query, datos)` con TTL de 1 hora
  - Implementar `_consultar_sia_http(query)` con petición a `sia.udea.edu.co` con timeout=15s
  - Implementar `_parsear_json_sia(datos_json, query)` y `_parsear_oferta_html(html, query)` como parsers alternativos
  - Implementar `_generar_datos_ejemplo(query)` como fallback cuando el portal no está accesible
  - Implementar `formatear_respuesta_sia(cursos)` que genera texto formateado con emojis de estado de cupos para el Answerer
  - Implementar `obtener_stats_cache()` y `limpiar_cache()` para los endpoints del backend
  - Agregar detección de keywords SIA en `search_agent.py` (`_es_consulta_sia(query)`) para activar el scraper automáticamente
  - _Requerimientos: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.8_

  - [ ]* 19.1 Escribir prueba de propiedad P14: Invariante de caché TTL
    - **Propiedad 14: Caché con TTL estricto**
    - Usar `hypothesis` con `@given(st.floats(min_value=3601.0, max_value=7200.0))` como tiempo transcurrido; verificar que `_obtener_del_cache()` retorna `None` si la entrada expiró
    - **Valida: Requerimiento 17.4**

- [x] 20. Integrar los tres módulos nuevos en el Search Agent y el backend
  - Actualizar `agentes/search_agent.py` para orquestar los tres niveles: RAG check → runtime_extractor → sia_scraper (si aplica)
  - El campo `agente_usado` del Estado debe reflejar el nivel usado: `"search_runtime"` | `"search_sia"` | `"rag_suficiente"` | `"search"`
  - Agregar en `backend/main.py` el startup/shutdown del DocWatcher scheduler
  - Agregar endpoints: `GET /api/documentos/estado`, `POST /api/documentos/actualizar`, `POST /api/documentos/registrar`
  - Agregar endpoints: `GET /api/sia/oferta`, `GET /api/sia/cache/stats`, `DELETE /api/sia/cache`
  - _Requerimientos: 15.1, 16.9, 17.7_

## Notes

- Las tareas marcadas con `*` son opcionales y pueden omitirse para acelerar el MVP del hackathon
- Cada tarea referencia los requerimientos específicos para trazabilidad
- Los checkpoints (tareas 8 y 15) garantizan validación incremental
- Las pruebas de propiedad usan `hypothesis` con mínimo 100 ejemplos por prueba
- El archivo `tramites.json` puede enriquecerse con más trámites sin modificar el código

## Task Dependency Graph

```json
{
  "waves": [
    {"wave": 1, "tasks": ["1 - Estructura del proyecto y dependencias base"]},
    {"wave": 2, "tasks": ["2 - Estado del Grafo y estructura de datos central"]},
    {"wave": 3, "tasks": ["3 - Router", "4 - RAG Agent", "5 - Tramite Agent y tramites.json"]},
    {"wave": 4, "tasks": ["6 - Answerer y grafo parcial"]},
    {"wave": 5, "tasks": ["7 - Grader y ciclo de calidad"]},
    {"wave": 6, "tasks": ["8 - Checkpoint básico del grafo"]},
    {"wave": 7, "tasks": ["9 - Search Agent", "10 - Urgency Agent y Calendario Agent"]},
    {"wave": 8, "tasks": ["11 - Interfaz Gradio multi-pestaña", "12 - Analytics y registro de sesión", "13 - Pipeline de ingesta de PDFs"]},
    {"wave": 9, "tasks": ["14 - Tests de integración end-to-end"]},
    {"wave": 10, "tasks": ["15 - Checkpoint final", "16 - README y documentación"]},
    {"wave": 11, "tasks": ["17 - Runtime Extractor", "18 - DocWatcher", "19 - SIA Scraper"]},
    {"wave": 12, "tasks": ["20 - Integración Search Agent + backend (runtime + docwatcher + sia)"]}
  ]
}
```
