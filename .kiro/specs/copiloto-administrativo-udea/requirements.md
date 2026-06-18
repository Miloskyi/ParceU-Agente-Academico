# Requirements Document

## Introduction

El **Copiloto Administrativo Agéntico — Universidad de Antioquia** es un sistema multi-agente diseñado para asistir a estudiantes, docentes y personal administrativo en la consulta de normativa universitaria, orientación en trámites, seguimiento de fechas del calendario académico y gestión de situaciones urgentes. El sistema utiliza un grafo de agentes LangGraph orquestado por Claude (Anthropic), con recuperación híbrida (RAG local + búsqueda web en tiempo real), una interfaz Gradio multi-pestaña y almacenamiento vectorial en ChromaDB. A diferencia de un chatbot de preguntas y respuestas simple, el Copiloto ejecuta ciclos de auto-evaluación y reintento para garantizar respuestas de calidad.

El sistema está dirigido principalmente a los 8.000 estudiantes de la Facultad de Ingeniería UdeA, con arquitectura escalable para los 45.000 estudiantes de la universidad.

---

## Glossary

- **Copiloto**: El sistema completo descrito en este documento.
- **Grafo**: El grafo de agentes implementado con LangGraph que orquesta el flujo de procesamiento.
- **Estado**: La estructura `TypedDict` que viaja entre nodos del Grafo y acumula información de la sesión.
- **Router**: Nodo del Grafo que clasifica la intención del usuario y detecta urgencias.
- **RAG_Agent**: Nodo del Grafo que recupera fragmentos relevantes desde ChromaDB.
- **Search_Agent**: Nodo del Grafo que busca en el portal normativo en tiempo real.
- **Tramite_Agent**: Nodo del Grafo que guía al usuario paso a paso en un trámite administrativo.
- **Calendario_Agent**: Nodo del Grafo que extrae fechas importantes del calendario académico.
- **Urgency_Agent**: Nodo del Grafo que detecta casos críticos y escala a contactos de emergencia.
- **Answerer**: Nodo del Grafo que genera la respuesta final citando fuentes.
- **Grader**: Nodo del Grafo que auto-evalúa la calidad de la respuesta candidata.
- **ChromaDB**: Base de datos vectorial que almacena embeddings de los PDFs normativos.
- **tramites.json**: Archivo JSON estructurado que contiene la información de los trámites administrativos disponibles.
- **Ingesta**: Pipeline que procesa PDFs normativos y los indexa en ChromaDB.
- **Chunk**: Fragmento de texto resultante de dividir un documento PDF para indexación.
- **Perfil_Usuario**: Categoría del usuario (pregrado, posgrado, docente, administrativo).
- **Intención**: Clasificación de la consulta del usuario en una de cinco categorías: normativa, trámite, calendario, urgencia u otro.
- **Calidad**: Evaluación del Grader sobre la respuesta candidata: aceptable, mejorar o sin_info.
- **PII**: Información de identificación personal (Personally Identifiable Information).

---

## Requirements

---

### Requirement 1: Pipeline de Ingesta de Documentos Normativos

**User Story:** Como administrador del sistema, quiero procesar PDFs normativos y almacenar su contenido en ChromaDB, para que el RAG_Agent pueda recuperar información normativa relevante.

#### Acceptance Criteria

1. WHEN el administrador ejecuta `run_ingesta.py` con un directorio que contiene archivos PDF, THE Ingesta SHALL extraer el texto y tablas de cada PDF usando PyMuPDF y pdfplumber, respetando la estructura de artículos.
2. WHEN un PDF es procesado, THE Ingesta SHALL dividir el texto en Chunks con tamaño máximo de 700 caracteres, solapamiento de 120 caracteres y separadores definidos por artículos normativos.
3. WHEN los Chunks son generados, THE Ingesta SHALL generar embeddings mediante la API de OpenAI y, si esta no está disponible, THE Ingesta SHALL utilizar sentence-transformers como fallback.
4. WHEN los embeddings son generados, THE Ingesta SHALL persistir los vectores y metadatos en ChromaDB bajo un cliente PersistentClient en el directorio `data/chroma_db/`.
5. IF un archivo PDF ya fue indexado previamente con el mismo nombre, THEN THE Ingesta SHALL omitir el reprocesamiento y registrar un mensaje informativo en el log.
6. THE Ingesta SHALL registrar el progreso de cada etapa (extracción, chunking, embedding, indexación) en los logs del sistema.

