"""
interfaz/componentes/chat.py
----------------------------
Tab de Chat Principal para el Copiloto Administrativo UdeA.
Compatible con Gradio 6.x
"""

from __future__ import annotations

import gradio as gr
from langchain_core.messages import HumanMessage

from utils.logger import get_logger

logger = get_logger(__name__)

PERFILES = [
    "Estudiante Pregrado",
    "Estudiante Posgrado",
    "Docente",
    "Personal Administrativo",
]

MAPEO_PERFILES = {
    "Estudiante Pregrado": "pregrado",
    "Estudiante Posgrado": "posgrado",
    "Docente": "docente",
    "Personal Administrativo": "administrativo",
}

PREGUNTAS_EJEMPLO = [
    "¿Cuántas materias puedo cancelar sin perder el cupo?",
    "¿Qué documentos necesito para inscribir trabajo de grado?",
    "Quedé en prueba académica, ¿qué hago?",
    "¿Cuál es la fecha límite de matrícula este semestre?",
    "¿Cómo solicito una transferencia interna?",
    "¿Cómo solicito un certificado de notas?",
    "¿Cuáles son los requisitos para una beca socioeconómica?",
    "¿Cómo interpongo un recurso de reposición?",
]

TEXTO_ALERTA_URGENTE = (
    "⚠️ **Caso urgente detectado.** Esta situación puede afectar tu continuidad "
    "académica. Contacta: secretaria.ingenieria@udea.edu.co | (604) 219 5555 | "
    "Línea crisis: 106"
)


def crear_tab_chat(app_grafo, registrar_consulta_fn=None):
    """Crea el tab de chat compatible con Gradio 6."""

    with gr.Tab("💬 Consulta") as tab_bloque:
        gr.Markdown("## Copiloto Administrativo — Facultad de Ingeniería UdeA")
        gr.Markdown("Selecciona tu perfil y escribe tu consulta académica o administrativa.")

        selector_perfil = gr.Dropdown(
            choices=PERFILES,
            value="Estudiante Pregrado",
            label="Tu perfil",
            interactive=True,
        )

        # Gradio 6: historial como lista de tuplas (user_msg, bot_msg)
        chatbot = gr.Chatbot(height=450, label="Conversación")

        with gr.Row():
            entrada_texto = gr.Textbox(
                placeholder="Escribe tu pregunta aquí...",
                lines=2,
                scale=4,
                show_label=False,
                container=False,
            )
            boton_enviar = gr.Button("Enviar →", variant="primary", scale=1)

        alerta_urgente = gr.Markdown(value="", visible=False)
        fuentes_md = gr.Markdown(value="")

        gr.Examples(
            examples=[[p] for p in PREGUNTAS_EJEMPLO],
            inputs=[entrada_texto],
            label="Preguntas frecuentes — haz clic para usar",
            examples_per_page=8,
        )

        boton_nueva = gr.Button("🔄 Nueva conversación", variant="secondary")

        # ── Funciones de callback ────────────────────────────────────────────

        def _enviar(mensaje: str, historial: list, perfil: str):
            """Invoca el grafo y actualiza el chatbot."""
            if not mensaje or not mensaje.strip():
                return historial, "", False, ""

            perfil_interno = MAPEO_PERFILES.get(perfil, "pregrado")

            try:
                resultado = app_grafo.invoke({
                    "mensajes": [HumanMessage(content=mensaje)],
                    "perfil_usuario": perfil_interno,
                    "intentos": 0,
                    "documentos_rag": [],
                    "documentos_web": [],
                    "es_urgente": False,
                })
                respuesta   = resultado.get("respuesta_candidata", "") or "Sin respuesta disponible."
                es_urgente  = bool(resultado.get("es_urgente", False))
                fuentes     = resultado.get("fuentes_citadas", [])
                agente_usado = resultado.get("agente_usado", "")
                intencion   = resultado.get("intencion", "")
                calidad     = resultado.get("calidad", "")

            except Exception as exc:
                logger.error("Error al invocar el grafo: %s", exc, exc_info=True)
                respuesta    = "⚠️ Error al procesar tu consulta. Intenta de nuevo."
                es_urgente   = False
                fuentes      = []
                agente_usado = "error"
                intencion    = ""
                calidad      = ""

            # Gradio 6.18 requiere formato messages: lista de dicts {role, content}
            historial = list(historial or [])
            historial.append({"role": "user", "content": mensaje})
            historial.append({"role": "assistant", "content": respuesta})

            # Fuentes
            texto_fuentes = ""
            if fuentes:
                texto_fuentes = "**📄 Fuentes:**\n" + "\n".join(f"- {f}" for f in fuentes)

            # Registrar analytics
            if registrar_consulta_fn:
                try:
                    registrar_consulta_fn(
                        intencion=intencion,
                        perfil_usuario=perfil_interno,
                        calidad_final=calidad,
                        agente_usado=agente_usado,
                        es_urgente=es_urgente,
                    )
                except Exception:
                    pass

            alerta_texto = TEXTO_ALERTA_URGENTE if es_urgente else ""
            return historial, texto_fuentes, es_urgente, alerta_texto

        def _limpiar():
            return [], "", False, ""

        # ── Eventos ──────────────────────────────────────────────────────────

        def _on_enviar(mensaje, historial, perfil):
            h, f, urgente, alerta = _enviar(mensaje, historial, perfil)
            return h, "", f, gr.update(visible=urgente, value=alerta)

        def _on_limpiar():
            return [], "", gr.update(visible=False, value="")

        boton_enviar.click(
            fn=_on_enviar,
            inputs=[entrada_texto, chatbot, selector_perfil],
            outputs=[chatbot, entrada_texto, fuentes_md, alerta_urgente],
        )

        entrada_texto.submit(
            fn=_on_enviar,
            inputs=[entrada_texto, chatbot, selector_perfil],
            outputs=[chatbot, entrada_texto, fuentes_md, alerta_urgente],
        )

        boton_nueva.click(
            fn=_on_limpiar,
            inputs=[],
            outputs=[chatbot, fuentes_md, alerta_urgente],
        )

    return tab_bloque, chatbot
