"""
run_ingesta.py
--------------
Pipeline completo de ingesta de PDFs normativos de la UdeA.

Ejecutar desde la raíz del proyecto:
    python run_ingesta.py

Flujo por cada PDF en data/raw/:
    1. procesar_pdf()   → extrae bloques de texto (PyMuPDF)
    2. extraer_tablas() → extrae tablas (pdfplumber)
    3. chunkear_fragmentos() → divide en chunks <= 700 chars
    4. crear_indice()   → indexa en ChromaDB (OpenAI o sentence-transformers)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Asegurar que el directorio raíz esté en sys.path cuando se ejecuta directamente
_RAIZ = Path(__file__).parent
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

from ingesta.procesador_pdf import procesar_pdf, extraer_tablas
from ingesta.chunker import chunkear_fragmentos
from ingesta.indexador import crear_indice
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Configuración de rutas
# ---------------------------------------------------------------------------
DIR_RAW = _RAIZ / "data" / "raw"
DIR_CHROMA = str(_RAIZ / "data" / "chroma_db")


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def main() -> None:
    logger.info("=" * 60)
    logger.info("Copiloto Administrativo UdeA — Pipeline de Ingesta")
    logger.info("=" * 60)

    # Listar PDFs disponibles
    pdfs = sorted(DIR_RAW.glob("*.pdf"))

    if not pdfs:
        logger.warning(
            f"No se encontraron archivos PDF en '{DIR_RAW}'.\n"
            "Por favor, coloque los PDFs normativos en la carpeta data/raw/ "
            "y vuelva a ejecutar este script.\n"
            "Ejemplo: data/raw/reglamento_estudiantil.pdf"
        )
        print(
            "\n⚠️  No hay PDFs en data/raw/\n"
            "   Agregue los archivos PDF y ejecute nuevamente:\n"
            "       python run_ingesta.py\n"
        )
        return

    logger.info(f"PDFs encontrados: {len(pdfs)}")
    for pdf in pdfs:
        logger.info(f"  · {pdf.name}")

    # Contadores del reporte final
    total_fragmentos = 0
    total_chunks = 0

    # Procesar cada PDF
    for pdf in pdfs:
        logger.info("-" * 50)
        logger.info(f"Procesando: {pdf.name}")

        try:
            # 1. Extraer texto
            fragmentos_texto = procesar_pdf(pdf)

            # 2. Extraer tablas
            fragmentos_tablas = extraer_tablas(pdf)

            todos_fragmentos = fragmentos_texto + fragmentos_tablas
            total_fragmentos += len(todos_fragmentos)

            if not todos_fragmentos:
                logger.warning(f"  → Sin fragmentos útiles en '{pdf.name}'. Saltando.")
                continue

            # 3. Chunkear
            chunks = chunkear_fragmentos(todos_fragmentos)
            total_chunks += len(chunks)

            # 4. Indexar
            crear_indice(chunks, persist_dir=DIR_CHROMA)

        except Exception as exc:
            logger.error(f"Error procesando '{pdf.name}': {exc}. Continuando con el siguiente.")

    # Reporte final
    logger.info("=" * 60)
    logger.info("REPORTE FINAL DE INGESTA")
    logger.info(f"  PDFs procesados  : {len(pdfs)}")
    logger.info(f"  Fragmentos totales: {total_fragmentos}")
    logger.info(f"  Chunks indexados  : {total_chunks}")
    logger.info("=" * 60)

    print(
        f"\n✅ Ingesta completada\n"
        f"   PDFs procesados   : {len(pdfs)}\n"
        f"   Fragmentos totales: {total_fragmentos}\n"
        f"   Chunks indexados  : {total_chunks}\n"
    )


if __name__ == "__main__":
    main()
