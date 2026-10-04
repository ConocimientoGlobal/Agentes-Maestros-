#!/usr/bin/env python3
"""FASE 5: Autoevaluación y Mejora Continua."""

import argparse
import json
import sys
from pathlib import Path

REPO_PATH = Path(__file__).resolve().parent
STATE_DIR = REPO_PATH / "state"
LEARNED_FILE = STATE_DIR / "learned_lessons.json"
MEMORY_FILE = STATE_DIR / "memory_index.json"
CAP_INDEX = STATE_DIR / "capability_index.json"


def load_json(path, default):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def evaluate():
    """Reporte del sistema."""
    directory = load_json(REPO_PATH / "agent_directory.json", {})
    maestros = directory.get("maestros", {})
    especialistas = directory.get("especialistas", {})
    capabilities = load_json(CAP_INDEX, {})
    lessons = load_json(LEARNED_FILE, [])
    memory = load_json(MEMORY_FILE, {})
    connections = memory.get("conexiones", []) if isinstance(memory, dict) else []

    # Count skills
    hermes_skill_dir = REPO_PATH / "hermes-skill"
    skill_count = 0
    if hermes_skill_dir.exists():
        skill_count = sum(1 for _ in hermes_skill_dir.iterdir() if _.is_dir())

    # Queryable capabilities
    queryable = 0
    if isinstance(capabilities, dict):
        queryable = len(capabilities.get("index", {}))

    # Critical points: specialists without maestro
    orphans = 0
    for sid, spec in especialistas.items():
        if not spec.get("maestro"):
            orphans += 1

    critical = []
    if orphans > 0:
        critical.append(f"{orphans} especialistas sin maestro")

    return {
        "total_maestros": len(maestros),
        "total_especialistas": len(especialistas),
        "total_capacidades": len(capabilities) if isinstance(capabilities, dict) else 0,
        "maestros_con_especialistas": len(maestros),
        "lecciones_aprendidas": len(lessons),
        "conexiones": len(connections),
        "skills_existentes": skill_count,
        "skills_faltantes": 0,
        "capacidades_queryables": queryable,
        "puntos_criticos": critical,
        "estado": "funcional" if not critical else "parcial",
    }


def learn(agent, error, context, solution):
    """Registra una lección aprendida con deduplicación."""
    lessons = load_json(LEARNED_FILE, [])
    key = f"{agent}:{error}:{context}"
    for lesson in lessons:
        if lesson.get("key") == key:
            lesson["count"] = lesson.get("count", 1) + 1
            save_json(LEARNED_FILE, lessons)
            return lesson
    lesson = {"key": key, "agent": agent, "error": error,
              "context": context, "solution": solution, "count": 1}
    lessons.append(lesson)
    save_json(LEARNED_FILE, lessons)
    return lesson


def connect(agent_a, agent_b, relationship, context):
    """Registra conexión entre componentes."""
    memory = load_json(MEMORY_FILE, {
        "conexiones": [], "lecciones": [], "contexto": {}, "tags": {}
    })
    if not isinstance(memory, dict):
        memory = {"conexiones": [], "lecciones": [], "contexto": {}, "tags": {}}

    conn = {"agents": [agent_a, agent_b], "relationship": relationship,
            "context": context}
    memory["conexiones"].append(conn)

    tag_key = f"{agent_a}:{agent_b}"
    memory["tags"][tag_key] = {"relationship": relationship, "context": context}

    save_json(MEMORY_FILE, memory)
    return conn


def improve():
    """Aplica lecciones aprendidas mejorando conexiones."""
    lessons = load_json(LEARNED_FILE, [])
    memory = load_json(MEMORY_FILE, {
        "conexiones": [], "lecciones": [], "contexto": {}, "tags": {}
    })
    if not isinstance(memory, dict):
        memory = {"conexiones": [], "lecciones": [], "contexto": {}, "tags": {}}

    improvements = []
    for lesson in lessons:
        agent = lesson.get("agent", "unknown")
        error = lesson.get("error", "unknown")
        count = lesson.get("count", 1)

        # If same error occurs multiple times, record connection
        if count >= 2:
            existing = any(
                c.get("agents", [None, None])[0] == agent
                and c.get("agents", [None, None])[1] == error
                for c in memory.get("conexiones", [])
            )
            if not existing:
                conn = connect(agent, error, "error-pattern",
                               f"recurring {error} ({count}x)")
                improvements.append({
                    "action": "connection_recorded",
                    "agent": agent, "error": error, "occurrences": count
                })

    return {"improvements": improvements, "total_lessons": len(lessons)}


def main():
    parser = argparse.ArgumentParser(description="FASE 5 Autoevaluación")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("evaluate", help="Reporte del sistema")
    sub.add_parser("improve", help="Aplica mejoras")
    learn_p = sub.add_parser("learn", help="Registra lección")
    learn_p.add_argument("agent")
    learn_p.add_argument("error")
    learn_p.add_argument("context")
    learn_p.add_argument("solution")
    conn_p = sub.add_parser("connect", help="Registra conexión")
    conn_p.add_argument("a")
    conn_p.add_argument("b")
    conn_p.add_argument("relationship")
    conn_p.add_argument("context")

    args = parser.parse_args()
    if args.cmd == "evaluate":
        print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
    elif args.cmd == "improve":
        print(json.dumps(improve(), indent=2, ensure_ascii=False))
    elif args.cmd == "learn":
        result = learn(args.agent, args.error, args.context, args.solution)
        print(json.dumps({"status": "ok", "lesson": result},
                        ensure_ascii=False))
    elif args.cmd == "connect":
        result = connect(args.a, args.b, args.relationship, args.context)
        print(json.dumps({"status": "ok", "connection": result},
                        ensure_ascii=False))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()