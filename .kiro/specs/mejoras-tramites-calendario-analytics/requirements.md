# Requirements Document

## Introduction

Esta feature cubre tres mejoras independientes sobre el **Copiloto Administrativo Agéntico de la Universidad de Antioquia**:

1. **Expansión del catálogo de trámites**: Ampliar `tramites.json` de 5 a al menos 20 trámites, cubriendo los procesos administrativos más frecuentemente consultados por estudiantes de pregrado y posgrado en UdeA.

2. **Enriquecimiento del calendario académico**: Ampliar el endpoint `/api/calendario` para exponer múltiples semestres (históricos y futuros), enriquecer las notas descriptivas de cada evento, y añadir soporte en el frontend para navegar entre semestres.

3. **Corrección y expansión de analytics**: Diagnosticar y corregir por qué la pestaña de analytics no muestra datos, e implementar métricas y visualizaciones adicionales que aporten valor analítico real (distribución temporal, tasa de éxito por agente, preguntas frecuentes estimadas por intención, etc.).

El sistema existente usa Python 3.11+, LangGraph, Groq (llama-3.3-70b-versatile), ChromaDB, FastAPI y un frontend React + Vite.

---

## Glossary

- **Tramite_Agent**: Nodo del grafo LangGraph que busca el trámite más relevante en `tramites.json` por coincidencia de keywords.
- **tramites.json**: Archivo JSON en `data/tramites/tramites.json` que contiene la lista de trámites con esquema definido.
- **Calendario_Agent**: Nodo del grafo que extrae fechas académicas relevantes de documentos RAG y web.
- **Endpoint_Calendario**: Endpoint REST `/api/calendario` en `backend/main.py` que retorna eventos del semestre activo.
- **Analytics_Registry**: Módulo `utils/analytics.py` que registra métricas de sesión en memoria y las expone vía `obtener_resumen()`.
- **Endpoint_Analytics**: Endpoint REST `/api/analytics` en `backend/main.py` que consulta el Analytics_Registry.
- **registrar_consulta**: Función en `utils/analytics.py` que agrega una entrada al registro en memoria; actualmente **no está siendo llamada** desde ningún nodo del grafo.
- **Answerer**: Nodo del grafo que genera la respuesta final y es el punto natural para invocar `registrar_consulta`.
- **Grader**: Nodo del grafo que evalúa la calidad de la respuesta y produce `calidad_final`.
- **CalendarioTab**: Componente React `frontend/src/components/CalendarioTab.jsx` que muestra la tabla de eventos.
- **AnalyticsTab**: Componente React `frontend/src/components/AnalyticsTab.jsx` que muestra KPIs y gráficos de barras horizontales.
- **TramitesTab**: Componente React `frontend/src/components/TramitesTab.jsx` que muestra el grid de trámites con modal.
- **Semestre**: Período académico identificado por el patrón `AAAA-S` (p.ej. `2025-1`, `2026-2`).
- **KPI**: Indicador clave de rendimiento (Key Performance Indicator) mostrado como tarjeta en el dashboard de analytics.

---

## Requirements

---

### Requisito 1: Expansión del Catálogo de Trámites

**User Story:** Como estudiante de la Universidad de Antioquia, quiero encontrar guías paso a paso de al menos 20 trámites administrativos comunes, para no tener que buscar información dispersa cuando necesito hacer un proceso en la universidad.

#### Criterios de Aceptación

1. THE tramites.json SHALL contener al menos 20 trámites administrativos, incluyendo los 5 existentes más los siguientes nuevos: liquidación y pago de matrícula, transferencia interna entre programas, solicitud de paz y salvo académico, solicitud de duplicado de carné, homologación de materias, reserva de cupo por período académico, solicitud de reintegro después de retiro voluntario, inscripción de asignaturas en período ordinario, solicitud de grado, solicitud de doble titulación o programa complementario, cambio de jornada o modalidad, reconocimiento de saberes previos, solicitud de permiso de trabajo de campo o práctica, constancia de matrícula activa, y solicitud de préstamo en Biblioteca Universidad de Antioquia.
2. WHEN el Tramite_Agent procesa una consulta cuyo texto contenga al menos un keyword definido en la lista `keywords` de un nuevo trámite, THE Tramite_Agent SHALL retornar ese trámite con puntuación mayor a 0 basada en coincidencia de keywords.
3. THE tramites.json SHALL mantener el esquema existente para cada trámite nuevo: `nombre` (str), `descripcion` (str), `categoria` (str, valor dentro del conjunto `{certificados, gestion_academica, grado, bienestar, normativa_academica, biblioteca, financiero}`), `tiempo_estimado` (str), `costo` (str), `oficina` (str), `url_oficial` (str), `keywords` (list[str] con al menos 5 entradas no vacías), `pasos` (list[str] con al menos 3 pasos no vacíos), `documentos_requeridos` (list[str] con al menos 1 entrada), y `advertencias` (list[str] con al menos 1 entrada).
4. WHEN el frontend TramitesTab carga los trámites desde `/api/tramites`, THE TramitesTab SHALL renderizar en el grid un número de tarjetas igual al total de trámites retornados por el endpoint.
5. THE tramites.json SHALL organizar los trámites nuevos en categorías coherentes: `certificados`, `gestion_academica`, `grado`, `bienestar`, `normativa_academica`, `biblioteca`, y `financiero`.
6. IF la lista de keywords de un trámite incluye términos sinónimos comunes (p.ej. "paz y salvo" y "paz y salvo académico"), THEN el Tramite_Agent SHALL retornar ese trámite con puntuación mayor a 0 ante cualquiera de esos términos en la consulta del usuario.

