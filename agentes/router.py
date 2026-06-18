"""
agentes/router.py
-----------------
Nodo Router del grafo LangGraph para el Copiloto Administrativo UdeA.

Responsabilidades:
  1. Pre-check de palabras clave críticas de urgencia (sin llamada a LLM).
  2. Pre-check de dominio UdeA (sin llamada a LLM) — filtra consultas claramente
     fuera del ámbito universitario antes de llamar al clasificador.
  3. Clasificación de intención en 5 categorías usando Groq (gratuito).
  4. Actualización del Estado con intencion, categoria, es_urgente,
     nivel_urgencia y pregunta_reformulada.
  5. Función de enrutamiento condicional decidir_ruta().

Uso:
    from agentes.router import router_node, decidir_ruta
"""

import json
import re

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from agentes.estado import EstadoCopiloto
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Tokens de dominio UdeA — Capa 1 (determinística) del filtro out-of-scope
# ---------------------------------------------------------------------------
# Solo se usa para descartar consultas OBVIAMENTE fuera del ámbito universitario
# (recetas de cocina, deportes, entretenimiento, etc.) sin gastar tokens de LLM.
# Si la pregunta tiene alguna relación posible con la UdeA, se deja pasar al LLM.
# La lista cubre los grandes dominios del copiloto: matrícula, trámites,
# reglamentos, bienestar, admisiones y calendario académico.
TOKENS_DOMINIO_UDEA: list[str] = [
    # ── Institución ────────────────────────────────────────────────────────────
    "udea", "universidad de antioquia", "alma mater", "portaludea",
    "portal universitario", "correo institucional", "carné", "carne estudiantil",

    # ── Matrícula / pagos ─────────────────────────────────────────────────────
    "matrícula", "matricula", "pago", "recibo", "liquidación", "liquidacion",
    "semestre", "período académico", "periodo academico",
    "valor matrícula", "descuento matrícula", "exento de pago",
    "paz y salvo", "deuda", "cobro académico",

    # ── Admisiones / cupos ────────────────────────────────────────────────────
    "admisión", "admision", "inscripción", "inscripcion", "aspirante",
    "nuevo ingreso", "cupo", "prueba de admisión", "prueba de admision",
    "puntaje", "icfes", "saber 11", "resultado admisión",
    "lista de admitidos", "proceso de admisión", "convocatoria admisión",
    "estudiante nuevo",

    # ── Reglamentos / normas ──────────────────────────────────────────────────
    "reglamento", "estatuto", "artículo", "articulo", "norma", "régimen",
    "regimen", "disciplinario", "sanción", "sancion",
    "recurso de reposición", "recurso de reposicion",
    "recurso de apelación", "recurso de apelacion",
    "acuerdo superior", "acuerdo académico", "resolución rectoral",
    "comité de carrera", "consejo de facultad",
    "proceso disciplinario", "falta disciplinaria",

    # ── Trámites académicos ───────────────────────────────────────────────────
    "certificado", "constancia", "cancelación", "cancelacion",
    "retiro", "homologación", "homologacion", "transferencia",
    "trabajo de grado", "grado", "graduación", "graduacion",
    "monitoría", "monitoria", "pasantía", "pasantia",
    "práctica", "practica profesional", "auxiliatura",
    "solicitud", "radicado", "trámite", "tramite",
    "registro y control", "secretaria académica",
    "reintegro", "reserva de cupo", "reserva de matrícula",
    "doble programa", "segunda carrera",

    # ── Calendario ────────────────────────────────────────────────────────────
    "calendario académico", "calendario academico", "fecha", "plazo",
    "período", "periodo", "inicio de clases", "fin de semestre",
    "semana de inducción", "semana de inductión",
    "vacaciones", "receso académico", "habilitación",
    "supletorios", "examen final", "parcial",

    # ── Estructura curricular / plan de estudios ──────────────────────────────
    "programa", "carrera", "facultad", "pregrado", "posgrado", "doctorado",
    "maestría", "maestria", "especialización", "especializacion",
    "asignatura", "materia", "crédito", "credito", "nota", "calificación",
    "calificacion", "prueba académica", "prueba academica",
    "malla curricular", "malla", "pensum", "plan de estudios",
    "electiva", "componente", "ciclo básico", "ciclo profesional",
    "semestre académico", "prerrequisito", "requisito académico",
    "intensidad horaria", "código de materia", "grupo",
    "inscripción de materias", "inscripcion de asignaturas",
    "inscribir materia", "horario", "oferta académica",
    "reprobado", "reprobada", "perdí", "perdi la materia",
    "promedio acumulado", "promedio ponderado", "rendimiento académico",
    "habilitación de materia", "supletorios",

    # ── Bienestar ─────────────────────────────────────────────────────────────
    "bienestar", "beca", "apoyo económico", "apoyo economico", "subsidio",
    "alimentación", "alimentacion", "transporte", "residencia universitaria",
    "salud", "psicología", "psicologia",
    "auxilio", "apoyo financiero", "dificultades económicas",
    "sostenimiento", "fondo de becas", "convocatoria beca",
    "descuento", "exoneración", "exoneracion",
    "deportes", "cultura", "actividad física", "actividad fisica",
    "bienestar estudiantil", "orientación psicológica",

    # ── SIA / sistemas ────────────────────────────────────────────────────────
    "sia", "sistema de información académica", "sistema de informacion academica",
    "portal de servicios", "autoservicio", "plataforma académica",

    # ── Intercambio / movilidad ───────────────────────────────────────────────
    "intercambio", "movilidad", "convenio",
    "movilidad estudiantil", "programa de intercambio",
    "homologar", "reconocimiento de créditos",

    # ── Posgrado / investigación ──────────────────────────────────────────────
    "tesis", "anteproyecto", "director de trabajo",
    "director de tesis", "comité de posgrado",
    "seminario", "línea de investigación", "grupo de investigación",
    "proyecto de investigación",

    # ── Graduación / títulos ──────────────────────────────────────────────────
    "diploma", "acta de grado", "ceremonia de grado",
    "título profesional", "opción de grado", "titulación",
    "egresado", "egresada",

    # ── Docentes / evaluaciones ───────────────────────────────────────────────
    "docente", "profesor", "evaluación", "evaluacion",
    "apelación de nota", "apelacion de nota",
    "impugnar", "inconformidad", "revisión de nota", "revision de nota",

    # ── Términos coloquiales frecuentes de estudiantes UdeA ───────────────────
    "profe", "parcero", "parcerú", "bloque", "sapiens", "ciudadela",
    "volante", "sala de sistemas", "biblioteca udea",
    "sistema de bibliotecas", "bases de datos udea",
    "estudiar", "estudie", "estudias", "estudio",
    "estoy en", "soy estudiante", "soy de", "entré a",
    "me quedé", "me salí", "me retiré", "me echaron",
    "cuántos semestres", "cuánto dura", "cuanto dura",
    "cuándo empieza", "cuando empieza", "cuándo termina",
    "qué necesito", "que necesito", "qué debo", "que debo",
    "puedo", "puede", "cómo hago", "como hago",
    "me ayudas", "ayúdame", "ayudame", "necesito saber",
    "tengo una duda", "quiero saber", "quisiera saber",

    # ── Créditos y carga académica ────────────────────────────────────────────
    "crédito", "credito", "créditos", "creditos",
    "créditos académicos", "creditos academicos",
    "ects", "unidad de crédito", "unidades de crédito",
    "carga académica", "carga academica",
    "intensidad", "horas académicas",

    # ── ULA / Unidad de Labor Académica ───────────────────────────────────────
    "ula", "labor académica", "labor academica",
    "unidad de labor", "horas labor",

    # ── Prácticas (variantes con y sin tilde, singular y plural) ─────────────
    "práctica", "practica", "prácticas", "practicas",
    "práctica profesional", "practica profesional",
    "prácticas profesionales", "practicas profesionales",
    "práctica empresarial", "practica empresarial",
    "práctica formativa", "practica formativa",
    "práctica académica", "practica academica",
    "práctica universitaria", "practica universitaria",
    "visita empresarial", "visita técnica", "visita tecnica",

    # ── Trabajo de grado (variantes) ──────────────────────────────────────────
    "trabajo de grado", "trabajo grado",
    "proyecto de grado", "proyecto grado",
    "opción de grado", "opcion de grado",
    "monografía", "monografia",
    "tesis de grado", "proyecto final",
    "emprendimiento", "spin off",

    # ── Monitorías (variantes) ────────────────────────────────────────────────
    "monitoría", "monitoria", "monitorías", "monitorias",
    "monitor académico", "auxiliar de docencia",
    "auxiliatura académica",

    # ── Pasantías ─────────────────────────────────────────────────────────────
    "pasantía", "pasantia", "pasantías", "pasantias",
    "pasante", "empresa práctica",

    # ── Términos de evaluación y notas ────────────────────────────────────────
    "habilitar", "habilitación", "habilitacion",
    "suplir", "supletorio", "supletorios",
    "nota definitiva", "nota final",
    "porcentaje", "corte", "primer corte", "segundo corte",

    # ── Sedes y lugares UdeA ──────────────────────────────────────────────────
    "ciudad universitaria", "sede medellín", "sede medellin",
    "regionalización", "regionalizacion", "sede regional",
    "caucasia", "turbo", "amalfi", "apartadó", "apartado",
    "carmen de viboral", "andes", "santa fe de antioquia",

    # ── Programas / carreras conocidos ───────────────────────────────────────
    "ingeniería", "ingenieria", "medicina", "derecho", "psicología",
    "psicologia", "enfermería", "enfermeria", "comunicaciones",
    "administración", "administracion", "contaduría", "contaduria",
    "filosofía", "filosofia", "historia", "sociología", "sociologia",
    "economía", "economia", "arquitectura", "odontología", "odontologia",
    "bacteriología", "bacteriologia", "química farmacéutica",
    "química", "quimica", "física", "fisica", "matemáticas", "matematicas",
    "sistemas", "industrial", "civil", "ambiental", "electrónica",
    "electronica", "mecánica", "mecanica", "agropecuaria",

    # ── Términos financieros y de pago ────────────────────────────────────────
    "derechos complementarios", "estampilla",
    "bancolombia", "pse", "pago en línea", "pago en linea",
    "pago virtual", "portal de pagos",
    "descuento por hermanos", "descuento funcionario",
    "exención", "exencion", "exento",
    "acuerdo de pago", "financiación matrícula",

    # ── Documentos y certificados ─────────────────────────────────────────────
    "diploma", "acta", "apostilla", "legalización", "legalizacion",
    "autenticación", "autenticacion", "notariar",
    "título apostillado", "titulo apostillado",
    "constancia de egresado", "certificado de egresado",

    # ── Vida estudiantil ──────────────────────────────────────────────────────
    "comedor universitario", "restaurante universitario",
    "residencias", "alojamiento universitario",
    "transporte universitario", "ruta universitaria",
    "actividad cultural", "evento académico",
    "semillero de investigación", "grupo estudiantil",
    "fondo universitario",
]

