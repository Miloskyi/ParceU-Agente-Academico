"""
tests/test_rag.py
-----------------
Pruebas unitarias para el Grader y el Router pre-check del Copiloto UdeA.

NO requieren API keys ni ChromaDB real:
  - El grader es completamente determinístico (sin LLM).
  - El router pre-check (_precheck_urgencia) tampoco usa LLM.
  - Las pruebas del grader_node que necesiten LLM se mockean con unittest.mock.

Ejecutar:
    pytest tests/test_rag.py -v
"""

from unittest.mock import MagicMock, patch

import pytest

from agentes.estado import estado_inicial
from agentes.grader import _evaluar_calidad, decidir_post_grader, grader_node
from agentes.router import PALABRAS_URGENCIA, _precheck_urgencia

# ===========================================================================
# SECCIÓN 1: Pruebas de _evaluar_calidad (grader determinístico)
# ===========================================================================


class TestEvaluarCalidad:
    """Pruebas para la función _evaluar_calidad del grader."""

    # --- Caso: respuesta vacía → sin_info ---

    def test_respuesta_vacia_es_sin_info(self):
        """Respuesta vacía ('') debe retornar 'sin_info'."""
        estado = estado_inicial()
        estado["respuesta_candidata"] = ""
        assert _evaluar_calidad(estado) == "sin_info"

    def test_respuesta_solo_espacios_es_sin_info(self):
        """Respuesta con solo espacios/saltos de línea debe retornar 'sin_info'."""
        estado = estado_inicial()
        estado["respuesta_candidata"] = "   \n\t  "
        assert _evaluar_calidad(estado) == "sin_info"

    # --- Caso: frases de no-información → sin_info ---

    def test_frase_no_encontre_es_sin_info(self):
        """Frase 'no encontré' en la respuesta debe retornar 'sin_info'."""
        estado = estado_inicial()
        estado["respuesta_candidata"] = "Lo siento, no encontré información sobre ese tema."
        assert _evaluar_calidad(estado) == "sin_info"

    def test_frase_no_tengo_informacion_es_sin_info(self):
        """Frase 'no tengo información' debe retornar 'sin_info'."""
        estado = estado_inicial()
        estado["respuesta_candidata"] = "No tengo información sobre ese procedimiento."
        assert _evaluar_calidad(estado) == "sin_info"

    def test_frase_no_esta_disponible_es_sin_info(self):
        """Frase 'no está disponible' debe retornar 'sin_info'."""
        estado = estado_inicial()
        estado["respuesta_candidata"] = "Esa información no está disponible en mi base de datos."
        assert _evaluar_calidad(estado) == "sin_info"

    def test_frase_no_dispongo_es_sin_info(self):
        """Frase 'no dispongo' debe retornar 'sin_info'."""
        estado = estado_inicial()
        estado["respuesta_candidata"] = "No dispongo de datos sobre ese trámite."
        assert _evaluar_calidad(estado) == "sin_info"

    def test_frase_no_puedo_responder_es_sin_info(self):
        """Frase 'no puedo responder' debe retornar 'sin_info'."""
        estado = estado_inicial()
        estado["respuesta_candidata"] = "No puedo responder a esa consulta con la información disponible."
        assert _evaluar_calidad(estado) == "sin_info"

    def test_frase_sin_info_mayusculas_insensible(self):
        """La detección de frases de no-info debe ser insensible a mayúsculas."""
        estado = estado_inicial()
        estado["respuesta_candidata"] = "LO SIENTO, NO ENCONTRÉ NADA RELEVANTE."
        assert _evaluar_calidad(estado) == "sin_info"

    # --- Caso: respuesta sustancial con citas → aceptable ---

    def test_respuesta_larga_con_cita_es_aceptable(self):
        """
        Respuesta de más de 100 caracteres con '(Fuente:' debe ser 'aceptable'.
        """
        estado = estado_inicial()
        estado["respuesta_candidata"] = (
            "Para cancelar una materia debes ingresar al portal universitario "
            "y seguir los pasos indicados en el reglamento estudiantil. "
            "(Fuente: Acuerdo Superior 1, Art. 45)"
        )
        assert _evaluar_calidad(estado) == "aceptable"

    def test_respuesta_larga_con_pasos_numerados_es_aceptable(self):
        """
        Respuesta de más de 100 caracteres con pasos numerados (1.) debe ser 'aceptable'.
        """
        estado = estado_inicial()
        estado["respuesta_candidata"] = (
            "Para solicitar el certificado de notas sigue estos pasos: "
            "1. Ingresa al portal universitario con tu usuario y contraseña. "
            "2. Ve a Servicios Académicos. "
            "3. Selecciona Solicitud de Certificados y confirma."
        )
        assert _evaluar_calidad(estado) == "aceptable"

    def test_respuesta_larga_con_rag_es_aceptable(self):
        """
        Respuesta de más de 100 caracteres con documentos_rag no vacíos → 'aceptable'.
        """
        estado = estado_inicial()
        estado["respuesta_candidata"] = (
            "Según el reglamento estudiantil de la Universidad de Antioquia, "
            "el estudiante puede cancelar materias dentro de las fechas "
            "establecidas en el calendario académico vigente para el semestre."
        )
        estado["documentos_rag"] = [{"contenido": "Art. 45 - Cancelaciones", "score": 0.9}]
        assert _evaluar_calidad(estado) == "aceptable"

    # --- Caso: respuesta corta o sin citas → mejorar ---

    def test_respuesta_corta_sin_citas_es_mejorar(self):
        """Respuesta corta sin citas ni pasos debe retornar 'mejorar'."""
        estado = estado_inicial()
        estado["respuesta_candidata"] = "Puedes cancelar materias en el portal."
        assert _evaluar_calidad(estado) == "mejorar"

    def test_respuesta_larga_sin_citas_ni_rag_es_mejorar(self):
        """
        Respuesta larga pero sin citas, sin pasos numerados y sin RAG → 'mejorar'.
        """
        estado = estado_inicial()
        estado["respuesta_candidata"] = (
            "La Universidad de Antioquia ofrece muchos servicios académicos "
            "a sus estudiantes. Puedes consultar la página web oficial para "
            "obtener más información sobre los trámites disponibles y los "
            "requisitos necesarios para completar cada proceso administrativo."
        )
        # Sin documentos_rag, sin citas, sin pasos numerados
        assert _evaluar_calidad(estado) == "mejorar"