---

### Requirement 2: Clasificación de Intención y Detección de Urgencias

**User Story:** Como usuario, quiero que el sistema entienda correctamente el tipo de consulta que realizo, para que me dirija al agente más adecuado sin necesidad de navegar menús.

#### Acceptance Criteria

1. WHEN el Router recibe una consulta del usuario, THE Router SHALL clasificar la intención en exactamente una de las cinco categorías: normativa, trámite, calendario, urgencia u otro.
2. WHEN el Router recibe una consulta, THE Router SHALL evaluar si la consulta contiene indicadores de urgencia utilizando un pre-check rápido basado en palabras clave críticas antes de invocar a Claude.
3. WHEN el Router clasifica una consulta como urgencia o detecta palabras clave críticas, THE Router SHALL establecer el campo `es_urgente` del Estado en `True` y asignar el `nivel_urgencia` correspondiente.
4. WHEN el Router determina la intención, THE Router SHALL actualizar los campos `intencion`, `categoria` y `pregunta_reformulada` del Estado antes de enrutar al siguiente nodo.
5. IF la consulta no encaja claramente en ninguna categoría, THEN THE Router SHALL clasificarla como "otro" y enrutar al RAG_Agent con búsqueda general.
6. THE Router SHALL completar la clasificación en menos de 3 segundos para consultas de texto de hasta 500 caracteres.

---

### Requirement 3: Recuperación de Información Normativa (RAG)

**User Story:** Como usuario, quiero obtener respuestas basadas en los reglamentos oficiales de la universidad, para que la información sea precisa y con fuentes verificables.

#### Acceptance Criteria

1. WHEN el RAG_Agent recibe una consulta clasificada, THE RAG_Agent SHALL realizar una búsqueda semántica en ChromaDB filtrando por la categoría determinada por el Router.
2. WHEN el RAG_Agent ejecuta la búsqueda, THE RAG_Agent SHALL retornar únicamente fragmentos con score de similitud igual o superior a 0.3.
3. WHEN el RAG_Agent obtiene resultados, THE RAG_Agent SHALL retornar los 6 fragmentos más relevantes con sus metadatos (fuente, artículo, página) y almacenarlos en el campo `documentos_rag` del Estado.
4. IF el RAG_Agent no encuentra fragmentos con score mínimo 0.3, THEN THE RAG_Agent SHALL establecer `documentos_rag` como lista vacía y permitir que el flujo continúe al Search_Agent.
5. THE RAG_Agent SHALL completar la búsqueda en ChromaDB en menos de 2 segundos para colecciones de hasta 10.000 Chunks.

---

### Requirement 4: Búsqueda Web en Tiempo Real

**User Story:** Como usuario, quiero que el sistema busque información actualizada cuando la base de datos local no tenga la respuesta, para que no reciba respuestas incompletas u obsoletas.

#### Acceptance Criteria

1. WHEN el Search_Agent es invocado con una consulta, THE Search_Agent SHALL realizar una solicitud HTTP al portal normativa.udea.edu.co para recuperar contenido relevante.
2. IF el portal normativa.udea.edu.co no está accesible, THEN THE Search_Agent SHALL utilizar una URL alternativa predefinida y registrar el fallback en los logs.
3. WHEN el Search_Agent obtiene resultados web, THE Search_Agent SHALL almacenarlos en el campo `documentos_web` del Estado con sus URL de origen.
4. IF la búsqueda web no retorna resultados útiles, THEN THE Search_Agent SHALL establecer `documentos_web` como lista vacía sin interrumpir el flujo del Grafo.
5. THE Search_Agent SHALL completar la búsqueda web con timeout de 10 segundos para evitar bloqueos en el flujo del Grafo.

---

### Requirement 5: Orientación en Trámites Administrativos

**User Story:** Como estudiante, quiero recibir una guía paso a paso de los trámites que necesito realizar, para no perder tiempo buscando información dispersa en la web.

#### Acceptance Criteria