# ---------------------------------------------------------------------------
# Tokens de exclusión explícita — consultas OBVIAMENTE fuera del ámbito
# ---------------------------------------------------------------------------
# Solo si la pregunta coincide con varios de estos patrones sin ningún token
# UdeA se descarta directamente. Se deben cubrir temas completamente ajenos
# a la vida universitaria.
TOKENS_EXCLUSION_OBVIA: list[str] = [
    # Recetas / cocina
    "receta", "ingrediente", "cocinar", "hornear", "hervir", "freír",
    # Deportes (sin contexto académico)
    "fútbol", "futbol", "partido de", "marcador", "gol", "liga colombiana",
    "premier league", "champions league", "mundial de fútbol",
    # Entretenimiento
    "netflix", "película", "pelicula", "serie de tv", "videojuego",
    "spotify", "canción", "cancion", "artista musical",
    # Política general (no UdeA)
    "presidente de colombia", "congreso de colombia", "senado",
    "partido político", "partido politico", "elecciones presidenciales",
    # Finanzas personales (no UdeA)
    "precio del dólar", "precio del dolar", "tasa de cambio",
    "criptomoneda", "bitcoin", "acciones de bolsa",
    # Viajes / turismo (sin contexto UdeA)
    "vuelo a", "hotel en", "reservar hotel", "pasaporte",
    "visa turista", "destino turístico",
    # Salud general (no bienestar UdeA)
    "síntoma", "sintoma", "diagnóstico", "diagnostico", "medicamento",
    "farmacia", "vacuna contra",
]

