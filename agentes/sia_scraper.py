"""
agentes/sia_scraper.py
-----------------------
Scraper del Sistema de Información Académica (SIA) de la UdeA.

Extrae en tiempo real:
  - Oferta de cursos del semestre actual (nombre, código, créditos)
  - Cupos disponibles por grupo
  - Horarios y docentes

A diferencia de los PDFs normativos que se actualizan cada semanas,
los datos del SIA cambian diariamente durante períodos de matrícula.

El scraper:
  1. Consulta el portal SIA con nombre o código de materia.
  2. Parsea la respuesta HTML/JSON.
  3. Retorna los datos estructurados para el Answerer.

También mantiene un caché en memoria con TTL de 1 hora para evitar
sobrecargar el SIA con consultas repetidas.

Uso:
    from agentes.sia_scraper import consultar_sia
    datos = consultar_sia("cálculo diferencial")
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from threading import Lock

import httpx

from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# URL del SIA de la UdeA (portal de consulta pública de oferta académica)
_URL_SIA_OFERTA = "https://sia.udea.edu.co/Catalogo/OfertaAcademica"
_URL_SIA_CURSOS = "https://sia.udea.edu.co/Catalogo/Cursos"
_TIMEOUT = 15   # segundos
_TTL_CACHE = 3600  # 1 hora en segundos

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CopilotoUdeA-SIA/1.0)",
    "Accept": "text/html,application/json",
}

# Patrones para extraer datos del HTML del SIA
_RE_CURSO = re.compile(
    r'<tr[^>]*>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>'  # código, nombre
    r'(?:\s*<td[^>]*>([^<]*)</td>)?'   # créditos (opcional)
    r'(?:\s*<td[^>]*>([^<]*)</td>)?',  # cupos (opcional)
    re.IGNORECASE | re.DOTALL,
)

_RE_NUMERO = re.compile(r'\d+')


# ---------------------------------------------------------------------------
# Caché en memoria
# ---------------------------------------------------------------------------

_cache: dict[str, dict] = {}   # query_normalizada → {datos, timestamp}
_cache_lock = Lock()


def _normalizar_query(query: str) -> str:
    """Normaliza la query para usar como clave de caché."""
    return re.sub(r'\s+', ' ', query.lower().strip())


def _obtener_del_cache(query: str) -> list[dict] | None:
    """Retorna datos del caché si aún son válidos."""
    clave = _normalizar_query(query)
    with _cache_lock:
        entrada = _cache.get(clave)
        if not entrada:
            return None
        edad = time.time() - entrada["timestamp"]
        if edad > _TTL_CACHE:
            del _cache[clave]
            return None
        edad_min = int(edad / 60)
        logger.info("SIAScraper: caché válido para '%s' (edad: %d min)", query[:50], edad_min)
        return entrada["datos"]


def _guardar_en_cache(query: str, datos: list[dict]) -> None:
    """Guarda datos en caché."""
    clave = _normalizar_query(query)
    with _cache_lock:
        _cache[clave] = {"datos": datos, "timestamp": time.time()}


def limpiar_cache() -> int:
    """Limpia todo el caché. Retorna el número de entradas eliminadas."""
    with _cache_lock:
        n = len(_cache)
        _cache.clear()
    logger.info("SIAScraper: caché limpiado (%d entradas)", n)
    return n


def obtener_stats_cache() -> dict:
    """Retorna estadísticas del caché actual."""
    with _cache_lock:
        ahora = time.time()
        entradas_validas = sum(
            1 for v in _cache.values()
            if ahora - v["timestamp"] <= _TTL_CACHE
        )
        return {
            "total_entradas": len(_cache),
            "entradas_validas": entradas_validas,
            "ttl_segundos": _TTL_CACHE,
        }


# ---------------------------------------------------------------------------
# Parseo del HTML del SIA
# ---------------------------------------------------------------------------


def _parsear_oferta_html(html: str, query: str) -> list[dict]:
    """
    Extrae cursos del HTML de la página de oferta académica del SIA.

    Args:
        html:  Contenido HTML de la respuesta.
        query: Query original para filtrar resultados relevantes.

    Returns:
        Lista de dicts con información de cada curso.
    """
    cursos = []
    query_lower = query.lower()

    for match in _RE_CURSO.finditer(html):
        codigo = match.group(1).strip() if match.group(1) else ""
        nombre = match.group(2).strip() if match.group(2) else ""
        creditos = match.group(3).strip() if match.group(3) else "N/D"
        cupos_raw = match.group(4).strip() if match.group(4) else ""

        # Filtrar filas de encabezado o vacías
        if not nombre or len(nombre) < 3 or nombre.lower() in ("nombre", "materia", "asignatura"):
            continue

        # Filtrar por relevancia con la query
        if query_lower not in nombre.lower() and query_lower not in codigo.lower():
            # Verificar si alguna palabra clave aparece en el nombre
            palabras_clave = [p for p in query_lower.split() if len(p) > 3]
            if not any(p in nombre.lower() for p in palabras_clave):
                continue

        # Extraer número de cupos si está disponible
        cupos_numeros = _RE_NUMERO.findall(cupos_raw)
        cupos_disponibles = int(cupos_numeros[0]) if cupos_numeros else None

        cursos.append({
            "codigo": codigo,
            "nombre": nombre,
            "creditos": creditos,
            "cupos_disponibles": cupos_disponibles,
            "estado_cupos": (
                "✅ Con cupos" if cupos_disponibles and cupos_disponibles > 0
                else "❌ Sin cupos" if cupos_disponibles == 0
                else "⚪ No disponible"
            ),
            "fuente": "SIA UdeA (tiempo real)",
            "timestamp_consulta": datetime.now(timezone.utc).isoformat(),
        })

    return cursos


def _parsear_json_sia(datos_json: dict, query: str) -> list[dict]:
    """
    Parsea respuesta JSON del SIA si el portal retorna JSON.

    Args:
        datos_json: Dict con la respuesta JSON del SIA.
        query:      Query original.

    Returns:
        Lista de cursos parseados.
    """
    cursos = []
    query_lower = query.lower()

    # Intentar extraer de diferentes estructuras posibles del SIA
    lista_cursos = (
        datos_json.get("cursos")
        or datos_json.get("oferta")
        or datos_json.get("results")
        or datos_json.get("data")
        or []
    )

    if not isinstance(lista_cursos, list):
        return []

    for item in lista_cursos:
        if not isinstance(item, dict):
            continue

        nombre = (
            item.get("nombre") or item.get("name") or
            item.get("nombreCurso") or item.get("materia") or ""
        ).strip()

        codigo = (
            item.get("codigo") or item.get("code") or
            item.get("codigoCurso") or ""
        ).strip()

        if not nombre:
            continue

        # Filtrar por relevancia
        palabras = [p for p in query_lower.split() if len(p) > 3]
        if not any(p in nombre.lower() for p in palabras) and query_lower not in codigo.lower():
            continue

        cupos = item.get("cupos") or item.get("cuposDisponibles") or item.get("available_slots")

        cursos.append({
            "codigo": codigo,
            "nombre": nombre,
            "creditos": str(item.get("creditos") or item.get("credits") or "N/D"),
            "cupos_disponibles": cupos,
            "estado_cupos": (
                "✅ Con cupos" if cupos and int(cupos) > 0
                else "❌ Sin cupos" if cupos == 0
                else "⚪ No disponible"
            ),
            "horario": item.get("horario") or item.get("schedule") or "No disponible",
            "docente": item.get("docente") or item.get("professor") or "No disponible",
            "fuente": "SIA UdeA (tiempo real)",
            "timestamp_consulta": datetime.now(timezone.utc).isoformat(),
        })

    return cursos


# ---------------------------------------------------------------------------
# Consulta al SIA
# ---------------------------------------------------------------------------


def _consultar_sia_http(query: str) -> list[dict]:
    """
    Realiza la petición HTTP al SIA y parsea la respuesta.

    Intenta primero como JSON; si falla, parsea como HTML.

    Args:
        query: Término de búsqueda (nombre o código de materia).

    Returns:
        Lista de cursos encontrados.
    """
    params = {
        "busqueda": query,
        "semestre": "2026-2",   # Semestre actual
        "nivel": "pregrado",
    }

    try:
        logger.info("SIAScraper: consultando SIA para '%s'", query[:60])
        resp = httpx.get(
            _URL_SIA_OFERTA,
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )

        if resp.status_code != 200:
            logger.warning("SIAScraper: SIA respondió %d", resp.status_code)
            return _generar_datos_ejemplo(query)

        content_type = resp.headers.get("content-type", "")

        # Intentar parseo JSON primero
        if "json" in content_type:
            try:
                datos_json = resp.json()
                cursos = _parsear_json_sia(datos_json, query)
                if cursos:
                    logger.info("SIAScraper: JSON — %d cursos encontrados", len(cursos))
                    return cursos
            except Exception as exc:
                logger.warning("SIAScraper: error parseando JSON — %s", exc)

        # Fallback: parseo HTML
        cursos = _parsear_oferta_html(resp.text, query)
        if cursos:
            logger.info("SIAScraper: HTML — %d cursos encontrados", len(cursos))
            return cursos

        # Si el portal no devolvió datos estructurados reconocibles,
        # retornar datos de ejemplo para la demo del hackathon
        logger.info("SIAScraper: sin datos estructurados, usando datos demo para '%s'", query[:50])
        return _generar_datos_ejemplo(query)

    except httpx.TimeoutException:
        logger.warning("SIAScraper: timeout al consultar SIA para '%s'", query[:60])
        return _generar_datos_ejemplo(query)
    except Exception as exc:  # noqa: BLE001
        logger.error("SIAScraper: error inesperado — %s", exc)
        return _generar_datos_ejemplo(query)


def _generar_datos_ejemplo(query: str) -> list[dict]:
    """
    Genera datos de ejemplo cuando el SIA no es accesible.
    Útil para demos y para cuando el portal está caído.

    NOTA: Estos datos son ilustrativos — en producción se usarían datos reales.
    """
    query_lower = query.lower()
    timestamp = datetime.now(timezone.utc).isoformat()

    # Catálogo básico de ejemplo para demostración
    catalogo_demo = [
        {"codigo": "3000002", "nombre": "Cálculo Diferencial", "creditos": "4", "cupos": 35, "facultad": "Ingeniería"},
        {"codigo": "3000003", "nombre": "Cálculo Integral",    "creditos": "4", "cupos": 28, "facultad": "Ingeniería"},
        {"codigo": "3000010", "nombre": "Álgebra Lineal",      "creditos": "3", "cupos": 0,  "facultad": "Ciencias Exactas"},
        {"codigo": "1000001", "nombre": "Introducción a la Programación", "creditos": "3", "cupos": 42, "facultad": "Ingeniería"},
        {"codigo": "1000015", "nombre": "Estructuras de Datos","creditos": "3", "cupos": 15, "facultad": "Ingeniería"},
        {"codigo": "2000005", "nombre": "Física Mecánica",     "creditos": "4", "cupos": 20, "facultad": "Ciencias Exactas"},
        {"codigo": "5000001", "nombre": "Ética Profesional",   "creditos": "2", "cupos": 60, "facultad": "General"},
    ]

    resultados = []
    for item in catalogo_demo:
        # Filtro básico por relevancia
        palabras = [p for p in query_lower.split() if len(p) > 2]
        if not any(p in item["nombre"].lower() for p in palabras):
            continue

        cupos = item["cupos"]
        resultados.append({
            "codigo": item["codigo"],
            "nombre": item["nombre"],
            "creditos": item["creditos"],
            "cupos_disponibles": cupos,
            "estado_cupos": "✅ Con cupos" if cupos > 0 else "❌ Sin cupos",
            "horario": "Consultar SIA para horario actualizado",
            "docente": "Consultar SIA para docente asignado",
            "fuente": "SIA UdeA (datos demo — portal no disponible)",
            "timestamp_consulta": timestamp,
            "es_demo": True,
        })

    return resultados


# ---------------------------------------------------------------------------
# Función principal pública
# ---------------------------------------------------------------------------


def consultar_sia(query: str, forzar_actualizacion: bool = False) -> list[dict]:
    """
    Consulta el SIA de la UdeA para obtener oferta académica en tiempo real.

    Usa caché con TTL de 1 hora para evitar sobrecargar el portal.
    Si `forzar_actualizacion=True`, ignora el caché.

    Args:
        query:               Nombre o código del curso a buscar.
        forzar_actualizacion: Si True, omite el caché y consulta directo al SIA.

    Returns:
        Lista de cursos con código, nombre, créditos, cupos y estado.
        Retorna [] si no se encontró nada.

    Example:
        >>> cursos = consultar_sia("cálculo diferencial")
        >>> cursos[0]["estado_cupos"]
        '✅ Con cupos'
    """
    if not query or not query.strip():
        return []

    # Verificar caché
    if not forzar_actualizacion:
        datos_cache = _obtener_del_cache(query)
        if datos_cache is not None:
            return datos_cache

    # Consultar SIA en tiempo real
    datos = _consultar_sia_http(query)

    # Guardar en caché
    if datos:
        _guardar_en_cache(query, datos)

    return datos


def formatear_respuesta_sia(cursos: list[dict]) -> str:
    """
    Formatea la lista de cursos para presentarla en una respuesta del Answerer.

    Args:
        cursos: Lista de cursos retornada por consultar_sia().

    Returns:
        Texto formateado para incluir en la respuesta del copiloto.
    """
    if not cursos:
        return "No se encontraron cursos que coincidan con tu búsqueda en el SIA."

    es_demo = any(c.get("es_demo") for c in cursos)
    aviso = "\n⚠️ *Datos ilustrativos — portal SIA no disponible en este momento*\n" if es_demo else ""

    timestamp = cursos[0].get("timestamp_consulta", "")[:19].replace("T", " ") if cursos else ""
    encabezado = f"📚 **Oferta académica SIA UdeA** (consultado: {timestamp} UTC){aviso}\n"

    lineas = [encabezado]
    for curso in cursos:
        lineas.append(
            f"• **{curso['nombre']}** ({curso['codigo']})\n"
            f"  Créditos: {curso['creditos']} | "
            f"Cupos: {curso['estado_cupos']}"
        )
        if curso.get("horario") and curso["horario"] != "Consultar SIA para horario actualizado":
            lineas.append(f"  Horario: {curso['horario']}")
        if curso.get("docente") and curso["docente"] != "Consultar SIA para docente asignado":
            lineas.append(f"  Docente: {curso['docente']}")
        lineas.append("")

    lineas.append(f"*Fuente: {cursos[0].get('fuente', 'SIA UdeA')}*")
    return "\n".join(lineas)
