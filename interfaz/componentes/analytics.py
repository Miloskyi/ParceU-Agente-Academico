"""
interfaz/componentes/analytics.py
-----------------------------------
Tab de Analytics para el Copiloto Administrativo UdeA.

Registra consultas en memoria (sin almacenar datos identificables) y
muestra estadísticas de uso de la sesión actual.

Expone:
    registrar_consulta(intencion, perfil_usuario, calidad_final, agente_usado, es_urgente)
    obtener_datos_analytics(registro) → dict con métricas calculadas
    crear_tab_analytics(obtener_datos_fn) → tab_bloque
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable

import gradio as gr

from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Registro en memoria (sin datos personales identificables)
# ---------------------------------------------------------------------------

# Lista compartida de registros de la sesión actual.
# Estructura de cada entrada:
#   { timestamp, intencion, perfil_usuario, calidad_final, agente_usado, es_urgente }
_REGISTRO_SESION: list[dict] = []


def registrar_consulta(
    intencion: str = "",
    perfil_usuario: str = "",
    calidad_final: str = "",
    agente_usado: str = "",
    es_urgente: bool = False,
) -> None:
    """
    Registra los metadatos de una consulta en el registro de sesión.

    No almacena el texto de la consulta ni datos identificables del usuario.

    Args:
        intencion:      Intención clasificada por el router.
        perfil_usuario: Perfil interno del usuario.
        calidad_final:  Evaluación del Grader.
        agente_usado:   Nombre del agente principal que respondió.
        es_urgente:     True si la consulta fue marcada como urgente.
    """
    entrada = {
        "timestamp": datetime.now().isoformat(),
        "intencion": intencion or "desconocida",
        "perfil_usuario": perfil_usuario or "desconocido",
        "calidad_final": calidad_final or "desconocida",
        "agente_usado": agente_usado or "desconocido",
        "es_urgente": bool(es_urgente),
    }
    _REGISTRO_SESION.append(entrada)
    logger.debug("Analytics: consulta registrada — intención=%s", entrada["intencion"])


def obtener_datos_analytics(registro: list[dict] | None = None) -> dict:
    """
    Calcula métricas de uso a partir del registro de sesión.

    Args:
        registro: Lista de dicts de consulta. Si es None, usa _REGISTRO_SESION.

    Returns:
        Dict con:
            - total_consultas (int)
            - urgentes (int)
            - tasa_calidad_aceptable (float, 0.0–1.0)
            - distribucion_intencion (dict[str, int])
            - distribucion_perfil (dict[str, int])
            - distribucion_agente (dict[str, int])
    """
    datos = registro if registro is not None else _REGISTRO_SESION

    total = len(datos)
    if total == 0:
        return {
            "total_consultas": 0,
            "urgentes": 0,
            "tasa_calidad_aceptable": 0.0,
            "distribucion_intencion": {},
            "distribucion_perfil": {},
            "distribucion_agente": {},
        }

    urgentes = sum(1 for e in datos if e.get("es_urgente", False))
    aceptables = sum(1 for e in datos if e.get("calidad_final") == "aceptable")
    tasa_calidad = round(aceptables / total, 3)

    dist_intencion: dict[str, int] = {}
    dist_perfil: dict[str, int] = {}
    dist_agente: dict[str, int] = {}

    for entrada in datos:
        intencion = entrada.get("intencion", "desconocida")
        perfil = entrada.get("perfil_usuario", "desconocido")
        agente = entrada.get("agente_usado", "desconocido")

        dist_intencion[intencion] = dist_intencion.get(intencion, 0) + 1
        dist_perfil[perfil] = dist_perfil.get(perfil, 0) + 1
        dist_agente[agente] = dist_agente.get(agente, 0) + 1

    return {
        "total_consultas": total,
        "urgentes": urgentes,
        "tasa_calidad_aceptable": tasa_calidad,
        "distribucion_intencion": dist_intencion,
        "distribucion_perfil": dist_perfil,
        "distribucion_agente": dist_agente,
    }


def _construir_tabla_distribucion(distribucion: dict[str, int], titulo: str) -> list[list]:
    """
    Convierte un dict de distribución en filas para gr.Dataframe.

    Args:
        distribucion: Dict {categoría: cantidad}.
        titulo:       Nombre de la primera columna.

    Returns:
        Lista de filas [categoría, cantidad, porcentaje].
    """
    total = sum(distribucion.values()) or 1
    filas = []
    for categoria, cantidad in sorted(distribucion.items(), key=lambda x: -x[1]):
        pct = round(cantidad / total * 100, 1)
        filas.append([categoria, cantidad, f"{pct}%"])
    return filas


def crear_tab_analytics(obtener_datos_fn: Callable | None = None):
    """
    Crea y retorna el bloque del Tab de Analytics.

    Args:
        obtener_datos_fn: Función que retorna el dict de métricas.
                          Si es None, usa la función interna obtener_datos_analytics.

    Returns:
        tab_bloque: El bloque gr.Tab listo para usar.
    """
    _fn = obtener_datos_fn if obtener_datos_fn is not None else obtener_datos_analytics

    with gr.Tab("📊 Analytics") as tab_bloque:
        gr.Markdown("## Analytics de la Sesión")
        gr.Markdown(
            "Estadísticas de uso de esta sesión. "
            "**No se almacena el texto de las consultas ni datos identificables.**"
        )

        with gr.Row():
            kpi_total = gr.Textbox(
                label="Total de consultas",
                value="0",
                interactive=False,
            )
            kpi_urgentes = gr.Textbox(
                label="Consultas urgentes",
                value="0",
                interactive=False,
            )
            kpi_calidad = gr.Textbox(
                label="Tasa de calidad aceptable",
                value="0.0%",
                interactive=False,
            )

        gr.Markdown("### Distribución por intención")
        tabla_intencion = gr.Dataframe(
            headers=["Intención", "Consultas", "Porcentaje"],
            datatype=["str", "number", "str"],
            value=[],
            interactive=False,
            label="",
        )

        gr.Markdown("### Distribución por perfil de usuario")
        tabla_perfil = gr.Dataframe(
            headers=["Perfil", "Consultas", "Porcentaje"],
            datatype=["str", "number", "str"],
            value=[],
            interactive=False,
            label="",
        )

        gr.Markdown("### Agentes utilizados")
        tabla_agente = gr.Dataframe(
            headers=["Agente", "Consultas", "Porcentaje"],
            datatype=["str", "number", "str"],
            value=[],
            interactive=False,
            label="",
        )

        boton_actualizar = gr.Button("🔄 Actualizar estadísticas", variant="secondary")

        gr.Markdown(
            "---\n"
            "> 🔒 **Privacidad:** Solo se registran metadatos no identificables "
            "(intención, perfil, calidad, agente). No se almacena el texto de las "
            "consultas, nombres ni información personal."
        )

        # ---------------------------------------------------------------------------
        # Función de actualización
        # ---------------------------------------------------------------------------

        def _actualizar_analytics():
            datos = _fn()
            total = datos.get("total_consultas", 0)
            urgentes = datos.get("urgentes", 0)
            tasa = datos.get("tasa_calidad_aceptable", 0.0)

            dist_int = datos.get("distribucion_intencion", {})
            dist_per = datos.get("distribucion_perfil", {})
            dist_age = datos.get("distribucion_agente", {})

            filas_int = _construir_tabla_distribucion(dist_int, "Intención") or [["—", 0, "0%"]]
            filas_per = _construir_tabla_distribucion(dist_per, "Perfil") or [["—", 0, "0%"]]
            filas_age = _construir_tabla_distribucion(dist_age, "Agente") or [["—", 0, "0%"]]

            return (
                str(total),
                str(urgentes),
                f"{round(tasa * 100, 1)}%",
                filas_int,
                filas_per,
                filas_age,
            )

        boton_actualizar.click(
            fn=_actualizar_analytics,
            inputs=[],
            outputs=[
                kpi_total,
                kpi_urgentes,
                kpi_calidad,
                tabla_intencion,
                tabla_perfil,
                tabla_agente,
            ],
        )

    return tab_bloque
