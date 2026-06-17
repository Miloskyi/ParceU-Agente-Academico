"""
ingesta/chunker.py
-------------------
Divide FragmentoNormativos en chunks apropiados para indexación vectorial.

Usa RecursiveCharacterTextSplitter con separadores normativos para respetar
la estructura de artículos y párrafos durante la división.

Uso:
    from ingesta.chunker import chunkear_fragmentos
    chunks = chunkear_fragmentos(fragmentos)
"""

from __future__ import annotations

import re
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

from ingesta.procesador_pdf import FragmentoNormativo
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Configuración del splitter
# ---------------------------------------------------------------------------
_CHUNK_SIZE = 700
_CHUNK_OVERLAP = 120
_SEPARADORES = [
    "\nARTÍCULO",
    "\nArtículo",
    "\nPARÁGRAFO",
    "\n\n",
    "\n",
    ". ",
]

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=_CHUNK_SIZE,
    chunk_overlap=_CHUNK_OVERLAP,
    separators=_SEPARADORES,
)


# ---------------------------------------------------------------------------
# Función auxiliar para generar ID de chunk
# ---------------------------------------------------------------------------
def _id_chunk(fragmento_id: str, indice: int) -> str:
    """Genera un ID único para un chunk derivado de un fragmento."""
    base = f"{fragmento_id}_chunk_{indice}"
    return re.sub(r"[^a-zA-Z0-9_]", "_", base).lower()


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def chunkear_fragmentos(fragmentos: list[FragmentoNormativo]) -> list[dict[str, Any]]:
    """
    Divide una lista de FragmentoNormativo en chunks listos para indexar.

    Reglas:
    - Si el texto del fragmento tiene <= 700 caracteres: se retorna como chunk único.
    - Si supera 700 caracteres: se divide con RecursiveCharacterTextSplitter.

    Cada chunk resultante tiene la forma:
    {
        "id": str,
        "texto": str,
        "metadata": {
            "documento": str,
            "pagina": int,
            "articulo": str,
            "capitulo": str,
            "categoria": str,
            "tipo": str,
        }
    }

    Args:
        fragmentos: Lista de FragmentoNormativo producidos por procesador_pdf.

    Returns:
        Lista de dicts con id, texto y metadata.
    """
    chunks: list[dict[str, Any]] = []

    for fragmento in fragmentos:
        texto = fragmento.texto.strip()

        if not texto:
            continue

        metadata = {
            "documento": fragmento.documento,
            "pagina": fragmento.pagina,
            "articulo": fragmento.articulo,
            "capitulo": fragmento.capitulo,
            "categoria": fragmento.categoria,
            "tipo": fragmento.tipo,
        }

        if len(texto) <= _CHUNK_SIZE:
            # Fragmento pequeño: un único chunk sin dividir
            chunks.append(
                {
                    "id": _id_chunk(fragmento.id, 0),
                    "texto": texto,
                    "metadata": metadata,
                }
            )
        else:
            # Fragmento largo: dividir con el splitter
            sub_textos = _splitter.split_text(texto)
            for idx, sub_texto in enumerate(sub_textos):
                sub_texto = sub_texto.strip()
                if not sub_texto:
                    continue
                chunks.append(
                    {
                        "id": _id_chunk(fragmento.id, idx),
                        "texto": sub_texto,
                        "metadata": metadata,
                    }
                )

    logger.info(
        f"Chunking completado: {len(fragmentos)} fragmentos → {len(chunks)} chunks"
    )
    return chunks
