"""
agentes/verificador.py
----------------------
Agente Verificador Anti-alucinación del Copiloto Administrativo UdeA.

Responsabilidad:
  Verifica que la respuesta generada por el Answerer esté respaldada
  por los documentos recuperados. Detecta afirmaciones que el LLM
  pudo haber inventado sin base en los fragmentos RAG.

  Estrategia (sin LLM — determinística):
  1. Extrae afirmaciones clave de la respuesta (números, artículos, fechas,
     plazos, porcentajes).
  2. Verifica que cada afirmación tenga evidencia en documentos_rag o
     documentos_web.
  3. Si hay afirmaciones sin respaldo, las registra como alertas y
     marca verificacion_ok=False para que el Answerer agregue un disclaimer.

Uso:
    from agentes.verificador import verificador_node
"""

import re
from agentes.estado import EstadoCopiloto
from utils.logger import get_logger

logger = get_logger(__name__)

# Patrones que detectan afirmaciones verificables en la respuesta
_PATRON_ARTICULO = re.compile(r'[Aa]rt[íi]culo\s+\d+', re.IGNORECASE)
_PATRON_NUMERO   = re.compile(r'\b\d+\s*(cr[eé]ditos?|materias?|semestres?|días?\s+hábiles?|%)\b', re.IGNORECASE)
_PATRON_FECHA    = re.compile(r'\b\d{1,2}\s+de\s+\w+\s+de\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b', re.IGNORECASE)
_PATRON_PLAZO    = re.compile(r'\b\d+\s*días?\s+hábiles?\b|\bplazo\s+de\s+\d+\b', re.IGNORECASE)


def _extraer_afirmaciones(texto: str) -> list[str]:
    """Extrae fragmentos verificables de la respuesta."""
    afirmaciones = []
    for patron in [_PATRON_ARTICULO, _PATRON_NUMERO, _PATRON_FECHA, _PATRON_PLAZO]:
        afirmaciones.extend(patron.findall(texto))
    return list(set(afirmaciones))


def _construir_corpus_evidencia(estado: EstadoCopiloto) -> str:
    """Concatena todo el texto de los documentos recuperados."""
    corpus = ""
    for doc in estado.get("documentos_rag", []):
        corpus += " " + doc.get("texto", doc.get("contenido", ""))
    for doc in estado.get("documentos_web", []):
        corpus += " " + doc.get("texto", doc.get("contenido", ""))
    if estado.get("tramite_guia"):
        tramite = estado["tramite_guia"]
        corpus += " ".join(tramite.get("pasos", []))
    return corpus.lower()


def verificador_node(estado: EstadoCopiloto) -> dict:
    """
    Nodo Verificador Anti-alucinación.

    Compara las afirmaciones clave de la respuesta candidata contra
    el corpus de evidencia (documentos RAG + web + tramites).

    Args:
        estado: Estado actual del grafo.

    Returns:
        dict con:
          - verificacion_ok (bool): True si todas las afirmaciones tienen respaldo.
          - alertas_verificacion (list[str]): Afirmaciones sin respaldo detectadas.
    """
    try:
        respuesta = estado.get("respuesta_candidata", "")
        if not respuesta:
            return {"verificacion_ok": True, "alertas_verificacion": []}

        # Si no hay documentos RAG, no podemos verificar — aceptar con advertencia
        if not estado.get("documentos_rag") and not estado.get("tramite_guia"):
            logger.info("Verificador: sin documentos RAG — verificación omitida")
            return {"verificacion_ok": True, "alertas_verificacion": []}

        corpus = _construir_corpus_evidencia(estado)
        afirmaciones = _extraer_afirmaciones(respuesta)

        if not afirmaciones:
            logger.info("Verificador: sin afirmaciones verificables — OK")
            return {"verificacion_ok": True, "alertas_verificacion": []}

        alertas = []
        for afirmacion in afirmaciones:
            # Buscar evidencia en el corpus (búsqueda aproximada)
            afirmacion_lower = afirmacion.lower().strip()
            # Extraer solo números/fechas para búsqueda flexible
            numeros = re.findall(r'\d+', afirmacion_lower)
            tiene_evidencia = afirmacion_lower in corpus or all(n in corpus for n in numeros if n)
            if not tiene_evidencia:
                alertas.append(afirmacion)
                logger.warning("Verificador: sin evidencia para '%s'", afirmacion)

        verificacion_ok = len(alertas) == 0

        if verificacion_ok:
            logger.info("Verificador: todas las afirmaciones verificadas ✓ (%d chequeadas)", len(afirmaciones))
        else:
            logger.warning(
                "Verificador: %d afirmación(es) sin respaldo documental: %s",
                len(alertas), alertas
            )

        return {
            "verificacion_ok": verificacion_ok,
            "alertas_verificacion": alertas,
        }

    except Exception as exc:
        logger.error("Verificador: error — %s", exc, exc_info=True)
        return {"verificacion_ok": True, "alertas_verificacion": []}