---

### Requisito 2: Enriquecimiento del Calendario Académico con Múltiples Semestres

**User Story:** Como estudiante o docente, quiero consultar el calendario académico de diferentes semestres (pasados y futuros) con notas descriptivas completas, para planificar mis actividades académicas con contexto suficiente y sin ambigüedades.

#### Criterios de Aceptación

1. WHEN el frontend CalendarioTab hace GET a `/api/calendario`, THE Endpoint_Calendario SHALL retornar una estructura que incluya al menos los semestres `2025-1`, `2025-2`, `2026-1` y `2026-2` en un campo `semestres` de tipo lista.
2. THE Endpoint_Calendario SHALL incluir para cada semestre: identificador `semestre` (str con formato `AAAA-S` donde AAAA es un año de 4 dígitos y S ∈ {1, 2}), `estado` (`historico`, `activo` o `futuro`), `descripcion` (str con nombre completo del período), y una lista `eventos` (puede ser lista vacía) de objetos `{evento, inicio, fin, notas, tipo_evento}`.
3. THE campo `tipo_evento` de cada evento SHALL ser uno de los siguientes valores: `matricula`, `clases`, `evaluacion`, `receso`, `grado`, `tramite`, u `otro`; para permitir filtrado y codificación visual en el frontend.
4. THE campo `notas` de cada evento SHALL contener una descripción de al menos 20 caracteres explicando el contexto o implicaciones académicas del evento, en lugar de notas vacías o de una sola palabra.
5. IF el endpoint `/api/calendario` retorna múltiples semestres en el campo `semestres`, THEN THE CalendarioTab SHALL mostrar un selector de semestre que permita al usuario navegar entre los semestres disponibles sin recargar la página.
6. WHEN el usuario selecciona un semestre diferente en el CalendarioTab, THE CalendarioTab SHALL actualizar la tabla de eventos en menos de 500ms mostrando únicamente los eventos del semestre seleccionado; si el semestre no tiene eventos, SHALL mostrar un mensaje indicando que no hay eventos registrados.
7. THE CalendarioTab SHALL resaltar visualmente el semestre con `estado` igual a `activo` en el selector usando un estilo diferenciado (fondo, borde o etiqueta de texto) que lo distinga de los demás semestres.
8. IF el endpoint `/api/calendario` retorna un semestre con `estado` igual a `futuro`, THEN THE CalendarioTab SHALL mostrar junto a los eventos de ese semestre una etiqueta o leyenda visible indicando que las fechas son provisionales y pueden cambiar.
9. WHEN el CalendarioTab carga inicialmente, THE CalendarioTab SHALL seleccionar y mostrar automáticamente el semestre con `estado` igual a `activo`; si ningún semestre tiene estado `activo`, SHALL seleccionar el primero de la lista.

---

### Requisito 3: Corrección del Registro de Analytics

**User Story:** Como administrador del sistema, quiero que la pestaña de analytics muestre datos reales de las consultas procesadas, para poder verificar que el sistema está funcionando y entender los patrones de uso.

#### Criterios de Aceptación

1. WHEN el Answerer completa la generación de una respuesta exitosamente, THE Answerer SHALL invocar `registrar_consulta` del Analytics_Registry con los campos: `intencion` (valor del campo `intencion` del Estado), `perfil_usuario` (valor del campo `perfil_usuario` del Estado), `calidad_final` (`"pendiente"` ya que el Grader aún no evaluó), `agente_usado` (valor del campo `agente_usado` del Estado), y `es_urgente` (valor del campo `es_urgente` del Estado).
2. WHEN el Grader completa la evaluación de una respuesta, THE Grader SHALL actualizar la entrada más reciente del Analytics_Registry reemplazando el valor `"pendiente"` de `calidad_final` con el valor real del campo `calidad` del Estado (`aceptable`, `mejorar`, o `sin_info`).
3. WHEN el frontend AnalyticsTab hace GET a `/api/analytics` y hay al menos una consulta registrada, THE Endpoint_Analytics SHALL retornar un objeto JSON con los campos: `total` (int ≥ 1), `urgentes` (int ≥ 0), `tasa_aceptable` (float entre 0.0 y 1.0 con precisión de 2 decimales), `por_intencion` (dict str→int), `por_perfil` (dict str→int), y `por_agente` (dict str→int); cuando `total` sea 0, SHALL retornar todos los campos con valores vacíos o cero.
4. IF el Answerer lanza una excepción durante la generación de respuesta (bloque `except`), THEN THE Answerer SHALL igualmente invocar `registrar_consulta` con `calidad_final="error"` para que el fallo quede reflejado en el analytics.
5. THE Analytics_Registry SHALL ser thread-safe bajo concurrencia de múltiples requests simultáneos, usando el `threading.Lock` ya implementado en `utils/analytics.py`.

