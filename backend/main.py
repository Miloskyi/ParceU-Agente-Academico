"""
backend/main.py
---------------
API REST FastAPI que expone el grafo LangGraph al frontend React.

Ejecutar:
    py -m uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

# ── PATH setup ──────────────────────────────────────────────────────────────
_RAIZ = Path(__file__).parent.parent
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

# ── Cargar .env ANTES de importar agentes ───────────────────────────────────
from dotenv import load_dotenv
load_dotenv(_RAIZ / ".env")

# ── FastAPI ──────────────────────────────────────────────────────────────────
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Copiloto Administrativo UdeA", version="1.0.0")

# CORS: permite todos los orígenes (necesario para Vercel ↔ Railway)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Arrancar DocWatcher scheduler al iniciar la app ──────────────────────────
@app.on_event("startup")
async def startup_event():
    """Inicia el scheduler de monitoreo de documentos en background."""
    try:
        from agentes.doc_watcher import iniciar_scheduler
        iniciar_scheduler()
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("No se pudo iniciar DocWatcher: %s", exc)


@app.on_event("shutdown")
async def shutdown_event():
    """Detiene el scheduler de monitoreo."""
    try:
        from agentes.doc_watcher import detener_scheduler
        detener_scheduler()
    except Exception:
        pass

# ── Lazy-load del grafo (evita tiempos de inicio largos) ────────────────────
_grafo = None

def get_grafo():
    global _grafo
    if _grafo is None:
        from agentes.grafo import app_grafo
        _grafo = app_grafo
    return _grafo

# ── Modelos Pydantic ─────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    mensaje: str
    perfil: str = "pregrado"

class ChatResponse(BaseModel):
    respuesta: str
    fuentes: list[str] = []
    es_urgente: bool = False
    agente_usado: str = ""
    intencion: str = ""
    calidad: str = ""
    documentos_info: list[dict] = []  # {documento, fecha_modificacion, articulo, pagina}

# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Procesa una consulta del usuario a través del grafo LangGraph."""
    try:
        from langchain_core.messages import HumanMessage

        grafo = get_grafo()
        resultado = grafo.invoke({
            "mensajes": [HumanMessage(content=request.mensaje)],
            "perfil_usuario": request.perfil,
            "intentos": 0,
            "documentos_rag": [],
            "documentos_web": [],
            "es_urgente": False,
            "memoria_resumen": "",
            "turno": 0,
            "verificacion_ok": True,
            "alertas_verificacion": [],
            "plan_agentes": [],
            "complejidad": "simple",
        })

        # Extraer info de documentos con fecha de modificación
        docs_rag = resultado.get("documentos_rag", [])
        documentos_info = []
        vistos = set()
        for doc in docs_rag:
            nombre = doc.get("documento", "")
            fecha = doc.get("fecha_modificacion", "Fecha no disponible")
            clave = f"{nombre}|{fecha}"
            if clave not in vistos:
                vistos.add(clave)
                documentos_info.append({
                    "documento": nombre,
                    "fecha_modificacion": fecha,
                    "articulo": doc.get("articulo", ""),
                    "pagina": str(doc.get("pagina", "")),
                })

        return ChatResponse(
            respuesta=resultado.get("respuesta_candidata", "Sin respuesta disponible."),
            fuentes=resultado.get("fuentes_citadas", []),
            es_urgente=bool(resultado.get("es_urgente", False)),
            agente_usado=resultado.get("agente_usado", ""),
            intencion=resultado.get("intencion", ""),
            calidad=resultado.get("calidad", ""),
            documentos_info=documentos_info,
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/tramites")
def tramites():
    """Retorna el catálogo de trámites desde tramites.json."""
    try:
        ruta = _RAIZ / "data" / "tramites" / "tramites.json"
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
        return datos
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/calendario")
def calendario():
    """Retorna el calendario académico multi-semestre (2025-1, 2025-2, 2026-1, 2026-2)."""
    return {
        "semestres": [
            {
                "semestre": "2025-1",
                "estado": "historico",
                "descripcion": "Primer semestre académico 2025 (enero–junio)",
                "eventos": [
                    {
                        "evento": "Matrícula financiera",
                        "inicio": "14 enero 2025",
                        "fin": "24 enero 2025",
                        "notas": "Pago de matrícula en línea mediante el portal universitario o en bancos autorizados. Los estudiantes deben verificar su liquidación en el SIA antes de pagar.",
                        "tipo_evento": "matricula",
                    },
                    {
                        "evento": "Inicio de clases",
                        "inicio": "27 enero 2025",
                        "fin": "",
                        "notas": "Inicio oficial del período académico 2025-1 para pregrado y posgrado en todas las sedes de la Universidad de Antioquia.",
                        "tipo_evento": "clases",
                    },
                    {
                        "evento": "Período de adiciones y cancelaciones de materias",
                        "inicio": "27 enero 2025",
                        "fin": "7 febrero 2025",
                        "notas": "Ventana oficial para agregar o cancelar asignaturas al horario inscrito. Las cancelaciones en este período no afectan el promedio académico del estudiante.",
                        "tipo_evento": "tramite",
                    },
                    {
                        "evento": "Primer corte evaluativo",
                        "inicio": "17 febrero 2025",
                        "fin": "28 febrero 2025",
                        "notas": "Primer período de evaluaciones parciales del semestre. Cubre aproximadamente el 30% del contenido programático de cada asignatura.",
                        "tipo_evento": "evaluacion",
                    },
                    {
                        "evento": "Semana de receso (Semana Santa)",
                        "inicio": "14 abril 2025",
                        "fin": "18 abril 2025",
                        "notas": "Semana de receso académico por Semana Santa. No hay clases ni actividades evaluativas presenciales durante este período.",
                        "tipo_evento": "receso",
                    },
                    {
                        "evento": "Segundo corte evaluativo",
                        "inicio": "7 abril 2025",
                        "fin": "17 abril 2025",
                        "notas": "Segundo período de evaluaciones parciales. Acumulado hasta el 60% del contenido del curso según los planes de trabajo de cada docente.",
                        "tipo_evento": "evaluacion",
                    },
                    {
                        "evento": "Solicitud de grado",
                        "inicio": "",
                        "fin": "30 mayo 2025",
                        "notas": "Fecha límite para que los egresados del semestre 2025-1 radiquen su solicitud de grado en la respectiva facultad o unidad académica.",
                        "tipo_evento": "grado",
                    },
                    {
                        "evento": "Fin de clases",
                        "inicio": "7 junio 2025",
                        "fin": "",
                        "notas": "Último día oficial de clases del semestre 2025-1. Después de esta fecha inicia el período de exámenes finales.",
                        "tipo_evento": "clases",
                    },
                    {
                        "evento": "Exámenes finales",
                        "inicio": "9 junio 2025",
                        "fin": "21 junio 2025",
                        "notas": "Período de exámenes finales del semestre 2025-1. Los horarios específicos son publicados por cada facultad en el SIA con anticipación.",
                        "tipo_evento": "evaluacion",
                    },
                    {
                        "evento": "Habilitaciones y validaciones",
                        "inicio": "23 junio 2025",
                        "fin": "28 junio 2025",
                        "notas": "Período para presentar exámenes de habilitación o validación según lo estipulado en el Reglamento Estudiantil de pregrado de la UdeA.",
                        "tipo_evento": "evaluacion",
                    },
                    {
                        "evento": "Entrega de notas finales",
                        "inicio": "30 junio 2025",
                        "fin": "",
                        "notas": "Fecha límite para que los docentes ingresen las notas finales al sistema SIA. Después de esta fecha se cierra el período académico 2025-1.",
                        "tipo_evento": "otro",
                    },
                ],
            },
            {
                "semestre": "2025-2",
                "estado": "historico",
                "descripcion": "Segundo semestre académico 2025 (julio–diciembre)",
                "eventos": [
                    {
                        "evento": "Matrícula financiera",
                        "inicio": "14 julio 2025",
                        "fin": "25 julio 2025",
                        "notas": "Pago de matrícula para el período 2025-2 mediante el portal universitario o bancos autorizados. Estudiantes nuevos deben consultar su liquidación en la oficina de admisiones.",
                        "tipo_evento": "matricula",
                    },
                    {
                        "evento": "Inicio de clases",
                        "inicio": "28 julio 2025",
                        "fin": "",
                        "notas": "Inicio oficial del período académico 2025-2 para pregrado y posgrado. Incluye todas las sedes y facultades de la Universidad de Antioquia.",
                        "tipo_evento": "clases",
                    },
                    {
                        "evento": "Período de adiciones y cancelaciones de materias",
                        "inicio": "28 julio 2025",
                        "fin": "8 agosto 2025",
                        "notas": "Período para agregar o cancelar asignaturas sin afectación en el promedio académico. Trámite realizado a través del portal SIA del estudiante.",
                        "tipo_evento": "tramite",
                    },
                    {
                        "evento": "Primer corte evaluativo",
                        "inicio": "18 agosto 2025",
                        "fin": "29 agosto 2025",
                        "notas": "Primer período evaluativo del semestre 2025-2. Evalúa aproximadamente el 30% del contenido de cada asignatura según el plan de trabajo docente.",
                        "tipo_evento": "evaluacion",
                    },
                    {
                        "evento": "Segundo corte evaluativo",
                        "inicio": "6 octubre 2025",
                        "fin": "17 octubre 2025",
                        "notas": "Segundo período de evaluaciones parciales del semestre 2025-2. Cubre contenidos acumulados hasta el 60% del programa de cada asignatura.",
                        "tipo_evento": "evaluacion",
                    },
                    {
                        "evento": "Semana de receso",
                        "inicio": "3 noviembre 2025",
                        "fin": "7 noviembre 2025",
                        "notas": "Semana de receso académico institucional. No hay clases ni evaluaciones durante estos días en ninguna de las sedes de la universidad.",
                        "tipo_evento": "receso",
                    },
                    {
                        "evento": "Solicitud de grado",
                        "inicio": "",
                        "fin": "28 noviembre 2025",
                        "notas": "Fecha límite para que los egresados del período 2025-2 presenten su solicitud formal de grado ante la respectiva facultad o unidad académica.",
                        "tipo_evento": "grado",
                    },
                    {
                        "evento": "Fin de clases",
                        "inicio": "6 diciembre 2025",
                        "fin": "",
                        "notas": "Último día oficial de actividades académicas del semestre 2025-2. Inicia el período de exámenes finales a partir de la siguiente semana.",
                        "tipo_evento": "clases",
                    },
                    {
                        "evento": "Exámenes finales",
                        "inicio": "8 diciembre 2025",
                        "fin": "20 diciembre 2025",
                        "notas": "Período de exámenes finales del semestre 2025-2. Los calendarios por asignatura son publicados por cada facultad con al menos dos semanas de anticipación.",
                        "tipo_evento": "evaluacion",
                    },
                    {
                        "evento": "Habilitaciones y validaciones",
                        "inicio": "22 diciembre 2025",
                        "fin": "23 diciembre 2025",
                        "notas": "Período breve para exámenes de habilitación y validación conforme al Reglamento Estudiantil. Solo aplica para asignaturas con nota entre 2.0 y 2.9.",
                        "tipo_evento": "evaluacion",
                    },
                    {
                        "evento": "Entrega de notas finales",
                        "inicio": "30 diciembre 2025",
                        "fin": "",
                        "notas": "Fecha límite para el registro de notas finales por parte de los docentes en el sistema SIA. Cierre oficial del período académico 2025-2.",
                        "tipo_evento": "otro",
                    },
                ],
            },
            {
                "semestre": "2026-1",
                "estado": "activo",
                "descripcion": "Primer semestre académico 2026 (enero–junio) — Período vigente",
                "eventos": [
                    {
                        "evento": "Matrícula financiera",
                        "inicio": "15 enero 2026",
                        "fin": "23 enero 2026",
                        "notas": "Pago de matrícula en línea mediante el portal universitario o en bancos autorizados. Los estudiantes deben verificar su liquidación en el SIA antes de efectuar el pago.",
                        "tipo_evento": "matricula",
                    },
                    {
                        "evento": "Inicio de clases",
                        "inicio": "27 enero 2026",
                        "fin": "",
                        "notas": "Inicio oficial del período académico 2026-1 para pregrado y posgrado en todas las sedes y facultades de la Universidad de Antioquia.",
                        "tipo_evento": "clases",
                    },
                    {
                        "evento": "Período de adiciones",
                        "inicio": "27 enero 2026",
                        "fin": "30 enero 2026",
                        "notas": "Período oficial para agregar asignaturas al horario ya inscrito. El trámite se realiza directamente en el portal SIA del estudiante, sujeto a disponibilidad de cupos.",
                        "tipo_evento": "tramite",
                    },
                    {
                        "evento": "Cancelación de materias",
                        "inicio": "3 febrero 2026",
                        "fin": "13 febrero 2026",
                        "notas": "Ventana para cancelar asignaturas sin que afecte el promedio académico. Pasada esta fecha, las cancelaciones se registran como reprobación según el Reglamento Estudiantil.",
                        "tipo_evento": "tramite",
                    },
                    {
                        "evento": "Primer corte evaluativo",
                        "inicio": "17 febrero 2026",
                        "fin": "28 febrero 2026",
                        "notas": "Primer período de evaluaciones parciales del semestre 2026-1. Cubre aproximadamente el 30% del contenido programático de cada asignatura.",
                        "tipo_evento": "evaluacion",
                    },
                    {
                        "evento": "Segundo corte evaluativo",
                        "inicio": "6 abril 2026",
                        "fin": "17 abril 2026",
                        "notas": "Segundo período de evaluaciones parciales. Acumulado hasta el 60% del contenido del curso. Los docentes publican el cronograma con al menos una semana de anticipación.",
                        "tipo_evento": "evaluacion",
                    },
                    {
                        "evento": "Semana de receso (Semana Santa)",
                        "inicio": "20 abril 2026",
                        "fin": "24 abril 2026",
                        "notas": "Semana de receso académico por Semana Santa. No hay clases ni actividades evaluativas presenciales. Las actividades virtuales siguen el criterio de cada docente.",
                        "tipo_evento": "receso",
                    },
                    {
                        "evento": "Tercer corte evaluativo",
                        "inicio": "4 mayo 2026",
                        "fin": "15 mayo 2026",
                        "notas": "Tercer y último período de evaluaciones parciales del semestre 2026-1. Abarca los contenidos finales antes de los exámenes de cierre de semestre.",
                        "tipo_evento": "evaluacion",
                    },
                    {
                        "evento": "Solicitud de grado",
                        "inicio": "",
                        "fin": "30 mayo 2026",
                        "notas": "Fecha límite para que los egresados del semestre 2026-1 radiquen su solicitud de grado ante la facultad correspondiente. Requiere paz y salvo académico y financiero.",
                        "tipo_evento": "grado",
                    },
                    {
                        "evento": "Fin de clases",
                        "inicio": "6 junio 2026",
                        "fin": "",
                        "notas": "Último día oficial de actividades académicas del semestre 2026-1. A partir de esta fecha inicia el período de exámenes finales.",
                        "tipo_evento": "clases",
                    },
                    {
                        "evento": "Exámenes finales",
                        "inicio": "8 junio 2026",
                        "fin": "20 junio 2026",
                        "notas": "Período de exámenes finales del semestre 2026-1. Los horarios específicos de cada asignatura son publicados por las facultades en el SIA.",
                        "tipo_evento": "evaluacion",
                    },
                    {
                        "evento": "Habilitaciones y validaciones",
                        "inicio": "23 junio 2026",
                        "fin": "27 junio 2026",
                        "notas": "Período para exámenes de habilitación y validación según el Reglamento Estudiantil. Aplica a estudiantes con nota entre 2.0 y 2.9 en la asignatura respectiva.",
                        "tipo_evento": "evaluacion",
                    },
                    {
                        "evento": "Entrega de notas finales",
                        "inicio": "25 junio 2026",
                        "fin": "",
                        "notas": "Fecha límite para que los docentes ingresen las notas finales al sistema SIA. El incumplimiento de este plazo debe ser reportado a la respectiva dirección de programa.",
                        "tipo_evento": "otro",
                    },
                ],
            },
            {
                "semestre": "2026-2",
                "estado": "futuro",
                "descripcion": "Segundo semestre académico 2026 (julio–diciembre) — Fechas provisionales",
                "eventos": [
                    {
                        "evento": "Matrícula financiera (provisional)",
                        "inicio": "13 julio 2026",
                        "fin": "24 julio 2026",
                        "notas": "Fechas provisionales para el pago de matrícula del semestre 2026-2. Se confirmarán en el calendario oficial que publica la Vicerrectoría de Docencia. Consultar el portal universitario.",
                        "tipo_evento": "matricula",
                    },
                    {
                        "evento": "Inicio de clases (provisional)",
                        "inicio": "27 julio 2026",
                        "fin": "",
                        "notas": "Fecha provisional de inicio de actividades académicas para el semestre 2026-2. Aplica para todos los programas de pregrado y posgrado, sujeto a confirmación oficial.",
                        "tipo_evento": "clases",
                    },
                    {
                        "evento": "Período de adiciones y cancelaciones (provisional)",
                        "inicio": "27 julio 2026",
                        "fin": "7 agosto 2026",
                        "notas": "Ventana provisional para agregar o cancelar asignaturas sin afectación al promedio. Las fechas exactas serán confirmadas en el calendario académico oficial del semestre.",
                        "tipo_evento": "tramite",
                    },
                    {
                        "evento": "Primer corte evaluativo (provisional)",
                        "inicio": "17 agosto 2026",
                        "fin": "28 agosto 2026",
                        "notas": "Período provisional para el primer corte evaluativo del semestre 2026-2. Cubre aproximadamente el 30% del contenido de cada asignatura, según plan de trabajo docente.",
                        "tipo_evento": "evaluacion",
                    },
                    {
                        "evento": "Semana de receso (provisional)",
                        "inicio": "2 noviembre 2026",
                        "fin": "6 noviembre 2026",
                        "notas": "Semana de receso académico provisional. Sin clases ni evaluaciones. La fecha exacta puede ajustarse según el calendario oficial que apruebe el Consejo Académico.",
                        "tipo_evento": "receso",
                    },
                    {
                        "evento": "Segundo corte evaluativo (provisional)",
                        "inicio": "5 octubre 2026",
                        "fin": "16 octubre 2026",
                        "notas": "Período provisional para el segundo corte evaluativo del semestre 2026-2. Abarca contenidos acumulados hasta el 60% del programa de cada asignatura.",
                        "tipo_evento": "evaluacion",
                    },
                    {
                        "evento": "Solicitud de grado (provisional)",
                        "inicio": "",
                        "fin": "27 noviembre 2026",
                        "notas": "Fecha límite provisional para radicar la solicitud de grado del semestre 2026-2 ante la facultad. Requiere paz y salvo académico, financiero y de biblioteca.",
                        "tipo_evento": "grado",
                    },
                    {
                        "evento": "Fin de clases (provisional)",
                        "inicio": "5 diciembre 2026",
                        "fin": "",
                        "notas": "Fecha provisional del último día de actividades académicas del semestre 2026-2. Inicia el período de exámenes finales a partir de la semana siguiente.",
                        "tipo_evento": "clases",
                    },
                    {
                        "evento": "Exámenes finales (provisional)",
                        "inicio": "7 diciembre 2026",
                        "fin": "19 diciembre 2026",
                        "notas": "Período provisional de exámenes finales del semestre 2026-2. Los horarios definitivos serán publicados por cada facultad con anticipación en el portal SIA.",
                        "tipo_evento": "evaluacion",
                    },
                    {
                        "evento": "Habilitaciones y validaciones (provisional)",
                        "inicio": "21 diciembre 2026",
                        "fin": "22 diciembre 2026",
                        "notas": "Período provisional para exámenes de habilitación y validación según el Reglamento Estudiantil vigente. Solo aplica para asignaturas con nota final entre 2.0 y 2.9.",
                        "tipo_evento": "evaluacion",
                    },
                ],
            },
        ]
    }


@app.get("/api/analytics")
def analytics():
    """Retorna estadísticas extendidas de uso (desde el módulo de analytics en memoria)."""
    try:
        from utils.analytics import obtener_resumen_extendido
        return obtener_resumen_extendido()
    except Exception:
        return {
            "total": 0,
            "urgentes": 0,
            "tasa_aceptable": 0.0,
            "por_intencion": {},
            "por_perfil": {},
            "por_agente": {},
            "por_calidad": {},
            "tasa_urgentes": 0.0,
            "agente_mas_usado": "",
            "intencion_mas_frecuente": "",
            "consultas_ultimo_minuto": 0,
        }


# ── Endpoints del sistema de monitoreo de documentos ─────────────────────────

@app.get("/api/documentos/estado")
def estado_documentos():
    """
    Retorna el estado de todos los documentos monitoreados por el DocWatcher.

    Cada documento incluye:
      - titulo: Nombre del documento
      - url: URL de descarga
      - estado: 'ok' | 'actualizado' | 'error' | 'pendiente'
      - ultima_revision: Timestamp ISO de la última verificación
      - ultima_actualizacion: Timestamp ISO de la última actualización real
    """
    try:
        from agentes.doc_watcher import obtener_estado_documentos
        docs = obtener_estado_documentos()
        return {
            "total": len(docs),
            "documentos": docs,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class ActualizarDocumentoRequest(BaseModel):
    url: str


@app.post("/api/documentos/actualizar")
def actualizar_documento(request: ActualizarDocumentoRequest):
    """
    Fuerza la re-descarga y re-indexación de un documento específico.

    Body: {"url": "https://normativa.udea.edu.co/Documentos/Descargar/123"}

    Útil para el botón 'Forzar actualización' en el frontend.
    """
    try:
        from agentes.doc_watcher import forzar_actualizacion
        resultado = forzar_actualizacion(request.url)
        return resultado
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/documentos/registrar")
def registrar_documento(request: ActualizarDocumentoRequest):
    """
    Registra una nueva URL para ser monitoreada por el DocWatcher.

    Body: {"url": "https://normativa.udea.edu.co/Documentos/Descargar/123"}
    """
    try:
        from agentes.doc_watcher import registrar_documento
        titulo = request.url.split("/")[-1] or request.url
        registrar_documento(request.url, titulo)
        return {"mensaje": f"Documento registrado para monitoreo: {request.url}", "exito": True}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Endpoints del SIA ─────────────────────────────────────────────────────────

@app.get("/api/sia/oferta")
def sia_oferta(q: str, forzar: bool = False):
    """
    Consulta la oferta académica del SIA en tiempo real.

    Parámetros:
      - q: Nombre o código del curso a buscar
      - forzar: Si True, ignora el caché y consulta directo al SIA

    Retorna lista de cursos con cupos disponibles en tiempo real.
    """
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="El parámetro 'q' es requerido")
    try:
        from agentes.sia_scraper import consultar_sia
        cursos = consultar_sia(q.strip(), forzar_actualizacion=forzar)
        return {
            "query": q,
            "total": len(cursos),
            "cursos": cursos,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/sia/cache/stats")
def sia_cache_stats():
    """Retorna estadísticas del caché del SIA scraper."""
    try:
        from agentes.sia_scraper import obtener_stats_cache
        return obtener_stats_cache()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/api/sia/cache")
def sia_cache_limpiar():
    """Limpia el caché del SIA scraper."""
    try:
        from agentes.sia_scraper import limpiar_cache
        n = limpiar_cache()
        return {"mensaje": f"Caché limpiado: {n} entradas eliminadas", "eliminadas": n}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
