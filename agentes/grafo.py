"""
agentes/grafo.py
----------------
Grafo principal del Copiloto Administrativo UdeA.

Arquitectura multi-agente con 11 nodos:

    supervisor          → analiza complejidad y crea plan de agentes
    memoria_agent       → actualiza el resumen conversacional
    router              → clasifica intención y detecta urgencias
    rag_agent           → busca en ChromaDB
    search_agent        → busca en portal normativo (web)
    tramite_agent       → guía de trámites desde JSON
    urgency_agent       → escala emergencias con contactos
    calendario_agent    → extrae fechas académicas
    answerer            → genera respuesta con Groq + memoria + plan
    verificador         → detecta afirmaciones sin respaldo (anti-alucinación)
    grader              → evalúa calidad y decide si reintentar

Flujo:
    supervisor → memoria_agent → router
    router → (decidir_ruta) → rag_agent | tramite_agent | urgency_agent
    rag_agent → search_agent → calendario_agent → answerer
    tramite_agent → answerer
    urgency_agent → answerer
    answerer → verificador → grader
    grader → (decidir_post_grader) → END | search_agent

Uso:
    from agentes.grafo import app_grafo
    resultado = app_grafo.invoke(estado_inicial())
"""

from langgraph.graph import END, StateGraph

from agentes.answerer import answerer_node
from agentes.calendario_agent import calendario_agent_node
from agentes.estado import EstadoCopiloto
from agentes.grader import decidir_post_grader, grader_node
from agentes.memoria_agent import memoria_agent_node
from agentes.rag_agent import rag_agent_node
from agentes.router import decidir_ruta, router_node
from agentes.search_agent import search_agent_node
from agentes.supervisor import supervisor_node
from agentes.tramite_agent import tramite_agent_node
from agentes.urgency_agent import urgency_agent_node
from agentes.verificador import verificador_node
from utils.logger import get_logger

logger = get_logger(__name__)


def _construir_grafo() -> StateGraph:
    """
    Construye el StateGraph completo con los 11 nodos del sistema multi-agente.
    """
    grafo = StateGraph(EstadoCopiloto)

    # ── Registrar todos los nodos ─────────────────────────────────────────────
    grafo.add_node("supervisor",      supervisor_node)
    grafo.add_node("memoria_agent",   memoria_agent_node)
    grafo.add_node("router",          router_node)
    grafo.add_node("rag_agent",       rag_agent_node)
    grafo.add_node("search_agent",    search_agent_node)
    grafo.add_node("tramite_agent",   tramite_agent_node)
    grafo.add_node("urgency_agent",   urgency_agent_node)
    grafo.add_node("calendario_agent",calendario_agent_node)
    grafo.add_node("answerer",        answerer_node)
    grafo.add_node("verificador",     verificador_node)
    grafo.add_node("grader",          grader_node)

    # ── Punto de entrada: el Supervisor siempre va primero ───────────────────
    grafo.set_entry_point("supervisor")

    # ── Pipeline inicial: Supervisor → Memoria → Router ─────────────────────
    grafo.add_edge("supervisor",    "memoria_agent")
    grafo.add_edge("memoria_agent", "router")

    # ── Router → agente especializado (condicional) ──────────────────────────
    grafo.add_conditional_edges(
        "router",
        decidir_ruta,
        {
            "rag_agent":      "rag_agent",
            "tramite_agent":  "tramite_agent",
            "urgency_agent":  "urgency_agent",
        },
    )

    # ── Flujo RAG: rag → search → calendario → answerer ─────────────────────
    grafo.add_edge("rag_agent",        "search_agent")
    grafo.add_edge("search_agent",     "calendario_agent")
    grafo.add_edge("calendario_agent", "answerer")

    # ── Flujos directos a answerer ───────────────────────────────────────────
    grafo.add_edge("tramite_agent",  "answerer")
    grafo.add_edge("urgency_agent",  "answerer")

    # ── Answerer → Verificador → Grader ─────────────────────────────────────
    grafo.add_edge("answerer",    "verificador")
    grafo.add_edge("verificador", "grader")

    # ── Grader: terminar o reintentar con búsqueda web ───────────────────────
    grafo.add_conditional_edges(
        "grader",
        decidir_post_grader,
        {
            "fin":          END,
            "busqueda_web": "search_agent",
        },
    )

    logger.info("Grafo multi-agente construido con 11 nodos")
    return grafo


# ── Compilar y exponer ────────────────────────────────────────────────────────
_grafo_sin_compilar = _construir_grafo()
app_grafo = _grafo_sin_compilar.compile()

logger.info("app_grafo compilado y listo para usar")
