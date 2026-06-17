"""
utils/formateador.py
--------------------
Funciones auxiliares de formateo para el Copiloto Administrativo UdeA.

Centraliza la transformación de datos estructurados del Estado en strings
listos para incluir en respuestas o para logging.

Uso:
    from utils.formateador import formatear_cita, formatear_pasos, formatear_fechas
"""

from typing import Optional

from utils.logger import get_logger

logger = get_logger(__name__)


def formatear_cita(
    fuente: str,
    articulo: Optional[str] = None,
    pagina: Optional[int] = None,
) -> str:
    """
    Formatea una referencia bibliográfica en el estilo estándar del Copiloto.

    El formato de salida es: ``(Fuente: X, Artículo Y, pág. Z)``
    Los campos opcionales se omiten si no se proporcionan.

    Args:
        fuente:   Nombre del documento fuente (ej. "Reglamento Estudiantil").
        articulo: Identificador del artículo (ej. "Artículo 45"). Opcional.
        pagina:   Número de página. Opcional.

    Returns:
        String con la cita formateada lista para insertar en la respuesta.

    Examples:
        >>> formatear_cita("Reglamento Estudiantil", "Artículo 45", 12)
        '(Fuente: Reglamento Estudiantil, Artículo 45, pág. 12)'

        >>> formatear_cita("Reglamento Estudiantil", "Artículo 45")
        '(Fuente: Reglamento Estudiantil, Artículo 45)'

        >>> formatear_cita("Portal UdeA")
        '(Fuente: Portal UdeA)'
    """
    if not fuente or not fuente.strip():
        logger.warning("formatear_cita: se recibió fuente vacía; retornando string vacío")
        return ""

    partes = [f"Fuente: {fuente.strip()}"]

    if articulo and articulo.strip():
        partes.append(articulo.strip())

    if pagina is not None:
        partes.append(f"pág. {pagina}")

    return f"({', '.join(partes)})"


def formatear_pasos(pasos: list[str]) -> str:
    """
    Formatea una lista de pasos de trámite en un bloque de texto numerado.

    Si la lista ya incluye numeración (ej. "1. Paso"), la respeta.
    Si no, añade numeración automática.

    Args:
        pasos: Lista de strings con los pasos del trámite.

    Returns:
        String con cada paso en su propia línea, numerados.
        Retorna string vacío si la lista está vacía.

    Examples:
        >>> formatear_pasos(["Ingresar al portal", "Seleccionar el servicio"])
        '1. Ingresar al portal\\n2. Seleccionar el servicio'

        >>> formatear_pasos([])
        ''
    """
    if not pasos:
        return ""

    lineas = []
    for i, paso in enumerate(pasos, start=1):
        paso = paso.strip()
        if not paso:
            continue
        # Si el paso ya empieza con numeración (ej. "1.", "2."), lo usamos tal cual
        if paso and paso[0].isdigit() and "." in paso[:4]:
            lineas.append(paso)
        else:
            lineas.append(f"{i}. {paso}")

    return "\n".join(lineas)


def formatear_fechas(fechas: list[dict]) -> str:
    """
    Formatea una lista de fechas académicas en texto legible.

    Cada elemento de la lista debe tener las claves ``evento``, ``fecha``
    y ``periodo``. Las claves faltantes se sustituyen por "N/D".

    Args:
        fechas: Lista de dicts con estructura ``{evento, fecha, periodo}``.

    Returns:
        String con cada fecha en su propia línea, formato:
        ``• <evento>: <fecha> (<periodo>)``
        Retorna string vacío si la lista está vacía.

    Examples:
        >>> fechas = [{"evento": "Inicio de semestre", "fecha": "2024-02-05", "periodo": "2024-1"}]
        >>> formatear_fechas(fechas)
        '• Inicio de semestre: 2024-02-05 (2024-1)'
    """
    if not fechas:
        return ""

    lineas = []
    for fecha in fechas:
        if not isinstance(fecha, dict):
            logger.warning("formatear_fechas: elemento ignorado — no es un dict: %s", fecha)
            continue

        evento = fecha.get("evento", "N/D")
        fecha_str = fecha.get("fecha", "N/D")
        periodo = fecha.get("periodo", "N/D")

        lineas.append(f"• {evento}: {fecha_str} ({periodo})")

    return "\n".join(lineas)