1. WHEN el Tramite_Agent recibe una consulta clasificada como trámite, THE Tramite_Agent SHALL buscar el trámite más relevante en `tramites.json` utilizando coincidencia de palabras clave.
2. WHEN el Tramite_Agent encuentra un trámite, THE Tramite_Agent SHALL extraer y almacenar en el Estado los campos: nombre, descripcion, pasos, documentos_requeridos, tiempo_estimado, costo, oficina, url_oficial y advertencias.
3. THE tramites.json SHALL contener al menos los siguientes cinco trámites: certificado de notas, cancelación de materias, inscripción de trabajo de grado, beca socioeconómica y recurso de reposición.
4. WHEN el Tramite_Agent recupera un trámite, THE Tramite_Agent SHALL almacenar los pasos en el campo `pasos_tramite` del Estado para que el Answerer los presente de forma numerada.
5. IF el Tramite_Agent no encuentra ningún trámite que coincida con la consulta, THEN THE Tramite_Agent SHALL establecer `tramite_guia` como vacío y enrutar al RAG_Agent para búsqueda normativa complementaria.
6. THE tramites.json SHALL seguir el esquema definido con los campos: nombre, descripcion, categoria, tiempo_estimado, costo, oficina, url_oficial, keywords, pasos, documentos_requeridos y advertencias.

---

### Requirement 6: Monitoreo del Calendario Académico

**User Story:** Como estudiante, quiero consultar las fechas importantes del calendario académico, para planificar mis actividades sin depender de buscar el PDF del calendario manualmente.

#### Acceptance Criteria

1. WHEN el Calendario_Agent recibe una consulta sobre fechas académicas, THE Calendario_Agent SHALL extraer las fechas relevantes del contenido disponible (RAG o web) y almacenarlas en el campo `fechas_relevantes` del Estado.
2. WHEN el Calendario_Agent identifica fechas, THE Calendario_Agent SHALL incluir el tipo de evento, la fecha específica y el periodo académico correspondiente.
3. WHEN el sistema presenta fechas al usuario, THE Answerer SHALL formatear las fechas en orden cronológico con descripción clara del evento.
4. IF no se encuentran fechas relacionadas con la consulta, THEN THE Calendario_Agent SHALL informar al usuario que no dispone de esa información en la base de conocimiento actual.

---

### Requirement 7: Detección y Escalamiento de Urgencias

**User Story:** Como estudiante en situación crítica, quiero que el sistema identifique mi urgencia y me proporcione los contactos de emergencia de inmediato, para recibir ayuda oportuna.

#### Acceptance Criteria

1. WHEN el Estado tiene `es_urgente` igual a `True`, THE Urgency_Agent SHALL agregar a la respuesta los contactos de emergencia relevantes según el tipo de urgencia detectada.
2. WHEN se detecta una urgencia, THE Copiloto SHALL mostrar una alerta visual destacada en la interfaz antes de presentar la respuesta completa.
3. THE Urgency_Agent SHALL reconocer al menos los siguientes tipos de urgencias: crisis de salud mental, acoso o violencia, situación académica crítica (ej. prueba académica con riesgo de pérdida de cupo) y problemas económicos severos.
4. WHEN el Router detecta palabras clave de urgencia en la consulta, THE Router SHALL activar el pre-check de urgencia antes de la clasificación completa por Claude para minimizar la latencia.
5. IF se detecta una urgencia de salud mental o violencia, THEN THE Copiloto SHALL incluir en la respuesta los números de línea de crisis y bienestar universitario.

---

### Requirement 8: Generación de Respuestas con Citas

**User Story:** Como usuario, quiero recibir respuestas claras que indiquen de dónde proviene cada afirmación, para poder verificar la información por mi cuenta.

#### Acceptance Criteria

1. WHEN el Answerer recibe el Estado con documentos recuperados, THE Answerer SHALL generar una respuesta en lenguaje natural usando Claude que integre la información de `documentos_rag` y `documentos_web`.
2. WHEN el Answerer genera una respuesta con información de fuentes, THE Answerer SHALL incluir citas en el formato estándar: `(Fuente: X, Artículo Y, pág. Z)`.
3. WHEN el Answerer genera una respuesta con pasos de trámite, THE Answerer SHALL presentar los pasos del campo `pasos_tramite` en formato numerado con los documentos requeridos listados al final.
4. THE Answerer SHALL adaptar el tono y nivel de detalle de la respuesta al Perfil_Usuario del Estado (pregrado, posgrado, docente, administrativo).
5. IF el Estado no contiene documentos relevantes en ningún campo, THEN THE Answerer SHALL informar claramente al usuario que no tiene información disponible y sugerir canales oficiales de consulta.
6. THE Answerer SHALL almacenar la respuesta generada en el campo `respuesta_candidata` y las fuentes utilizadas en `fuentes_citadas` del Estado.

