#!/usr/bin/env python3
"""Orquestador Dinámico — task → capability → especialista → maestro → ejecución."""

import argparse
import json
import sys
import os
import re
from pathlib import Path

REPO_PATH = Path(__file__).resolve().parent
AGENT_DIR = REPO_PATH / "agent_directory.json"
CAP_INDEX = REPO_PATH / "state" / "capability_index.json"

# Importar capa de ejecución reutilizable
import ejecutor_real

# Integración EvolutionProposer — capability gap → propuesta de evolución
from network_evolution import PerformanceTracker, EvolutionProposer

_tracker = PerformanceTracker()


def load_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _load_json(path):
    """Alias for load_json — used by bridge integration."""
    return load_json(path)


def query_capability_index(task_text, top_n=5):
    """Find capabilities matching a task description."""
    idx = load_json(CAP_INDEX)
    task_lower = task_text.lower()
    scores = []
    for cap, data in idx.items():
        cap_lower = cap.lower()
        # Skip very short capabilities (1-2 chars) to avoid random matches
        if len(cap_lower) <= 2:
            continue
        # Direct substring match
        if cap_lower in task_lower or task_lower in cap_lower:
            score = 2.0
        else:
            # Word overlap
            cap_words = set(cap_lower.split("-"))
            task_words = set(task_lower.split())
            overlap = cap_words & task_words
            score = len(overlap) / max(len(cap_words), 1) * 1.0
        if score > 0:
            agents = data.get("agentes", {})
            masters = data.get("maestros", {})
            scores.append((cap, score, agents, masters))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_n]


def route_to_master(capability, agent_dir):
    """Given a capability, find the best master."""
    idx = load_json(CAP_INDEX)
    cap_data = idx.get(capability, {})
    masters = cap_data.get("maestros", {})
    if not masters:
        return None, 0
    # Return master with highest weight
    best = max(masters.items(), key=lambda x: x[1])
    return best[0], best[1]


def find_specialists(capability, agent_dir):
    """Find specialists for a capability."""
    idx = load_json(CAP_INDEX)
    cap_data = idx.get(capability, {})
    agents = cap_data.get("agentes", {})
    results = []
    for agent_id, agent_info in agents.items():
        agent_meta = agent_dir.get("especialistas", {}).get(agent_id, {})
        results.append({
            "id": agent_id,
            "source": agent_info.get("source", "unknown"),
            "peso": agent_info.get("peso", 0),
            "maestro": agent_meta.get("maestro"),
            "capacidades": agent_meta.get("capacidades", []),
        })
    results.sort(key=lambda x: x["peso"], reverse=True)
    return results


def orquestar(task, top_n=3):
    """Main orchestration: task → capabilities → specialists → master."""
    agent_dir = load_json(AGENT_DIR)
    caps = query_capability_index(task, top_n=top_n)
    if not caps:
        return {
            "task": task,
            "match": False,
            "message": "No capabilities matched",
        }
    results = []
    for cap, score, agents, masters in caps:
        master, master_weight = route_to_master(cap, agent_dir)
        specialists = find_specialists(cap, agent_dir)
        results.append({
            "capability": cap,
            "score": round(score, 3),
            "master": master,
            "master_weight": master_weight,
            "specialists": specialists[:5],
        })
    best = results[0]
    return {
        "task": task,
        "match": True,
        "best_capability": best["capability"],
        "best_score": best["score"],
        "master": best["master"],
        "all_matches": results,
    }


# ============================================================================
# CAPA DE EJECUCIÓN — conecta el routing con handlers ejecutables reales
# ============================================================================

# Estrategias de ejecución disponibles (registro paramétrico, NO handlers por especialista).
# Cada estrategia es una función en ejecutor_real.py reutilizable.
EXECUTION_STRATEGIES = {
    "api_rest": ejecutor_real._ejecutar_api,
    "data_pipeline": ejecutor_real._ejecutar_pipeline,
    "analisis_financiero": ejecutor_real._ejecutar_analisis_financiero,
    "diseno_visual": ejecutor_real._ejecutar_diseño,
    "videojuego": ejecutor_real._ejecutar_videojuego,
}

# Reglas de resolución: (specialist, capability_pattern) → strategy_name
# Data-driven: se agrega resolución sin tocar código.
RESOLUTION_RULES = {
    # NEXUS / Engineering
    ("engineering-backend-architect", "apis"): "api_rest",
    ("engineering-backend-architect", "api"): "api_rest",
    ("engineering-backend-architect", "scalable-systems"): "api_rest",
    ("engineering-data-engineer", "data-pipelines"): "data_pipeline",
    ("engineering-data-engineer", "data-pipeline"): "data_pipeline",
    # AURUM / Finance
    ("finance-financial-analyst", "modeling"): "analisis_financiero",
    ("finance-financial-analyst", "forecasting"): "analisis_financiero",
    ("finance-financial-analyst", "financial-analysis"): "analisis_financiero",
    # ARCAN / Design
    ("design-brand-guardian", "identidad-marca"): "diseno_visual",
    ("design-brand-guardian", "guia-estilo"): "diseno_visual",
    ("design-brand-guardian", "consistencia"): "diseno_visual",
    # CRONUS / Game
    ("game-development-game-designer", "gdd"): "videojuego",
    ("game-development-game-designer", "mechanics"): "videojuego",
}

