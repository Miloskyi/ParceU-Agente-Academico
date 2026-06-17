"""
interfaz/estilos.py
-------------------
Constantes de estilos visuales para la interfaz del Copiloto Administrativo UdeA.

Proporciona el CSS personalizado con la paleta institucional de la Universidad
de Antioquia y el HTML del encabezado de la aplicación.

Uso:
    from interfaz.estilos import CSS_UDEA, CABECERA_HTML

    with gr.Blocks(css=CSS_UDEA) as demo:
        gr.HTML(CABECERA_HTML)
        ...
"""

# ---------------------------------------------------------------------------
# CSS — Paleta institucional UdeA
# ---------------------------------------------------------------------------

CSS_UDEA = """
:root {
    --azul: #003087;
    --amarillo: #FFD100;
    --rojo: #E8401C;
    --gris: #F5F7FA;
    --texto: #1A1A1A;
}
.gradio-container { font-family: 'Segoe UI', sans-serif !important; }
.header-udea {
    background: var(--azul);
    color: white;
    padding: 18px 32px;
    border-radius: 10px;
    margin-bottom: 12px;
    border-left: 6px solid var(--amarillo);
}
.alerta-urgente {
    background: #FFF3CD;
    border-left: 4px solid #E8401C;
    padding: 10px 16px;
    border-radius: 0 8px 8px 0;
    margin: 8px 0;
}
.fuentes-box {
    background: #EEF4FF;
    border-left: 3px solid var(--azul);
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    font-size: 13px;
}
"""

# ---------------------------------------------------------------------------
# HTML — Cabecera de la aplicación
# ---------------------------------------------------------------------------

CABECERA_HTML = """
<div class="header-udea">
  <h1 style="margin:0; font-size:20px; font-weight:700;">
    🎓 Copiloto Administrativo — Facultad de Ingeniería
  </h1>
  <p style="margin:4px 0 0; font-size:13px; opacity:0.85;">
    Universidad de Antioquia · Información basada en normativa oficial ·
    <strong>Solo orientativo</strong> — consulta oficinas para decisiones definitivas
  </p>
</div>
"""
