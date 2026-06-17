"""
agentes/supervisor.py
---------------------
Agente Supervisor del Copiloto Administrativo UdeA.

Responsabilidad:
  Analiza la consulta ANTES del router y decide:
  1. La complejidad de la consulta (simple | media | compleja).
  2. El plan de agentes a activar (qué nodos del grafo serán necesarios).

  Para consultas simples: solo router → tramite/rag → answerer
  Para consultas medias: incluye búsqueda web y calendario
  Para consultas complejas: activa todos los agentes + verificador

Patrón: Supervisor → Workers (estándar en LangGraph multi-agente)

Uso:
    from agentes.supervisor import supervisor_node
"""

import re
from agentes.estado import EstadoCopiloto
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Heurísticas de complejidad (sin LLM — rápido y determinístico)
# ---------------------------------------------------------------------------

# Indicadores de consulta compleja (cruza múltiples dominios)
_PATRONES_COMPLEJA = [
    r"(beca|apoyo).*(prueba académica|pérdida de cupo)",
    r"(trabajo de grado).*(matrícula|beca|fecha)",
    r"(posgrado).*(reglamento|materia|cancelar)",
    r"(si.*pierdo|si.*repruebo).*(qué pasa|consecuencia)",
    r"(transferencia).*(créditos|homologación|reglamento)",
    r"y además|también|al mismo tiempo|combinado",
    r"(recurso).*(disciplinario|beca|matrícula)",
]

# Indicadores de consulta media (requiere búsqueda web o múltiples docs)
_PATRONES_MEDIA = [
    r"cuándo|fecha|plazo|límite|período|calendario",
    r"requisito|documento.*necesito|qué.*necesito",
    r"proceso|pasos|cómo.*solicitar|cómo.*hacer",
    r"vigente|actual|este semestre|2026",
]

# ---------------------------------------------------------------------------
# Nodo principal
# ---------------------------------------------------------------------------

def supervisor_node(estado: EstadoCopiloto) -> dict:
    """
    Nodo Supervisor del grafo LangGraph.

    Analiza la consulta y establece el plan de agentes antes de que
    el Router clasifique la intención. Actualiza:
      - complejidad: "simple" | "media" | "compleja"
      - plan_agentes: lista de nodos que se activarán
      - turno: incrementado en 1

    Args:
        estado: Estado actual del grafo.

    Returns:
        dict con complejidad, plan_agentes y turno actualizados.
    """
    try:
        mensajes = estado.get("mensajes", [])
        pregunta = ""
        for msg in reversed(mensajes):
            if hasattr(msg, "type") and msg.type == "human":
                pregunta = msg.content
                break
            elif isinstance(msg, dict) and msg.get("role") == "user":
                pregunta = msg.get("content", "")
                break

        pregunta_lower = pregunta.lower()
        turno_actual = estado.get("turno", 0) + 1

        # Determinar complejidad
        es_compleja = any(re.search(p, pregunta_lower) for p in _PATRONES_COMPLEJA)
        es_media = any(re.search(p, pregunta_lower) for p in _PATRONES_MEDIA)

        if es_compleja:
            complejidad = "compleja"
            plan = ["router", "rag_agent", "search_agent", "calendario_agent",
                    "answerer", "verificador", "grader"]
        elif es_media:
            complejidad = "media"
            plan = ["router", "rag_agent", "search_agent", "answerer", "verificador", "grader"]
        else:
            complejidad = "simple"
            plan = ["router", "rag_agent", "answerer", "grader"]

        logger.info(
            "Supervisor [turno=%d]: complejidad='%s' | plan=%s",
            turno_actual, complejidad, plan
        )

        return {
            "complejidad": complejidad,
            "plan_agentes": plan,
            "turno": turno_actual,
        }

    except Exception as exc:
        logger.error("Supervisor: error — %s", exc, exc_info=True)
        return {"complejidad": "simple", "plan_agentes": [], "turno": estado.get("turno", 0) + 1}
