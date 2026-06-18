"""
utils/analytics.py
------------------
Módulo de analytics en memoria para el Copiloto Administrativo UdeA.

Registra métricas de uso por sesión sin almacenar PII ni el texto de las consultas.
Thread-safe mediante un Lock estándar de Python.

Uso:
    from utils.analytics import registrar_consulta, obtener_resumen

    registrar_consulta(
        intencion="normativa",
        perfil_usuario="pregrado",
        calidad_final="aceptable",
        agente_usado="RAG_Agent",
        es_urgente=False,
    )

    resumen = obtener_resumen()
    print(resumen["total"])          # 1
    print(resumen["tasa_aceptable"]) # 100.0
"""

import threading
from datetime import datetime
from typing import Optional

from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Estado global del módulo
# ---------------------------------------------------------------------------

_registro: list[dict] = []
_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Funciones públicas
# ---------------------------------------------------------------------------


def registrar_consulta(
    intencion: str,
    perfil_usuario: str,
    calidad_final: str,
    agente_usado: str,
    es_urgente: bool,
) -> None:
    """
    Agrega una entrada al registro global en memoria.

    No almacena el texto de la consulta ni ningún dato de identificación
    personal (PII) del usuario.

    Args:
        intencion:      Intención clasificada (normativa, trámite, calendario,
                        urgencia, otro).
        perfil_usuario: Perfil del usuario (pregrado, posgrado, docente,
                        administrativo).
        calidad_final:  Evaluación del Grader (aceptable, mejorar, sin_info).
        agente_usado:   Nombre del nodo/agente que procesó la consulta.
        es_urgente:     True si la consulta fue marcada como urgente.

    Example:
        >>> registrar_consulta("normativa", "pregrado", "aceptable", "RAG_Agent", False)
    """
    entrada = {
        "timestamp": datetime.now().isoformat(),
        "intencion": intencion,
        "perfil_usuario": perfil_usuario,
        "calidad_final": calidad_final,
        "agente_usado": agente_usado,
        "es_urgente": es_urgente,
    }

    with _lock:
        _registro.append(entrada)

    logger.info(
        "Consulta registrada | intencion=%s perfil=%s calidad=%s urgente=%s",
        intencion,
        perfil_usuario,
        calidad_final,
        es_urgente,
    )


def obtener_resumen() -> dict:
    """
    Calcula y retorna un resumen estadístico del registro en memoria.

    Returns:
        dict con las siguientes claves:
            - ``total`` (int): Total de consultas registradas.
            - ``urgentes`` (int): Consultas marcadas como urgentes.
            - ``por_intencion`` (dict): Conteo de consultas por categoría de intención.
            - ``por_perfil`` (dict): Conteo de consultas por perfil de usuario.
            - ``tasa_aceptable`` (float): Porcentaje de consultas con calidad "aceptable".
            - ``por_agente`` (dict): Conteo de consultas por agente usado.

    Example:
        >>> resumen = obtener_resumen()
        >>> resumen["total"]
        0
        >>> resumen["tasa_aceptable"]
        0.0
    """
    with _lock:
        copia = list(_registro)

    total = len(copia)

    if total == 0:
        return {
            "total": 0,
            "urgentes": 0,
            "por_intencion": {},
            "por_perfil": {},
            "tasa_aceptable": 0.0,
            "por_agente": {},
        }

    urgentes = sum(1 for e in copia if e.get("es_urgente"))

    por_intencion: dict[str, int] = {}
    por_perfil: dict[str, int] = {}
    por_agente: dict[str, int] = {}
    aceptables = 0

    for entrada in copia:
        intencion = entrada.get("intencion", "desconocida")
        por_intencion[intencion] = por_intencion.get(intencion, 0) + 1

        perfil = entrada.get("perfil_usuario", "desconocido")
        por_perfil[perfil] = por_perfil.get(perfil, 0) + 1

        agente = entrada.get("agente_usado", "desconocido")
        por_agente[agente] = por_agente.get(agente, 0) + 1

        if entrada.get("calidad_final") == "aceptable":
            aceptables += 1

    tasa_aceptable = round(aceptables / total * 100, 1)

    return {
        "total": total,
        "urgentes": urgentes,
        "por_intencion": por_intencion,
        "por_perfil": por_perfil,
        "tasa_aceptable": tasa_aceptable,
        "por_agente": por_agente,
    }


def obtener_texto_resumen() -> str:
    """
    Genera un resumen en formato Markdown para mostrar en la pestaña Analytics.

    Returns:
        String Markdown con estadísticas de la sesión actual.

    Example:
        >>> texto = obtener_texto_resumen()
        >>> texto.startswith("## 📊 Analytics")
        True
    """
    resumen = obtener_resumen()

    lineas = [
        "## 📊 Analytics — Sesión Actual",
        "",
        f"| Métrica | Valor |",
        f"|---------|-------|",
        f"| Total de consultas | {resumen['total']} |",
        f"| Consultas urgentes | {resumen['urgentes']} |",
        f"| Tasa de calidad aceptable | {resumen['tasa_aceptable']}% |",
        "",
    ]

    # Distribución por intención
    lineas.append("### Consultas por Intención")
    lineas.append("")
    if resumen["por_intencion"]:
        lineas.append("| Intención | Consultas |")
        lineas.append("|-----------|-----------|")
        for intencion, count in sorted(
            resumen["por_intencion"].items(), key=lambda x: x[1], reverse=True
        ):
            lineas.append(f"| {intencion} | {count} |")
    else:
        lineas.append("_Sin datos registrados aún._")
    lineas.append("")

    # Distribución por perfil
    lineas.append("### Consultas por Perfil de Usuario")
    lineas.append("")
    if resumen["por_perfil"]:
        lineas.append("| Perfil | Consultas |")
        lineas.append("|--------|-----------|")
        for perfil, count in sorted(
            resumen["por_perfil"].items(), key=lambda x: x[1], reverse=True
        ):
            lineas.append(f"| {perfil} | {count} |")
    else:
        lineas.append("_Sin datos registrados aún._")
    lineas.append("")

    # Distribución por agente
    lineas.append("### Consultas por Agente")
    lineas.append("")
    if resumen["por_agente"]:
        lineas.append("| Agente | Consultas |")
        lineas.append("|--------|-----------|")
        for agente, count in sorted(
            resumen["por_agente"].items(), key=lambda x: x[1], reverse=True
        ):
            lineas.append(f"| {agente} | {count} |")
    else:
        lineas.append("_Sin datos registrados aún._")
    lineas.append("")

    lineas.append(
        "_Los datos corresponden únicamente a la sesión en curso. "
        "No se almacena información personal de los usuarios._"
    )

    return "\n".join(lineas)


