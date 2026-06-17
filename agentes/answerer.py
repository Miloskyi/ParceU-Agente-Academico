"""
agentes/answerer.py
-------------------
Nodo Answerer del grafo LangGraph para el Copiloto Administrativo UdeA.

Responsabilidades:
  1. Construir el contexto combinando todas las fuentes disponibles del Estado:
     documentos_rag, tramite_guia, pasos_tramite, fechas_relevantes, documentos_web.
  2. Llamar a Groq (llama-3.3-70b-versatile, gratuito) con un prompt de sistema fijo
     y el contexto + pregunta del usuario.
  3. Extraer las fuentes citadas en la respuesta mediante regex.
  4. Retornar respuesta_candidata, fuentes_citadas y agente_usado.

Uso:
    from agentes.answerer import answerer_node
"""

import re
from typing import List

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from agentes.estado import EstadoCopiloto
from utils.formateador import formatear_cita, formatear_pasos, formatear_fechas
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Modelo LLM (lazy — se inicializa en la primera llamada)
# ---------------------------------------------------------------------------

_llm = None

def _get_llm():
    """Retorna el cliente Groq, inicializándolo la primera vez que se necesita."""
    global _llm
    if _llm is None:
        _llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    return _llm

# ---------------------------------------------------------------------------
# Prompt de sistema fijo
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """Eres el Copiloto Administrativo de la Universidad de Antioquia, Facultad de Ingeniería.

REGLA PRINCIPAL: Responde SIEMPRE con el siguiente formato estructurado en Markdown. Sin excepciones.

---

## 📌 Respuesta

[Respuesta directa y concisa a la pregunta en 2-4 oraciones. Sin relleno.]

## 📋 Detalle

[Explicación amplia si es necesaria. Listas con `-` para enumeraciones.
Para trámites: lista numerada `1.` para los pasos.]

## 📄 Fuentes

[Una línea por fuente: `• Fuente: X, Artículo Y, pág. Z — modificado: DD/MM/YYYY`
Si no hay fecha, omite ese campo. Si no hay fuentes, omite esta sección.]

## 🏛️ ¿Dónde acudir?

[Solo si aplica. Oficina y contacto. Omite si no es relevante.]

---

REGLAS ESTRICTAS:
1. Usa SOLO las secciones que aplican. Omite secciones vacías.
2. NO repitas la pregunta del usuario.
3. NO uses frases de relleno ("Espero haberte ayudado", "No dudes en consultar").
4. Cita siempre con fecha cuando el contexto la incluya: `(Fuente: X, Artículo Y, modificado: DD/MM/YYYY)`.
5. Si no tienes información responde: "## 📌 Respuesta\\n\\nNo encontré información sobre este tema. Contacta **registro@udea.edu.co** o llama al **(604) 219 5555**."
6. Adapta el vocabulario al perfil: pregrado=simple, posgrado=técnico, docente=reglamentario.
"""

# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------


