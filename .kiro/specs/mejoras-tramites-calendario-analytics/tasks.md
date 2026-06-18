# Implementation Plan: Mejoras Trámites, Calendario y Analytics

## Overview

Tres mejoras ortogonales sobre el Copiloto Administrativo de la UdeA. Las áreas de
trámites, calendario y analytics son completamente independientes entre sí en sus fases
de implementación, lo que permite máxima paralelización. Solo los tests de integración
y los checkpoints finales imponen dependencia.

Lenguaje de implementación: **Python 3.11** (backend / agentes) + **React/JSX** (frontend).

---

## Tasks

---

### Área 1: Expansión del Catálogo de Trámites

- [x] 1. Expandir `data/tramites/tramites.json` de 5 a 20+ trámites
  - [x] 1.1 Agregar los 15 trámites nuevos al array `tramites` en `data/tramites/tramites.json`
    - Añadir en orden: Liquidación y Pago de Matrícula, Transferencia Interna entre Programas,
      Solicitud de Paz y Salvo Académico, Solicitud de Duplicado de Carné, Homologación de
      Materias, Reserva de Cupo por Período Académico, Solicitud de Reintegro, Inscripción de
      Asignaturas en Período Ordinario, Solicitud de Grado, Solicitud de Doble Titulación,
      Cambio de Jornada o Modalidad, Reconocimiento de Saberes Previos, Solicitud de Permiso
      de Trabajo de Campo / Práctica, Constancia de Matrícula Activa, Solicitud de Préstamo
      en Biblioteca UdeA
    - Respetar el esquema existente: todos los campos obligatorios (`nombre`, `descripcion`,
      `categoria`, `tiempo_estimado`, `costo`, `oficina`, `url_oficial`, `keywords`, `pasos`,
      `documentos_requeridos`, `advertencias`)
    - Usar exclusivamente las categorías válidas: `certificados`, `gestion_academica`, `grado`,
      `bienestar`, `normativa_academica`, `biblioteca`, `financiero`
    - Cada trámite debe tener ≥ 5 keywords únicas en minúsculas; cada paso debe comenzar
      con `"N. "` (e.g. `"1. Ingresar al portal..."`); `url_oficial` debe comenzar con `https://`
    - Los keywords en conjunto deben cubrir: `"matrícula"`, `"certificado"`, `"cancelar"`,
      `"beca"`, `"grado"`, `"transferencia"`, `"homologación"`, `"reintegro"`, `"paz y salvo"`,
      `"carné"`, `"constancia"`, `"biblioteca"`, `"recurso"`, `"inscripción"`, `"reserva"`
    - _Requirements: 1.1, 1.3, 1.5, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 1.2 Escribir prueba de propiedad P1 — Cardinalidad del catálogo
    - **Property 1: Cardinalidad del catálogo de trámites**
    - **Validates: Requirements 1.1**
    - En `tests/test_tramites.py`: cargar `data/tramites/tramites.json` y verificar
      `len(data["tramites"]) >= 20`
    - Etiqueta: `# Feature: mejoras-tramites-calendario-analytics, Property 1`

  - [ ]* 1.3 Escribir prueba de propiedad P3 — Integridad del esquema de cada trámite
    - **Property 3: Integridad del esquema de cada trámite**
    - **Validates: Requirements 1.3, 5.2, 5.3, 5.4, 5.6**
    - En `tests/test_tramites.py`: usar `@given(st.sampled_from(tramites))` con
      `@settings(max_examples=100)` para verificar que cada trámite muestreado cumple
      todas las restricciones de esquema (campos presentes, tipos, longitudes mínimas,
      unicidad de keywords, formato de pasos, prefijo `https://` en url_oficial)
    - Etiqueta: `# Feature: mejoras-tramites-calendario-analytics, Property 3`

  - [ ]* 1.4 Escribir prueba de propiedad P4 — Categorías válidas
    - **Property 4: Categorías válidas en el catálogo**
    - **Validates: Requirements 1.5**
    - En `tests/test_tramites.py`: usar `@given(st.sampled_from(tramites))` para verificar
      que `tramite["categoria"]` ∈ `{certificados, gestion_academica, grado, bienestar,
      normativa_academica, biblioteca, financiero}`
    - Etiqueta: `# Feature: mejoras-tramites-calendario-analytics, Property 4`

  - [ ]* 1.5 Escribir prueba de propiedad P5 — Cobertura de términos requeridos
    - **Property 5: Cobertura de términos requeridos en el catálogo**
    - **Validates: Requirements 5.5**
    - En `tests/test_tramites.py`: cargar el catálogo completo, calcular la unión de todos
      los keywords y verificar que contiene los 15 términos obligatorios
    - Etiqueta: `# Feature: mejoras-tramites-calendario-analytics, Property 5`

  - [ ]* 1.6 Escribir prueba de propiedad P2 — Keyword lookup produce puntuación positiva
    - **Property 2: Keyword lookup produce puntuación positiva**
    - **Validates: Requirements 1.2, 1.6**
    - En `tests/test_tramites.py`: usar
      `@given(st.sampled_from(tramites).flatmap(lambda t: st.tuples(st.just(t), st.sampled_from(t["keywords"]))))`
      para verificar que `_buscar_tramite_relevante(tramites, keyword)` retorna puntuación > 0
    - Etiqueta: `# Feature: mejoras-tramites-calendario-analytics, Property 2`