# Lista de palabras / frases clave que indican urgencia crítica.
# El pre-check busca estas cadenas en la pregunta del usuario ANTES de
# invocar a Claude, para minimizar latencia en casos críticos.
PALABRAS_URGENCIA: list[str] = [
    "suicidio",
    "hacerme daño",
    "no quiero vivir",
    "acoso",
    "violencia",
    "prueba académica",
    "pérdida de cupo",
    "cancelar semestre",
    "expulsión",
    "proceso disciplinario",
    "deuda matrícula",
    "perdí todas",
    "recurso de reposición urgente",
    "graduarme urgente",
    "plazo vence hoy",
    "emergencia académica",
    "sanción disciplinaria",
    "riesgo de cupo",
]

# Intenciones válidas que el LLM puede devolver
_INTENCIONES_VALIDAS = frozenset(
    {"normativa", "trámite", "calendario", "urgencia", "otro"}
)

# Categorías válidas que el LLM puede devolver
_CATEGORIAS_VALIDAS = frozenset(
    {
        "reglamento_pregrado",
        "reglamento_posgrado",
        "trabajo_grado",
        "matriculas",
        "becas",
        "bienestar",
        "estatuto",
        "general",
    }
)

# Niveles de urgencia válidos
_NIVELES_URGENCIA = frozenset({"bajo", "medio", "alto", "critico"})