# ===========================================================================
# SECCIÓN 2: Pruebas de grader_node (nodo completo)
# ===========================================================================


class TestGraderNode:
    """Pruebas para el nodo grader_node del grafo."""

    def test_grader_node_incrementa_intentos(self):
        """grader_node debe incrementar 'intentos' en 1 por cada llamada."""
        estado = estado_inicial()
        estado["respuesta_candidata"] = "Respuesta corta."
        estado["intentos"] = 0

        resultado = grader_node(estado)

        assert resultado["intentos"] == 1

    def test_grader_node_incrementa_intentos_desde_valor_existente(self):
        """grader_node debe partir del valor actual de 'intentos' y sumar 1."""
        estado = estado_inicial()
        estado["respuesta_candidata"] = "Respuesta corta."
        estado["intentos"] = 1

        resultado = grader_node(estado)

        assert resultado["intentos"] == 2

    def test_grader_node_intentos_nunca_supera_2_en_ciclo(self):
        """
        Simula el ciclo completo: el grader se llama hasta 2 veces.
        'intentos' no debe superar 2 mientras decidir_post_grader enruta correctamente.
        """
        # Primera pasada: respuesta mejorable, intentos va a 1
        estado = estado_inicial()
        estado["respuesta_candidata"] = "Respuesta corta sin detalles."
        estado["intentos"] = 0

        resultado1 = grader_node(estado)
        assert resultado1["intentos"] == 1
        assert resultado1["calidad"] == "mejorar"

        # Aplicar el resultado al estado
        estado.update(resultado1)

        # Verificar que decidir_post_grader enruta a búsqueda web (intentos=1 < 2)
        ruta1 = decidir_post_grader(estado)
        assert ruta1 == "busqueda_web"

        # Segunda pasada: sigue siendo mejorable, intentos va a 2
        resultado2 = grader_node(estado)
        assert resultado2["intentos"] == 2
        assert resultado2["calidad"] == "mejorar"

        # Aplicar el resultado al estado
        estado.update(resultado2)

        # Con intentos=2 >= 2, decidir_post_grader debe retornar "fin"
        ruta2 = decidir_post_grader(estado)
        assert ruta2 == "fin"

    def test_grader_node_retorna_calidad_y_intentos(self):
        """grader_node debe retornar siempre 'calidad' e 'intentos'."""
        estado = estado_inicial()
        estado["respuesta_candidata"] = ""

        resultado = grader_node(estado)

        assert "calidad" in resultado
        assert "intentos" in resultado

    def test_grader_node_con_respuesta_aceptable(self):
        """grader_node debe marcar 'aceptable' para respuestas sustanciales con citas."""
        estado = estado_inicial()
        estado["respuesta_candidata"] = (
            "Para cancelar materias debes ingresar al portal universitario. "
            "1. Ir a Servicios Académicos. "
            "2. Seleccionar Cancelación de Asignaturas. "
            "3. Confirmar y guardar el radicado. "
            "(Fuente: Portal UdeA, Registro y Control)"
        )
        estado["intentos"] = 0

        resultado = grader_node(estado)

        assert resultado["calidad"] == "aceptable"
        assert resultado["intentos"] == 1


# ===========================================================================
# SECCIÓN 3: Pruebas de decidir_post_grader
# ===========================================================================


