#!/usr/bin/env python3
"""
HERMES NEURAL BRIDGE — Integración Real
========================================
Puente completo entre Hermes Agent y Neural Fellowship.

Flujo de integración:
1. Hermes recibe tarea
2. Invoca route_task() → obtiene maestro + especialista + si es automatizable
3a. Si es automatizable → auto_execute() → terminal
3b. Si requiere IA → delegate_task() con prompt del especialista

Funciones:
  - route_task(description) -> dict
  - run_task(description) -> dict  (flujo completo)
  - auto_execute(description, dry_run) -> dict
  - remember(agent_id, error, context, solution) -> dict
  - recall_lessons(agent_id) -> list
  - get_system_status() -> dict
  - build_capability_index() -> dict (genera capability_index.json)
  - query_capability(capacidad) -> dict (consulta el índice)
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Path configuration
REPO_PATH = Path(__file__).parent
if str(REPO_PATH) not in sys.path:
    sys.path.insert(0, str(REPO_PATH))

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


def route_task(description: str) -> dict:
    """Route a task to the best agent."""
    if not description or not description.strip():
        return {"error": "Empty task description"}
    
    try:
        orchestrador = Orquestador()
        resultado = orchestrador.ruta_completa(description.strip())
        
        maestro_id = resultado["maestro"]["maestro"]
        maestro_info = AGENTES_MAESTROS.get(maestro_id, {})
        
        especialista_id = resultado["especialista"].get("especialista")
        especialista_info = {}
        if especialista_id and especialista_id in AGENTES_ESPECIALIZADOS:
            especialista_info = {
                "capacidades": AGENTES_ESPECIALIZADOS[especialista_id].get("capacidades", [])
            }
        
        return {
            "task": resultado["tarea"],
            "maestro": {
                "id": maestro_id,
                "name": maestro_id,
                "domain": maestro_info.get("dominio", ""),
                "division": maestro_info.get("division", ""),
                "confidence": resultado["maestro"]["confianza"],
                "reason": resultado["maestro"]["motivo"],
                "emoji": maestro_info.get("emoji", "❓"),
                "automatizable": maestro_info.get("automatizable", False),
            },
            "specialist": {
                "id": especialista_id,
                "name": especialista_id,
                "maestro": resultado["especialista"].get("maestro", ""),
                "confidence": resultado["especialista"].get("confianza", 0),
                "capabilities": especialista_info.get("capacidades", []),
            },
            "automatizable": resultado["automatizable"],
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": f"Route error: {str(e)}", "task": description}


def run_task(description: str, dry_run: bool = False) -> dict:
    """
    Full task execution flow.
    
    1. Route the task
    2. If automatizable → auto_execute
    3. If not → return delegation info for Hermes delegate_task
    """
    # Step 1: Route
    route = route_task(description)
    if "error" in route:
        return route
    
    result = {
        "route": route,
        "execution": None,
        "dry_run": dry_run,
    }
    
    # Step 2: Execute or delegate
    if route["automatizable"]:
        # Mechanical task → auto_execute
        executor = AutoExecutor()
        exec_result = executor.ejecutar(description.strip(), dry_run=dry_run)
        exec_result["timestamp"] = datetime.now().isoformat()
        # If AutoExecutor rejected the task (not a mechanical pattern), fall back to delegation
        if exec_result.get("status") == "no_automatizable":
            specialist = route["specialist"]
            maestro = route["maestro"]
            specialist_prompt = _build_specialist_prompt(
                task=description,
                specialist_id=specialist["id"],
                specialist_capabilities=specialist.get("capabilities", []),
                maestro_id=maestro["id"],
                maestro_domain=maestro["domain"],
            )
            result["execution"] = {
                "type": "delegate",
                "delegation": {
                    "specialist_id": specialist["id"],
                    "maestro_id": maestro["id"],
                    "prompt": specialist_prompt,
                    "confidence": specialist.get("confidence", 0),
                },
                "fallback_reason": "automatizable maestro but task is not a mechanical pattern",
            }
        else:
            result["execution"] = {
                "type": "auto",
                "result": exec_result,
            }
    else:
        # AI task → prepare delegation
        specialist = route["specialist"]
        maestro = route["maestro"]
        
        # Build the specialist prompt
        specialist_prompt = _build_specialist_prompt(
            task=description,
            specialist_id=specialist["id"],
            specialist_capabilities=specialist.get("capabilities", []),
            maestro_id=maestro["id"],
            maestro_domain=maestro["domain"],
        )
        
        result["execution"] = {
            "type": "delegate",
            "delegation": {
                "specialist_id": specialist["id"],
                "maestro_id": maestro["id"],
                "prompt": specialist_prompt,
                "confidence": specialist.get("confidence", 0),
            }
        }
    
    return result


def _build_specialist_prompt(task: str, specialist_id: str, 
                              specialist_capabilities: list,
                              maestro_id: str, maestro_domain: str) -> str:
    """Build a prompt for a specialist agent."""
    return f"""You are {specialist_id}, a specialist in {maestro_domain}.

