"""
agentes/search_agent.py
-----------------------
Nodo Search_Agent del Copiloto Administrativo UdeA.

Realiza búsqueda en el portal normativo de la UdeA cuando el RAG
no tiene suficiente información (score máximo < 0.6).

Estrategia en tres niveles:
  1. Búsqueda HTML clásica en el portal normativo.
  2. Extracción en runtime: descarga PDFs específicos en memoria y los
     procesa en la misma consulta (via runtime_extractor).
  3. Consulta al SIA en tiempo real si la pregunta parece sobre oferta
     académica, cupos o horarios (via sia_scraper).

URL principal:  https://normativa.udea.edu.co/Documentos/Consultar
URL fallback:   https://www.udea.edu.co/wps/portal/udea/web/inicio/institucional/normativa

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

# Palabras clave que indican una consulta sobre oferta académica / SIA
_KEYWORDS_SIA = {
    "cupos", "horario", "materia", "curso", "asignatura", "semestre",
    "oferta", "grupo", "docente", "profesor", "inscripción", "creditos",
    "créditos", "prerrequisito", "código", "cálculo", "física", "química",
    "programación", "algoritmos", "estructuras de datos",
}


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------


def _es_consulta_sia(query: str) -> bool:
    """Detecta si la query probablemente necesita datos del SIA."""
    palabras = set(query.lower().split())
    return bool(palabras & _KEYWORDS_SIA)


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
                "texto": titulo,
            }
        )
    logger.info("Search_Agent: extraídos %d documentos del HTML", len(resultados))
    return resultados


def _buscar_en_portal_html(query: str) -> list[dict]:
    """
    Realiza la petición HTTP al portal normativo (búsqueda HTML clásica).

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

    logger.warning("Search_Agent: ambas URLs fallaron; retornando []")
    return []


# ---------------------------------------------------------------------------
# Nodo del grafo
# ---------------------------------------------------------------------------


def search_agent_node(estado: EstadoCopiloto) -> dict:
    """
    Nodo Search_Agent del grafo LangGraph.

    Estrategia de tres niveles:
      1. Si el RAG ya tiene score suficiente → no busca.
      2. Descarga y procesa PDFs en runtime desde el portal normativo.
      3. Si la consulta parece sobre oferta académica, consulta el SIA en vivo.

    Args:
        estado: Estado actual del grafo.

    Returns:
        Dict con:
            - documentos_web (List[dict]): resultados encontrados.
            - agente_usado (str): 'search_runtime' | 'search_sia' | 'rag_suficiente' | 'search'.
    """
    try:
        # --- 1. ¿El RAG ya tiene información suficiente? ---
        docs_rag: list[dict] = estado.get("documentos_rag", [])
        mejor_score = max(
            (d.get("relevancia", 0) for d in docs_rag), default=0
        )

        if mejor_score >= _SCORE_UMBRAL:
            logger.info(
                "Search_Agent: RAG con score=%.2f >= %.1f — búsqueda omitida",
                mejor_score,
                _SCORE_UMBRAL,
            )
            return {"documentos_web": [], "agente_usado": "rag_suficiente"}

        logger.info(
            "Search_Agent: RAG con score=%.2f < %.1f — iniciando búsqueda multi-nivel",
            mejor_score,
            _SCORE_UMBRAL,
        )

        # --- 2. Construir query ---
        query = estado.get("pregunta_reformulada", "").strip()
        if not query:
            logger.warning("Search_Agent: pregunta_reformulada vacía")
            return {"documentos_web": [], "agente_usado": "search"}

        todos_los_docs: list[dict] = []
        agente_usado = "search"

        # --- 3. Extracción en runtime (descarga PDFs al vuelo) ---
        try:
            from agentes.runtime_extractor import extraer_documentos_runtime
            chunks_runtime = extraer_documentos_runtime(query)
            if chunks_runtime:
                # Convertir chunks al formato esperado por el Answerer
                for chunk in chunks_runtime:
                    todos_los_docs.append({
                        "contenido": chunk.get("contenido", ""),
                        "url": chunk.get("url_origen", ""),
                        "fuente": chunk.get("fuente", ""),
                        "fecha_publicacion": chunk.get("fecha_publicacion", ""),
                        "tipo": "runtime_pdf",
                    })
                agente_usado = "search_runtime"
                logger.info(
                    "Search_Agent: runtime extractor retornó %d chunks",
                    len(chunks_runtime),
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Search_Agent: runtime extractor falló — %s", exc)

        # Fallback HTML si el runtime extractor no trajo nada
        if not todos_los_docs:
            docs_html = _buscar_en_portal_html(query)
            todos_los_docs.extend(docs_html)

        # --- 4. Consulta SIA si la pregunta es sobre oferta académica ---
        if _es_consulta_sia(query):
            try:
                from agentes.sia_scraper import consultar_sia, formatear_respuesta_sia
                cursos_sia = consultar_sia(query)
                if cursos_sia:
                    texto_sia = formatear_respuesta_sia(cursos_sia)
                    todos_los_docs.append({
                        "contenido": texto_sia,
                        "url": "https://sia.udea.edu.co",
                        "fuente": "SIA UdeA (tiempo real)",
                        "tipo": "sia_live",
                    })
                    agente_usado = "search_sia"
                    logger.info(
                        "Search_Agent: SIA retornó %d cursos para '%s'",
                        len(cursos_sia), query[:50],
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Search_Agent: SIA scraper falló — %s", exc)

        return {"documentos_web": todos_los_docs, "agente_usado": agente_usado}

    except Exception as exc:  # noqa: BLE001
        logger.error("Search_Agent: excepción no controlada — %s", exc, exc_info=True)
        return {"documentos_web": [], "agente_usado": "search"}