class TestDecidirPostGrader:
    """Pruebas para la función de enrutamiento condicional decidir_post_grader."""

    def test_calidad_aceptable_retorna_fin(self):
        """calidad='aceptable' siempre retorna 'fin'."""
        estado = estado_inicial()
        estado["calidad"] = "aceptable"
        estado["intentos"] = 1
        assert decidir_post_grader(estado) == "fin"

    def test_calidad_sin_info_retorna_fin(self):
        """calidad='sin_info' siempre retorna 'fin'."""
        estado = estado_inicial()
        estado["calidad"] = "sin_info"
        estado["intentos"] = 1
        assert decidir_post_grader(estado) == "fin"

    def test_calidad_mejorar_intentos_menor_2_retorna_busqueda_web(self):
        """calidad='mejorar' con intentos=1 debe retornar 'busqueda_web'."""
        estado = estado_inicial()
        estado["calidad"] = "mejorar"
        estado["intentos"] = 1
        assert decidir_post_grader(estado) == "busqueda_web"

    def test_calidad_mejorar_intentos_igual_2_retorna_fin(self):
        """calidad='mejorar' con intentos=2 debe retornar 'fin' (evitar ciclo)."""
        estado = estado_inicial()
        estado["calidad"] = "mejorar"
        estado["intentos"] = 2
        assert decidir_post_grader(estado) == "fin"

    def test_calidad_mejorar_intentos_mayor_2_retorna_fin(self):
        """calidad='mejorar' con intentos>2 debe retornar 'fin'."""
        estado = estado_inicial()
        estado["calidad"] = "mejorar"
        estado["intentos"] = 5
        assert decidir_post_grader(estado) == "fin"


# ===========================================================================
# SECCIÓN 4: Pruebas de _precheck_urgencia (router sin LLM)
# ===========================================================================


class TestPrecheckUrgencia:
    """Pruebas para _precheck_urgencia del router (sin llamar al LLM)."""

    def test_pregunta_con_prueba_academica_es_urgente(self):
        """'prueba académica' está en PALABRAS_URGENCIA → debe retornar True."""
        assert _precheck_urgencia("Quedé en prueba académica, ¿qué hago?") is True

    def test_pregunta_con_perdida_de_cupo_es_urgente(self):
        """'pérdida de cupo' está en PALABRAS_URGENCIA → debe retornar True."""
        assert _precheck_urgencia("Tengo riesgo de pérdida de cupo este semestre") is True

    def test_pregunta_con_cancelar_semestre_es_urgente(self):
        """'cancelar semestre' está en PALABRAS_URGENCIA → debe retornar True."""
        assert _precheck_urgencia("Necesito cancelar semestre por problemas personales") is True

    def test_pregunta_con_acoso_es_urgente(self):
        """'acoso' está en PALABRAS_URGENCIA → debe retornar True."""
        assert _precheck_urgencia("Estoy sufriendo acoso por parte de un compañero") is True

    def test_pregunta_con_violencia_es_urgente(self):
        """'violencia' está en PALABRAS_URGENCIA → debe retornar True."""
        assert _precheck_urgencia("Hay violencia en el campus y no sé qué hacer") is True

    def test_pregunta_con_proceso_disciplinario_es_urgente(self):
        """'proceso disciplinario' está en PALABRAS_URGENCIA → debe retornar True."""
        assert _precheck_urgencia("Me abrieron un proceso disciplinario, ¿qué hago?") is True

    def test_pregunta_normal_no_es_urgente(self):
        """Una consulta ordinaria sin keywords críticas debe retornar False."""
        assert _precheck_urgencia("¿Cuáles son los requisitos para el certificado de notas?") is False

    def test_pregunta_tramite_no_es_urgente(self):
        """Una consulta de trámite sin urgencia debe retornar False."""
        assert _precheck_urgencia("¿Cómo inscribir mi trabajo de grado?") is False

    def test_pregunta_calendario_no_es_urgente(self):
        """Una consulta de calendario sin urgencia debe retornar False."""
        assert _precheck_urgencia("¿Cuál es la fecha de matrículas del próximo semestre?") is False

    def test_pregunta_vacia_no_es_urgente(self):
        """Una cadena vacía no debe detectar urgencia."""
        assert _precheck_urgencia("") is False

    def test_deteccion_insensible_a_mayusculas(self):
        """El pre-check debe funcionar independientemente de mayúsculas/minúsculas."""
        assert _precheck_urgencia("QUEDÉ EN PRUEBA ACADÉMICA") is True
        assert _precheck_urgencia("Prueba Académica primer semestre") is True

    def test_palabras_urgencia_no_vacia(self):
        """PALABRAS_URGENCIA debe ser una lista no vacía de strings."""
        assert isinstance(PALABRAS_URGENCIA, list)
        assert len(PALABRAS_URGENCIA) > 0
        for palabra in PALABRAS_URGENCIA:
            assert isinstance(palabra, str)

    def test_todas_palabras_urgencia_detectadas(self):
        """Cada keyword en PALABRAS_URGENCIA debe ser detectada por _precheck_urgencia."""
        for keyword in PALABRAS_URGENCIA:
            pregunta = f"Necesito ayuda porque {keyword} es un problema grave para mí"
            assert _precheck_urgencia(pregunta) is True, (
                f"La keyword '{keyword}' no fue detectada por _precheck_urgencia"
            )
