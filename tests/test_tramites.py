"""
tests/test_tramites.py
----------------------
Pruebas unitarias para el Tramite_Agent del Copiloto Administrativo UdeA.

Verifican que el agente encuentra el trámite correcto para las consultas
del hackathon usando solo tramites.json local (sin API keys ni red).

Ejecutar:
    pytest tests/test_tramites.py -v
"""

import os
from pathlib import Path

import pytest
from langchain_core.messages import HumanMessage

from agentes.estado import estado_inicial
from agentes.tramite_agent import tramite_agent_node

# ---------------------------------------------------------------------------
# Fixture: apuntar TRAMITES_PATH a la ruta absoluta del archivo local
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def set_tramites_path(monkeypatch):
    """
    Configura la variable de entorno TRAMITES_PATH con la ruta absoluta
    para que el agente encuentre tramites.json sin depender del directorio
    de trabajo actual.
    """
    ruta = Path(__file__).parent.parent / "data" / "tramites" / "tramites.json"
    monkeypatch.setenv("TRAMITES_PATH", str(ruta))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _estado_con_pregunta(pregunta: str) -> dict:
    """Crea un estado inicial con la pregunta del usuario como HumanMessage."""
    estado = estado_inicial()
    estado["mensajes"] = [HumanMessage(content=pregunta)]
    return estado


# ---------------------------------------------------------------------------
# Tests: trámites del hackathon
# ---------------------------------------------------------------------------

def test_cancelacion_materias_detectada():
    """
    Pregunta 1 del hackathon: cancelación de materias.
    El agente debe encontrar el trámite 'Cancelación de Materias'.
    """
    estado = _estado_con_pregunta("¿Cuántas materias puedo cancelar sin perder el cupo?")
    resultado = tramite_agent_node(estado)

    assert resultado["tramite_guia"] is not None, "Se esperaba encontrar un trámite"
    assert resultado["agente_usado"] == "tramite"
    assert "cancelaci" in resultado["tramite_guia"]["nombre"].lower()
    assert len(resultado["pasos_tramite"]) > 0


def test_inscripcion_trabajo_de_grado_detectada():
    """
    Pregunta 2 del hackathon: inscripción de trabajo de grado.
    El agente debe encontrar el trámite 'Inscripción de Trabajo de Grado'.
    """
    estado = _estado_con_pregunta("¿Qué documentos necesito para inscribir trabajo de grado?")
    resultado = tramite_agent_node(estado)

    assert resultado["tramite_guia"] is not None, "Se esperaba encontrar un trámite"
    assert resultado["agente_usado"] == "tramite"
    assert "grado" in resultado["tramite_guia"]["nombre"].lower()
    assert len(resultado["pasos_tramite"]) > 0


def test_prueba_academica_con_keywords_urgencia():
    """
    Pregunta 3 del hackathon: prueba académica.
    La frase 'prueba académica' está en PALABRAS_URGENCIA del router,
    pero para el tramite_agent lo relevante es si hay match en keywords.
    El agente puede o no encontrar un trámite (depende de keywords.json).
    Se valida que el nodo retorne siempre un dict con las claves esperadas.
    """
    estado = _estado_con_pregunta("Quedé en prueba académica, ¿qué hago?")
    resultado = tramite_agent_node(estado)

    assert "tramite_guia" in resultado
    assert "pasos_tramite" in resultado
    assert "agente_usado" in resultado
    # agente_usado puede ser 'tramite' o 'tramite_sin_match' según keywords
    assert resultado["agente_usado"] in {"tramite", "tramite_sin_match"}


def test_matricula_fecha_limite():
    """
    Pregunta 4 del hackathon: fecha límite de matrícula.
    Consulta de calendario/normativa; el tramite_agent puede o no hallar match.
    Se valida que el nodo retorne las claves esperadas correctamente.
    """
    estado = _estado_con_pregunta("¿Cuál es la fecha límite de matrícula este semestre?")
    resultado = tramite_agent_node(estado)

    assert "tramite_guia" in resultado
    assert "pasos_tramite" in resultado
    assert "agente_usado" in resultado


def test_transferencia_interna_no_match():
    """
    Pregunta 5 del hackathon: transferencia interna.
    No existe trámite de 'transferencia' en tramites.json, por lo tanto
    tramite_guia debe ser None y agente_usado debe ser 'tramite_sin_match'.
    """
    estado = _estado_con_pregunta("¿Cómo solicito una transferencia interna?")
    resultado = tramite_agent_node(estado)

    assert resultado["tramite_guia"] is None
    assert resultado["agente_usado"] == "tramite_sin_match"
    assert resultado["pasos_tramite"] == []


# ---------------------------------------------------------------------------
# Tests: sin match para consultas irrelevantes
# ---------------------------------------------------------------------------

def test_sin_match_consulta_irrelevante():
    """
    Una consulta completamente fuera de los trámites conocidos no debe
    producir ningún match: tramite_guia=None, agente_usado='tramite_sin_match'.
    """
    estado = _estado_con_pregunta("¿Cuál es la capital de Francia?")
    resultado = tramite_agent_node(estado)

    assert resultado["tramite_guia"] is None
    assert resultado["agente_usado"] == "tramite_sin_match"
    assert resultado["pasos_tramite"] == []


def test_sin_match_consulta_vacia():
    """
    Un estado sin mensajes y sin pregunta_reformulada no debe hacer crash:
    debe retornar tramite_guia=None de forma segura.
    """
    estado = estado_inicial()
    # No se agregan mensajes
    resultado = tramite_agent_node(estado)

    assert "tramite_guia" in resultado
    assert "agente_usado" in resultado


# ---------------------------------------------------------------------------
# Tests: trámites específicos del catálogo
# ---------------------------------------------------------------------------

def test_certificado_de_notas_detectado():
    """El agente debe encontrar 'Certificado de Notas' con keywords relevantes."""
    estado = _estado_con_pregunta("Necesito un certificado de notas con mi historial académico")
    resultado = tramite_agent_node(estado)

    assert resultado["tramite_guia"] is not None
    assert resultado["agente_usado"] == "tramite"
    assert "certificado" in resultado["tramite_guia"]["nombre"].lower()


def test_beca_socieconomica_detectada():
    """El agente debe encontrar 'Beca Socioeconómica' para consultas de apoyo económico."""
    estado = _estado_con_pregunta("¿Cómo solicito una beca o auxilio económico?")
    resultado = tramite_agent_node(estado)

    assert resultado["tramite_guia"] is not None
    assert resultado["agente_usado"] == "tramite"
    assert "beca" in resultado["tramite_guia"]["nombre"].lower()


def test_recurso_de_reposicion_detectado():
    """El agente debe encontrar 'Recurso de Reposición' para apelar una nota."""
    estado = _estado_con_pregunta("Quiero apelar una calificación, ¿cómo hago el recurso de reposición?")
    resultado = tramite_agent_node(estado)

    assert resultado["tramite_guia"] is not None
    assert resultado["agente_usado"] == "tramite"
    assert "reposici" in resultado["tramite_guia"]["nombre"].lower()


def test_tramite_incluye_pasos_cuando_hay_match():
    """
    Cuando se encuentra un trámite, los pasos_tramite deben ser una lista
    no vacía de strings.
    """
    estado = _estado_con_pregunta("¿Cómo cancelo una materia?")
    resultado = tramite_agent_node(estado)

    assert resultado["agente_usado"] == "tramite"
    assert isinstance(resultado["pasos_tramite"], list)
    assert len(resultado["pasos_tramite"]) > 0
    for paso in resultado["pasos_tramite"]:
        assert isinstance(paso, str)
