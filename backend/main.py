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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """Retorna las fechas del calendario académico 2026-1."""
    return {
        "semestre": "2026-1",
        "eventos": [
            {"evento": "Matrícula financiera",        "inicio": "15 enero 2026",   "fin": "23 enero 2026",   "notas": "Pago en línea o bancos autorizados"},
            {"evento": "Inicio de clases",             "inicio": "27 enero 2026",   "fin": "",                "notas": "Pregrado y posgrado"},
            {"evento": "Período de adiciones",         "inicio": "27 enero 2026",   "fin": "30 enero 2026",   "notas": "Agregar materias al horario"},
            {"evento": "Cancelación de materias",      "inicio": "3 febrero 2026",  "fin": "13 febrero 2026", "notas": "Sin afectar promedio"},
            {"evento": "Primer corte evaluativo",      "inicio": "17 febrero 2026", "fin": "28 febrero 2026", "notas": ""},
            {"evento": "Segundo corte evaluativo",     "inicio": "6 abril 2026",    "fin": "17 abril 2026",   "notas": ""},
            {"evento": "Semana de receso",             "inicio": "20 abril 2026",   "fin": "24 abril 2026",   "notas": "Semana Santa"},
            {"evento": "Tercer corte evaluativo",      "inicio": "4 mayo 2026",     "fin": "15 mayo 2026",    "notas": ""},
            {"evento": "Fin de clases",                "inicio": "6 junio 2026",    "fin": "",                "notas": ""},
            {"evento": "Exámenes finales",             "inicio": "8 junio 2026",    "fin": "20 junio 2026",   "notas": ""},
            {"evento": "Entrega de notas finales",     "inicio": "25 junio 2026",   "fin": "",                "notas": "Plazo para docentes"},
            {"evento": "Habilitaciones / validaciones","inicio": "23 junio 2026",   "fin": "27 junio 2026",   "notas": "Según reglamento"},
            {"evento": "Solicitud de grado",           "inicio": "",                "fin": "30 mayo 2026",    "notas": "Egresados del semestre"},
        ]
    }


@app.get("/api/analytics")
def analytics():
    """Retorna estadísticas de uso (desde el módulo de analytics en memoria)."""
    try:
        from utils.analytics import obtener_resumen
        return obtener_resumen()
    except Exception:
        return {"total": 0, "urgentes": 0, "tasa_aceptable": 0.0}
