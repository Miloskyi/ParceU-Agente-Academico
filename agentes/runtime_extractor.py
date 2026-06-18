"""
agentes/runtime_extractor.py
-----------------------------
Extractor de documentos en tiempo real desde el portal normativo de la UdeA.

En lugar de depender solo de documentos pre-indexados, este módulo:
  1. Consulta normativa.udea.edu.co con el término de búsqueda del usuario.
  2. Descarga el PDF específico directamente en memoria.
  3. Lo procesa (extrae texto y tablas) en la misma consulta.
  4. Retorna chunks listos para ser usados por el Answerer.

El efecto es que el sistema tiene acceso a TODOS los documentos de la UdeA
sin haberlos indexado previamente.

Uso:
    from agentes.runtime_extractor import extraer_documentos_runtime
    docs = extraer_documentos_runtime("cancelación de materias")
"""

from __future__ import annotations

import hashlib
import io
import re
from urllib.parse import urljoin

import httpx

from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_BASE_NORMATIVA = "https://normativa.udea.edu.co"
_URL_BUSQUEDA = f"{_BASE_NORMATIVA}/Documentos/Consultar"
_TIMEOUT_BUSQUEDA = 10   # segundos para búsqueda HTML
_TIMEOUT_PDF = 20        # segundos para descarga de PDF (pueden ser grandes)
_MAX_PDFS_POR_QUERY = 3  # descargar máximo N PDFs por consulta para no bloquear

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CopilotoUdeA/1.0)",
    "Accept": "text/html,application/xhtml+xml",
}

# Patrón para encontrar enlaces de descarga en el HTML del portal
_RE_ENLACE_DOC = re.compile(
    r'href="(/Documentos/Descargar/\d+)"[^>]*>\s*([^<]+?)\s*</a>',
    re.IGNORECASE,
)

# Patrón para encontrar fecha de publicación en el HTML
_RE_FECHA_DOC = re.compile(
    r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})'
)

_CHUNK_SIZE = 700
_CHUNK_OVERLAP = 120


# ---------------------------------------------------------------------------
# Búsqueda de documentos en el portal
# ---------------------------------------------------------------------------


def _buscar_en_portal(query: str) -> list[dict]:
    """
    Consulta el portal normativo y extrae los enlaces a documentos.

    Args:
        query: Término de búsqueda (ej. "cancelación de materias").

    Returns:
        Lista de dicts: {titulo, url_descarga, fecha_publicacion}
    """
    try:
        logger.info("RuntimeExtractor: buscando '%s' en portal normativo", query[:80])
        resp = httpx.get(
            _URL_BUSQUEDA,
            params={"search": query},
            headers=_HEADERS,
            timeout=_TIMEOUT_BUSQUEDA,
            follow_redirects=True,
        )
        if resp.status_code != 200:
            logger.warning(
                "RuntimeExtractor: portal respondió %d para query='%s'",
                resp.status_code, query[:60],
            )
            return []

        html = resp.text
        resultados = []
        for match in _RE_ENLACE_DOC.finditer(html):
            ruta, titulo = match.group(1), match.group(2).strip()
            if not titulo or len(titulo) < 3:
                continue
            url_completa = urljoin(_BASE_NORMATIVA, ruta)

            # Intentar extraer fecha cercana al enlace
            pos = match.start()
            contexto_cercano = html[max(0, pos - 200): pos + 200]
            fechas = _RE_FECHA_DOC.findall(contexto_cercano)
            fecha = fechas[0] if fechas else "No disponible"

            resultados.append({
                "titulo": titulo,
                "url_descarga": url_completa,
                "fecha_publicacion": fecha,
            })

        logger.info(
            "RuntimeExtractor: encontrados %d documentos para '%s'",
            len(resultados), query[:60],
        )
        return resultados[:_MAX_PDFS_POR_QUERY]

    except httpx.TimeoutException:
        logger.warning("RuntimeExtractor: timeout al buscar '%s'", query[:60])
        return []
    except Exception as exc:  # noqa: BLE001
        logger.error("RuntimeExtractor: error en búsqueda — %s", exc)
        return []


# ---------------------------------------------------------------------------
# Descarga y extracción de PDF en memoria
# ---------------------------------------------------------------------------


def _descargar_pdf_en_memoria(url: str) -> bytes | None:
    """
    Descarga un PDF en memoria sin guardarlo en disco.

    Args:
        url: URL de descarga del PDF.

    Returns:
        Bytes del PDF, o None si falló.
    """
    try:
        logger.info("RuntimeExtractor: descargando PDF desde %s", url)
        resp = httpx.get(
            url,
            headers=_HEADERS,
            timeout=_TIMEOUT_PDF,
            follow_redirects=True,
        )
        if resp.status_code != 200:
            logger.warning("RuntimeExtractor: PDF respondió %d — %s", resp.status_code, url)
            return None

        content_type = resp.headers.get("content-type", "")
        if "pdf" not in content_type.lower() and not url.endswith(".pdf"):
            # Puede ser HTML si el portal redirige a página de error
            logger.warning("RuntimeExtractor: contenido no es PDF (%s) — %s", content_type, url)
            return None

        logger.info("RuntimeExtractor: PDF descargado %.1f KB", len(resp.content) / 1024)
        return resp.content

    except httpx.TimeoutException:
        logger.warning("RuntimeExtractor: timeout descargando %s", url)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error("RuntimeExtractor: error descargando PDF — %s", exc)
        return None