# ---------------------------------------------------------------------------
# Modelo LLM (lazy — se inicializa en la primera llamada)
# ---------------------------------------------------------------------------

_llm = None

def _get_llm():
    """Retorna el cliente Groq, inicializándolo la primera vez que se necesita."""
    global _llm
    if _llm is None:
        _llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    return _llm

# ---------------------------------------------------------------------------
# Prompt de clasificación
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """Eres el módulo de clasificación del Copiloto Administrativo de la Universidad de Antioquia.

Tu tarea es analizar la consulta del usuario y responder ÚNICAMENTE con un objeto JSON válido (sin texto adicional, sin markdown, sin bloques de código) con exactamente estos campos:

{
  "intencion": "<normativa|trámite|calendario|urgencia|otro>",
  "categoria": "<reglamento_pregrado|reglamento_posgrado|trabajo_grado|matriculas|becas|bienestar|estatuto|general>",
  "es_urgente": <true|false>,
  "nivel_urgencia": "<bajo|medio|alto|critico>",
  "pregunta_reformulada": "<versión normalizada, clara y enriquecida de la consulta>"
}

Reglas de clasificación:
- intencion:
  * "normativa"  → pregunta sobre reglamentos, estatutos, artículos, normas o regulaciones universitarias.
  * "trámite"    → solicitud de guía para realizar un proceso administrativo (certificados, cancelaciones, inscripciones, etc.).
  * "calendario" → consulta sobre fechas, plazos, períodos académicos o eventos del calendario.
  * "urgencia"   → situación crítica personal, académica o de seguridad que requiere atención inmediata.
  * "otro"       → cualquier consulta que no encaje en las categorías anteriores.
- categoria: elige la más específica según el contenido; usa "general" si no encaja en ninguna otra.
- es_urgente: true si la situación requiere atención inmediata o implica riesgo para el usuario.
- nivel_urgencia:
  * "bajo"    → consulta informativa estándar.
  * "medio"   → plazo próximo o trámite con consecuencias pero gestionable.
  * "alto"    → problema académico serio (prueba académica, pérdida de cupo, recurso de reposición).
  * "critico" → riesgo para la integridad personal, crisis de salud mental o situación extrema.
- pregunta_reformulada: reescribe la consulta de forma clara, sin ambigüedades y con el contexto universitario implícito.

Responde SOLO con el JSON. Sin explicaciones adicionales."""


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------


def _precheck_dominio(pregunta: str) -> bool:
    """
    Verifica si la pregunta es CLARAMENTE ajena al dominio UdeA.

    Esta es la Capa 1 (determinística) del filtro out-of-scope. El enfoque
    es permisivo: solo retorna False (fuera de dominio) cuando la pregunta
    cumple AMBAS condiciones:
      1. No contiene NINGÚN token de dominio UdeA (TOKENS_DOMINIO_UDEA).
      2. Contiene al menos 2 tokens de exclusión obvia (TOKENS_EXCLUSION_OBVIA),
         lo que indica una temática completamente ajena a la universidad.

    Para cualquier consulta ambigua o que pueda estar relacionada con la UdeA,
    retorna True para que el LLM sea quien decida.

    Args:
        pregunta: Texto de la consulta del usuario.

    Returns:
        True si la pregunta podría estar dentro del dominio UdeA (pasar al LLM);
        False solo si la consulta es claramente ajena a la universidad.
    """
    pregunta_lower = pregunta.lower()

    # Si tiene algún token UdeA, claramente es del dominio
    for token in TOKENS_DOMINIO_UDEA:
        if token in pregunta_lower:
            return True

    # Sin tokens UdeA: contar cuántos tokens de exclusión aparecen
    exclusiones_encontradas = sum(
        1 for token in TOKENS_EXCLUSION_OBVIA if token in pregunta_lower
    )

    # Solo rechazar si hay 2+ señales claras de tema off-topic
    # (evita falsos negativos con preguntas cortas o implícitas)
    if exclusiones_encontradas >= 2:
        return False

    # Duda razonable → dejar al LLM decidir
    return True