def _construir_contexto(estado: EstadoCopiloto) -> str:
    """
    Construye el bloque de contexto para el HumanMessage combinando todas
    las fuentes disponibles en el Estado.

    Args:
        estado: Estado actual del grafo.

    Returns:
        String con el contexto estructurado listo para enviar al LLM.
    """
    secciones: List[str] = []

    # --- 1. Documentos RAG ---
    documentos_rag = estado.get("documentos_rag", [])
    if documentos_rag:
        secciones.append("### DOCUMENTOS NORMATIVOS (ChromaDB)")
        for i, doc in enumerate(documentos_rag, start=1):
            fuente = doc.get("documento", doc.get("fuente", "Documento desconocido"))
            articulo = doc.get("articulo", "")
            pagina = doc.get("pagina", None)
            texto = doc.get("texto", doc.get("contenido", ""))
            relevancia = doc.get("relevancia", doc.get("score", ""))
            fecha_mod = doc.get("fecha_modificacion", "")

            cita = formatear_cita(fuente, articulo if articulo else None, pagina if pagina else None)
            fecha_str = f" | Última modificación: {fecha_mod}" if fecha_mod and fecha_mod != "Fecha no disponible" else ""
            secciones.append(
                f"[Fragmento {i}] {cita}{fecha_str}\n"
                f"Relevancia: {relevancia}\n"
                f"Contenido: {texto}"
            )

    # --- 2. Trámite guía ---
    tramite_guia = estado.get("tramite_guia")
    if tramite_guia:
        nombre = tramite_guia.get("nombre", "")
        descripcion = tramite_guia.get("descripcion", "")
        oficina = tramite_guia.get("oficina", "")
        tiempo = tramite_guia.get("tiempo_estimado", "")
        costo = tramite_guia.get("costo", "")
        url = tramite_guia.get("url_oficial", "")
        docs_requeridos = tramite_guia.get("documentos_requeridos", [])
        advertencias = tramite_guia.get("advertencias", [])

        secciones.append(f"### TRÁMITE: {nombre}")
        secciones.append(f"Descripción: {descripcion}")
        if oficina:
            secciones.append(f"Oficina: {oficina}")
        if tiempo:
            secciones.append(f"Tiempo estimado: {tiempo}")
        if costo:
            secciones.append(f"Costo: {costo}")
        if url:
            secciones.append(f"URL oficial: {url}")
        if docs_requeridos:
            secciones.append("Documentos requeridos: " + ", ".join(docs_requeridos))
        if advertencias:
            secciones.append("Advertencias: " + " | ".join(advertencias))

    # --- 3. Pasos del trámite ---
    pasos_tramite = estado.get("pasos_tramite", [])
    if pasos_tramite:
        pasos_formateados = formatear_pasos(pasos_tramite)
        secciones.append("### PASOS DEL TRÁMITE")
        secciones.append(pasos_formateados)

    # --- 4. Fechas relevantes ---
    fechas_relevantes = estado.get("fechas_relevantes", [])
    if fechas_relevantes:
        fechas_formateadas = formatear_fechas(fechas_relevantes)
        secciones.append("### FECHAS ACADÉMICAS RELEVANTES")
        secciones.append(fechas_formateadas)

    # --- 5. Documentos web ---
    documentos_web = estado.get("documentos_web", [])
    if documentos_web:
        secciones.append("### INFORMACIÓN WEB (portal normativa UdeA)")
        for i, doc in enumerate(documentos_web, start=1):
            contenido = doc.get("contenido", "")
            url = doc.get("url", "")
            secciones.append(f"[Web {i}] Fuente: {url}\n{contenido}")

    if not secciones:
        return "(No hay información de contexto disponible para esta consulta.)"

    return "\n\n".join(secciones)


def _extraer_fuentes_citadas(texto_respuesta: str) -> List[str]:
    """
    Extrae todas las citas en formato (Fuente: ...) del texto de la respuesta.

    Busca el patrón: (Fuente: X, ...) o (Fuente: X)

    Args:
        texto_respuesta: Texto completo de la respuesta generada.

    Returns:
        Lista de strings únicos con las citas encontradas.
    """
    patron = r"\(Fuente:[^)]+\)"
    coincidencias = re.findall(patron, texto_respuesta)
    # Deduplicar manteniendo orden de aparición
    vistas = set()
    unicas = []
    for cita in coincidencias:
        cita_norm = cita.strip()
        if cita_norm not in vistas:
            vistas.add(cita_norm)
            unicas.append(cita_norm)
    return unicas


def _determinar_agente_usado(estado: EstadoCopiloto) -> str:
    """
    Determina el identificador del agente principal usado según qué campos
    del Estado contienen datos.

    Prioridad:
      1. es_urgente=True → "urgency_agent"
      2. tramite_guia con datos → "tramite_agent"
      3. documentos_rag con datos → "rag_agent"
      4. documentos_web con datos → "search_agent"
      5. Sin datos → "answerer_sin_contexto"

    Args:
        estado: Estado actual del grafo.

    Returns:
        String con el nombre del agente principal.
    """
    if estado.get("es_urgente", False):
        return "urgency_agent"

    if estado.get("tramite_guia"):
        return "tramite_agent"

    if estado.get("documentos_rag"):
        return "rag_agent"

    if estado.get("documentos_web"):
        return "search_agent"

    return "answerer_sin_contexto"


# ---------------------------------------------------------------------------
# Nodo principal del grafo
# ---------------------------------------------------------------------------


