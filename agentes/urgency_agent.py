"""
agentes/urgency_agent.py
------------------------
Nodo Urgency_Agent del grafo LangGraph.

Detecta el tipo de urgencia a partir de las palabras clave en la pregunta
del usuario y construye una lista de contactos institucionales de la UdeA
apropiados para la situación, retornándolos como documentos_web para que
el Answerer los incluya en su respuesta.

Uso:
    from agentes.urgency_agent import urgency_agent_node
"""

import re

from agentes.estado import EstadoCopiloto
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Mapa de contactos institucionales por tipo de urgencia
# ---------------------------------------------------------------------------

CONTACTOS_URGENCIA: dict[str, list[str]] = {
    "salud_mental": [
        "Línea de crisis: 106 (nacional)",
        "Bienestar Universitario: bienestar@udea.edu.co",
        "Línea UdeA: (604) 219 5555",
    ],
    "violencia_acoso": [
        "Defensoría del Estudiantado UdeA",
        "Bienestar Universitario: bienestar@udea.edu.co",
        "Línea UdeA: (604) 219 5555",
    ],
    "academica": [
        "Secretaría Académica Ingeniería: secretaria.ingenieria@udea.edu.co",
        "División de Registro: registro@udea.edu.co",
        "Línea UdeA: (604) 219 5555",
    ],
    "economica": [
        "Bienestar Universitario — Apoyo Socioeconómico: bienestar@udea.edu.co",
        "Línea UdeA: (604) 219 5555",
    ],
    "general": [
        "Línea UdeA: (604) 219 5555",
        "Bienestar Universitario: bienestar@udea.edu.co",
    ],
}

# Palabras clave para detectar el tipo de urgencia (minúsculas)
_PALABRAS_SALUD_MENTAL = ["suicidio", "hacerme daño", "no quiero vivir"]
_PALABRAS_VIOLENCIA = ["acoso", "violencia", "amenaza"]
_PALABRAS_ACADEMICA = ["prueba académica", "pérdida de cupo", "expulsión"]
_PALABRAS_ECONOMICA = ["deuda", "matrícula", "beca"]


def _detectar_tipo_urgencia(estado: EstadoCopiloto) -> str:
    """
    Determina el tipo de urgencia combinando el nivel registrado en el estado
    y las palabras clave presentes en la pregunta del usuario.

    Args:
        estado: Estado actual del grafo.

    Returns:
        Tipo de urgencia: "salud_mental" | "violencia_acoso" | "academica" |
        "economica" | "general".
    """
    # Obtener el texto de la última pregunta en minúsculas
    pregunta = ""
    mensajes = estado.get("mensajes", [])
    if mensajes:
        ultimo_mensaje = mensajes[-1]
        # El mensaje puede ser un objeto con .content o un dict
        if hasattr(ultimo_mensaje, "content"):
            pregunta = ultimo_mensaje.content.lower()
        elif isinstance(ultimo_mensaje, dict):
            pregunta = ultimo_mensaje.get("content", "").lower()

    # Prioridad: salud mental (más crítico primero)
    if any(kw in pregunta for kw in _PALABRAS_SALUD_MENTAL):
        return "salud_mental"

    if any(kw in pregunta for kw in _PALABRAS_VIOLENCIA):
        return "violencia_acoso"

    if any(kw in pregunta for kw in _PALABRAS_ACADEMICA):
        return "academica"

    if any(kw in pregunta for kw in _PALABRAS_ECONOMICA):
        return "economica"

    return "general"


def urgency_agent_node(estado: EstadoCopiloto) -> dict:
    """
    Nodo del grafo que maneja situaciones de urgencia.

    Detecta el tipo de urgencia a partir del estado y las palabras clave
    en la pregunta, luego construye una lista de contactos institucionales
    de la UdeA como documentos_web para que el Answerer los integre
    en su respuesta.

    Args:
        estado: Estado actual del grafo con al menos:
            - mensajes: historial de conversación
            - nivel_urgencia: severidad detectada por el Router

    Returns:
        dict con:
            - documentos_web: lista de dicts {titulo, url, texto} con contactos
            - agente_usado: "urgency"

    Example:
        >>> estado = {"mensajes": [HumanMessage("tengo deuda de matrícula")],
        ...           "nivel_urgencia": "alto", ...}
        >>> resultado = urgency_agent_node(estado)
        >>> resultado["agente_usado"]
        'urgency'
    """
    try:
        nivel = estado.get("nivel_urgencia", "desconocido")
        tipo = _detectar_tipo_urgencia(estado)

        logger.info(
            "Urgency_Agent: nivel=%s, tipo=%s — construyendo contactos",
            nivel,
            tipo,
        )

        contactos = CONTACTOS_URGENCIA.get(tipo, CONTACTOS_URGENCIA["general"])

        # Convertir cada contacto a un dict compatible con documentos_web
        documentos_contacto = [
            {
                "titulo": "Contacto de emergencia",
                "url": "",
                "texto": contacto_str,
            }
            for contacto_str in contactos
        ]

        logger.info(
            "Urgency_Agent: %d contactos preparados para tipo '%s'",
            len(documentos_contacto),
            tipo,
        )

        return {
            "documentos_web": documentos_contacto,
            "agente_usado": "urgency",
        }

    except Exception as exc:
        logger.error("Urgency_Agent: error inesperado — %s", exc, exc_info=True)
        # Retornar contactos generales como fallback seguro
        return {
            "documentos_web": [
                {
                    "titulo": "Contacto de emergencia",
                    "url": "",
                    "texto": contacto,
                }
                for contacto in CONTACTOS_URGENCIA["general"]
            ],
            "agente_usado": "urgency",
        }