def _precheck_urgencia(pregunta: str) -> bool:
    """
    Verifica si la pregunta contiene alguna de las palabras/frases de urgencia
    crítica de PALABRAS_URGENCIA sin invocar al LLM.

    La comparación se hace en minúsculas y permite coincidencias parciales
    dentro de la oración (no requiere palabra completa exacta), lo que asegura
    máxima sensibilidad para casos críticos.

    Args:
        pregunta: Texto de la consulta del usuario.

    Returns:
        True si se detecta al menos una keyword crítica; False en caso contrario.
    """
    pregunta_lower = pregunta.lower()
    for keyword in PALABRAS_URGENCIA:
        if keyword in pregunta_lower:
            return True
    return False


def _extraer_json_respuesta(texto: str) -> dict:
    """
    Extrae y parsea el JSON de la respuesta del LLM.

    Intenta primero parsear el texto completo; si falla, busca un bloque
    JSON con llaves { } en el texto.

    Args:
        texto: Texto de respuesta del modelo.

    Returns:
        Diccionario con los campos clasificados.

    Raises:
        ValueError: Si no se puede extraer un JSON válido.
    """
    texto = texto.strip()

    # Intentar parseo directo
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass

    # Extraer bloque JSON con regex
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No se pudo extraer JSON válido de la respuesta: {texto[:200]}")


def _sanitizar_clasificacion(datos: dict) -> dict:
    """
    Valida y normaliza los campos de la clasificación del LLM.
    Si algún campo tiene un valor inválido, lo reemplaza con un valor seguro.

    Args:
        datos: Diccionario con los campos retornados por el LLM.

    Returns:
        Diccionario con valores validados y normalizados.
    """
    intencion = datos.get("intencion", "otro")
    if intencion not in _INTENCIONES_VALIDAS:
        logger.warning("Intención inválida '%s', usando 'otro'", intencion)
        intencion = "otro"

    categoria = datos.get("categoria", "general")
    if categoria not in _CATEGORIAS_VALIDAS:
        logger.warning("Categoría inválida '%s', usando 'general'", categoria)
        categoria = "general"

    es_urgente = bool(datos.get("es_urgente", False))

    nivel_urgencia = datos.get("nivel_urgencia", "bajo")
    if nivel_urgencia not in _NIVELES_URGENCIA:
        logger.warning("Nivel de urgencia inválido '%s', usando 'bajo'", nivel_urgencia)
        nivel_urgencia = "bajo"

    pregunta_reformulada = str(datos.get("pregunta_reformulada", "")).strip()

    return {
        "intencion": intencion,
        "categoria": categoria,
        "es_urgente": es_urgente,
        "nivel_urgencia": nivel_urgencia,
        "pregunta_reformulada": pregunta_reformulada,
    }


# ---------------------------------------------------------------------------
# Nodo principal del grafo
# ---------------------------------------------------------------------------