- [~] 2. Checkpoint — Área de trámites
  - Ejecutar `python -c "import json; d=json.load(open('data/tramites/tramites.json')); print(f'OK: {len(d[\"tramites\"])} trámites')"` y verificar que imprime ≥ 20 trámites
  - Ejecutar `pytest tests/test_tramites.py -v` y asegurar que todos los tests pasan (incluyendo los ya existentes)
  - Preguntar al usuario si tiene dudas antes de continuar

---

### Área 2: Calendario Multi-Semestre

- [x] 3. Refactorizar `backend/main.py` — endpoint `/api/calendario` multi-semestre
  - [x] 3.1 Reemplazar la función `calendario()` actual por la versión multi-semestre
    - Cambiar el return para que retorne `{"semestres": [...]}` en lugar de `{"semestre": ..., "eventos": [...]}`
    - Incluir los cuatro semestres: `2025-1` (estado `historico`), `2025-2` (estado `historico`),
      `2026-1` (estado `activo`), `2026-2` (estado `futuro`)
    - Cada semestre debe tener: `semestre` (str `AAAA-S`), `estado` (`historico`/`activo`/`futuro`),
      `descripcion` (str no vacío), `eventos` (lista)
    - Cada evento debe incluir el campo `tipo_evento` ∈ `{matricula, clases, evaluacion, receso,
      grado, tramite, otro}`; el campo `notas` debe tener ≥ 20 caracteres cuando no está vacío
    - Migrar los 13 eventos de `2026-1` existentes al nuevo formato, añadiendo `tipo_evento` y
      enriqueciendo las notas que están vacías o son muy cortas
    - Añadir eventos representativos para `2025-1`, `2025-2` y `2026-2` (mínimo 5 eventos por
      semestre; las fechas de `2026-2` son provisionales)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ]* 3.2 Escribir prueba de propiedad P6 — Semestres requeridos en la respuesta
    - **Property 6: Semestres requeridos en la respuesta de `/api/calendario`**
    - **Validates: Requirements 2.1**
    - Crear `tests/test_calendario.py`; llamar `calendario()` directamente e importar la función
      desde `backend.main`; verificar que la respuesta contiene `semestres` y que los IDs
      `["2025-1", "2025-2", "2026-1", "2026-2"]` están todos presentes
    - Etiqueta: `# Feature: mejoras-tramites-calendario-analytics, Property 6`

  - [ ]* 3.3 Escribir prueba de propiedad P7 — Esquema válido de cada semestre
    - **Property 7: Esquema válido de cada semestre en la respuesta**
    - **Validates: Requirements 2.2**
    - En `tests/test_calendario.py`: usar `@given(st.sampled_from(calendario()["semestres"]))` con
      `@settings(max_examples=100)` para verificar que cada semestre tiene los campos requeridos
      con los tipos y formatos correctos (`semestre` ∝ `^\d{4}-[12]$`, `estado` ∈ conjunto válido,
      `descripcion` no vacío, `eventos` es lista)
    - Etiqueta: `# Feature: mejoras-tramites-calendario-analytics, Property 7`

  - [ ]* 3.4 Escribir prueba de propiedad P8 — `tipo_evento` pertenece al conjunto válido
    - **Property 8: `tipo_evento` pertenece al conjunto de valores válidos**
    - **Validates: Requirements 2.3**
    - En `tests/test_calendario.py`: aplanar todos los eventos de todos los semestres y usar
      `@given(st.sampled_from(todos_los_eventos))` para verificar `tipo_evento` ∈ conjunto válido
    - Etiqueta: `# Feature: mejoras-tramites-calendario-analytics, Property 8`

  - [ ]* 3.5 Escribir prueba de propiedad P9 — Longitud de notas ≥ 20 caracteres
    - **Property 9: Notas de eventos tienen longitud suficiente**
    - **Validates: Requirements 2.4**
    - En `tests/test_calendario.py`: filtrar eventos donde `notas != ""` y usar
      `@given(st.sampled_from(eventos_con_notas))` para verificar `len(ev["notas"]) >= 20`
    - Etiqueta: `# Feature: mejoras-tramites-calendario-analytics, Property 9`

