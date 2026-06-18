"""
agentes/out_of_scope.py
-----------------------
Nodo Out-of-Scope del Copiloto Administrativo UdeA.

Responsabilidad:
  Responder de forma amigable a consultas que no pertenecen al dominio de
  la Universidad de Antioquia, sin consultar ChromaDB, llamar a otros
  agentes ni consumir tokens de búsqueda.

  Este nodo es alcanzado cuando decidir_ruta() devuelve "out_of_scope",
  lo que ocurre en dos situaciones:
    1. Pre-check de dominio (Capa 1): la pregunta no contiene ningún token
       relacionado con la UdeA → clasificación determinística sin LLM.
    2. Clasificador LLM (Capa 2): el modelo devuelve intencion="otro"
       después de revisar la consulta.

Uso:
    from agentes.out_of_scope import out_of_scope_node
"""

from langchain_core.messages import AIMessage

from agentes.estado import EstadoCopiloto
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Mensaje de rechazo
# ---------------------------------------------------------------------------

_MENSAJE_RECHAZO = (
    "¡Hola! Soy Parcerú, el copiloto administrativo de la Universidad de Antioquia. 🎓\n\n"
    "Solo puedo ayudarte con temas relacionados con la UdeA, como:\n"
    "• Trámites académicos (certificados, cancelaciones, inscripciones)\n"
    "• Reglamentos y normativas universitarias\n"
    "• Calendario académico y fechas importantes\n"
    "• Bienestar universitario, becas y apoyos\n"
    "• Admisiones y proceso de ingreso\n\n"
    "Tu pregunta parece estar fuera de ese ámbito. "
    "¿Hay algo relacionado con la Universidad de Antioquia en lo que pueda ayudarte?"
)


# ---------------------------------------------------------------------------
# Nodo principal
# ---------------------------------------------------------------------------


def out_of_scope_node(estado: EstadoCopiloto) -> dict:
    """
    Nodo Out-of-Scope del grafo LangGraph.

    Genera directamente la respuesta de rechazo sin invocar ChromaDB,
    el LLM de respuesta ni ningún otro agente especializado.

    Actualiza el Estado con:
      - respuesta_candidata: el mensaje de rechazo listo para mostrar.
      - agente_usado: "out_of_scope"
      - calidad: "aceptable" (no requiere evaluación del Grader)
      - mensajes: el mensaje de IA agregado al historial.

    Args:
        estado: Estado actual del grafo.

    Returns:
        dict parcial con los campos actualizados.
    """
    try:
        pregunta = ""
        for msg in reversed(estado.get("mensajes", [])):
            if hasattr(msg, "type") and msg.type == "human":
                pregunta = msg.content
                break
            elif isinstance(msg, dict) and msg.get("role") == "user":
                pregunta = msg.get("content", "")
                break

        logger.info(
            "OutOfScope: consulta fuera de ámbito detectada. "
            "Pregunta resumida: '%.80s'",
            pregunta,
        )

        return {
            "respuesta_candidata": _MENSAJE_RECHAZO,
            "agente_usado": "out_of_scope",
            "calidad": "aceptable",
            "mensajes": [AIMessage(content=_MENSAJE_RECHAZO)],
        }

    except Exception as exc:
        logger.error("OutOfScope: error inesperado: %s", exc, exc_info=True)
        return {
            "respuesta_candidata": _MENSAJE_RECHAZO,
            "agente_usado": "out_of_scope",
            "calidad": "aceptable",
            "mensajes": [AIMessage(content=_MENSAJE_RECHAZO)],
        }