---

### Requisito 4: Dashboard de Analytics con Métricas Estadísticas Adicionales

**User Story:** Como administrador, quiero un dashboard de analytics con métricas adicionales que permitan entender mejor los patrones de uso del copiloto, para tomar decisiones sobre qué contenido enriquecer o qué trámites agregar.

#### Criterios de Aceptación

1. THE Analytics_Registry SHALL exponer una función `obtener_resumen_extendido()` que retorne todos los campos de `obtener_resumen()` sin modificar sus nombres ni tipos, más los siguientes campos adicionales: `por_calidad` (dict str→int con conteo por valor de `calidad_final`), `tasa_urgentes` (float calculado como `round(urgentes/total*100, 1)` cuando `total > 0`, o `0.0` cuando `total = 0`), `agente_mas_usado` (str con el nombre del agente con más consultas; en caso de empate, el primero alfabéticamente; `""` si no hay registros), `intencion_mas_frecuente` (str con la intención más consultada; en caso de empate, la primera alfabéticamente; `""` si no hay registros), y `consultas_ultimo_minuto` (int con el conteo de entradas cuyo timestamp sea posterior a `now - 60s`).
2. THE Endpoint_Analytics SHALL usar `obtener_resumen_extendido()` en lugar de `obtener_resumen()` para que el frontend reciba los datos adicionales.
3. WHEN el frontend AnalyticsTab recibe un resumen con `total > 0`, THE AnalyticsTab SHALL mostrar en la fila de KPIs exactamente 4 tarjetas: total de consultas (`total`), casos urgentes (`urgentes`), tasa de calidad aceptable (`tasa_aceptable` formateado como porcentaje), y número de tipos de agentes activos (`len(data.por_agente)`).
4. WHEN el frontend AnalyticsTab recibe datos con `por_calidad` poblado, THE AnalyticsTab SHALL mostrar una sección "Distribución de calidad" con una barra horizontal de progreso por cada valor de `calidad_final`, renderizada de forma idéntica a las secciones `por_intencion` y `por_perfil` ya existentes.
5. WHEN el frontend AnalyticsTab recibe `consultas_ultimo_minuto` mayor que 0, THE AnalyticsTab SHALL mostrar un indicador de actividad reciente con el texto "{N} consulta(s) en el último minuto".
6. THE AnalyticsTab SHALL mostrar un mensaje de estado vacío claro cuando `data.total` sea 0, indicando que se deben realizar consultas en el chat para ver estadísticas.
7. WHEN el usuario hace clic en el botón "Actualizar" del AnalyticsTab, THE AnalyticsTab SHALL volver a llamar al endpoint `/api/analytics` y re-renderizar todas las secciones con los datos más recientes.

---

### Requisito 5: Integridad y Cobertura del Catálogo Expandido de Trámites

**User Story:** Como desarrollador del sistema, quiero garantizar que todos los trámites del catálogo sean consistentes y completos, para que el Tramite_Agent pueda responder con precisión cualquier consulta sobre trámites de UdeA.

#### Criterios de Aceptación

1. THE tramites.json SHALL ser un JSON válido que parsee sin errores con `json.loads()`.
2. THE tramites.json SHALL tener el campo `keywords` en cada trámite con al menos 5 entradas únicas en minúsculas y sin duplicados dentro del mismo trámite.
3. THE tramites.json SHALL tener el campo `pasos` en cada trámite con al menos 3 entradas no vacías, donde cada paso comience con un número seguido de punto y espacio (p.ej. `"1. Ingresar al portal..."`).
4. THE tramites.json SHALL tener el campo `url_oficial` en cada trámite con un valor que comience con `https://`.
5. THE conjunto de keywords de todos los trámites SHALL cubrir al menos los términos: `"matrícula"`, `"certificado"`, `"cancelar"`, `"beca"`, `"grado"`, `"transferencia"`, `"homologación"`, `"reintegro"`, `"paz y salvo"`, `"carné"`, `"constancia"`, `"biblioteca"`, `"recurso"`, `"inscripción"`, y `"reserva"`.
6. THE tramites.json SHALL tener el campo `documentos_requeridos` en cada trámite con al menos 1 entrada no vacía.
7. IF el archivo `data/tramites/tramites.json` no existe o no es parseable, THEN THE Tramite_Agent SHALL registrar el error en los logs y retornar `tramite_guia` vacío sin interrumpir el flujo del grafo.

