"""
ingesta/indexador.py
---------------------
Indexa chunks normativos en ChromaDB con embeddings (OpenAI o fallback local).

Uso:
    from ingesta.indexador import crear_indice
    crear_indice(chunks, persist_dir="./data/chroma_db")
"""

from __future__ import annotations

import os
from typing import Any

import chromadb
from chromadb.utils import embedding_functions

from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
_NOMBRE_COLECCION = "normativa_udea"
_LOTE_SIZE = 100
_MODELO_FALLBACK = "paraphrase-multilingual-MiniLM-L12-v2"


# ---------------------------------------------------------------------------
# Funciones auxiliares privadas
# ---------------------------------------------------------------------------

def _obtener_embedding_function() -> Any:
    """
    Retorna la función de embeddings adecuada.

    Prioridad:
    1. OpenAIEmbeddingFunction si OPENAI_API_KEY está disponible.
    2. SentenceTransformerEmbeddingFunction con modelo multilingüe como fallback.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()

    if api_key:
        logger.info("Usando OpenAI embeddings (OPENAI_API_KEY detectada)")
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name="text-embedding-3-small",
        )

    logger.info(
        f"OPENAI_API_KEY no encontrada — usando SentenceTransformer '{_MODELO_FALLBACK}'"
    )
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=_MODELO_FALLBACK
    )


def _chunk_existe(coleccion: chromadb.Collection, chunk_id: str) -> bool:
    """Verifica si un chunk con el ID dado ya está en la colección."""
    resultado = coleccion.get(ids=[chunk_id])
    return len(resultado["ids"]) > 0


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def crear_indice(
    chunks: list[dict[str, Any]],
    persist_dir: str = "./data/chroma_db",
) -> None:
    """
    Indexa los chunks en ChromaDB con verificación de duplicados.

    Flujo:
    1. Crea o abre el cliente persistente en persist_dir.
    2. Obtiene o crea la colección 'normativa_udea'.
    3. Para cada chunk, verifica si el ID ya existe (idempotencia).
    4. Inserta los nuevos chunks en lotes de 100 usando upsert().

    Args:
        chunks: Lista de dicts con keys 'id', 'texto' y 'metadata'.
        persist_dir: Directorio donde ChromaDB persiste sus datos.
    """
    if not chunks:
        logger.warning("No hay chunks para indexar.")
        return

    # Inicializar cliente persistente
    cliente = chromadb.PersistentClient(path=persist_dir)
    ef = _obtener_embedding_function()

    coleccion = cliente.get_or_create_collection(
        name=_NOMBRE_COLECCION,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    logger.info(
        f"Colección '{_NOMBRE_COLECCION}' lista. "
        f"Documentos existentes: {coleccion.count()}"
    )

    # Filtrar duplicados
    nuevos: list[dict[str, Any]] = []
    omitidos = 0

    for chunk in chunks:
        chunk_id = chunk["id"]
        if _chunk_existe(coleccion, chunk_id):
            omitidos += 1
        else:
            nuevos.append(chunk)

    if omitidos:
        logger.info(f"  → {omitidos} chunks omitidos (ya existen en el índice)")

    if not nuevos:
        logger.info("Todos los chunks ya están indexados. Nada nuevo que insertar.")
        return

    # Inserción en lotes
    total = len(nuevos)
    insertados = 0

    for inicio in range(0, total, _LOTE_SIZE):
        lote = nuevos[inicio : inicio + _LOTE_SIZE]

        ids = [c["id"] for c in lote]
        documentos = [c["texto"] for c in lote]
        metadatas = [c["metadata"] for c in lote]

        coleccion.upsert(
            ids=ids,
            documents=documentos,
            metadatas=metadatas,
        )

        insertados += len(lote)
        logger.info(
            f"  → Lote indexado: {insertados}/{total} chunks "
            f"({inicio + 1}–{min(inicio + _LOTE_SIZE, total)})"
        )

    logger.info(
        f"Indexación completada: {insertados} chunks nuevos insertados. "
        f"Total en colección: {coleccion.count()}"
    )