def actualizar_ultima_calidad(calidad: str) -> None:
    """
    Actualiza calidad_final de la última entrada registrada.
    Es no-op si el registro está vacío.

    Args:
        calidad: Valor de calidad final ('aceptable', 'mejorar', 'sin_info', etc.)

    Example:
        >>> registrar_consulta("normativa", "pregrado", "pendiente", "RAG_Agent", False)
        >>> actualizar_ultima_calidad("aceptable")
        >>> obtener_registro()[-1]["calidad_final"]
        'aceptable'
    """
    with _lock:
        if _registro:
            _registro[-1]["calidad_final"] = calidad


def limpiar_registro() -> None:
    """
    Vacía el registro global en memoria.

    Útil para tests y para reiniciar las estadísticas sin reiniciar el proceso.

    Example:
        >>> registrar_consulta("normativa", "pregrado", "aceptable", "RAG_Agent", False)
        >>> limpiar_registro()
        >>> obtener_resumen()["total"]
        0
    """
    with _lock:
        _registro.clear()

    logger.info("Registro de analytics limpiado.")


def obtener_registro() -> list[dict]:
    """
    Retorna una copia del registro actual.

    Returns:
        Lista de dicts con las entradas registradas. Cada entrada contiene:
        ``timestamp``, ``intencion``, ``perfil_usuario``, ``calidad_final``,
        ``agente_usado`` y ``es_urgente``.

    Example:
        >>> limpiar_registro()
        >>> registrar_consulta("trámite", "posgrado", "mejorar", "Tramite_Agent", False)
        >>> registro = obtener_registro()
        >>> len(registro)
        1
        >>> registro[0]["intencion"]
        'trámite'
    """
    with _lock:
        return list(_registro)


def obtener_resumen_extendido() -> dict:
    """
    Extiende obtener_resumen() con campos adicionales sin modificar los existentes.

    Backward compatible: todos los campos de ``obtener_resumen()`` están presentes
    sin cambios en nombre ni tipo.

    Campos adicionales:
        - ``por_calidad`` (dict str->int): Conteo por valor de ``calidad_final``.
        - ``tasa_urgentes`` (float): ``round(urgentes/total*100, 1)`` o ``0.0`` si
          ``total == 0``.
        - ``agente_mas_usado`` (str): Agente con más entradas en ``por_agente``; en
          empate, el primero alfabéticamente; ``""`` si el registro está vacío.
        - ``intencion_mas_frecuente`` (str): Misma lógica que ``agente_mas_usado``
          sobre ``por_intencion``.
        - ``consultas_ultimo_minuto`` (int): Entradas cuyo ``timestamp`` es posterior
          a ``now - 60 s``.

    Returns:
        dict con todos los campos de ``obtener_resumen()`` más los cinco campos
        adicionales descritos arriba.

    Example:
        >>> limpiar_registro()
        >>> registrar_consulta("normativa", "pregrado", "aceptable", "RAG_Agent", True)
        >>> r = obtener_resumen_extendido()
        >>> r["total"]
        1
        >>> r["tasa_urgentes"]
        100.0
        >>> r["agente_mas_usado"]
        'RAG_Agent'
        >>> r["consultas_ultimo_minuto"]
        1
    """
    base = obtener_resumen()  # reutiliza lógica existente, backward compatible
    with _lock:
        copia = list(_registro)

    # por_calidad
    por_calidad: dict[str, int] = {}
    for e in copia:
        c = e.get("calidad_final", "desconocida")
        por_calidad[c] = por_calidad.get(c, 0) + 1

    total = base["total"]
    urgentes = base["urgentes"]

    # tasa_urgentes
    tasa_urgentes = round(urgentes / total * 100, 1) if total > 0 else 0.0

    # agente_mas_usado
    por_agente = base["por_agente"]
    agente_mas_usado = (
        min(k for k, v in por_agente.items() if v == max(por_agente.values()))
        if por_agente else ""
    )

    # intencion_mas_frecuente
    por_intencion = base["por_intencion"]
    intencion_mas_frecuente = (
        min(k for k, v in por_intencion.items() if v == max(por_intencion.values()))
        if por_intencion else ""
    )

    # consultas_ultimo_minuto
    ahora = datetime.now()
    consultas_ultimo_minuto = sum(
        1 for e in copia
        if (ahora - datetime.fromisoformat(e["timestamp"])).total_seconds() <= 60
    )

    return {
        **base,
        "por_calidad": por_calidad,
        "tasa_urgentes": tasa_urgentes,
        "agente_mas_usado": agente_mas_usado,
        "intencion_mas_frecuente": intencion_mas_frecuente,
        "consultas_ultimo_minuto": consultas_ultimo_minuto,
    }
