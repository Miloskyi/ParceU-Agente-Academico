"""
agentes/calendario_agent.py
---------------------------
Nodo Calendario_Agent del grafo LangGraph.

Extrae fechas y eventos académicos relevantes a partir de los documentos
ya recuperados (documentos_rag y documentos_web) presentes en el estado,
usando expresiones regulares y palabras clave de calendario.

Si no se encuentran fechas, retorna una lista vacía en fechas_relevantes.
El nodo es no-destructivo: si no hay información de fechas, deja el estado
sin cambios relevantes.

Uso:
    from agentes.calendario_agent import calendario_agent_node
"""

import re
from typing import Optional

from agentes.estado import EstadoCopiloto
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Patrones de expresiones regulares para detección de fechas
# ---------------------------------------------------------------------------

# Formato verbal: "15 de enero de 2025", "1 de marzo de 2024"
_RE_FECHA_VERBAL = re.compile(
    r"\b(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})\b",
    re.IGNORECASE,
)

# Formato ISO: "2025-01-15"
_RE_FECHA_ISO = re.compile(
    r"\b(\d{4}-\d{2}-\d{2})\b",
)

# Palabras clave que suelen aparecer junto a fechas académicas relevantes
_PALABRAS_CLAVE_CALENDARIO = [
    "período",
    "periodo",
    "plazo",
    "fecha límite",
    "fecha limite",
    "inicio",
    "fin de",
    "cierre",
    "apertura",
    "matrícula",
    "matricula",
    "inscripción",
    "inscripcion",
    "examen",
    "evaluación",
    "evaluacion",
    "semestre",
]


def _extraer_texto_documento(doc: dict) -> str:
    """
    Extrae el texto de un documento independientemente de si el campo
    se llama 'contenido', 'texto' o 'content'.

    Args:
        doc: Diccionario con los datos del documento.

    Returns:
        Texto del documento o cadena vacía si no se encuentra.
    """
    for campo in ("contenido", "texto", "content"):
        valor = doc.get(campo, "")
        if valor:
            return str(valor)
    return ""


def _extraer_contexto_fecha(texto: str, fecha: str, ventana: int = 120) -> str:
    """
    Extrae un fragmento de contexto alrededor de la fecha encontrada
    para usarlo como descripción del evento.

    Args:
        texto: Texto completo donde se encontró la fecha.
        fecha: La cadena de fecha encontrada.
        ventana: Número de caracteres a cada lado de la fecha.

    Returns:
        Fragmento de texto contextual limpio.
    """
    pos = texto.lower().find(fecha.lower())
    if pos == -1:
        return fecha

    inicio = max(0, pos - ventana)
    fin = min(len(texto), pos + len(fecha) + ventana)
    fragmento = texto[inicio:fin].strip()

    # Limpiar saltos de línea múltiples
    fragmento = re.sub(r"\s+", " ", fragmento)
    return fragmento


def _detectar_periodo(contexto: str) -> str:
    """
    Intenta inferir el período académico a partir del contexto textual.

    Args:
        contexto: Fragmento de texto que rodea la fecha.

    Returns:
        Período inferido (e.g., "2025-1", "2024-2") o cadena vacía.
    """
    # Buscar año-semestre explícito: "2025-1", "2024-2"
    match = re.search(r"\b(20\d{2})[-–](1|2)\b", contexto)
    if match:
        return f"{match.group(1)}-{match.group(2)}"

    # Buscar solo año
    match_anio = re.search(r"\b(20\d{2})\b", contexto)
    if match_anio:
        return match_anio.group(1)

    return ""