- [x] 4. Actualizar `frontend/src/components/CalendarioTab.jsx` — selector de semestres
  - [x] 4.1 Adaptar el componente para consumir la nueva estructura `{ semestres: [...] }`
    - Actualizar el state: `const [semestres, setSemestres] = useState([])`  y
      `const [semestreActual, setSemestreActual] = useState(null)`
    - En el efecto de carga, leer `r.data.semestres ?? []` con fallback a `[]` si la API
      retorna la estructura antigua
    - Seleccionar automáticamente el semestre activo al cargar:
      `semestres.find(s => s.estado === 'activo') || semestres[0]`
    - Renderizar botones/tabs horizontales para cada semestre; el semestre `activo` lleva fondo
      `C.petroleo` + texto blanco; los `futuro` muestran el sufijo "(provisional)" en su etiqueta
    - Al cambiar de semestre, actualizar `semestreActual` sin hacer nueva petición (cambio local
      en < 500 ms); si el semestre no tiene eventos, mostrar mensaje "No hay eventos registrados"
    - Cuando `semestreActual.estado === 'futuro'`, mostrar banner:
      "⚠️ Las fechas de este semestre son provisionales y pueden cambiar."
    - _Requirements: 2.5, 2.6, 2.7, 2.8, 2.9_

  - [ ]* 4.2 Escribir prueba de propiedad P10 — Selección automática del semestre activo
    - **Property 10: Selección automática del semestre activo en CalendarioTab**
    - **Validates: Requirements 2.9**
    - Crear `frontend/src/test/CalendarioTab.pbt.test.jsx`; generar 100 listas de semestres con
      posición aleatoria del semestre activo; renderizar `<CalendarioTab>` con mock de axios;
      verificar que el semestre con `estado === 'activo'` queda seleccionado tras el render inicial
    - Usar `fc.array` con `fc.constantFrom(...estados)` para variar la posición del activo
    - Etiqueta: `// Feature: mejoras-tramites-calendario-analytics, Property 10`

  - [ ]* 4.3 Escribir tests unitarios para CalendarioTab
    - En `frontend/src/test/CalendarioTab.test.jsx`:
      - Verificar que el selector de semestres se renderiza cuando llegan 2+ semestres
      - Verificar que el banner "provisional" aparece al seleccionar semestre `futuro`
      - Verificar que el mensaje "No hay eventos" se muestra cuando `eventos` está vacío
    - _Requirements: 2.5, 2.6, 2.8_