# Fallback por capability genérica (sin especialista específico)
CAPABILITY_STRATEGY = {
    "apis": "api_rest",
    "api": "api_rest",
    "data-pipelines": "data_pipeline",
    "data-pipeline": "data_pipeline",
    "financial-analysis": "analisis_financiero",
    "financial-planning": "analisis_financiero",
    "modeling": "analisis_financiero",
    "forecasting": "analisis_financiero",
    "identidad-marca": "diseno_visual",
    "guia-estilo": "diseno_visual",
    "consistencia": "diseno_visual",
    "game-design": "videojuego",
    "level-design": "videojuego",
    "gdd": "videojuego",
    "mechanics": "videojuego",
}

# Keywords de task → strategy (fallback paramétrico)
TASK_KEYWORD_STRATEGY = {
    ("api", "rest"): "api_rest",
    ("endpoint",): "api_rest",
    ("fastapi",): "api_rest",
    ("pipeline", "datos"): "data_pipeline",
    ("csv", "analizar"): "data_pipeline",
    ("financiero",): "analisis_financiero",
    ("ingresos", "gastos"): "analisis_financiero",
    ("logo", "marca"): "diseno_visual",
    ("diseño", "visual"): "diseno_visual",
    ("videojuego",): "videojuego",
    ("3d", "motor"): "videojuego",
}


def resolve_execution(specialist, capabilities, task):
    """Determina la estrategia de ejecución de forma paramétrica.

    Cadena de resolución:
      1. RESOLUTION_RULES (specialist, capability) → strategy
      2. CAPABILITY_STRATEGY (capability genérica) → strategy
      3. TASK_KEYWORD_STRATEGY (keywords de tarea) → strategy
      4. None → no_ejecutable

    NO es una lista if/else gigante. Es búsqueda data-driven.
    """
    task_lower = task.lower()

    # 1. Por (specialist, capability)
    for (spec, cap), strategy in RESOLUTION_RULES.items():
        if spec == specialist and cap in capabilities:
            return strategy, specialist, "resolution_rule"

    # 2. Por capability genérica
    for cap, strategy in CAPABILITY_STRATEGY.items():
        if cap in capabilities:
            return strategy, specialist, "capability"

    # 3. Por keywords de tarea
    for keywords, strategy in TASK_KEYWORD_STRATEGY.items():
        if all(kw in task_lower for kw in keywords):
            return strategy, specialist, "task_keyword"

    return None, specialist, "sin_handler"


def _registrar_leccion(resultado):
    """Registra en autoeval.py como señal de aprendizaje, no como modificación de identidad.

    - Fallo/no_ejecutable → lección de disponibilidad (no de identidad del agente).
    - Éxito → conexión tarea→handler (contexto, no modificación permanente).
    - Nunca auto-modifica routing/scoring/especialistas.
    """
    try:
        import autoeval
    except Exception:
        return None

    status = resultado.get("status", "unknown")
    master = resultado.get("master") or "unknown"
    spec = resultado.get("especialista") or "none"
    handler = resultado.get("handler") or "none"
    reason = resultado.get("reason", "")
    task = resultado.get("task", "")

    if status == "completed":
        # Éxito → registro ligero, no permanente (count=1, no acumula)
        return autoeval.learn(
            agent=f"{master}/{spec}",
            error="none",
            context=f"handler={handler} task={task[:60]}",
            solution=f"Ejecución completada vía {handler}.",
        )
    elif status == "no_ejecutable":
        # Fallo explícito → señal de aprendizaje para evolución
        return autoeval.learn(
            agent=f"{master}/{spec}",
            error=f"no_ejecutable:{handler or 'sin_handler'}",
            context=reason[:200],
            solution=f"Sin handler mapeado para {spec}. Requiere capability coverage.",
        )
    else:
        # error_ejecución → señal con razón
        return autoeval.learn(
            agent=f"{master}/{spec}",
            error=f"error_ejecucion:{handler or 'unknown'}",
            context=reason[:200],
            solution="Revisar handler o dependencias.",
        )


