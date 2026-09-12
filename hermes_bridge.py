#!/usr/bin/env python3
"""
HERMES BRIDGE — Puente de integración con Neural Fellowship
============================================================

Este módulo expone funciones de alto nivel para que Hermes Agent
pueda invocar el sistema Neural Fellowship (neural_fellowship.py)
como biblioteca Python.

Funciones expuestas:
  - route_task(description) -> dict
  - auto_execute(description) -> dict
  - remember(agent_id, error, context, solution) -> dict
  - recall_lessons(agent_id) -> list
  - get_system_status() -> dict

Uso desde Hermes (via Python terminal):
  import sys
  sys.path.insert(0, '/data/data/com.termux/files/home/tmp/Agentes-Maestros-')
  from hermes_bridge import route_task, auto_execute, remember, recall_lessons, get_system_status
  
  result = route_task("Crear API REST con FastAPI")
  print(result)
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

# Path to the repository containing neural_fellowship.py
REPO_PATH = Path("/data/data/com.termux/files/home/tmp/Agentes-Maestros-")

# Ensure we can import neural_fellowship
if str(REPO_PATH) not in sys.path:
    sys.path.insert(0, str(REPO_PATH))

# ============================================================================
# IMPORTS from neural_fellowship.py
# ============================================================================

try:
    from neural_fellowship import (
        Orquestador,
        AutoExecutor,
        LearningSystem,
        MemorySystem,
        Orchestrator,
        DetectorTareas,
        AGENTES_MAESTROS,
        AGENTES_ESPECIALIZADOS,
    )
except ImportError as e:
    raise ImportError(
        f"No se pudo importar neural_fellowship.py desde {REPO_PATH}. "
        f"Asegúrate de que el archivo existe. Error: {e}"
    )


# ============================================================================
# BRIDGE FUNCTIONS
# ============================================================================

def route_task(description: str) -> dict:
    """
    Determina el mejor agente (maestro + especialista) para una tarea.
    
    Invoca el Orquestador de Neural Fellowship para hacer routing
    inteligente basado en scoring de palabras clave.
    
    Args:
        description: Descripción de la tarea en lenguaje natural.
        
    Returns:
        dict con keys:
          - tarea: descripción original
          - maestro: {maestro, confianza, motivo}
          - especialista: {especialista, maestro, confianza, capacidades}
          - automatizable: bool (True si se puede auto-ejecutar)
          
    Ejemplo:
        >>> route_task("Crear API REST con FastAPI")
        {
            "tarea": "Crear API REST con FastAPI",
            "maestro": {"maestro": "NEXUS", "confianza": 75, "motivo": "Match scoring: 75 pts"},
            "especialista": {"especialista": "engineering-backend-architect", ...},
            "automatizable": True
        }
    """
    if not description or not description.strip():
        return {"error": "Descripción de tarea vacía"}
    
    try:
        orchestrador = Orquestador()
        resultado = orchestrador.ruta_completa(description.strip())
        
        # Enrich with agent metadata
        maestro_id = resultado["maestro"]["maestro"]
        maestro_info = AGENTES_MAESTROS.get(maestro_id, {})
        
        especialista_id = resultado["especialista"].get("especialista")
        especialista_info = {}
        if especialista_id and especialista_id in AGENTES_ESPECIALIZADOS:
            especialista_info = {
                "capacidades": AGENTES_ESPECIALIZADOS[especialista_id].get("capacidades", [])
            }
        
        return {
            "tarea": resultado["tarea"],
            "maestro": {
                "id": maestro_id,
                "nombre": maestro_id,
                "dominio": maestro_info.get("dominio", ""),
                "division": maestro_info.get("division", ""),
                "confianza": resultado["maestro"]["confianza"],
                "motivo": resultado["maestro"]["motivo"],
                "emoji": maestro_info.get("emoji", "❓"),
                "automatizable": maestro_info.get("automatizable", False),
            },
            "especialista": {
                "id": especialista_id,
                "nombre": especialista_id,
                "maestro": resultado["especialista"].get("maestro", ""),
                "confianza": resultado["especialista"].get("confianza", 0),
                "capacidades": especialista_info.get("capacidades", []),
            },
            "automatizable": resultado["automatizable"],
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": f"Error en route_task: {str(e)}", "tarea": description}
    
    return {"error": "Resultado no generado", "tarea": description}


def auto_execute(description: str, dry_run: bool = False) -> dict:
    """
    Intenta auto-ejecutar una tarea mecánica.
    
    Invoca el AutoExecutor de Neural Fellowship para detectar y ejecutar
    comandos seguros: mkdir, touch, cp, mv, git, pip, npm, etc.
    
    Args:
        description: Descripción de la tarea mecánica.
        dry_run: Si True, solo simula la ejecución.
        
    Returns:
        dict con keys:
          - tarea: descripción original
          - accion: tipo de acción detectada (mkdir, git_commit, etc.)
          - status: success | error | denied | no_automatizable
          - mensaje: descripción del resultado
          - dry_run: si fue simulación
          
    Ejemplo:
        >>> auto_execute("crear carpeta ~/projects/mi-app")
        {
            "tarea": "crear carpeta ~/projects/mi-app",
            "accion": "mkdir",
            "status": "success",
            "mensaje": "Carpeta creada: /data/data/com.termux/files/home/projects/mi-app"
        }
    """
    if not description or not description.strip():
        return {"error": "Descripción de tarea vacía"}
    
    try:
        executor = AutoExecutor()
        resultado = executor.ejecutar(description.strip(), dry_run=dry_run)
        resultado["timestamp"] = datetime.now().isoformat()
        return resultado
    except Exception as e:
        return {
            "error": f"Error en auto_execute: {str(e)}",
            "tarea": description,
            "status": "error",
        }


def remember(agent_id: str, error: str, context: str, solution: str, tags=None) -> dict:
    """
    Registra un error/lección aprendida de un agente.
    
    Invoca el LearningSystem de Neural Fellowship para persistir
    el conocimiento y evitar repetir errores.
    
    Args:
        agent_id: identificador del agente (ej: "NEXUS", "design-ui-designer")
        error: descripción del error cometido
        context: contexto donde ocurrió el error
        solution: solución aplicada
        tags: lista de tags opcionales para clasificar
        
    Returns:
        dict con la lección registrada/actualizada
        
    Ejemplo:
        >>> remember("NEXUS", "ModuleNotFoundError", "FastAPI sin instalar", "pip install fastapi")
        {
            "agent_id": "NEXUS",
            "error": "ModuleNotFoundError",
            "context": "FastAPI sin instalar",
            "solution": "pip install fastapi",
            "occurrences": 1
        }
    """
    if not agent_id or not error:
        return {"error": "Se requieren agent_id y error"}
    
    try:
        ls = LearningSystem()
        resultado = ls.record_error(
            agent_id=agent_id.strip(),
            error=error.strip(),
            context=context.strip() if context else "",
            solution=solution.strip() if solution else "",
            tags=tags or [],
        )
        resultado["timestamp"] = datetime.now().isoformat()
        return resultado
    except Exception as e:
        return {
            "error": f"Error en remember: {str(e)}",
            "agent_id": agent_id,
            "error_desc": error,
        }


def recall_lessons(agent_id: str) -> list:
    """
    Recupera todas las lecciones aprendidas de un agente.
    
    Invoca el LearningSystem de Neural Fellowship para consultar
    lecciones previas registradas por el agente.
    
    Args:
        agent_id: identificador del agente
        
    Returns:
        lista de lecciones (dicts) ordenadas por relevancia
        
    Ejemplo:
        >>> recall_lessons("NEXUS")
        [
            {
                "agent_id": "NEXUS",
                "error": "ModuleNotFoundError",
                "context": "FastAPI sin instalar",
                "solution": "pip install fastapi",
                "occurrences": 2
            }
        ]
    """
    if not agent_id:
        return []
    
    try:
        ls = LearningSystem()
        lessons = ls.get_agent_lessons(agent_id.strip())
        # Sort by occurrences (most frequent first)
        return sorted(lessons, key=lambda x: x.get("occurrences", 0), reverse=True)
    except Exception as e:
        return [{"error": f"Error en recall_lessons: {str(e)}"}]


def get_warnings_for_agent(agent_id: str) -> list:
    """
    Obtiene advertencias para un agente (errores con 2+ ocurrencias).
    
    Args:
        agent_id: identificador del agente
        
    Returns:
        lista de advertencias con soluciones
    """
    if not agent_id:
        return []
    
    try:
        ls = LearningSystem()
        return ls.get_warnings_for_agent(agent_id.strip())
    except Exception as e:
        return [{"error": f"Error en get_warnings: {str(e)}"}]


def generate_pre_execution_checklist(agent_id: str, task: str) -> list:
    """
    Genera una checklist pre-ejecución basada en errores pasados.
    
    Args:
        agent_id: identificador del agente
        task: descripción de la tarea a ejecutar
        
    Returns:
        lista de strings con advertencias y recordatorios
    """
    if not agent_id or not task:
        return []
    
    try:
        ls = LearningSystem()
        return ls.generate_pre_execution_checklist(agent_id.strip(), task.strip())
    except Exception as e:
        return [f"Error en generate_pre_execution_checklist: {str(e)}"]


def get_system_status() -> dict:
    """
    Obtiene el estado completo del sistema Neural Fellowship.
    
    Invoca todos los subsistemas: Orchestrator, MemorySystem,
    LearningSystem, y DetectorTareas.
    
    Returns:
        dict con el estado completo del sistema
        
    Ejemplo:
        >>> get_system_status()
        {
            "orchestrator": {"active_agents": 0, "completed_tasks": 3, ...},
            "memory": {"conexiones": 12, "lecciones": 5, ...},
            "learning": {"total_lessons": 5, "agents_with_lessons": 2, ...},
            "tasks": {"total": 15, "pendientes": 10, ...},
            "agentes_maestros": 63,
            "agentes_especializados": 85,
            "timestamp": "2025-01-15T10:30:00"
        }
    """
    try:
        # Orchestrator status
        orch = Orchestrator()
        orch_status = orch.get_status()
    except Exception as e:
        orch_status = {"error": str(e)}
    
    try:
        # Memory system status
        mem = MemorySystem()
        mem_stats = mem.get_stats()
    except Exception as e:
        mem_stats = {"error": str(e)}
    
    try:
        # Learning system status
        ls = LearningSystem()
        learn_stats = ls.get_stats()
    except Exception as e:
        learn_stats = {"error": str(e)}
    
    try:
        # Task detector status
        detector = DetectorTareas()
        task_stats = detector.get_stats()
    except Exception as e:
        task_stats = {"error": str(e)}
    
    return {
        "orchestrator": orch_status,
        "memory": mem_stats,
        "learning": learn_stats,
        "tasks": task_stats,
        "agentes_maestros": len(AGENTES_MAESTROS),
        "agentes_especializados": len(AGENTES_ESPECIALIZADOS),
        "timestamp": datetime.now().isoformat(),
    }


def search_memory(query: str) -> list:
    """
    Busca en la memoria del sistema.
    
    Args:
        query: texto a buscar
        
    Returns:
        lista de resultados encontrados
    """
    if not query:
        return []
    
    try:
        mem = MemorySystem()
        return mem.buscar_en_memoria(query.strip())
    except Exception as e:
        return [{"error": f"Error en search_memory: {str(e)}"}]


# ============================================================================
# CLI for testing
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Hermes Bridge — Neural Fellowship Integration")
    parser.add_argument("command", choices=[
        "route", "auto", "remember", "recall", "status",
        "warnings", "checklist", "memory"
    ])
    parser.add_argument("--description", "-d", type=str, help="Descripción de la tarea")
    parser.add_argument("--agent", "-a", type=str, help="ID del agente")
    parser.add_argument("--error", "-e", type=str, help="Descripción del error")
    parser.add_argument("--context", "-c", type=str, help="Contexto del error")
    parser.add_argument("--solution", "-s", type=str, help="Solución aplicada")
    parser.add_argument("--tags", "-t", type=str, help="Tags separados por coma")
    parser.add_argument("--query", "-q", type=str, help="Query para búsqueda en memoria")
    parser.add_argument("--dry-run", action="store_true", help="Simular ejecución")
    
    args = parser.parse_args()
    
    if args.command == "route":
        if not args.description:
            print("Se requiere --description")
            sys.exit(1)
        result = route_task(args.description)
        
    elif args.command == "auto":
        if not args.description:
            print("Se requiere --description")
            sys.exit(1)
        result = auto_execute(args.description, dry_run=args.dry_run)
        
    elif args.command == "remember":
        if not all([args.agent, args.error, args.context, args.solution]):
            print("Se requieren --agent, --error, --context, --solution")
            sys.exit(1)
        tags = args.tags.split(",") if args.tags else []
        result = remember(args.agent, args.error, args.context, args.solution, tags=tags)
        
    elif args.command == "recall":
        if not args.agent:
            print("Se requiere --agent")
            sys.exit(1)
        result = recall_lessons(args.agent)
        
    elif args.command == "warnings":
        if not args.agent:
            print("Se requiere --agent")
            sys.exit(1)
        result = get_warnings_for_agent(args.agent)
        
    elif args.command == "checklist":
        if not all([args.agent, args.description]):
            print("Se requieren --agent y --description")
            sys.exit(1)
        result = generate_pre_execution_checklist(args.agent, args.description)
        
    elif args.command == "status":
        result = get_system_status()
        
    elif args.command == "memory":
        if not args.query:
            print("Se requiere --query")
            sys.exit(1)
        result = search_memory(args.query)
    
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
