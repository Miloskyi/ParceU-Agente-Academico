"""
interfaz/app.py
---------------
Punto de entrada de la interfaz Gradio del Copiloto Administrativo UdeA.

Ensambla los cuatro tabs (Chat, Trámites, Calendario, Analytics) y
lanza la aplicación en http://0.0.0.0:7860

Uso:
    python interfaz/app.py
"""

from __future__ import annotations

import sys
import os

# Asegurar que el directorio raíz del proyecto esté en sys.path
_RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, _RAIZ_PROYECTO)

# Cargar variables de entorno desde .env ANTES de cualquier otro import
from dotenv import load_dotenv
load_dotenv(os.path.join(_RAIZ_PROYECTO, ".env"))

import gradio as gr

from interfaz.componentes.chat import crear_tab_chat
from interfaz.componentes.tramites import crear_tab_tramites
from interfaz.componentes.calendario import crear_tab_calendario
from interfaz.componentes.analytics import crear_tab_analytics, registrar_consulta
from interfaz.estilos import CSS_UDEA, CABECERA_HTML

from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# CSS adicional que extiende el de estilos.py
# ---------------------------------------------------------------------------

CSS_EXTRA = """
/* Disclaimer */
.disclaimer-box {
    background-color: #E8EDF5;
    border-left: 4px solid var(--azul);
    padding: 10px 16px;
    border-radius: 0 6px 6px 0;
    font-size: 0.85rem;
    color: #333333;
    margin-top: 8px;
}

/* Tabs */
.tab-nav button {
    color: var(--azul) !important;
    font-weight: 600;
}

.tab-nav button.selected {
    border-bottom: 3px solid var(--amarillo) !important;
    color: var(--azul) !important;
}
"""

# CSS combinado: base de estilos.py + extensiones adicionales
CSS_COMBINADO = CSS_UDEA + CSS_EXTRA

# Reutilizar el header de estilos.py
HEADER_HTML = CABECERA_HTML

DISCLAIMER_HTML = """
<div class="disclaimer-box">
    🔒 <strong>Privacidad:</strong> Este sistema no almacena el contenido de tus consultas
    ni datos personales identificables. Solo se registran metadatos estadísticos anónimos
    (intención, perfil, calidad de respuesta) para mejorar el servicio.
    Las respuestas son orientativas; para decisiones académicas formales consulta
    siempre las fuentes oficiales de la Universidad.
</div>
"""


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------


def main() -> None:
    """
    Carga el grafo de agentes y lanza la interfaz Gradio multi-pestaña.
    """
    logger.info("Iniciando Copiloto Administrativo UdeA...")

    # --- Cargar el grafo ---
    try:
        from agentes.grafo import app_grafo
        logger.info("Grafo de agentes cargado correctamente")
    except Exception as exc:
        logger.error("No se pudo cargar el grafo de agentes: %s", exc, exc_info=True)
        # Crear un grafo dummy para que la UI inicie igualmente
        app_grafo = _crear_grafo_fallback()

    # --- Construir la interfaz ---
    with gr.Blocks(title="Copiloto Administrativo UdeA") as demo:

        # Header
        gr.HTML(HEADER_HTML)

        # Tabs principales
        crear_tab_chat(app_grafo, registrar_consulta_fn=registrar_consulta)
        crear_tab_tramites()
        crear_tab_calendario()
        crear_tab_analytics(obtener_datos_fn=None)  # usa registro interno

        # Disclaimer de privacidad
        gr.HTML(DISCLAIMER_HTML)

    logger.info("Lanzando servidor en http://0.0.0.0:7860")
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        css=CSS_COMBINADO,
    )


def _crear_grafo_fallback():
    """
    Crea un objeto que simula el grafo cuando no se puede cargar el real.
    Retorna un mensaje de error genérico ante cualquier invoke.
    """

    class GrafoFallback:
        def invoke(self, estado: dict) -> dict:
            return {
                "respuesta_candidata": (
                    "⚠️ El motor de IA no está disponible en este momento. "
                    "Por favor verifica la configuración del servidor y que las "
                    "variables de entorno estén correctamente definidas (.env)."
                ),
                "es_urgente": False,
                "fuentes_citadas": [],
                "agente_usado": "fallback",
                "intencion": "",
                "calidad": "sin_info",
            }

    logger.warning("Usando grafo fallback — las respuestas serán limitadas")
    return GrafoFallback()


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