---

### Requirement 9: Auto-evaluación y Reintento de Calidad

**User Story:** Como usuario, quiero que el sistema verifique internamente si su respuesta es buena antes de enviármela, para recibir respuestas de mayor calidad.

#### Acceptance Criteria

1. WHEN el Grader recibe el Estado con una `respuesta_candidata`, THE Grader SHALL evaluar la calidad de la respuesta y clasificarla en una de tres categorías: `aceptable`, `mejorar` o `sin_info`.
2. WHEN el Grader clasifica la respuesta como `aceptable`, THE Grader SHALL finalizar el flujo y permitir que la respuesta sea presentada al usuario.
3. WHEN el Grader clasifica la respuesta como `mejorar` y el campo `intentos` del Estado es menor a 2, THE Grader SHALL enrutar el flujo al Search_Agent para obtener información adicional y reintentar.
4. WHEN el Grader clasifica la respuesta como `mejorar` y el campo `intentos` es igual o mayor a 2, THE Grader SHALL finalizar el flujo con la mejor respuesta disponible para evitar ciclos infinitos.
5. WHEN el Grader clasifica la respuesta como `sin_info`, THE Grader SHALL finalizar el flujo e informar al usuario que no se encontró información suficiente.
6. THE Grader SHALL incrementar el campo `intentos` del Estado en 1 cada vez que evalúe una respuesta.

---

### Requirement 10: Interfaz de Usuario Multi-pestaña

**User Story:** Como usuario, quiero una interfaz web clara con accesos directos a las funciones principales, para interactuar con el Copiloto sin necesidad de conocer comandos técnicos.

#### Acceptance Criteria

