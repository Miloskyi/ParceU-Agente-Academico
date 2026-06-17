"""
interfaz/componentes/tramites.py
---------------------------------
Tab de Trámites para el Copiloto Administrativo UdeA.

Lee data/tramites/tramites.json y muestra un Accordion por cada trámite
con sus pasos formateados en Markdown.

Expone:
    crear_tab_tramites() → tab_bloque
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import gradio as gr

from utils.logger import get_logger

logger = get_logger(__name__)

# Ruta al archivo JSON de trámites
_RUTA_JSON = Path(__file__).resolve().parents[2] / "data" / "tramites" / "tramites.json"


def _cargar_tramites() -> list[dict]:
    """
    Carga y retorna la lista de trámites desde tramites.json.

    Returns:
        Lista de dicts de trámite, o lista vacía si hay error.
    """
    try:
        with open(_RUTA_JSON, encoding="utf-8") as f:
            datos = json.load(f)
        tramites = datos.get("tramites", [])
        logger.info("Tab Trámites: %d trámite(s) cargados", len(tramites))
        return tramites
    except FileNotFoundError:
        logger.error("Tab Trámites: no se encontró %s", _RUTA_JSON)
        return []
    except json.JSONDecodeError as exc:
        logger.error("Tab Trámites: JSON malformado — %s", exc)
        return []


def _formatear_tramite(tramite: dict) -> str:
    """
    Convierte un dict de trámite en texto Markdown formateado.

    Args:
        tramite: Dict con los campos del trámite.

    Returns:
        String Markdown listo para gr.Markdown.
    """
    lineas: list[str] = []

    descripcion = tramite.get("descripcion", "")
    if descripcion:
        lineas.append(f"{descripcion}\n")

    # Metadatos
    tiempo = tramite.get("tiempo_estimado", "")
    costo = tramite.get("costo", "")
    oficina = tramite.get("oficina", "")
    url = tramite.get("url_oficial", "")

    if tiempo or costo or oficina:
        lineas.append("**Información general:**")
        if tiempo:
            lineas.append(f"- ⏱️ Tiempo estimado: {tiempo}")
        if costo:
            lineas.append(f"- 💰 Costo: {costo}")
        if oficina:
            lineas.append(f"- 🏛️ Oficina: {oficina}")
        if url:
            lineas.append(f"- 🔗 [Trámite oficial en portal UdeA]({url})")
        lineas.append("")

    # Pasos
    pasos = tramite.get("pasos", [])
    if pasos:
        lineas.append("**Pasos a seguir:**")
        for paso in pasos:
            lineas.append(f"{paso}")
        lineas.append("")

    # Documentos requeridos
    docs = tramite.get("documentos_requeridos", [])
    if docs:
        lineas.append("**Documentos requeridos:**")
        for doc in docs:
            lineas.append(f"- {doc}")
        lineas.append("")

    # Advertencias
    advertencias = tramite.get("advertencias", [])
    if advertencias:
        lineas.append("**⚠️ Advertencias importantes:**")
        for adv in advertencias:
            lineas.append(f"- {adv}")

    return "\n".join(lineas)


def crear_tab_tramites():
    """
    Crea y retorna el bloque del Tab de Trámites.

    Lee tramites.json y construye un gr.Accordion por cada trámite
    con sus pasos formateados en Markdown.

    Returns:
        tab_bloque: El bloque gr.Tab listo para usar.
    """
    tramites = _cargar_tramites()

    with gr.Tab("📋 Trámites") as tab_bloque:
        gr.Markdown("## Guía de Trámites Académicos")
        gr.Markdown(
            "Consulta el paso a paso para los trámites más frecuentes de la "
            "Universidad de Antioquia. Haz clic en cada trámite para expandir."
        )

        if not tramites:
            gr.Markdown(
                "⚠️ No se pudieron cargar los trámites. "
                "Verifica que el archivo `data/tramites/tramites.json` exista."
            )
        else:
            for tramite in tramites:
                nombre = tramite.get("nombre", "Trámite sin nombre")
                categoria = tramite.get("categoria", "")
                titulo_accordion = f"📄 {nombre}"
                if categoria:
                    titulo_accordion += f"  —  *{categoria}*"

                with gr.Accordion(titulo_accordion, open=False):
                    contenido_md = _formatear_tramite(tramite)
                    gr.Markdown(contenido_md)

        gr.Markdown(
            "---\n*Para trámites no listados, visita el "
            "[Portal Universitario](https://portaludea.udea.edu.co) "
            "o contacta Registro y Control Académico.*"
        )

    return tab_bloque