- [~] 5. Checkpoint — Área de calendario
  - Ejecutar `pytest tests/test_calendario.py -v` y asegurar que todos los tests pasan
  - Verificar manualmente que el selector de semestres se muestra en el frontend (correr `npm run dev` y revisar la pestaña Calendario)
  - Preguntar al usuario si tiene dudas antes de continuar

---

### Área 3: Fix Analytics + Dashboard

- [x] 6. Agregar funciones a `utils/analytics.py`
  - [x] 6.1 Implementar `actualizar_ultima_calidad(calidad: str) -> None` en `utils/analytics.py`
    - La función debe usar `with _lock:` y verificar `if _registro:` antes de mutar
    - Si el registro está vacío es un no-op (no debe lanzar excepción)
    - Añadir docstring y ejemplo en el estilo existente del módulo
    - _Requirements: 3.2_

  - [x] 6.2 Implementar `obtener_resumen_extendido() -> dict` en `utils/analytics.py`
    - Llamar `obtener_resumen()` para reutilizar la lógica existente (backward compatible)
    - Calcular `por_calidad` (dict `str→int`, suma debe ser igual a `total`)
    - Calcular `tasa_urgentes = round(urgentes/total*100, 1)` cuando `total > 0`, `0.0` si `total == 0`
    - Calcular `agente_mas_usado`: agente con más entradas; en empate, el primero alfabético; `""` si vacío
    - Calcular `intencion_mas_frecuente`: misma lógica sobre `por_intencion`
    - Calcular `consultas_ultimo_minuto`: contar entradas con `(now - datetime.fromisoformat(e["timestamp"])).total_seconds() <= 60`
    - Retornar `{**base, "por_calidad": ..., "tasa_urgentes": ..., ...}`
    - _Requirements: 4.1_

  - [ ]* 6.3 Escribir prueba de propiedad P14 — Schema y cálculos de `obtener_resumen_extendido`
    - **Property 14: `obtener_resumen_extendido()` retorna schema correcto con cálculos válidos**
    - **Validates: Requirements 4.1, 3.3**
    - Crear `tests/test_analytics.py`; usar el generador del diseño:
      `@given(st.lists(st.tuples(intenciones, perfiles, calidades, agentes, st.booleans()), min_size=1, max_size=200))`
      con `@settings(max_examples=100)`; llamar `limpiar_registro()` antes de cada ejemplo;
      poblar el registro y verificar todas las invariantes del schema
    - Etiqueta: `# Feature: mejoras-tramites-calendario-analytics, Property 14`

- [x] 7. Integrar `registrar_consulta` en `agentes/answerer.py`
  - [x] 7.1 Añadir llamada a `registrar_consulta` al final del bloque `try` exitoso en `answerer_node`
    - Agregar `from utils.analytics import registrar_consulta` al nivel de módulo (o dentro de la
      función para evitar importación circular; preferir nivel de módulo)
    - Llamar `registrar_consulta(intencion=estado.get("intencion", "desconocida"), perfil_usuario=...,
      calidad_final="pendiente", agente_usado=agente_usado, es_urgente=...)`
    - Envolver la llamada en su propio `try/except` independiente (log del error + continuar)
      para no interrumpir el retorno de la respuesta al usuario
    - La llamada debe ir **después** de construir `texto_respuesta` y `agente_usado` y **antes** del `return`
    - _Requirements: 3.1_

  - [x] 7.2 Añadir llamada a `registrar_consulta` en el bloque `except` de `answerer_node`
    - En el `except Exception as exc` existente, añadir `registrar_consulta(..., calidad_final="error",
      agente_usado="error", ...)` antes del `return` de fallback
    - Envolver también esta llamada en `try/except` independiente
    - _Requirements: 3.4_

  - [ ]* 7.3 Escribir prueba de propiedad P11 — Answerer registra consulta tras ejecución exitosa
    - **Property 11: Answerer registra consulta en analytics tras cada ejecución exitosa**
    - **Validates: Requirements 3.1**
    - En `tests/test_analytics.py`: mockear el LLM con `unittest.mock.patch`; usar
      `@given(st.builds(estado_valido))` con estados generados aleatoriamente;
      llamar `limpiar_registro()` antes; ejecutar `answerer_node(estado)`; verificar que
      `len(obtener_registro()) == 1` y que la entrada tiene `calidad_final="pendiente"` con los
      campos correctos del estado
    - Etiqueta: `# Feature: mejoras-tramites-calendario-analytics, Property 11`

