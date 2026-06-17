"""
agentes/search_agent.py
-----------------------
Nodo Search_Agent del Copiloto Administrativo UdeA.

Realiza búsqueda web en el portal normativo de la UdeA cuando el RAG
no tiene suficiente información (score máximo < 0.6).

URL principal:  https://normativa.udea.edu.co/Documentos/Consultar
URL fallback:   https://www.udea.edu.co/wps/portal/udea/web/inicio/institucional/normativa

Flujo:
    1. Verifica si documentos_rag tienen score suficiente (>= 0.6).
       Si sí → retorna documentos_web=[] con agente_usado='rag_suficiente'.
    2. Construye la query desde pregunta_reformulada.
    3. Hace GET al portal normativo con timeout=10 s.
    4. Si responde 200 → extrae documentos con regex del HTML.
    5. Si falla (timeout, error HTTP, status != 200) → loguea y retorna [].

Uso:
    from agentes.search_agent import search_agent_node
"""

import re

import httpx

from agentes.estado import EstadoCopiloto
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_URL_PRINCIPAL = "https://normativa.udea.edu.co/Documentos/Consultar"
_URL_FALLBACK = (
    "https://www.udea.edu.co/wps/portal/udea/web/inicio/institucional/normativa"
)
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CopilotoUdeA/1.0)",
    "Accept": "text/html",
}
_TIMEOUT = 10  # segundos
_SCORE_UMBRAL = 0.6

# Extrae: href="/Documentos/Descargar/123">Título del documento</a>
_REGEX_DOCS = re.compile(
    r'href="(/Documentos/Descargar/\d+)"[^>]*>([^<]+)</a>'
)
_BASE_NORMATIVA = "https://normativa.udea.edu.co"


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------


def _extraer_documentos(html: str) -> list[dict]:
    """
    Extrae lista de documentos desde el HTML del portal normativo.

    Args:
        html: Contenido HTML de la respuesta.

    Returns:
        Lista de dicts con {titulo, url, texto}.
    """
    resultados = []
    for match in _REGEX_DOCS.finditer(html):
        ruta, titulo = match.group(1), match.group(2).strip()
        resultados.append(
            {
                "titulo": titulo,
                "url": f"{_BASE_NORMATIVA}{ruta}",
                "texto": titulo,  # el texto disponible en el HTML es el propio título
            }
        )
    logger.info("Search_Agent: extraídos %d documentos del HTML", len(resultados))
    return resultados


def _buscar_en_portal(query: str) -> list[dict]:
    """
    Realiza la petición HTTP al portal normativo.

    Primero intenta la URL principal; si falla, intenta el fallback.

    Args:
        query: Texto de búsqueda.

    Returns:
        Lista de documentos encontrados o [] si ambas URLs fallan.
    """
    params = {"q": query}

    for url in (_URL_PRINCIPAL, _URL_FALLBACK):
        try:
            logger.info("Search_Agent: consultando %s con query='%s'", url, query[:80])
            response = httpx.get(
                url,
                params=params,
                headers=_HEADERS,
                timeout=_TIMEOUT,
                follow_redirects=True,
            )
            if response.status_code == 200:
                documentos = _extraer_documentos(response.text)
                logger.info(
                    "Search_Agent: respuesta 200 desde %s — %d documentos",
                    url,
                    len(documentos),
                )
                return documentos
            else:
                logger.warning(
                    "Search_Agent: status %d desde %s — intentando siguiente URL",
                    response.status_code,
                    url,
                )
        except httpx.TimeoutException:
            logger.warning("Search_Agent: timeout al consultar %s", url)
        except httpx.RequestError as exc:
            logger.warning("Search_Agent: error de red en %s — %s", url, exc)
        except Exception as exc:  # noqa: BLE001
            logger.error("Search_Agent: error inesperado en %s — %s", url, exc)

    logger.warning("Search_Agent: ambas URLs fallaron; retornando documentos_web=[]")
    return []


# ---------------------------------------------------------------------------
# Nodo del grafo
# ---------------------------------------------------------------------------


def search_agent_node(estado: EstadoCopiloto) -> dict:
    """
    Nodo Search_Agent del grafo LangGraph.

    Busca documentos en el portal normativo de la UdeA solo si el RAG
    no encontró información suficiente (score máximo < 0.6).

    Args:
        estado: Estado actual del grafo.

    Returns:
        Dict con:
            - documentos_web (List[dict]): resultados encontrados, o [] si RAG
              ya tenía buena info o si la búsqueda falló.
            - agente_usado (str): 'search' | 'rag_suficiente'.
    """
    try:
        # --- 1. ¿El RAG ya tiene información suficiente? ---
        docs_rag: list[dict] = estado.get("documentos_rag", [])
        mejor_score = max(
            (d.get("relevancia", 0) for d in docs_rag), default=0
        )

        if mejor_score >= _SCORE_UMBRAL:
            logger.info(
                "Search_Agent: RAG con score=%.2f >= %.1f — búsqueda web omitida",
                mejor_score,
                _SCORE_UMBRAL,
            )
            return {"documentos_web": [], "agente_usado": "rag_suficiente"}

        logger.info(
            "Search_Agent: RAG con score=%.2f < %.1f — iniciando búsqueda web",
            mejor_score,
            _SCORE_UMBRAL,
        )

        # --- 2. Construir query ---
        query = estado.get("pregunta_reformulada", "").strip()
        if not query:
            logger.warning(
                "Search_Agent: pregunta_reformulada vacía — retornando documentos_web=[]"
            )
            return {"documentos_web": [], "agente_usado": "search"}

        # --- 3. Buscar en el portal ---
        resultados = _buscar_en_portal(query)

        return {"documentos_web": resultados, "agente_usado": "search"}

    except Exception as exc:  # noqa: BLE001
        logger.error("Search_Agent: excepción no controlada — %s", exc, exc_info=True)
        return {"documentos_web": [], "agente_usado": "search"}