def router_node(estado: EstadoCopiloto) -> dict:
    """
    Nodo Router del grafo LangGraph.

    Flujo:
      1. Extrae la última pregunta del usuario desde estado["mensajes"].
      2. Ejecuta pre-check de palabras clave de urgencia (sin LLM).
         Si encuentra keywords críticas → es_urgente=True, nivel_urgencia="critico".
      3. Invoca a Claude con el prompt de clasificación para obtener
         intencion, categoria, nivel_urgencia y pregunta_reformulada.
      4. Si el pre-check ya marcó urgencia crítica, sobreescribe es_urgente
         y nivel_urgencia independientemente de lo que diga el LLM.
      5. Retorna un dict parcial con los campos actualizados del Estado.

    Si ocurre cualquier excepción, retorna un dict con calidad="sin_info"
    y agente_usado="error" para que el flujo pueda continuar de forma segura.

    Args:
        estado: Estado actual del grafo.

    Returns:
        Dict parcial con campos actualizados: intencion, categoria,
        es_urgente, nivel_urgencia, pregunta_reformulada.
        En caso de error: {"calidad": "sin_info", "agente_usado": "error"}.
    """
    try:
        # --- 1. Extraer la pregunta del usuario ---
        mensajes = estado.get("mensajes", [])
        pregunta = ""
        for msg in reversed(mensajes):
            # Soporta tanto objetos LangChain como dicts
            if hasattr(msg, "type"):
                if msg.type == "human":
                    pregunta = msg.content
                    break
            elif isinstance(msg, dict):
                if msg.get("type") == "human" or msg.get("role") == "user":
                    pregunta = msg.get("content", "")
                    break

        if not pregunta:
            logger.warning("Router: no se encontró mensaje humano en el estado.")
            pregunta = ""

        logger.info("Router: procesando consulta (%d caracteres)", len(pregunta))

        # --- 2. Pre-check de palabras clave de urgencia ---
        urgencia_critica = _precheck_urgencia(pregunta)
        if urgencia_critica:
            logger.info(
                "Router: pre-check detectó keywords de urgencia crítica en la consulta."
            )

        # --- 3. Capa 1: Pre-check de dominio UdeA (sin LLM) ---
        # Si la pregunta no contiene ningún token UdeA y tampoco es urgencia,
        # la marcamos como "otro" directamente y evitamos la llamada al LLM.
        en_dominio = _precheck_dominio(pregunta)
        if not en_dominio and not urgencia_critica:
            logger.info(
                "Router: pre-check de dominio → consulta claramente fuera de ámbito UdeA "
                "(múltiples tokens off-topic, ningún token UdeA). Clasificando como 'otro' sin LLM."
            )
            return {
                "intencion": "otro",
                "categoria": "general",
                "es_urgente": False,
                "nivel_urgencia": "bajo",
                "pregunta_reformulada": pregunta,
            }

        # --- 4. Capa 2: Clasificación con Groq (llama-3.3-70b) ---
        mensajes_llm = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=pregunta if pregunta else "(consulta vacía)"),
        ]

        respuesta_llm = _get_llm().invoke(mensajes_llm)
        texto_respuesta = respuesta_llm.content

        logger.debug("Router: respuesta del LLM: %s", texto_respuesta[:300])

        # --- 5. Parsear y validar la clasificación ---
        datos_crudos = _extraer_json_respuesta(texto_respuesta)
        clasificacion = _sanitizar_clasificacion(datos_crudos)

        # --- 5. El pre-check sobreescribe si detectó urgencia crítica ---
        if urgencia_critica:
            clasificacion["es_urgente"] = True
            clasificacion["nivel_urgencia"] = "critico"

        logger.info(
            "Router: clasificación final → intencion=%s, categoria=%s, "
            "es_urgente=%s, nivel_urgencia=%s",
            clasificacion["intencion"],
            clasificacion["categoria"],
            clasificacion["es_urgente"],
            clasificacion["nivel_urgencia"],
        )

        return clasificacion

    except Exception as exc:
        logger.error("Router: error inesperado: %s", exc, exc_info=True)
        return {"calidad": "sin_info", "agente_usado": "error"}


# ---------------------------------------------------------------------------
# Función de enrutamiento condicional
# ---------------------------------------------------------------------------


def decidir_ruta(estado: EstadoCopiloto) -> str:
    """
    Función de enrutamiento condicional del grafo LangGraph.

    Determina el siguiente nodo a ejecutar según el Estado actualizado
    por router_node.

    Lógica de decisión:
      - Si es_urgente=True Y nivel_urgencia="critico" → "urgency_agent"
      - Si intencion="trámite" → "tramite_agent"
      - Si intencion="otro" → "out_of_scope"
      - En cualquier otro caso → "rag_agent"

    Args:
        estado: Estado actual del grafo (ya actualizado por router_node).

    Returns:
        Nombre del siguiente nodo: "urgency_agent", "tramite_agent",
        "out_of_scope" o "rag_agent".
    """
    es_urgente: bool = estado.get("es_urgente", False)
    nivel_urgencia: str = estado.get("nivel_urgencia", "")
    intencion: str = estado.get("intencion", "otro")

    if es_urgente and nivel_urgencia == "critico":
        logger.info("Router: ruta → urgency_agent (urgencia crítica detectada)")
        return "urgency_agent"

    match intencion:
        case "trámite":
            logger.info("Router: ruta → tramite_agent")
            return "tramite_agent"
        case "otro":
            logger.info("Router: ruta → out_of_scope (consulta fuera de ámbito UdeA)")
            return "out_of_scope"
        case _:
            logger.info("Router: ruta → rag_agent (intencion=%s)", intencion)
            return "rag_agent"