def answerer_node(estado: EstadoCopiloto) -> dict:
    """
    Nodo Answerer del grafo LangGraph.

    Flujo:
      1. Construye el contexto combinando todas las fuentes del Estado.
      2. Extrae la pregunta del último mensaje humano.
      3. Llama a Claude con SystemMessage (prompt fijo) + HumanMessage (contexto + pregunta).
         Si es_urgente=True, antepone ⚠️ ATENCIÓN y los contactos de emergencia al prompt.
      4. Extrae las fuentes citadas con regex del texto de la respuesta.
      5. Determina el agente_usado según los campos con datos en el Estado.
      6. Retorna respuesta_candidata, fuentes_citadas y agente_usado.

    Si ocurre cualquier excepción, retorna un mensaje de fallback seguro.

    Args:
        estado: Estado actual del grafo.

    Returns:
        Dict con: respuesta_candidata, fuentes_citadas, agente_usado.
    """
    try:
        # --- 1. Extraer la pregunta del último mensaje humano ---
        mensajes = estado.get("mensajes", [])
        pregunta = ""
        for msg in reversed(mensajes):
            if hasattr(msg, "type"):
                if msg.type == "human":
                    pregunta = msg.content
                    break
            elif isinstance(msg, dict):
                if msg.get("type") == "human" or msg.get("role") == "user":
                    pregunta = msg.get("content", "")
                    break

        if not pregunta:
            pregunta = estado.get("pregunta_reformulada", "")

        logger.info("Answerer: procesando respuesta para consulta (%d caracteres)", len(pregunta))

        # --- 2. Construir el contexto ---
        contexto = _construir_contexto(estado)
        perfil = estado.get("perfil_usuario", "pregrado")
        es_urgente = estado.get("es_urgente", False)

        # --- 3. Construir el HumanMessage ---
        prefijo_urgencia = ""
        if es_urgente:
            nivel = estado.get("nivel_urgencia", "alto")
            prefijo_urgencia = (
                f"⚠️ ATENCIÓN: Esta consulta ha sido marcada como URGENTE (nivel: {nivel}).\n"
                "Debes iniciar tu respuesta con '⚠️ ATENCIÓN' y proporcionar inmediatamente "
                "los contactos de emergencia relevantes antes de dar la información solicitada.\n\n"
                "CONTACTOS DE EMERGENCIA A INCLUIR:\n"
                "- Secretaría Académica Ingeniería: secretaria.ingenieria@udea.edu.co\n"
                "- División de Registro: registro@udea.edu.co\n"
                "- Bienestar Universitario: bienestar@udea.edu.co\n"
                "- Línea UdeA: (604) 219 5555\n"
                "- Línea de crisis/salud mental: 106 (línea nacional Colombia)\n\n"
            )

        human_content = (
            f"{prefijo_urgencia}"
            f"PERFIL DEL USUARIO: {perfil}\n\n"
        )

        # Inyectar memoria conversacional si existe
        memoria = estado.get("memoria_resumen", "").strip()
        if memoria:
            human_content += f"CONTEXTO DE CONVERSACIÓN PREVIA:\n{memoria}\n\n"

        # Plan del supervisor
        plan = estado.get("plan_agentes", [])
        complejidad = estado.get("complejidad", "simple")
        if plan:
            human_content += f"[Supervisor: complejidad='{complejidad}', agentes activados={plan}]\n\n"

        human_content += (
            f"CONTEXTO DISPONIBLE:\n{contexto}\n\n"
            f"PREGUNTA DEL USUARIO:\n{pregunta}"
        )

        mensajes_llm = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=human_content),
        ]

        # --- 4. Llamar al LLM ---
        logger.info("Answerer: invocando Groq llama-3.3-70b-versatile...")
        respuesta_llm = _get_llm().invoke(mensajes_llm)
        texto_respuesta = respuesta_llm.content

        logger.info(
            "Answerer: respuesta generada (%d caracteres)", len(texto_respuesta)
        )
        logger.debug("Answerer: respuesta: %s", texto_respuesta[:300])

        # --- 5. Extraer fuentes citadas ---
        fuentes_citadas = _extraer_fuentes_citadas(texto_respuesta)
        logger.info("Answerer: %d fuente(s) citada(s) en la respuesta", len(fuentes_citadas))

        # --- 6. Determinar agente_usado ---
        agente_usado = _determinar_agente_usado(estado)
        logger.info("Answerer: agente_usado='%s'", agente_usado)

        # --- 7. Agregar disclaimer si verificación anterior falló ---
        alertas_prev = estado.get("alertas_verificacion", [])
        if alertas_prev:
            disclaimer = (
                "\n\n---\n⚠️ *Nota de verificación: Algunas afirmaciones de esta respuesta "
                "no pudieron ser confirmadas directamente en los documentos disponibles. "
                "Te recomiendo verificar con la oficina correspondiente antes de tomar decisiones.*"
            )
            texto_respuesta += disclaimer
            logger.info("Answerer: disclaimer de verificación agregado (%d alertas previas)", len(alertas_prev))

        return {
            "respuesta_candidata": texto_respuesta,
            "fuentes_citadas": fuentes_citadas,
            "agente_usado": agente_usado,
        }

    except Exception as exc:
        logger.error("Answerer: error inesperado: %s", exc, exc_info=True)
        return {
            "respuesta_candidata": (
                "Lo siento, ocurrió un error al generar la respuesta. "
                "Por favor, intenta de nuevo. Si el problema persiste, "
                "contacta a la División de Registro: registro@udea.edu.co "
                "o llama a la Línea UdeA: (604) 219 5555."
            ),
            "fuentes_citadas": [],
            "agente_usado": "error",
        }
