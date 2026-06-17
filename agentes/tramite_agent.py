"""
agentes/tramite_agent.py
------------------------
Agente especializado en orientación paso a paso para trámites administrativos
de la Universidad de Antioquia.

Carga el catálogo de trámites desde `tramites.json` y selecciona el trámite
más relevante para la consulta del usuario mediante coincidencia de keywords.

Uso:
    from agentes.tramite_agent import tramite_agent_node
    resultado = tramite_agent_node(estado)
"""

import json
import os
from pathlib import Path
from typing import Optional

from agentes.estado import EstadoCopiloto
from utils.logger import get_logger

logger = get_logger(__name__)

# Ruta por defecto del catálogo de trámites
_RUTA_DEFECTO = "./data/tramites/tramites.json"


def _cargar_tramites() -> dict:
    """
    Carga el catálogo de trámites desde el archivo JSON.

    La ruta del archivo se determina mediante la variable de entorno
    ``TRAMITES_PATH``. Si la variable no está definida, se usa la ruta
    por defecto ``./data/tramites/tramites.json``.

    Returns:
        dict con la clave ``"tramites"`` conteniendo la lista de trámites.

    Raises:
        FileNotFoundError: Si el archivo no existe en la ruta configurada.
        json.JSONDecodeError: Si el contenido del archivo no es JSON válido.

    Example:
        >>> datos = _cargar_tramites()
        >>> isinstance(datos["tramites"], list)
        True
    """
    ruta_str = os.getenv("TRAMITES_PATH", _RUTA_DEFECTO)
    ruta = Path(ruta_str)

    if not ruta.exists():
        logger.error(
            "No se encontró el archivo de trámites en la ruta: %s", ruta.resolve()
        )
        raise FileNotFoundError(
            f"Archivo tramites.json no encontrado en: {ruta.resolve()}"
        )

    logger.info("Cargando trámites desde: %s", ruta.resolve())
    contenido = ruta.read_text(encoding="utf-8")
    datos = json.loads(contenido)

    logger.info("Trámites cargados: %d trámites disponibles", len(datos.get("tramites", [])))
    return datos


def _buscar_tramite_relevante(tramites: list, pregunta: str) -> tuple[Optional[dict], int]:
    """
    Encuentra el trámite con mayor puntuación de coincidencia de keywords.

    Por cada trámite suma 1 punto por cada keyword que aparezca como
    subcadena en la versión en minúsculas de la pregunta.

    Args:
        tramites: Lista de trámites cargados del JSON.
        pregunta:  Texto de la consulta del usuario.

    Returns:
        Tupla (tramite_seleccionado, puntuacion_maxima).
        Si ningún trámite alcanza puntuación > 0, retorna (None, 0).
    """
    pregunta_lower = pregunta.lower()
    mejor_tramite: Optional[dict] = None
    mejor_puntuacion = 0

    for tramite in tramites:
        puntuacion = 0
        for keyword in tramite.get("keywords", []):
            if keyword.lower() in pregunta_lower:
                puntuacion += 1

        logger.debug(
            "Trámite '%s' — puntuación: %d", tramite.get("nombre", "?"), puntuacion
        )

        if puntuacion > mejor_puntuacion:
            mejor_puntuacion = puntuacion
            mejor_tramite = tramite

    return mejor_tramite, mejor_puntuacion


def tramite_agent_node(estado: EstadoCopiloto) -> dict:
    """
    Nodo del grafo LangGraph que guía al usuario en trámites administrativos.

    Flujo:
    1. Carga el catálogo de trámites desde ``tramites.json``.
    2. Extrae la pregunta del último mensaje del usuario.
    3. Calcula la puntuación de coincidencia de keywords para cada trámite.
    4. Si la puntuación máxima > 0, retorna el trámite más relevante con sus
       pasos y marca ``agente_usado = "tramite"``.
    5. Si ningún trámite coincide, retorna valores vacíos y marca
       ``agente_usado = "tramite_sin_match"`` para que el flujo pueda
       derivar al RAG_Agent.

    Args:
        estado: Estado actual del grafo con los mensajes de la conversación.

    Returns:
        dict parcial con las claves:
        - ``tramite_guia`` (dict | None): Trámite seleccionado o None.
        - ``pasos_tramite`` (list[str]): Lista de pasos del trámite o [].
        - ``agente_usado`` (str): ``"tramite"`` o ``"tramite_sin_match"``.

    Example:
        >>> from agentes.estado import estado_inicial
        >>> from langchain_core.messages import HumanMessage
        >>> estado = estado_inicial()
        >>> estado["mensajes"] = [HumanMessage(content="¿Cómo cancelo una materia?")]
        >>> resultado = tramite_agent_node(estado)
        >>> resultado["agente_usado"]
        'tramite'
        >>> resultado["tramite_guia"]["nombre"]
        'Cancelación de Materias'
    """
    try:
        # --- 1. Extraer la pregunta del último mensaje ---
        mensajes = estado.get("mensajes", [])
        if mensajes:
            pregunta = mensajes[-1].content
        else:
            pregunta = estado.get("pregunta_reformulada", "")

        logger.info("Tramite_Agent procesando consulta: '%s'", pregunta[:100])

        # --- 2. Cargar catálogo de trámites ---
        datos = _cargar_tramites()
        tramites = datos.get("tramites", [])

        if not tramites:
            logger.warning("El archivo tramites.json no contiene trámites definidos.")
            return {
                "tramite_guia": None,
                "pasos_tramite": [],
                "agente_usado": "tramite_sin_match",
            }

        # --- 3. Buscar trámite más relevante ---
        tramite_seleccionado, puntuacion = _buscar_tramite_relevante(tramites, pregunta)

        # --- 4. Retornar resultado según puntuación ---
        if puntuacion > 0 and tramite_seleccionado is not None:
            logger.info(
                "Trámite encontrado: '%s' (puntuación=%d)",
                tramite_seleccionado.get("nombre"),
                puntuacion,
            )
            return {
                "tramite_guia": tramite_seleccionado,
                "pasos_tramite": tramite_seleccionado.get("pasos", []),
                "agente_usado": "tramite",
            }
        else:
            logger.info(
                "No se encontró trámite relevante para la consulta (puntuación=0)."
            )
            return {
                "tramite_guia": None,
                "pasos_tramite": [],
                "agente_usado": "tramite_sin_match",
            }

    except FileNotFoundError as exc:
        logger.error("Error al cargar tramites.json: %s", exc)
        return {
            "tramite_guia": None,
            "pasos_tramite": [],
            "agente_usado": "tramite_sin_match",
        }
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Error inesperado en tramite_agent_node: %s", exc, exc_info=True)
        return {
            "tramite_guia": None,
            "pasos_tramite": [],
            "agente_usado": "tramite_sin_match",
        }
