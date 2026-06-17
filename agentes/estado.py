"""
agentes/estado.py
-----------------
Define el Estado central del grafo LangGraph para el Copiloto Administrativo UdeA.

El EstadoCopiloto es el objeto que viaja entre todos los nodos del grafo,
acumulando información a lo largo del flujo de procesamiento.

Uso:
    from agentes.estado import EstadoCopiloto, estado_inicial
    estado = estado_inicial()
"""

from typing import Annotated, List, Optional, TypedDict

from langgraph.graph.message import add_messages


class EstadoCopiloto(TypedDict):
    """
    Estado central del grafo de agentes.

    Todos los nodos reciben y retornan (parcialmente) este TypedDict.
    LangGraph fusiona las actualizaciones parciales con el estado acumulado.

    Campos:
        mensajes:             Historial de mensajes de la conversación (acumulativo via add_messages).
        perfil_usuario:       Perfil del usuario: pregrado | posgrado | docente | administrativo.

        intencion:            Intención clasificada: normativa | trámite | calendario | urgencia | otro.
        categoria:            Sub-categoría temática dentro de la intención.
        es_urgente:           True si la consulta contiene indicadores de urgencia.
        nivel_urgencia:       Severidad: bajo | medio | alto | critico.
        pregunta_reformulada: Versión normalizada y enriquecida de la consulta original.

        documentos_rag:       Fragmentos recuperados de ChromaDB con metadatos.
                              Cada elemento: {contenido, fuente, articulo, pagina, score}
        documentos_web:       Resultados de búsqueda web en tiempo real.
                              Cada elemento: {contenido, url}

        tramite_guia:         Trámite encontrado en tramites.json (None si no aplica).
        pasos_tramite:        Lista de pasos numerados del trámite seleccionado.

        fechas_relevantes:    Fechas académicas identificadas.
                              Cada elemento: {evento, fecha, periodo}

        respuesta_candidata:  Respuesta generada por el Answerer, pendiente de evaluación.
        fuentes_citadas:      Lista de strings con las citas incluidas en la respuesta.
        agente_usado:         Nombre del agente que proveyó los documentos principales.

        calidad:              Evaluación del Grader: aceptable | mejorar | sin_info.
        intentos:             Número de veces que el Grader ha evaluado en este ciclo.
    """

    # --- Conversación ---
    mensajes: Annotated[list, add_messages]
    perfil_usuario: str  # pregrado | posgrado | docente | administrativo

    # --- Clasificación ---
    intencion: str       # normativa | trámite | calendario | urgencia | otro
    categoria: str
    es_urgente: bool
    nivel_urgencia: str  # bajo | medio | alto | critico
    pregunta_reformulada: str

    # --- Documentos recuperados ---
    documentos_rag: List[dict]   # {contenido, fuente, articulo, pagina, score}
    documentos_web: List[dict]   # {contenido, url}

    # --- Trámites ---
    tramite_guia: Optional[dict]
    pasos_tramite: List[str]

    # --- Calendario ---
    fechas_relevantes: List[dict]  # {evento, fecha, periodo}

    # --- Generación ---
    respuesta_candidata: str
    fuentes_citadas: List[str]
    agente_usado: str

    # --- Control de calidad ---
    calidad: str   # aceptable | mejorar | sin_info
    intentos: int

    # --- Memoria conversacional ---
    memoria_resumen: str         # Resumen acumulativo del historial de la sesión
    turno: int                   # Número de turno en la conversación

    # --- Verificación anti-alucinación ---
    verificacion_ok: bool        # True si el verificador aprobó la respuesta
    alertas_verificacion: List[str]  # Afirmaciones sin respaldo en documentos

    # --- Supervisor ---
    plan_agentes: List[str]      # Secuencia de agentes que el supervisor decidió activar
    complejidad: str             # "simple" | "media" | "compleja"


def estado_inicial() -> dict:
    """
    Retorna un diccionario con valores por defecto seguros para iniciar
    una nueva sesión del grafo.

    Los campos con tipo lista se inicializan como listas vacías,
    los booleanos como False, los strings como "" y los enteros como 0.
    Los campos Optional se inicializan como None.

    Returns:
        dict con todos los campos de EstadoCopiloto en sus valores por defecto.

    Example:
        >>> estado = estado_inicial()
        >>> estado["intentos"]
        0
        >>> estado["es_urgente"]
        False
        >>> estado["documentos_rag"]
        []
    """
    return {
        # Conversación
        "mensajes": [],
        "perfil_usuario": "",

        # Clasificación
        "intencion": "",
        "categoria": "",
        "es_urgente": False,
        "nivel_urgencia": "",
        "pregunta_reformulada": "",

        # Documentos recuperados
        "documentos_rag": [],
        "documentos_web": [],

        # Trámites
        "tramite_guia": None,
        "pasos_tramite": [],

        # Calendario
        "fechas_relevantes": [],

        # Generación
        "respuesta_candidata": "",
        "fuentes_citadas": [],
        "agente_usado": "",

        # Control de calidad
        "calidad": "",
        "intentos": 0,

        # Memoria conversacional
        "memoria_resumen": "",
        "turno": 0,

        # Verificación anti-alucinación
        "verificacion_ok": True,
        "alertas_verificacion": [],

        # Supervisor
        "plan_agentes": [],
        "complejidad": "simple",
    }
