"""
agentes/grader.py
-----------------
Nodo Grader del grafo LangGraph para el Copiloto Administrativo UdeA.

Evalúa de forma determinística (sin LLM) la calidad de la respuesta candidata
y decide si el flujo termina o si se reintenta con el Search_Agent.

Clasificación de calidad:
  - sin_info  : La respuesta está vacía o indica explícitamente falta de información.
  - aceptable : Respuesta sustancial con citas o pasos estructurados, o RAG disponible.
  - mejorar   : Respuesta corta o sin citas suficientes; se puede mejorar con búsqueda web.

Uso:
    from agentes.grader import grader_node, decidir_post_grader
"""

from agentes.estado import EstadoCopiloto
from utils.analytics import actualizar_ultima_calidad
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Frases que indican ausencia de información en la respuesta
# ---------------------------------------------------------------------------

_FRASES_SIN_INFO: list[str] = [
    "no encontré",
    "no tengo información",
    "no está disponible",
    "no dispongo",
    "no tengo datos",
    "no se encontró",
    "no se dispone",
    "no hay información",
    "información no disponible",
    "no puedo responder",
    "fuera de mi conocimiento",
    "no encontré esto",
]

# Mínimo de caracteres para que una respuesta sea considerada sustancial
_MIN_CHARS_SUSTANCIAL = 100


# ---------------------------------------------------------------------------
# Lógica de evaluación
# ---------------------------------------------------------------------------


def _evaluar_calidad(estado: EstadoCopiloto) -> str:
    """
    Evalúa la calidad de ``respuesta_candidata`` de forma determinística.

    Lógica (en orden de precedencia):
      1. ``sin_info``  si la respuesta está vacía.
      2. ``sin_info``  si contiene alguna frase de _FRASES_SIN_INFO.
      3. ``aceptable`` si tiene más de _MIN_CHARS_SUSTANCIAL caracteres
                       Y (contiene citas '(Fuente:' OR pasos numerados OR
                       documentos_rag no vacíos en el estado).
      4. ``mejorar``   en cualquier otro caso.

    Args:
        estado: Estado actual del grafo.

    Returns:
        "aceptable" | "mejorar" | "sin_info"
    """
    respuesta = estado.get("respuesta_candidata", "").strip()

    # --- Regla 1: vacía ---
    if not respuesta:
        logger.debug("Grader: respuesta vacía → sin_info")
        return "sin_info"

    respuesta_lower = respuesta.lower()

    # --- Regla 2: frases de no-información ---
    for frase in _FRASES_SIN_INFO:
        if frase in respuesta_lower:
            logger.debug("Grader: frase de no-info detectada ('%s') → sin_info", frase)
            return "sin_info"

    # --- Regla 3: respuesta sustancial ---
    es_larga = len(respuesta) > _MIN_CHARS_SUSTANCIAL
    tiene_cita = "(fuente:" in respuesta_lower
    tiene_pasos = any(
        f"{i}." in respuesta for i in range(1, 10)
    )
    tiene_rag = bool(estado.get("documentos_rag"))

    if es_larga and (tiene_cita or tiene_pasos or tiene_rag):
        logger.debug(
            "Grader: respuesta sustancial "
            "(largo=%d, cita=%s, pasos=%s, rag=%s) → aceptable",
            len(respuesta),
            tiene_cita,
            tiene_pasos,
            tiene_rag,
        )
        return "aceptable"

    # --- Regla 4: mejorar ---
    logger.debug(
        "Grader: respuesta insuficiente (largo=%d, cita=%s, pasos=%s, rag=%s) → mejorar",
        len(respuesta),
        tiene_cita,
        tiene_pasos,
        tiene_rag,
    )
    return "mejorar"


# ---------------------------------------------------------------------------
# Nodo del grafo
# ---------------------------------------------------------------------------


def grader_node(estado: EstadoCopiloto) -> dict:
    """
    Nodo Grader del grafo LangGraph.

    Evalúa la calidad de ``respuesta_candidata``, incrementa ``intentos``
    y retorna los campos actualizados del Estado.

    Args:
        estado: Estado actual del grafo.

    Returns:
        dict con ``calidad`` (str) e ``intentos`` (int incrementado en 1).
        En caso de excepción retorna calidad='sin_info' para no bloquear el flujo.
    """
    try:
        intentos_previos = estado.get("intentos", 0)
        calidad = _evaluar_calidad(estado)
        nuevos_intentos = intentos_previos + 1

        logger.info(
            "Grader: calidad='%s', intentos=%d → %d",
            calidad,
            intentos_previos,
            nuevos_intentos,
        )

        # Actualizar calidad en analytics
        actualizar_ultima_calidad(calidad)

        return {
            "calidad": calidad,
            "intentos": nuevos_intentos,
        }

    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Grader: error inesperado: %s", exc, exc_info=True)
        return {
            "calidad": "sin_info",
            "intentos": estado.get("intentos", 0) + 1,
        }


# ---------------------------------------------------------------------------
# Función de enrutamiento condicional post-Grader
# ---------------------------------------------------------------------------


def decidir_post_grader(estado: EstadoCopiloto) -> str:
    """
    Función de enrutamiento condicional del grafo después del Grader.

    Decide si el flujo termina (``"fin"``) o si se reintenta con el
    Search_Agent (``"busqueda_web"``).

    Lógica:
      - calidad == 'aceptable'  → "fin"  (respuesta lista para el usuario)
      - calidad == 'sin_info'   → "fin"  (informar que no hay información)
      - calidad == 'mejorar' y intentos < 2  → "busqueda_web"  (reintentar)
      - calidad == 'mejorar' y intentos >= 2 → "fin"  (evitar ciclo infinito)

    Args:
        estado: Estado actual del grafo (ya actualizado por grader_node).

    Returns:
        "fin" para terminar el flujo, "busqueda_web" para reintentar.
    """
    calidad: str = estado.get("calidad", "sin_info")
    intentos: int = estado.get("intentos", 0)

    if calidad == "aceptable":
        logger.info("Grader routing → fin (calidad=aceptable)")
        return "fin"

    if calidad == "sin_info":
        logger.info("Grader routing → fin (calidad=sin_info)")
        return "fin"

    # calidad == "mejorar"
    if intentos >= 2:
        logger.info(
            "Grader routing → fin (calidad=mejorar, intentos=%d >= 2)", intentos
        )
        return "fin"

    logger.info(
        "Grader routing → busqueda_web (calidad=mejorar, intentos=%d < 2)", intentos
    )
    return "busqueda_web"
