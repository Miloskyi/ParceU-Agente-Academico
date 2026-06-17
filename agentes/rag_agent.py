"""
agentes/rag_agent.py
--------------------
RAG Agent: recupera fragmentos normativos relevantes desde ChromaDB.

El agente realiza una búsqueda semántica usando la `pregunta_reformulada`
del estado, filtra por categoría cuando aplica, y retorna los top-6
fragmentos con score >= 0.3.

Uso:
    from agentes.rag_agent import rag_agent_node
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

from agentes.estado import EstadoCopiloto
from utils.logger import get_logger

logger = get_logger(__name__)

# Nombre de la colección en ChromaDB
NOMBRE_COLECCION = "normativa_udea"

# Score mínimo para incluir un resultado (1 - distancia coseno >= 0.3)
SCORE_MINIMO = 0.3

# Número máximo de resultados a solicitar y retornar
MAX_RESULTADOS = 6


def _fecha_modificacion(nombre_documento: str) -> str:
    """
    Obtiene la fecha de última modificación del PDF fuente en data/raw/.
    Búsqueda flexible: tolera diferencias en nombre del stem.

    Returns:
        String formateado 'DD/MM/YYYY' o 'Fecha no disponible'.
    """
    if not nombre_documento:
        return "Fecha no disponible"
    raw_dir = Path(os.getenv("CHROMA_PATH", "./data/chroma_db")).parent / "raw"
    try:
        # Intento directo con extensión
        for ext in [".pdf", ""]:
            candidato = raw_dir / f"{nombre_documento}{ext}"
            if candidato.exists():
                return datetime.fromtimestamp(candidato.stat().st_mtime).strftime("%d/%m/%Y")
        # Búsqueda flexible por coincidencia parcial
        nombre_lower = nombre_documento.lower()
        for f in raw_dir.glob("*.pdf"):
            if nombre_lower in f.stem.lower() or f.stem.lower() in nombre_lower:
                return datetime.fromtimestamp(f.stat().st_mtime).strftime("%d/%m/%Y")
    except Exception:
        pass
    return "Fecha no disponible"


def _obtener_coleccion():
    """
    Inicializa el cliente ChromaDB y retorna la colección con la
    función de embedding apropiada.

    Selección de embedding:
    - Si existe OPENAI_API_KEY: usa OpenAI text-embedding-3-small.
    - Si no: usa sentence-transformers con paraphrase-multilingual-MiniLM-L12-v2.

    Returns:
        Colección de ChromaDB lista para consultar, o None si ocurre un error.
    """
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        chroma_path = os.getenv("CHROMA_PATH", "./data/chroma_db")
        logger.info(f"Inicializando ChromaDB en: {chroma_path}")

        client = chromadb.PersistentClient(path=chroma_path)

        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            logger.info("Usando OpenAI embedding function (text-embedding-3-small)")
            embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
                api_key=openai_api_key,
                model_name="text-embedding-3-small",
            )
        else:
            logger.info(
                "OPENAI_API_KEY no encontrada. "
                "Usando sentence-transformers: paraphrase-multilingual-MiniLM-L12-v2"
            )
            embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="paraphrase-multilingual-MiniLM-L12-v2"
            )

        coleccion = client.get_collection(
            name=NOMBRE_COLECCION,
            embedding_function=embedding_fn,
        )
        logger.info(
            f"Colección '{NOMBRE_COLECCION}' cargada. "
            f"Total de documentos: {coleccion.count()}"
        )
        return coleccion

    except Exception as e:
        # La colección puede no existir aún (primer arranque antes de la ingesta)
        logger.warning(f"No se pudo obtener la colección ChromaDB: {e}")
        return None


def rag_agent_node(estado: EstadoCopiloto) -> dict:
    """
    Nodo del grafo LangGraph que recupera fragmentos normativos desde ChromaDB.

    Flujo:
    1. Obtiene la colección ChromaDB.
    2. Ejecuta búsqueda semántica con `pregunta_reformulada`.
    3. Aplica filtro por `categoria` si no es "general".
    4. Filtra resultados con score >= 0.3 (score = 1 - distancia coseno).
    5. Retorna los top-6 fragmentos en `documentos_rag`.

    Args:
        estado: Estado actual del grafo con `pregunta_reformulada` y `categoria`.

    Returns:
        dict con `documentos_rag` (lista de fragmentos) y `agente_usado` = "rag".
        Si no hay resultados o ChromaDB no está disponible, retorna lista vacía.
    """
    resultado_vacio = {"documentos_rag": [], "agente_usado": "rag"}

    try:
        pregunta = estado.get("pregunta_reformulada", "").strip()
        categoria = estado.get("categoria", "").strip()

        if not pregunta:
            logger.warning("RAG Agent: pregunta_reformulada está vacía. Retornando lista vacía.")
            return resultado_vacio

        logger.info(f"RAG Agent iniciando búsqueda | pregunta='{pregunta}' | categoria='{categoria}'")

        coleccion = _obtener_coleccion()
        if coleccion is None:
            logger.warning("RAG Agent: ChromaDB no disponible. Retornando lista vacía.")
            return resultado_vacio

        # Construir parámetros de consulta
        query_kwargs = {
            "query_texts": [pregunta],
            "n_results": MAX_RESULTADOS,
            "include": ["documents", "metadatas", "distances"],
        }

        # Aplicar filtro de categoría solo si no es "general" ni está vacía
        if categoria and categoria.lower() != "general":
            query_kwargs["where"] = {"categoria": categoria}
            logger.info(f"RAG Agent: aplicando filtro where={{categoria: '{categoria}'}}")

        resultados = coleccion.query(**query_kwargs)

        # Extraer listas paralelas de la respuesta de ChromaDB
        documentos = resultados.get("documents", [[]])[0]
        metadatas = resultados.get("metadatas", [[]])[0]
        distances = resultados.get("distances", [[]])[0]

        # Si no hay resultados con filtro, reintentar sin filtro de categoría
        if not documentos and query_kwargs.get("where"):
            logger.info(f"RAG Agent: sin resultados con filtro de categoría '{categoria}'. Reintentando sin filtro.")
            query_kwargs_sin_filtro = {
                "query_texts": [pregunta],
                "n_results": MAX_RESULTADOS,
                "include": ["documents", "metadatas", "distances"],
            }
            resultados = coleccion.query(**query_kwargs_sin_filtro)
            documentos = resultados.get("documents", [[]])[0]
            metadatas = resultados.get("metadatas", [[]])[0]
            distances = resultados.get("distances", [[]])[0]

        if not documentos:
            logger.info("RAG Agent: sin resultados en ChromaDB para la consulta.")
            return resultado_vacio

        # Filtrar por score mínimo y construir fragmentos
        fragmentos = []
        for texto, metadata, distancia in zip(documentos, metadatas, distances):
            score = round(1 - distancia, 3)

            if score < SCORE_MINIMO:
                logger.debug(
                    f"RAG Agent: fragmento descartado por score bajo "
                    f"(score={score} < {SCORE_MINIMO})"
                )
                continue

            fragmento = {
                "texto": texto,
                "documento": metadata.get("fuente", metadata.get("documento", "")),
                "pagina": metadata.get("pagina", ""),
                "articulo": metadata.get("articulo", ""),
                "capitulo": metadata.get("capitulo", ""),
                "categoria": metadata.get("categoria", categoria),
                "relevancia": score,
                "fecha_modificacion": _fecha_modificacion(
                    metadata.get("documento", metadata.get("fuente", ""))
                ),
            }
            fragmentos.append(fragmento)

        # Ordenar por relevancia descendente y tomar top-6
        fragmentos = sorted(fragmentos, key=lambda x: x["relevancia"], reverse=True)[:MAX_RESULTADOS]

        logger.info(
            f"RAG Agent: {len(fragmentos)} fragmento(s) recuperado(s) con score >= {SCORE_MINIMO}"
        )

        return {
            "documentos_rag": fragmentos,
            "agente_usado": "rag",
        }

    except Exception as e:
        logger.error(f"RAG Agent: error inesperado durante la búsqueda: {e}", exc_info=True)
        return resultado_vacio