def _extraer_texto_pdf(pdf_bytes: bytes) -> str:
    """
    Extrae texto de un PDF en memoria usando PyMuPDF (fitz).

    Args:
        pdf_bytes: Contenido del PDF como bytes.

    Returns:
        Texto extraído del PDF.
    """
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        partes = []
        for num_pag, pagina in enumerate(doc, start=1):
            texto = pagina.get_text("text")
            if texto.strip():
                partes.append(f"[Página {num_pag}]\n{texto}")
        doc.close()
        return "\n\n".join(partes)

    except ImportError:
        logger.warning("RuntimeExtractor: PyMuPDF no disponible, usando fallback pypdf")
        return _extraer_texto_pdf_fallback(pdf_bytes)
    except Exception as exc:  # noqa: BLE001
        logger.error("RuntimeExtractor: error extrayendo texto del PDF — %s", exc)
        return ""


def _extraer_texto_pdf_fallback(pdf_bytes: bytes) -> str:
    """Fallback con pypdf si PyMuPDF no está disponible."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(pdf_bytes))
        partes = []
        for num_pag, pagina in enumerate(reader.pages, start=1):
            texto = pagina.extract_text() or ""
            if texto.strip():
                partes.append(f"[Página {num_pag}]\n{texto}")
        return "\n\n".join(partes)
    except Exception as exc:  # noqa: BLE001
        logger.error("RuntimeExtractor: fallback pypdf también falló — %s", exc)
        return ""


# ---------------------------------------------------------------------------
# Chunking del texto extraído
# ---------------------------------------------------------------------------


def _chunkear_texto(texto: str, fuente: str) -> list[dict]:
    """
    Divide el texto en chunks con solapamiento.

    Args:
        texto:  Texto completo del documento.
        fuente: Título o URL del documento (para metadatos).

    Returns:
        Lista de dicts: {contenido, fuente, tipo}
    """
    if not texto.strip():
        return []

    chunks = []
    inicio = 0
    while inicio < len(texto):
        fin = min(inicio + _CHUNK_SIZE, len(texto))
        fragmento = texto[inicio:fin].strip()
        if fragmento:
            chunks.append({
                "contenido": fragmento,
                "fuente": fuente,
                "tipo": "runtime_pdf",
            })
        if fin >= len(texto):
            break
        inicio = fin - _CHUNK_OVERLAP

    logger.info("RuntimeExtractor: generados %d chunks desde '%s'", len(chunks), fuente[:60])
    return chunks


# ---------------------------------------------------------------------------
# Función principal pública
# ---------------------------------------------------------------------------


def extraer_documentos_runtime(query: str) -> list[dict]:
    """
    Pipeline completo: búsqueda → descarga PDF → extracción → chunks.

    Busca documentos en normativa.udea.edu.co, descarga los PDFs más
    relevantes en memoria, extrae su texto y retorna chunks listos
    para el Answerer.

    Args:
        query: Consulta del usuario (ej. "cancelación de materias").

    Returns:
        Lista de chunks: [{contenido, fuente, tipo, fecha_publicacion}]
        Retorna [] si no se encontró nada o ocurrió un error.
    """
    if not query or not query.strip():
        return []

    # 1. Buscar documentos en el portal
    documentos_encontrados = _buscar_en_portal(query)
    if not documentos_encontrados:
        logger.info("RuntimeExtractor: no se encontraron documentos para '%s'", query[:60])
        return []

    # 2. Descargar y procesar cada PDF
    todos_los_chunks: list[dict] = []
    for doc_meta in documentos_encontrados:
        url = doc_meta["url_descarga"]
        titulo = doc_meta["titulo"]
        fecha = doc_meta["fecha_publicacion"]

        # Descargar PDF en memoria
        pdf_bytes = _descargar_pdf_en_memoria(url)
        if not pdf_bytes:
            continue

        # Extraer texto del PDF
        texto = _extraer_texto_pdf(pdf_bytes)
        if not texto.strip():
            logger.warning("RuntimeExtractor: PDF vacío o no legible — %s", url)
            continue

        # Generar chunks con metadatos enriquecidos
        chunks = _chunkear_texto(texto, fuente=titulo)
        for chunk in chunks:
            chunk["fecha_publicacion"] = fecha
            chunk["url_origen"] = url

        todos_los_chunks.extend(chunks)
        logger.info(
            "RuntimeExtractor: procesado '%s' — %d chunks extraídos en runtime",
            titulo[:60], len(chunks),
        )

    logger.info(
        "RuntimeExtractor: pipeline completo para '%s' — %d chunks totales",
        query[:60], len(todos_los_chunks),
    )
    return todos_los_chunks
