"""
agentes/memoria_agent.py
------------------------
Agente de Memoria Conversacional del Copiloto Administrativo UdeA.

Responsabilidad:
  Mantiene un resumen acumulativo del historial de la conversación entre turnos.
  Permite que el Answerer tenga contexto de preguntas anteriores sin
  pasar el historial completo al LLM en cada turno.

  Patrón: Summarization Memory (estándar en LangGraph con historial largo)

Uso:
    from agentes.memoria_agent import memoria_agent_node
"""

from agentes.estado import EstadoCopiloto
from utils.logger import get_logger

logger = get_logger(__name__)

# Número máximo de intercambios a conservar sin resumir
_MAX_INTERCAMBIOS_DIRECTOS = 3


def memoria_agent_node(estado: EstadoCopiloto) -> dict:
    """
    Nodo de Memoria Conversacional.

    Flujo:
    1. Si hay pocos mensajes (≤ MAX_INTERCAMBIOS_DIRECTOS pares), mantiene
       el resumen previo sin cambios.
    2. Si el historial creció, extrae los intercambios previos y construye
       un resumen textual simple para enriquecer el contexto del Answerer.
    3. El resumen se almacena en `memoria_resumen` del Estado.

    Args:
        estado: Estado actual del grafo.

    Returns:
        dict con `memoria_resumen` actualizado.
    """
    try:
        mensajes = estado.get("mensajes", [])
        resumen_previo = estado.get("memoria_resumen", "")
        turno = estado.get("turno", 1)

        # Solo actualizar si hay suficiente historial
        if turno <= _MAX_INTERCAMBIOS_DIRECTOS:
            return {"memoria_resumen": resumen_previo}

        # Extraer intercambios previos (excluir el mensaje actual)
        intercambios = []
        msgs_previos = mensajes[:-1] if len(mensajes) > 1 else []

        for msg in msgs_previos:
            if hasattr(msg, "type"):
                tipo = msg.type
                contenido = msg.content[:150]  # truncar para el resumen
            elif isinstance(msg, dict):
                tipo = "human" if msg.get("role") == "user" else "ai"
                contenido = msg.get("content", "")[:150]
            else:
                continue

            if tipo == "human":
                intercambios.append(f"Usuario preguntó: {contenido}")
            elif tipo in ("ai", "assistant"):
                intercambios.append(f"Copiloto respondió: {contenido}")

        if not intercambios:
            return {"memoria_resumen": resumen_previo}

        # Construir resumen acumulativo (sin LLM — determinístico y rápido)
        resumen_nuevo = f"[Contexto de la sesión — {turno} turnos]\n"

        # Mantener solo los últimos _MAX_INTERCAMBIOS_DIRECTOS intercambios en detalle
        intercambios_recientes = intercambios[-(2 * _MAX_INTERCAMBIOS_DIRECTOS):]
        resumen_nuevo += "\n".join(intercambios_recientes)

        # Si había resumen previo extenso, agregar solo una línea resumen
        if resumen_previo and len(resumen_previo) > 100:
            resumen_nuevo = f"[Historial resumido: {resumen_previo[:200]}...]\n\n" + resumen_nuevo

        logger.info(
            "Memoria [turno=%d]: resumen actualizado (%d chars)",
            turno, len(resumen_nuevo)
        )

        return {"memoria_resumen": resumen_nuevo}

    except Exception as exc:
        logger.error("Memoria_Agent: error — %s", exc, exc_info=True)
        return {"memoria_resumen": estado.get("memoria_resumen", "")}