## Your Role
- Domain: {maestro_domain}
- Capabilities: {', '.join(specialist_capabilities)}

## Task
{task}

## Instructions
1. Review your capabilities and execute the task
2. If you encounter errors, document them for learning
3. Report results clearly
4. If the task is outside your scope, indicate what specialist should handle it

## Output
Execute the task and report results."""


def auto_execute(description: str, dry_run: bool = False) -> dict:
    """Auto-execute a mechanical task."""
    if not description or not description.strip():
        return {"error": "Empty task description"}
    
    try:
        executor = AutoExecutor()
        resultado = executor.ejecutar(description.strip(), dry_run=dry_run)
        resultado["timestamp"] = datetime.now().isoformat()
        return resultado
    except Exception as e:
        return {"error": f"Auto-execute error: {str(e)}", "task": description, "status": "error"}


def remember(agent_id: str, error: str, context: str, solution: str, tags=None) -> dict:
    """Record a lesson learned."""
    if not agent_id or not error:
        return {"error": "agent_id and error are required"}
    
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
        return {"error": f"Remember error: {str(e)}", "agent_id": agent_id}


def recall_lessons(agent_id: str) -> list:
    """Recall all lessons for an agent."""
    if not agent_id:
        return []
    
    try:
        ls = LearningSystem()
        lessons = ls.get_agent_lessons(agent_id.strip())
        return sorted(lessons, key=lambda x: x.get("occurrences", 0), reverse=True)
    except Exception as e:
        return [{"error": f"Recall error: {str(e)}"}]


def get_warnings_for_agent(agent_id: str) -> list:
    """Get warnings for an agent (2+ occurrences)."""
    if not agent_id:
        return []
    
    try:
        ls = LearningSystem()
        return ls.get_warnings_for_agent(agent_id.strip())
    except Exception as e:
        return [{"error": f"Warnings error: {str(e)}"}]


def generate_pre_execution_checklist(agent_id: str, task: str) -> list:
    """Generate pre-execution checklist based on past errors."""
    if not agent_id or not task:
        return []
    
    try:
        ls = LearningSystem()
        return ls.generate_pre_execution_checklist(agent_id.strip(), task.strip())
    except Exception as e:
        return [f"Checklist error: {str(e)}"]


def search_memory(query: str) -> list:
    """Search in system memory."""
    if not query:
        return []
    
    try:
        mem = MemorySystem()
        return mem.buscar_en_memoria(query.strip())
    except Exception as e:
        return [{"error": f"Search error: {str(e)}"}]


def get_system_status() -> dict:
    """Get complete system status."""
    try:
        orch = Orchestrator()
        orch_status = orch.get_status()
    except Exception as e:
        orch_status = {"error": str(e)}

    try:
        mem = MemorySystem()
        mem_stats = mem.get_stats()
    except Exception as e:
        mem_stats = {"error": str(e)}

    try:
        ls = LearningSystem()
        learn_stats = ls.get_stats()
    except Exception as e:
        learn_stats = {"error": str(e)}

    try:
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


def build_capability_index() -> dict:
    """Build inverted index: capability -> {agents, maestros} from agent_directory.json."""
    from collections import defaultdict

    repo = REPO_PATH
    dir_file = repo / "agent_directory.json"
    if not dir_file.exists():
        return {}

    data = json.loads(dir_file.read_text(encoding="utf-8"))
    especialistas = data.get("especialistas", {})

    cap_to_agents = defaultdict(dict)
    cap_to_maestros = defaultdict(float)

    for esp_id, esp_data in especialistas.items():
        caps = esp_data.get("capacidades", [])
        maestro = esp_data.get("maestro", "")
        for cap in caps:
            key = cap.lower().strip()
            cap_to_agents[key][esp_id] = {"source": "json", "peso": 1.0}
            if maestro:
                cap_to_maestros[key] += 0.5

    index = {}
    for cap, agents in cap_to_agents.items():
        maestros_dict = {}
        for m, w in cap_to_maestros.items():
            if m:
                maestros_dict[m] = w
        index[cap] = {"agentes": agents, "maestros": maestros_dict}

    out = repo / "state" / "capability_index.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return index


def query_capability(capacidad: str) -> dict:
    """Query the capability index for a single capability."""
    idx = get_capability_index()
    key = capacidad.lower().strip()
    if key in idx:
        return {key: idx[key]}
    # fuzzy: substring match
    matches = {k: v for k, v in idx.items() if key in k}
    if not matches:
        return {}
    return matches


def get_capability_index() -> dict:
    """Load capability_index.json from state directory."""
    idx_file = REPO_PATH / "state" / "capability_index.json"
    if not idx_file.exists():
        return {}
    return json.loads(idx_file.read_text(encoding="utf-8"))


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Hermes Neural Bridge — Integration")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # route
    route_parser = subparsers.add_parser("route", help="Route a task to best agent")
    route_parser.add_argument("description", type=str, help="Task description")
    
    # run (full flow)
    run_parser = subparsers.add_parser("run", help="Run full task flow")
    run_parser.add_argument("description", type=str, help="Task description")
    run_parser.add_argument("--dry-run", action="store_true", help="Simulate execution")
    
    # auto
    auto_parser = subparsers.add_parser("auto", help="Auto-execute mechanical task")
    auto_parser.add_argument("description", type=str, help="Task description")
    auto_parser.add_argument("--dry-run", action="store_true", help="Simulate execution")
    
    # remember
    remember_parser = subparsers.add_parser("remember", help="Record a lesson")
    remember_parser.add_argument("--agent", "-a", required=True, help="Agent ID")
    remember_parser.add_argument("--error", "-e", required=True, help="Error description")
    remember_parser.add_argument("--context", "-c", required=True, help="Context")
    remember_parser.add_argument("--solution", "-s", required=True, help="Solution")
    remember_parser.add_argument("--tags", "-t", help="Comma-separated tags")
    
    # recall
    recall_parser = subparsers.add_parser("recall", help="Recall lessons")
    recall_parser.add_argument("--agent", "-a", required=True, help="Agent ID")
    
    # warnings
    warn_parser = subparsers.add_parser("warnings", help="Get warnings")
    warn_parser.add_argument("--agent", "-a", required=True, help="Agent ID")
    
    # checklist
    check_parser = subparsers.add_parser("checklist", help="Pre-execution checklist")
    check_parser.add_argument("--agent", "-a", required=True, help="Agent ID")
    check_parser.add_argument("--task", "-t", required=True, help="Task description")
    
    # memory
    mem_parser = subparsers.add_parser("memory", help="Search memory")
    mem_parser.add_argument("--query", "-q", required=True, help="Search query")
    
    # status
    subparsers.add_parser("status", help="System status")

    # capabilities
    cap_parser = subparsers.add_parser("capabilities", help="Search capabilities")
    cap_parser.add_argument("query", nargs="?", help="Search query")

    # build-cap-index
    subparsers.add_parser("build-cap-index", help="Build capability index")

    # cap-query
    capq_parser = subparsers.add_parser("cap-query", help="Query capability index")
    capq_parser.add_argument("capacidad", help="Capability name")

    args = parser.parse_args()
    
    if args.command == "route":
        result = route_task(args.description)
    elif args.command == "run":
        result = run_task(args.description, dry_run=args.dry_run)
    elif args.command == "auto":
        result = auto_execute(args.description, dry_run=args.dry_run)
    elif args.command == "remember":
        tags = args.tags.split(",") if args.tags else []
        result = remember(args.agent, args.error, args.context, args.solution, tags=tags)
    elif args.command == "recall":
        result = recall_lessons(args.agent)
    elif args.command == "warnings":
        result = get_warnings_for_agent(args.agent)
    elif args.command == "checklist":
        result = generate_pre_execution_checklist(args.agent, args.task)
    elif args.command == "memory":
        result = search_memory(args.query)
    elif args.command == "status":
        result = get_system_status()
    elif args.command == "capabilities":
        from hermes_bridge import get_capability_index
        idx = get_capability_index()
        q = (args.query or "").lower()
        matches = {k: v for k, v in idx.items() if q in k} if q else idx
        for k, v in sorted(matches.items())[:20]:
            print(f"  • {k} → {len(v['agentes'])} agents, {len(v['maestros'])} maestros")
    elif args.command == "build-cap-index":
        from hermes_bridge import build_capability_index
        idx = build_capability_index()
        print(f"✅ Built index: {len(idx)} capabilities")
    elif args.command == "cap-query":
        from hermes_bridge import query_capability
        result = query_capability(args.capacidad) or {"message": "No match"}
    else:
        parser.print_help()
        sys.exit(1)
    
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
