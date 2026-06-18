"""
agentes/doc_watcher.py
-----------------------
Sistema de monitoreo y actualización automática de documentos normativos.

Cada documento indexado tiene guardado su hash SHA-256. Un job periódico
(APScheduler) verifica si el contenido del documento cambió comparando
el hash actual con el almacenado. Si detecta un cambio:

  1. Descarga el nuevo PDF.
  2. Re-procesa y re-indexa en ChromaDB (borra chunks viejos, inserta nuevos).
  3. Registra el evento de actualización con timestamp.

También expone una función `forzar_actualizacion(url)` para re-indexar
manualmente desde el backend/frontend.

El módulo arranca el scheduler automáticamente al importarse.
Para detenerlo, llamar a `detener_scheduler()`.

Uso:
    from agentes.doc_watcher import iniciar_scheduler, obtener_estado_documentos
    iniciar_scheduler()
    estado = obtener_estado_documentos()
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

import httpx

from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_INTERVALO_NORMATIVA_HORAS = 6   # documentos normativos (cambian poco)
_INTERVALO_SIA_HORAS = 1         # datos SIA (horarios, cupos — cambian diario)
_RUTA_REGISTRO = Path("data/doc_watcher_state.json")
_TIMEOUT_DESCARGA = 20           # segundos

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CopilotoUdeA-Watcher/1.0)",
}


# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------


class RegistroDocumento(TypedDict):
    url: str
    titulo: str
    hash_sha256: str
    ultima_revision: str     # ISO 8601
    ultima_actualizacion: str  # ISO 8601 o "nunca"
    estado: str              # "ok" | "actualizado" | "error" | "pendiente"


# ---------------------------------------------------------------------------
# Almacenamiento en memoria + persistencia JSON liviana
# ---------------------------------------------------------------------------

_lock = threading.Lock()
_registro: dict[str, RegistroDocumento] = {}   # URL → RegistroDocumento
_scheduler_thread: threading.Thread | None = None
_scheduler_activo = False


def _cargar_registro() -> None:
    """Carga el estado persistido desde disco si existe."""
    global _registro
    if _RUTA_REGISTRO.exists():
        try:
            with open(_RUTA_REGISTRO, encoding="utf-8") as f:
                _registro = json.load(f)
            logger.info("DocWatcher: registro cargado — %d documentos monitoreados", len(_registro))
        except Exception as exc:  # noqa: BLE001
            logger.warning("DocWatcher: no se pudo cargar registro — %s", exc)
            _registro = {}


def _guardar_registro() -> None:
    """Persiste el estado actual en disco."""
    try:
        _RUTA_REGISTRO.parent.mkdir(parents=True, exist_ok=True)
        with open(_RUTA_REGISTRO, "w", encoding="utf-8") as f:
            json.dump(_registro, f, ensure_ascii=False, indent=2)
    except Exception as exc:  # noqa: BLE001
        logger.warning("DocWatcher: no se pudo guardar registro — %s", exc)


def _ahora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Cálculo de hash
# ---------------------------------------------------------------------------


def _calcular_hash(contenido: bytes) -> str:
    """Calcula SHA-256 del contenido binario."""
    return hashlib.sha256(contenido).hexdigest()


def _obtener_hash_remoto(url: str) -> tuple[str | None, bytes | None]:
    """
    Descarga el contenido de una URL y calcula su hash.

    Returns:
        Tupla (hash_hex, bytes) o (None, None) si falló.
    """
    try:
        resp = httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT_DESCARGA, follow_redirects=True)
        if resp.status_code != 200:
            logger.warning("DocWatcher: status %d para %s", resp.status_code, url)
            return None, None
        contenido = resp.content
        return _calcular_hash(contenido), contenido
    except httpx.TimeoutException:
        logger.warning("DocWatcher: timeout al descargar %s", url)
        return None, None
    except Exception as exc:  # noqa: BLE001
        logger.error("DocWatcher: error descargando %s — %s", url, exc)
        return None, None


# ---------------------------------------------------------------------------
# Re-indexación en ChromaDB
# ---------------------------------------------------------------------------


def _reindexar_documento(url: str, titulo: str, contenido_bytes: bytes) -> bool:
    """
    Borra los chunks viejos del documento en ChromaDB y los reemplaza
    con los nuevos chunks del PDF actualizado.

    Args:
        url:             URL del documento.
        titulo:          Título del documento.
        contenido_bytes: Bytes del PDF actualizado.

    Returns:
        True si la re-indexación fue exitosa, False si falló.
    """
    try:
        import fitz  # PyMuPDF

        # Extraer texto del nuevo PDF
        doc = fitz.open(stream=contenido_bytes, filetype="pdf")
        texto_completo = ""
        for pagina in doc:
            texto_completo += pagina.get_text("text") + "\n"
        doc.close()

        if not texto_completo.strip():
            logger.warning("DocWatcher: PDF sin texto legible — %s", url)
            return False

        # Conectar a ChromaDB y reemplazar documentos
        import chromadb
        from langchain_community.vectorstores import Chroma

        chroma_path = Path("data/chroma_db")
        client = chromadb.PersistentClient(path=str(chroma_path))
        collection_name = "documentos_udea"

        # Verificar si la colección existe
        try:
            coleccion = client.get_collection(collection_name)
        except Exception:
            logger.info("DocWatcher: colección '%s' no existe aún, omitiendo re-indexación", collection_name)
            return False

        # Borrar chunks que tengan esta URL como fuente
        resultados = coleccion.get(where={"fuente": url})
        ids_a_borrar = resultados.get("ids", [])
        if ids_a_borrar:
            coleccion.delete(ids=ids_a_borrar)
            logger.info("DocWatcher: borrados %d chunks viejos de '%s'", len(ids_a_borrar), titulo[:60])

        # Generar nuevos chunks
        chunk_size = 700
        chunk_overlap = 120
        chunks = []
        inicio = 0
        while inicio < len(texto_completo):
            fin = min(inicio + chunk_size, len(texto_completo))
            fragmento = texto_completo[inicio:fin].strip()
            if fragmento:
                chunks.append(fragmento)
            if fin >= len(texto_completo):
                break
            inicio = fin - chunk_overlap

        # Intentar generar embeddings y re-insertar
        try:
            from langchain_openai import OpenAIEmbeddings
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        except Exception:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        nuevos_ids = []
        nuevos_docs = []
        nuevos_meta = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{_calcular_hash(url.encode()[:8])}_{i}"
            nuevos_ids.append(chunk_id)
            nuevos_docs.append(chunk)
            nuevos_meta.append({
                "fuente": url,
                "titulo": titulo,
                "chunk_idx": i,
                "fecha_actualizacion": _ahora_iso(),
            })

        if nuevos_docs:
            vectores = embeddings.embed_documents(nuevos_docs)
            coleccion.add(
                ids=nuevos_ids,
                documents=nuevos_docs,
                embeddings=vectores,
                metadatas=nuevos_meta,
            )
            logger.info(
                "DocWatcher: re-indexados %d nuevos chunks para '%s'",
                len(nuevos_docs), titulo[:60],
            )

        return True

    except Exception as exc:  # noqa: BLE001
        logger.error("DocWatcher: error re-indexando '%s' — %s", titulo[:60], exc)
        return False


# ---------------------------------------------------------------------------
# Registro y verificación de documentos
# ---------------------------------------------------------------------------


def registrar_documento(url: str, titulo: str) -> None:
    """
    Registra un documento para ser monitoreado.

    Si el documento ya está registrado, no hace nada.
    La primera vez que se registra, se descarga para obtener su hash inicial.

    Args:
        url:    URL de descarga del documento.
        titulo: Nombre descriptivo del documento.
    """
    with _lock:
        if url in _registro:
            return

        logger.info("DocWatcher: registrando nuevo documento '%s'", titulo[:60])
        hash_inicial, _ = _obtener_hash_remoto(url)

        _registro[url] = RegistroDocumento(
            url=url,
            titulo=titulo,
            hash_sha256=hash_inicial or "",
            ultima_revision=_ahora_iso(),
            ultima_actualizacion="nunca" if hash_inicial else "error",
            estado="ok" if hash_inicial else "error",
        )
        _guardar_registro()


def verificar_documento(url: str) -> bool:
    """
    Verifica si un documento cambió y lo re-indexa si es necesario.

    Args:
        url: URL del documento a verificar.

    Returns:
        True si el documento fue actualizado, False si no cambió o hubo error.
    """
    with _lock:
        if url not in _registro:
            logger.warning("DocWatcher: URL no registrada — %s", url)
            return False

        entrada = _registro[url]
        titulo = entrada["titulo"]

    logger.info("DocWatcher: verificando '%s'", titulo[:60])
    nuevo_hash, contenido_bytes = _obtener_hash_remoto(url)

    with _lock:
        _registro[url]["ultima_revision"] = _ahora_iso()

        if nuevo_hash is None:
            _registro[url]["estado"] = "error"
            _guardar_registro()
            return False

        hash_anterior = _registro[url]["hash_sha256"]

        if nuevo_hash == hash_anterior:
            _registro[url]["estado"] = "ok"
            _guardar_registro()
            logger.info("DocWatcher: sin cambios en '%s'", titulo[:60])
            return False

        # ¡Cambio detectado!
        logger.info("DocWatcher: 🔄 CAMBIO detectado en '%s'", titulo[:60])
        _registro[url]["hash_sha256"] = nuevo_hash

    # Re-indexar fuera del lock para no bloquear
    exito = _reindexar_documento(url, titulo, contenido_bytes)

    with _lock:
        if exito:
            _registro[url]["ultima_actualizacion"] = _ahora_iso()
            _registro[url]["estado"] = "actualizado"
        else:
            _registro[url]["estado"] = "error"
        _guardar_registro()

    return exito


def forzar_actualizacion(url: str) -> dict:
    """
    Fuerza la re-descarga y re-indexación de un documento,
    independientemente de si su hash cambió.

    Args:
        url: URL del documento a actualizar.

    Returns:
        Dict con {exito: bool, mensaje: str, timestamp: str}
    """
    if url not in _registro:
        return {"exito": False, "mensaje": f"URL no registrada: {url}", "timestamp": _ahora_iso()}

    titulo = _registro[url]["titulo"]
    logger.info("DocWatcher: actualización forzada para '%s'", titulo[:60])

    _, contenido_bytes = _obtener_hash_remoto(url)
    if not contenido_bytes:
        return {"exito": False, "mensaje": "No se pudo descargar el documento", "timestamp": _ahora_iso()}

    nuevo_hash = _calcular_hash(contenido_bytes)
    exito = _reindexar_documento(url, titulo, contenido_bytes)

    with _lock:
        _registro[url]["hash_sha256"] = nuevo_hash
        _registro[url]["ultima_revision"] = _ahora_iso()
        _registro[url]["ultima_actualizacion"] = _ahora_iso() if exito else _registro[url]["ultima_actualizacion"]
        _registro[url]["estado"] = "actualizado" if exito else "error"
        _guardar_registro()

    return {
        "exito": exito,
        "mensaje": f"Documento '{titulo}' actualizado correctamente" if exito else "Error al re-indexar",
        "timestamp": _ahora_iso(),
    }


# ---------------------------------------------------------------------------
# Estado público de documentos
# ---------------------------------------------------------------------------


def obtener_estado_documentos() -> list[dict]:
    """
    Retorna el estado actual de todos los documentos monitoreados.

    Returns:
        Lista de dicts con info de cada documento: titulo, url, estado,
        ultima_revision, ultima_actualizacion.
    """
    with _lock:
        return [
            {
                "titulo": v["titulo"],
                "url": v["url"],
                "estado": v["estado"],
                "ultima_revision": v["ultima_revision"],
                "ultima_actualizacion": v["ultima_actualizacion"],
            }
            for v in _registro.values()
        ]


def obtener_estado_url(url: str) -> dict | None:
    """Retorna el estado de un documento específico por URL."""
    with _lock:
        return _registro.get(url)


# ---------------------------------------------------------------------------
# Scheduler en background
# ---------------------------------------------------------------------------


def _ciclo_polling() -> None:
    """
    Loop del scheduler que verifica documentos periódicamente.
    Corre en un hilo daemon separado.
    """
    global _scheduler_activo
    logger.info("DocWatcher: scheduler iniciado")

    while _scheduler_activo:
        with _lock:
            urls = list(_registro.keys())

        for url in urls:
            if not _scheduler_activo:
                break
            try:
                verificar_documento(url)
            except Exception as exc:  # noqa: BLE001
                logger.error("DocWatcher: error no controlado en ciclo de polling — %s", exc)

        # Dormir en intervalos de 60 segundos para poder detener rápido
        intervalo_segundos = _INTERVALO_NORMATIVA_HORAS * 3600
        dormido = 0
        while _scheduler_activo and dormido < intervalo_segundos:
            time.sleep(60)
            dormido += 60

    logger.info("DocWatcher: scheduler detenido")


def iniciar_scheduler() -> None:
    """
    Inicia el hilo de polling en background.
    Idempotente: si el scheduler ya está corriendo, no hace nada.
    """
    global _scheduler_thread, _scheduler_activo

    if _scheduler_activo and _scheduler_thread and _scheduler_thread.is_alive():
        logger.info("DocWatcher: scheduler ya está corriendo")
        return

    _cargar_registro()
    _scheduler_activo = True
    _scheduler_thread = threading.Thread(
        target=_ciclo_polling,
        daemon=True,
        name="DocWatcher-Scheduler",
    )
    _scheduler_thread.start()
    logger.info("DocWatcher: scheduler arrancado en hilo daemon")


def detener_scheduler() -> None:
    """Detiene el scheduler de polling."""
    global _scheduler_activo
    _scheduler_activo = False
    logger.info("DocWatcher: señal de stop enviada al scheduler")
