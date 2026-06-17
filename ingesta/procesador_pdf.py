"""
ingesta/procesador_pdf.py
--------------------------
Extrae texto y tablas de PDFs normativos de la UdeA.

Uso:
    from ingesta.procesador_pdf import procesar_pdf, extraer_tablas
    fragmentos = procesar_pdf(Path("data/raw/reglamento.pdf"))
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF
import pdfplumber

from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Mapeo de nombres de PDF a categorías temáticas
# ---------------------------------------------------------------------------
CATEGORIAS_DOCUMENTOS: dict[str, str] = {
    "reglamento_estudiantil": "reglamento_estudiantil",
    "reglamento estudiantil": "reglamento_estudiantil",
    "acuerdo_superior": "normativa_general",
    "acuerdo superior": "normativa_general",
    "estatuto_general": "normativa_general",
    "estatuto general": "normativa_general",
    "calendario_academico": "calendario",
    "calendario academico": "calendario",
    "reglamento_posgrado": "posgrado",
    "reglamento posgrado": "posgrado",
    "manual_convivencia": "convivencia",
    "manual convivencia": "convivencia",
    "politica_bienestar": "bienestar",
    "politica bienestar": "bienestar",
    "reglamento_docente": "docentes",
    "reglamento docente": "docentes",
    "estatuto_profesoral": "docentes",
    "estatuto profesoral": "docentes",
}

# Categoría por defecto cuando no hay coincidencia
_CATEGORIA_DEFAULT = "normativa_general"

# ---------------------------------------------------------------------------
# Patrones regex para detectar estructura normativa
# ---------------------------------------------------------------------------
_RE_ARTICULO = re.compile(r"(ARTÍCULO|Artículo)\s+(\d+)", re.UNICODE)
_RE_CAPITULO = re.compile(r"(CAPÍTULO|Capítulo)\s+([IVXLCDM]+|\d+)", re.UNICODE)
_RE_PARAGRAFO = re.compile(r"(PARÁGRAFO|Parágrafo)\s*(\d*)", re.UNICODE)

# Longitud mínima de un bloque para ser considerado válido
_MIN_CHARS = 50


# ---------------------------------------------------------------------------
# Dataclass principal
# ---------------------------------------------------------------------------
@dataclass
class FragmentoNormativo:
    """Unidad mínima de texto extraído de un PDF normativo."""

    id: str
    texto: str
    documento: str
    pagina: int
    articulo: str = ""
    capitulo: str = ""
    categoria: str = _CATEGORIA_DEFAULT
    tipo: str = "texto"  # "texto" | "tabla"


# ---------------------------------------------------------------------------
# Funciones auxiliares privadas
# ---------------------------------------------------------------------------

def _resolver_categoria(ruta: Path) -> str:
    """Retorna la categoría basada en el nombre del archivo (sin extensión)."""
    nombre = ruta.stem.lower().replace("-", "_").replace(" ", "_")
    # Primero intentamos clave exacta
    if nombre in CATEGORIAS_DOCUMENTOS:
        return CATEGORIAS_DOCUMENTOS[nombre]
    # Luego buscamos si alguna clave está contenida en el nombre
    for clave, categoria in CATEGORIAS_DOCUMENTOS.items():
        if clave.replace(" ", "_") in nombre:
            return categoria
    return _CATEGORIA_DEFAULT


def _generar_id(documento: str, pagina: int, indice: int, tipo: str = "texto") -> str:
    """Genera un ID único y legible para un fragmento."""
    base = f"{documento}_p{pagina}_{tipo}_{indice}"
    # Normalizar para que sea un ID limpio
    base = re.sub(r"[^a-zA-Z0-9_]", "_", base).lower()
    return base


def _detectar_articulo(texto: str) -> str:
    """Extrae la referencia al artículo más reciente en un bloque de texto."""
    match = _RE_ARTICULO.search(texto)
    if match:
        return f"Artículo {match.group(2)}"
    return ""


def _detectar_capitulo(texto: str) -> str:
    """Extrae la referencia al capítulo más reciente en un bloque de texto."""
    match = _RE_CAPITULO.search(texto)
    if match:
        return f"Capítulo {match.group(2)}"
    return ""


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def procesar_pdf(ruta: Path) -> list[FragmentoNormativo]:
    """
    Extrae bloques de texto de un PDF usando PyMuPDF (fitz).

    Por cada página se extraen los bloques de texto, detectando artículos,
    capítulos y parágrafos. Se descartan bloques con menos de 50 caracteres.

    Args:
        ruta: Ruta al archivo PDF.

    Returns:
        Lista de FragmentoNormativo con el texto y metadatos de cada bloque.
    """
    fragmentos: list[FragmentoNormativo] = []
    nombre_doc = ruta.stem
    categoria = _resolver_categoria(ruta)

    articulo_actual = ""
    capitulo_actual = ""

    try:
        doc = fitz.open(str(ruta))
        logger.info(f"Procesando PDF '{nombre_doc}' — {doc.page_count} páginas")

        for num_pag in range(doc.page_count):
            pagina = doc[num_pag]
            bloques = pagina.get_text("blocks")  # lista de (x0,y0,x1,y1,texto,blk_n,blk_type)

            for idx, bloque in enumerate(bloques):
                # bloque[6] == 0 → texto (1 == imagen)
                if bloque[6] != 0:
                    continue

                texto_bloque: str = bloque[4].strip()

                # Filtrar bloques demasiado cortos
                if len(texto_bloque) < _MIN_CHARS:
                    continue

                # Actualizar contexto de artículo/capítulo
                if _RE_CAPITULO.search(texto_bloque):
                    capitulo_actual = _detectar_capitulo(texto_bloque)
                if _RE_ARTICULO.search(texto_bloque):
                    articulo_actual = _detectar_articulo(texto_bloque)

                # Detectar tipo de fragmento
                if _RE_PARAGRAFO.search(texto_bloque):
                    tipo = "paragrafo"
                elif _RE_ARTICULO.search(texto_bloque):
                    tipo = "articulo"
                elif _RE_CAPITULO.search(texto_bloque):
                    tipo = "capitulo"
                else:
                    tipo = "texto"

                fragmento_id = _generar_id(nombre_doc, num_pag + 1, idx, tipo)

                fragmentos.append(
                    FragmentoNormativo(
                        id=fragmento_id,
                        texto=texto_bloque,
                        documento=nombre_doc,
                        pagina=num_pag + 1,
                        articulo=articulo_actual,
                        capitulo=capitulo_actual,
                        categoria=categoria,
                        tipo=tipo,
                    )
                )

        doc.close()
        logger.info(f"  → {len(fragmentos)} fragmentos de texto extraídos de '{nombre_doc}'")

    except Exception as exc:
        logger.error(f"Error procesando PDF '{ruta}': {exc}")

    return fragmentos


def extraer_tablas(ruta: Path) -> list[FragmentoNormativo]:
    """
    Extrae tablas de un PDF usando pdfplumber y las convierte a texto estructurado.

    Cada tabla se convierte a una representación de texto con filas separadas
    por saltos de línea y columnas por ' | '.

    Args:
        ruta: Ruta al archivo PDF.

    Returns:
        Lista de FragmentoNormativo con el contenido de cada tabla.
    """
    fragmentos: list[FragmentoNormativo] = []
    nombre_doc = ruta.stem
    categoria = _resolver_categoria(ruta)

    try:
        with pdfplumber.open(str(ruta)) as pdf:
            logger.info(f"Extrayendo tablas de '{nombre_doc}' — {len(pdf.pages)} páginas")

            for num_pag, pagina in enumerate(pdf.pages, start=1):
                tablas = pagina.extract_tables()

                for idx_tabla, tabla in enumerate(tablas):
                    if not tabla:
                        continue

                    # Convertir tabla 2D a texto legible
                    filas_texto = []
                    for fila in tabla:
                        celda_limpia = [str(c).strip() if c else "" for c in fila]
                        filas_texto.append(" | ".join(celda_limpia))

                    texto_tabla = "\n".join(filas_texto).strip()

                    # Descartar tablas cuyo texto sea demasiado corto
                    if len(texto_tabla) < _MIN_CHARS:
                        continue

                    fragmento_id = _generar_id(nombre_doc, num_pag, idx_tabla, "tabla")

                    fragmentos.append(
                        FragmentoNormativo(
                            id=fragmento_id,
                            texto=texto_tabla,
                            documento=nombre_doc,
                            pagina=num_pag,
                            articulo="",
                            capitulo="",
                            categoria=categoria,
                            tipo="tabla",
                        )
                    )

        logger.info(f"  → {len(fragmentos)} fragmentos de tabla extraídos de '{nombre_doc}'")

    except Exception as exc:
        logger.error(f"Error extrayendo tablas de '{ruta}': {exc}")

    return fragmentos
