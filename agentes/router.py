"""
agentes/router.py
-----------------
Nodo Router del grafo LangGraph para el Copiloto Administrativo UdeA.

Responsabilidades:
  1. Pre-check de palabras clave críticas de urgencia (sin llamada a LLM).
  2. Clasificación de intención en 5 categorías usando Groq (gratuito).
  3. Actualización del Estado con intencion, categoria, es_urgente,
     nivel_urgencia y pregunta_reformulada.
  4. Función de enrutamiento condicional decidir_ruta().

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

        # --- 3. Clasificación con Groq (llama-3.3-70b) ---
        mensajes_llm = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=pregunta if pregunta else "(consulta vacía)"),
        ]

        respuesta_llm = _get_llm().invoke(mensajes_llm)
        texto_respuesta = respuesta_llm.content

        logger.debug("Router: respuesta del LLM: %s", texto_respuesta[:300])

        # --- 4. Parsear y validar la clasificación ---
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
      - En cualquier otro caso → "rag_agent"

    Args:
        estado: Estado actual del grafo (ya actualizado por router_node).

    Returns:
        Nombre del siguiente nodo: "urgency_agent", "tramite_agent" o "rag_agent".
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
        case _:
            logger.info("Router: ruta → rag_agent (intencion=%s)", intencion)
            return "rag_agent"