- [x] 8. Integrar `actualizar_ultima_calidad` en `agentes/grader.py`
  - [x] 8.1 Llamar `actualizar_ultima_calidad(calidad)` al final de `grader_node` antes del `return`
    - Añadir `from utils.analytics import actualizar_ultima_calidad` al nivel de módulo
    - Colocar la llamada dentro del bloque `try`, después de calcular `calidad` y `nuevos_intentos`,
      antes del `return`
    - No es necesario envolver en `try/except` adicional (la función es no-op si el registro está vacío)
    - _Requirements: 3.2_

  - [ ]* 8.2 Escribir prueba de propiedad P12 — Grader actualiza `calidad_final` de la última entrada
    - **Property 12: Grader actualiza `calidad_final` de la última entrada**
    - **Validates: Requirements 3.2**
    - En `tests/test_analytics.py`: pre-poblar el registro con una entrada `calidad_final="pendiente"`;
      usar `@given(st.text(min_size=101))` como `respuesta_candidata` para forzar evaluación no-trivial;
      ejecutar `grader_node(estado)` y verificar que la última entrada del registro tiene
      `calidad_final` ∈ `{"aceptable", "mejorar", "sin_info"}` (≠ `"pendiente"`)
    - Etiqueta: `# Feature: mejoras-tramites-calendario-analytics, Property 12`

- [x] 9. Actualizar `backend/main.py` — endpoint `/api/analytics`
  - [x] 9.1 Reemplazar `obtener_resumen()` por `obtener_resumen_extendido()` en el endpoint `/api/analytics`
    - Cambiar el import dentro del `try`: `from utils.analytics import obtener_resumen_extendido`
    - Actualizar el `except` fallback para incluir todos los campos del schema extendido:
      `{"total": 0, "urgentes": 0, "tasa_aceptable": 0.0, "por_intencion": {}, "por_perfil": {},
      "por_agente": {}, "por_calidad": {}, "tasa_urgentes": 0.0, "agente_mas_usado": "",
      "intencion_mas_frecuente": "", "consultas_ultimo_minuto": 0}`
    - _Requirements: 4.2_