def _inferir_evento(contexto: str, fecha: str) -> str:
    """
    Intenta inferir el nombre del evento académico a partir del contexto.

    Args:
        contexto: Fragmento de texto que rodea la fecha.
        fecha: La cadena de fecha encontrada.

    Returns:
        Nombre del evento inferido o descripción genérica.
    """
    contexto_lower = contexto.lower()

    # Mapeo de palabras clave a nombres de eventos descriptivos
    mapeo_eventos = [
        (["inicio de semestre", "inicio de clases", "inicio del semestre"], "Inicio de semestre"),
        (["fin de semestre", "fin del semestre", "cierre de semestre"], "Fin de semestre"),
        (["matrícula", "matricula"], "Período de matrícula"),
        (["inscripción", "inscripcion"], "Período de inscripciones"),
        (["plazo", "fecha límite", "fecha limite"], "Fecha límite"),
        (["examen final", "exámenes finales"], "Exámenes finales"),
        (["evaluación", "evaluacion"], "Evaluación"),
        (["semana de receso", "vacaciones"], "Receso académico"),
        (["período", "periodo"], "Período académico"),
    ]

    for palabras, nombre_evento in mapeo_eventos:
        if any(p in contexto_lower for p in palabras):
            return nombre_evento

    # Si no se reconoce el evento, usar el fragmento truncado como descripción
    return contexto[:60].strip() if len(contexto) > 60 else contexto.strip()


def calendario_agent_node(estado: EstadoCopiloto) -> dict:
    """
    Nodo del grafo que extrae fechas académicas relevantes de los documentos
    ya recuperados en el estado.

    Escanea documentos_rag y documentos_web buscando fechas con patrones
    de expresión regular y palabras clave de calendario, luego estructura
    los hallazgos como una lista de eventos con fecha y período.

    Args:
        estado: Estado actual del grafo con al menos:
            - documentos_rag: fragmentos de ChromaDB
            - documentos_web: resultados de búsqueda web

    Returns:
        dict con:
            - fechas_relevantes: lista de dicts {evento, fecha, periodo}
              (vacía si no se encontraron fechas)

    Example:
        >>> estado = {"documentos_rag": [{"contenido": "Inicio de semestre: 3 de febrero de 2025"}],
        ...           "documentos_web": []}
        >>> resultado = calendario_agent_node(estado)
        >>> resultado["fechas_relevantes"][0]["fecha"]
        '3 de febrero de 2025'
    """
    try:
        docs_rag: list[dict] = estado.get("documentos_rag", []) or []
        docs_web: list[dict] = estado.get("documentos_web", []) or []
        todos_los_docs = docs_rag + docs_web

        if not todos_los_docs:
            logger.info("Calendario_Agent: sin documentos disponibles, retornando lista vacía")
            return {"fechas_relevantes": []}

        fechas_encontradas: list[dict] = []
        # Usamos un set para evitar fechas duplicadas en el mismo texto
        fechas_vistas: set[str] = set()

        for doc in todos_los_docs:
            texto = _extraer_texto_documento(doc)
            if not texto:
                continue

            # Buscar con ambos patrones
            matches_verbales = _RE_FECHA_VERBAL.findall(texto)
            matches_iso = _RE_FECHA_ISO.findall(texto)
            todas_las_fechas = matches_verbales + matches_iso

            for fecha_str in todas_las_fechas:
                if fecha_str in fechas_vistas:
                    continue
                fechas_vistas.add(fecha_str)

                contexto = _extraer_contexto_fecha(texto, fecha_str)

                # Verificar si el contexto contiene alguna palabra clave de calendario
                contexto_lower = contexto.lower()
                tiene_contexto_relevante = any(
                    kw in contexto_lower for kw in _PALABRAS_CLAVE_CALENDARIO
                )

                # Incluir la fecha si tiene contexto de calendario relevante
                if tiene_contexto_relevante:
                    evento = _inferir_evento(contexto, fecha_str)
                    periodo = _detectar_periodo(contexto)

                    fechas_encontradas.append(
                        {
                            "evento": evento,
                            "fecha": fecha_str,
                            "periodo": periodo,
                        }
                    )

        logger.info(
            "Calendario_Agent: %d fecha(s) relevante(s) encontrada(s) en %d documentos",
            len(fechas_encontradas),
            len(todos_los_docs),
        )

        return {"fechas_relevantes": fechas_encontradas}

    except Exception as exc:
        logger.error("Calendario_Agent: error inesperado — %s", exc, exc_info=True)
        return {"fechas_relevantes": []}