def _proponer_evolucion(task, especialista, master, collection):
    """Genera propuesta via EvolutionProposer para un capability gap.

    Registra la señal en PerformanceTracker y genera propuesta concreta.
    NO crea especialistas/maestros/capabilities/handlers automáticamente.
    """
    try:
        _tracker.record(
            task_description=task,
            success=False,
            confidence=0,
            specialist=especialista or None,
            master=master or "unknown",
        )
        proposer = EvolutionProposer(_tracker)
        propuestas = proposer.propose()
        collection.extend(propuestas)
    except Exception as e:
        collection.append({"id": "evo_error", "action": "error", "reason": f"EvolutionProposer: {e}"})


def ejecutar(task, top_n=3):
    """Flujo completo: task → Orquestador → maestro → especialista → ejecución → resultado.

    Usa el Orquestador canónico de neural_fellowship (el flujo normal).
    Devuelve siempre un dict con 'status'. Si no puede ejecutar,
    incluye 'reason' explícita (nunca inventa resultado).
    """
    # Reutilización: ejecutor real (no es un sistema paralelo)
    sys.path.insert(0, str(REPO_PATH))
    import ejecutor_real
    from neural_fellowship import Orquestador

    orq = Orquestador()
    routing = orq.ruta_completa(task)

    maestro_block = routing.get("maestro") or {}
    spec_block = routing.get("especialista") or {}

    base = {
        "task": task,
        "master": maestro_block.get("maestro"),
        "especialista": spec_block.get("especialista"),
        "automatizable": routing.get("automatizable"),
    }

    # ── EvolutionProposer integration ──
    # Solo no_ejecutable genera capability gap → propuesta.
    # error_ejecucion = handler existente pero falló → NO capability gap.
    evolution_proposals = []

    if not base["master"]:
        base.update({
            "status": "no_ejecutable",
            "reason": "El Orquestador no encontró ningún maestro compatible con la tarea.",
        })
        _registrar_leccion(base)
        # Capability gap: master no encontrado
        _proponer_evolucion(task, base.get("especialista") or "", base.get("master") or "", evolution_proposals)
        base["evolution_proposals"] = evolution_proposals
        return base

    handler, specialist, via = resolve_execution(
        base.get("especialista") or "",
        spec_block.get("capacidades", []),
        task,
    )
    base["handler"] = handler
    base["resuelto_via"] = via

    if handler is None:
        base.update({
            "status": "no_ejecutable",
            "reason": (
                f"Ningún ejecutor disponible para especialista='{specialist}' "
                f"(maestro='{base['master']}'). El especialista seleccionado no tiene "
                f"una herramienta de ejecución mapeada. Capacidades: {spec_block.get('capacidades', [])}."
            ),
        })
        _registrar_leccion(base)
        # Capability gap: especialista sin handler mapeado
        _proponer_evolucion(task, base.get("especialista") or "", base.get("master") or "", evolution_proposals)
        base["evolution_proposals"] = evolution_proposals
        return base

    # Dispatch al handler real (usando registro paramétrico)
    try:
        result = EXECUTION_STRATEGIES[handler](task, routing)
        base["resultado"] = result
        base["status"] = result.get("status", "completed")
    except Exception as e:
        base.update({
            "status": "error_ejecucion",
            "reason": f"El handler '{handler}' falló: {type(e).__name__}: {e}",
        })
        _registrar_leccion(base)
        # error_ejecucion NO genera capability gap
    else:
        _registrar_leccion(base)

    base["evolution_proposals"] = evolution_proposals
    return base


def main():
    parser = argparse.ArgumentParser(description="Orquestador Dinámico")
    sub = parser.add_subparsers(dest="cmd")

    p_orch = sub.add_parser("orquestar", help="Route task to master/especialista")
    p_orch.add_argument("task", help="Task description")
    p_orch.add_argument("--top", type=int, default=3, help="Top capabilities")

    p_ejec = sub.add_parser("ejecutar", help="Full flow: route + execute task")
    p_ejec.add_argument("task", help="Task description")
    p_ejec.add_argument("--top", type=int, default=3, help="Top capabilities")

    p_cap = sub.add_parser("query-cap", help="Query capability index")
    p_cap.add_argument("text", help="Search text")
    p_cap.add_argument("--top", type=int, default=5)

    p_master = sub.add_parser("routing", help="Find master for a capability")
    p_master.add_argument("capability", help="Capability name")

    args = parser.parse_args()
    if args.cmd == "orquestar":
        result = orquestar(args.task, args.top)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    elif args.cmd == "ejecutar":
        result = ejecutar(args.task, args.top)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    elif args.cmd == "query-cap":
        caps = query_capability_index(args.text, args.top)
        print(json.dumps([{"capabilidad": c, "score": s} for c, s, _, _ in caps], indent=2, ensure_ascii=False))
    elif args.cmd == "routing":
        master, weight = route_to_master(args.capability, load_json(AGENT_DIR))
        print(json.dumps({"capability": args.capability, "master": master, "weight": weight}, indent=2, ensure_ascii=False))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()