- [x] 10. Actualizar `frontend/src/components/AnalyticsTab.jsx` — dashboard expandido
  - [~] 10.1 Añadir las 4 KPI cards fijas cuando `data.total > 0`
    - Renderizar exactamente 4 tarjetas con `data-testid="kpi-card"` cuando `total > 0`:
      Total consultas (`data.total`), Casos urgentes (`data.urgentes`),
      Calidad aceptable (`${data.tasa_aceptable}%`), Agentes activos (`Object.keys(data.por_agente ?? {}).length`)
    - Usar iconos: `MessageSquare`, `AlertTriangle`, `CheckCircle`, `Bot`
    - _Requirements: 4.3_

  - [~] 10.2 Añadir sección "Distribución de calidad" con barras horizontales
    - Renderizar la sección "Distribución de calidad" cuando `data.por_calidad` tiene al menos una clave
    - Usar el mismo patrón de barras horizontales de progreso ya existente para `por_intencion` y `por_perfil`
    - Usar optional chaining: `data.por_calidad ?? {}`
    - _Requirements: 4.4_

  - [~] 10.3 Añadir indicador de actividad reciente y estado vacío mejorado
    - Cuando `(data.consultas_ultimo_minuto ?? 0) > 0`, mostrar badge verde con el texto
      `"{N} consulta(s) en el último minuto"`
    - Cuando `data.total === 0` (o `data === null`), mostrar el mensaje:
      "Realiza consultas en el chat para ver estadísticas aquí."
    - Usar optional chaining en todos los campos nuevos: `data?.por_calidad ?? {}`,
      `data?.consultas_ultimo_minuto ?? 0`
    - _Requirements: 4.5, 4.6_

  - [ ]* 10.4 Escribir prueba de propiedad P15 — 4 KPI cards cuando `total > 0`
    - **Property 15: AnalyticsTab muestra exactamente 4 KPI cards cuando `total > 0`**
    - **Validates: Requirements 4.3**
    - Crear `frontend/src/test/AnalyticsTab.pbt.test.jsx`; generar objetos `data` con
      `fc.integer({min:1, max:1000})` como `total`; renderizar `<AnalyticsTab>` con mock de axios
      que retorna ese `data`; verificar `screen.getAllByTestId("kpi-card").length === 4`
    - `numRuns: 100`
    - Etiqueta: `// Feature: mejoras-tramites-calendario-analytics, Property 15`

  - [ ]* 10.5 Escribir prueba de propiedad P16 — sección distribución de calidad
    - **Property 16: Sección de distribución de calidad aparece cuando `por_calidad` no está vacío**
    - **Validates: Requirements 4.4**
    - En `frontend/src/test/AnalyticsTab.pbt.test.jsx`: generar `por_calidad` con
      `fc.dictionary(fc.string(), fc.integer({min:1}), {minKeys:1, maxKeys:5})`; renderizar y
      verificar que existe el encabezado "Distribución de calidad" en el DOM
    - `numRuns: 100`
    - Etiqueta: `// Feature: mejoras-tramites-calendario-analytics, Property 16`

  - [ ]* 10.6 Escribir prueba de propiedad P17 — indicador de actividad reciente
    - **Property 17: Indicador de actividad reciente aparece cuando `consultas_ultimo_minuto > 0`**
    - **Validates: Requirements 4.5**
    - En `frontend/src/test/AnalyticsTab.pbt.test.jsx`: usar `fc.integer({min:1, max:100})` como N;
      renderizar con `consultas_ultimo_minuto: N`; verificar que el DOM contiene el texto
      `"${N} consulta(s) en el último minuto"`
    - `numRuns: 100`
    - Etiqueta: `// Feature: mejoras-tramites-calendario-analytics, Property 17`

  - [ ]* 10.7 Escribir tests unitarios para AnalyticsTab
    - En `frontend/src/test/AnalyticsTab.test.jsx`:
      - Verificar estado vacío cuando `total === 0` (mensaje guía al usuario)
      - Verificar que el botón "Actualizar" vuelve a llamar al endpoint (axios llamado 2 veces)
    - _Requirements: 4.6, 4.7_

- [~] 11. Checkpoint final — Área de analytics
  - Ejecutar `pytest tests/test_analytics.py -v` y asegurar que todos los tests pasan
  - Ejecutar `npm run test -- --run` en `frontend/` y verificar tests de AnalyticsTab y CalendarioTab
  - Preguntar al usuario si tiene dudas antes de dar por completado el spec

---

## Notes

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Las tres áreas (1, 3–5) / (6–11) son completamente paralelas en la fase de implementación
- Los checkpoints (2, 5, 11) garantizan validación incremental antes de integrar
- Los tests de propiedad Python usan `hypothesis` con `@settings(max_examples=100)`
- Los tests de propiedad frontend usan `fast-check` con `numRuns: 100`, igual que los tests existentes en `LandingPage.pbt.test.jsx`
- Ninguna tarea modifica la arquitectura del grafo LangGraph ni el flujo de inferencia

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "3.1", "6.1", "6.2"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4", "1.5", "1.6", "3.2", "3.3", "3.4", "3.5", "4.1", "6.3", "7.1", "7.2", "8.1", "9.1"] },
    { "id": 2, "tasks": ["4.2", "4.3", "7.3", "8.2", "10.1", "10.2", "10.3"] },
    { "id": 3, "tasks": ["10.4", "10.5", "10.6", "10.7"] }
  ]
}
```
