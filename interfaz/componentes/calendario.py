"""
interfaz/componentes/calendario.py
------------------------------------
Tab de Calendario Académico para el Copiloto Administrativo UdeA.

Muestra una tabla con las fechas clave del semestre 2026-1 más un disclaimer.

Expone:
    crear_tab_calendario() → tab_bloque
"""

from __future__ import annotations

import gradio as gr

from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Datos hardcoded del semestre 2026-1
# Fuente: Calendario Académico UdeA (diseño del sistema)
# ---------------------------------------------------------------------------

CALENDARIO_2026_1 = [
    # [Evento, Fechas, Periodo, Notas]
    ["📋 Matrícula financiera",       "15 – 23 enero 2026",    "2026-1", "Pago en línea o en bancos autorizados"],
    ["📚 Inicio de clases",           "27 enero 2026",          "2026-1", "Primer día hábil del semestre"],
    ["✏️ Periodo de adiciones",       "27 – 30 enero 2026",    "2026-1", "Agregar materias al horario"],
    ["❌ Periodo de cancelaciones",   "3 – 13 febrero 2026",   "2026-1", "Cancelar materias sin afectar promedio"],
    ["🔍 Primer corte evaluativo",    "17 – 28 febrero 2026",  "2026-1", "Evaluaciones parciales del primer tercio"],
    ["📝 Segundo corte evaluativo",   "6 – 17 abril 2026",     "2026-1", "Evaluaciones parciales del segundo tercio"],
    ["🏖️ Semana de receso",           "20 – 24 abril 2026",    "2026-1", "Semana Santa / receso estudiantil"],
    ["📊 Tercer corte evaluativo",    "4 – 15 mayo 2026",      "2026-1", "Evaluaciones parciales del tercer tercio"],
    ["🏁 Fin de clases",              "6 junio 2026",           "2026-1", "Último día de clases del semestre"],
    ["📑 Exámenes finales",           "8 – 20 junio 2026",     "2026-1", "Período de exámenes finales oficiales"],
    ["🎓 Entrega de notas finales",   "25 junio 2026",          "2026-1", "Plazo límite para docentes"],
    ["📁 Habilitaciones / validaciones", "23 – 27 junio 2026", "2026-1", "Según reglamento estudiantil"],
    ["📤 Solicitud de grado",         "Antes del 30 mayo 2026","2026-1", "Para egresados del semestre"],
    ["🔄 Inicio pre-inscripción 2026-2", "1 – 15 julio 2026",  "2026-2", "Inscripción anticipada próximo semestre"],
]

ENCABEZADOS = ["Evento", "Fechas", "Periodo", "Notas"]


def crear_tab_calendario():
    """
    Crea y retorna el bloque del Tab de Calendario Académico.

    Muestra una tabla con fechas clave del semestre 2026-1 y un disclaimer
    indicando que las fechas son referenciales.

    Returns:
        tab_bloque: El bloque gr.Tab listo para usar.
    """
    logger.info("Tab Calendario: construyendo con %d eventos", len(CALENDARIO_2026_1))

    with gr.Tab("📅 Calendario") as tab_bloque:
        gr.Markdown("## Calendario Académico 2026-1")
        gr.Markdown(
            "Fechas importantes del semestre **2026-1** de la Universidad de Antioquia. "
            "Haz clic en los encabezados para ordenar la tabla."
        )

        gr.Dataframe(
            value=CALENDARIO_2026_1,
            headers=ENCABEZADOS,
            datatype=["str", "str", "str", "str"],
            interactive=False,
            wrap=True,
            label="Fechas del Semestre 2026-1",
        )

        gr.Markdown(
            "---\n"
            "### Fechas clave de un vistazo\n"
            "| Hito | Fecha |\n"
            "|------|-------|\n"
            "| 🎯 Inicio de clases | **27 enero 2026** |\n"
            "| ❌ Cierre cancelaciones | **13 febrero 2026** |\n"
            "| 🏁 Fin de clases | **6 junio 2026** |\n"
            "| 📑 Exámenes finales | **8 – 20 junio 2026** |"
        )

        gr.Markdown(
            "---\n"
            "> ⚠️ **Disclaimer:** Las fechas mostradas son **referenciales** y están "
            "sujetas a cambios por parte de las autoridades académicas de la Universidad "
            "de Antioquia. Siempre consulta el calendario oficial vigente en "
            "[www.udea.edu.co](https://www.udea.edu.co) o en el Portal Universitario. "
            "Este copiloto no garantiza la exactitud de las fechas para semestres futuros."
        )

        gr.Markdown(
            "📞 Para información actualizada: "
            "**Registro y Control Académico** — registro@udea.edu.co | (604) 219 5555"
        )

    return tab_bloque