1. THE Copiloto SHALL presentar una interfaz Gradio con cuatro pestañas: Chat Principal, Trámites Paso a Paso, Calendario Académico y Analytics.
2. WHEN el usuario accede a la interfaz, THE Copiloto SHALL mostrar un selector de Perfil_Usuario con las opciones: pregrado, posgrado, docente y administrativo.
3. THE Copiloto SHALL aplicar la paleta de colores institucional de la Universidad de Antioquia (azul #003087, amarillo #FFD100) mediante CSS personalizado.
4. WHEN el Estado tiene `es_urgente` igual a `True`, THE Copiloto SHALL mostrar una alerta visual destacada en la interfaz con los contactos de emergencia.
5. THE interfaz SHALL mostrar 8 preguntas de ejemplo predefinidas en el Chat Principal para orientar a los usuarios nuevos.
6. WHEN el usuario selecciona una pregunta de ejemplo, THE Copiloto SHALL cargar automáticamente esa pregunta en el campo de entrada del chat.
7. IF el sistema tarda más de 30 segundos en responder, THEN THE Copiloto SHALL mostrar un indicador de progreso o mensaje de espera al usuario.

---

### Requirement 11: Panel de Analytics

**User Story:** Como administrador, quiero ver estadísticas de uso del sistema, para entender qué temas consultan más los usuarios y mejorar la base de conocimiento.

#### Acceptance Criteria

1. THE Copiloto SHALL registrar cada consulta procesada con su intención clasificada, Perfil_Usuario y timestamp en un almacenamiento local de sesión.
2. WHEN el usuario accede a la pestaña Analytics, THE Copiloto SHALL mostrar la distribución de consultas por categoría de intención en un gráfico de barras o tabla.
3. WHEN el usuario accede a la pestaña Analytics, THE Copiloto SHALL mostrar las 5 preguntas más frecuentes de la sesión actual.
4. THE Copiloto SHALL calcular y mostrar la tasa de respuestas clasificadas como `aceptable` por el Grader en la sesión actual.
5. THE Copiloto SHALL NO almacenar PII de los usuarios en ningún componente del sistema, incluyendo logs y analytics.

---

### Requirement 12: Ética, Privacidad y Transparencia

**User Story:** Como usuario, quiero saber que el sistema usa solo información pública y no almacena mis datos personales, para confiar en el Copiloto.

#### Acceptance Criteria

1. THE Copiloto SHALL mostrar un disclaimer visible en la interfaz indicando que el sistema usa exclusivamente fuentes de información pública de la Universidad de Antioquia.
2. THE Copiloto SHALL NO almacenar ni transmitir PII de los usuarios en ningún componente del sistema.
3. THE Ingesta SHALL procesar únicamente PDFs de dominio público descargados de fuentes oficiales de la Universidad de Antioquia.
4. WHEN el Copiloto no tenga certeza sobre una respuesta, THE Answerer SHALL incluir un aviso recomendando al usuario verificar la información con la dependencia oficial correspondiente.
5. THE Copiloto SHALL indicar en cada respuesta el agente o fuente que generó la información (campo `agente_usado` del Estado).

---

### Requirement 13: Configuración y Despliegue Local

**User Story:** Como miembro del equipo de desarrollo, quiero poder ejecutar el sistema en menos de 5 pasos, para demostrar el proyecto durante el hackathon sin complicaciones de configuración.

#### Acceptance Criteria

1. THE Copiloto SHALL incluir un archivo `requirements.txt` con todas las dependencias necesarias con versiones exactas o mínimas especificadas.
2. THE Copiloto SHALL incluir un archivo `.env.example` con todas las variables de entorno requeridas documentadas (incluyendo `ANTHROPIC_API_KEY` y `OPENAI_API_KEY`).
3. THE Copiloto SHALL incluir un `README.md` con instrucciones de instalación y ejecución en máximo 5 pasos.
4. WHEN el usuario ejecuta `run_ingesta.py`, THE Ingesta SHALL indexar todos los PDFs del directorio `data/raw/` sin configuración adicional.
5. WHEN el usuario ejecuta `python interfaz/app.py`, THE Copiloto SHALL iniciar la interfaz Gradio y mostrar la URL de acceso local en la consola.
6. IF la variable `OPENAI_API_KEY` no está configurada, THEN THE Ingesta SHALL usar sentence-transformers como alternativa gratuita para generar embeddings sin interrumpir la ejecución.

---

### Requirement 15: Extracción de Documentos en Tiempo Real (Runtime Extractor)

**User Story:** Como usuario, quiero que el sistema acceda a documentos normativos que no fueron pre-indexados, descargándolos y procesándolos en el momento de mi consulta, para obtener respuestas sobre cualquier resolución o acuerdo de la UdeA sin importar cuándo fue publicado.

#### Acceptance Criteria

1. WHEN el Search_Agent no encuentra información suficiente en el RAG local, THE Runtime_Extractor SHALL consultar `normativa.udea.edu.co/Documentos/Consultar?search=TÉRMINO` con el término reformulado de la consulta del usuario.
2. WHEN el portal normativo retorna resultados, THE Runtime_Extractor SHALL descargar hasta 3 PDFs relevantes directamente en memoria (sin guardarlos en disco) con timeout de 20 segundos por PDF.
3. WHEN un PDF es descargado en memoria, THE Runtime_Extractor SHALL extraer su texto usando PyMuPDF y dividirlo en chunks de máximo 700 caracteres con solapamiento de 120 caracteres.
4. WHEN los chunks son generados, THE Runtime_Extractor SHALL retornarlos con metadatos: {contenido, fuente, url_origen, fecha_publicacion, tipo: "runtime_pdf"}.
5. IF PyMuPDF no está disponible, THEN THE Runtime_Extractor SHALL usar pypdf como fallback para la extracción de texto.
6. IF el portal normativo no está accesible o el PDF no es legible, THEN THE Runtime_Extractor SHALL retornar lista vacía sin interrumpir el flujo del grafo.
7. THE Runtime_Extractor SHALL completar el pipeline completo (búsqueda + descarga + extracción) en menos de 35 segundos totales.

---

### Requirement 16: Monitoreo y Actualización Automática de Documentos (DocWatcher)

**User Story:** Como administrador del sistema, quiero que los documentos indexados se actualicen automáticamente cuando cambie su contenido, para que el sistema siempre tenga información vigente sin intervención manual.

#### Acceptance Criteria

1. WHEN un documento es registrado en el DocWatcher, THE DocWatcher SHALL calcular y almacenar el hash SHA-256 del contenido del PDF junto con el timestamp de registro.
2. WHEN el scheduler del DocWatcher ejecuta un ciclo, THE DocWatcher SHALL verificar cada documento registrado descargando su contenido y comparando el hash actual con el almacenado.
3. IF el hash de un documento cambió, THEN THE DocWatcher SHALL re-descargar el PDF, eliminar los chunks viejos de ChromaDB y re-indexar los nuevos chunks del documento actualizado.
4. THE DocWatcher SHALL verificar documentos normativos cada 6 horas y datos del SIA cada 1 hora.
5. WHEN el DocWatcher detecta un cambio en un documento, THE DocWatcher SHALL registrar el evento con timestamp en el log del sistema y actualizar el campo `ultima_actualizacion` del registro.
6. THE DocWatcher SHALL exponer `forzar_actualizacion(url)` que permite re-indexar un documento manualmente independientemente de si su hash cambió.
7. THE DocWatcher SHALL persistir el estado de todos los documentos monitoreados en `data/doc_watcher_state.json` para sobrevivir reinicios del sistema.
8. THE DocWatcher SHALL correr en un hilo daemon separado sin bloquear el flujo principal del grafo.
9. THE backend SHALL exponer los endpoints `/api/documentos/estado`, `/api/documentos/actualizar` y `/api/documentos/registrar` para gestionar el DocWatcher desde el frontend.

---

### Requirement 17: Consulta de Oferta Académica en Tiempo Real (SIA Scraper)

**User Story:** Como estudiante, quiero saber si hay cupos disponibles en una materia específica y su horario actual, sin tener que ingresar manualmente al SIA, para tomar decisiones de inscripción más rápido.

#### Acceptance Criteria

1. WHEN la consulta del usuario contiene palabras clave relacionadas con oferta académica (cupos, horario, materia, curso, créditos, docente), THE Search_Agent SHALL activar el SIA_Scraper para consultar datos en tiempo real.
2. WHEN el SIA_Scraper es invocado, THE SIA_Scraper SHALL realizar una petición HTTP al portal de oferta académica del SIA con timeout de 15 segundos.
3. WHEN el SIA retorna resultados, THE SIA_Scraper SHALL extraer: código del curso, nombre, créditos, cupos disponibles, horario y docente asignado.
4. THE SIA_Scraper SHALL implementar un caché en memoria con TTL de 1 hora para evitar consultas repetidas al portal del SIA.
5. IF el portal SIA no está accesible, THEN THE SIA_Scraper SHALL retornar datos de ejemplo claramente marcados como ilustrativos sin interrumpir el flujo del grafo.
6. WHEN el Answerer presenta datos del SIA, THE Answerer SHALL incluir el timestamp de la consulta y la etiqueta "(tiempo real)" para distinguir estos datos de los documentos pre-indexados.
7. THE backend SHALL exponer el endpoint `/api/sia/oferta?q=TÉRMINO` para que el frontend pueda consultar el SIA directamente.
8. THE SIA_Scraper SHALL detectar automáticamente si la respuesta del portal es JSON o HTML y usar el parser apropiado para cada caso.

**User Story:** Como miembro del equipo, quiero tener pruebas básicas que validen los componentes críticos, para poder verificar que el sistema funciona correctamente antes de la demo.

#### Acceptance Criteria

1. THE Copiloto SHALL incluir pruebas en `tests/test_rag.py` que validen que el RAG_Agent retorna resultados para las 5 preguntas de prueba definidas en los criterios de éxito del hackathon.
2. THE Copiloto SHALL incluir pruebas en `tests/test_tramites.py` que validen que el Tramite_Agent encuentra el trámite correcto para consultas relacionadas con los 5 trámites definidos en `tramites.json`.
3. THE Copiloto SHALL incluir el archivo `tests/preguntas_prueba.json` con al menos las 5 preguntas de prueba del hackathon y sus respuestas esperadas.
4. WHEN se ejecuta la suite de pruebas, THE sistema SHALL responder correctamente las 5 preguntas de prueba del hackathon: cancelación de materias, trabajo de grado, prueba académica, fecha límite de matrícula y transferencia interna.
5. THE Copiloto SHALL incluir manejo de errores explícito en todos los nodos del Grafo, de forma que un fallo en un nodo no detenga el flujo completo.
