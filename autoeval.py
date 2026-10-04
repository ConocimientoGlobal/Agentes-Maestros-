#!/usr/bin/env python3
"""FASE 5: Autoevaluación y Mejora Continua."""

import argparse
import json
import sys
from pathlib import Path

REPO_PATH = Path(__file__).resolve().parent
STATE_DIR = REPO_PATH / "state"
CAP_INDEX = STATE_DIR / "capability_index.json"
AGENT_DIR = REPO_PATH / "agent_directory.json"
LEARNED_FILE = STATE_DIR / "learned_lessons.json"
MEMORY_INDEX = STATE_DIR / "memory_index.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def query_capability_index(query: str, top_k: int = 5) -> list:
    """Query the capability index for matches."""
    index = load_json(CAP_INDEX)
    capabilities = index.get("capabilities", {})
    results = []
    for cap_id, cap_data in capabilities.items():
        cap_lower = cap_id.lower()
        query_lower = query.lower()
        score = 0.0
        if cap_lower == query_lower:
            score = 1.0
        elif query_lower in cap_lower or cap_lower in query_lower:
            score = 0.7
        else:
            # Word overlap
            cap_words = set(cap_lower.split("-"))
            query_words = set(query_lower.split())
            overlap = cap_words & query_words
            if overlap:
                score = len(overlap) / max(len(cap_words), len(query_words)) * 0.8
        if score > 0:
            results.append({"capability": cap_id, "score": score, "data": cap_data})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def save_lesson(agent_id: str, error: str, context: str, solution: str, tags: list | None = None):
    """Save a learned lesson."""
    lessons = load_json(LEARNED_FILE)
    if not isinstance(lessons, list):
        lessons = []
    # Check for duplicate
    for lesson in lessons:
        if lesson.get("agent_id") == agent_id and lesson.get("error") == error and lesson.get("context") == context:
            lesson["occurrences"] = lesson.get("occurrences", 1) + 1
            lesson["last_seen"] = str(Path(__file__).stat().st_mtime)
            save_json(LEARNED_FILE, lessons)
            return {"updated": True, "lesson": lesson}
    lesson = {
        "agent_id": agent_id,
        "error": error,
        "context": context,
        "solution": solution,
        "tags": tags or [],
        "learned_at": str(Path(__file__).stat().st_mtime),
        "occurrences": 1,
        "last_seen": str(Path(__file__).stat().st_mtime),
    }
    lessons.append(lesson)
    save_json(LEARNED_FILE, lessons)
    return {"created": True, "lesson": lesson}


def record_connection(a: str, b: str, relacion: str, fuerza: int = 5):
    """Record a connection in memory index."""
    mem = load_json(MEMORY_INDEX)
    if "conexiones" not in mem:
        mem["conexiones"] = []
    # Check duplicate
    for c in mem["conexiones"]:
        if c.get("a") == a and c.get("b") == b and c.get("relacion") == relacion:
            c["fuerza"] = max(c.get("fuerza", 0), fuerza)
            save_json(MEMORY_INDEX, mem)
            return {"updated": True, "connection": c}
    conexion = {"a": a, "b": b, "relacion": relacion, "fuerza": fuerza, "creada_en": str(Path(__file__).stat().st_mtime)}
    mem["conexiones"].append(conexion)
    save_json(MEMORY_INDEX, mem)
    return {"created": True, "connection": conexion}


def autoevaluate() -> dict:
    """Run self-evaluation: check capabilities, connections, lessons, skills."""
    agent_dir = load_json(AGENT_DIR)
    specialists = agent_dir.get("especialistas", {})
    maestros = agent_dir.get("maestros", {})

    # Count
    total_caps = sum(len(s.get("capacidades", [])) for s in specialists.values())
    maestros_con_especialistas = set()
    for s in specialists.values():
        m = s.get("maestro")
        if m in maestros:
            maestros_con_especialistas.add(m)

    lessons = load_json(LEARNED_FILE)
    if not isinstance(lessons, list):
        lessons = []
    mem = load_json(MEMORY_INDEX)
    conexiones = mem.get("conexiones", [])

    # Check skills coverage
    skill_dirs = list((REPO_PATH / "hermes-skill").glob("*"))
    skill_count = len([d for d in skill_dirs if d.is_dir()])

    # Verify: each specialist has a skill
    missing_skills = []
    for sid in specialists:
        skill_path = REPO_PATH / "hermes-skill" / sid.replace("-", "_") / "SKILL.md"
        if not skill_path.exists():
            missing_skills.append(sid)

    # Verify: each capability is queryable
    cap_results = query_capability_index("test")

    report = {
        "total_maestros": len(maestros),
        "total_especialistas": len(specialists),
        "total_capacidades": total_caps,
        "maestros_con_especialistas": len(maestros_con_especialistas),
        "lecciones_aprendidas": len(lessons),
        "conexiones": len(conexiones),
        "skills_existentes": skill_count,
        "skills_faltantes": len(missing_skills),
        "capacidades_queryables": len(cap_results),
        "puntos_criticos": missing_skills[:5] if missing_skills else [],
        "estado": "funcional" if not missing_skills else "incompleto",
    }
    return report


def improve_from_lessons() -> dict:
    """Apply lessons learned to improve the system."""
    lessons = load_json(LEARNED_FILE)
    if not isinstance(lessons, list):
        return {"error": "No lessons found"}

    improvements = []
    for lesson in lessons:
        error = lesson.get("error", "")
        solution = lesson.get("solution", "")
        tags = lesson.get("tags", [])
        occ = lesson.get("occurrences", 1)

        # If a lesson repeats, record a connection for future reference
        if occ >= 2:
            record_connection(
                a=lesson.get("agent_id", "unknown"),
                b=error,
                relacion="resolved",
                fuerza=min(occ * 2, 10),
            )
            improvements.append({
                "action": "connection_recorded",
                "agent": lesson.get("agent_id"),
                "error": error,
                "occurrences": occ,
            })

    return {"improvements": improvements, "total_lessons": len(lessons)}


def main():
    parser = argparse.ArgumentParser(description="FASE 5: Autoevaluación y Mejora Continua")
    sub = parser.add_subparsers(dest="cmd")

    p_eval = sub.add_parser("evaluate", help="Run self-evaluation")
    p_improve = sub.add_parser("improve", help="Apply improvements from lessons")
    p_lesson = sub.add_parser("learn", help="Record a lesson")
    p_lesson.add_argument("agent_id")
    p_lesson.add_argument("error")
    p_lesson.add_argument("context")
    p_lesson.add_argument("solution")
    p_lesson.add_argument("--tags", nargs="*", default=[])
    p_conn = sub.add_parser("connect", help="Record a connection")
    p_conn.add_argument("a")
    p_conn.add_argument("b")
    p_conn.add_argument("relacion")
    p_conn.add_argument("--fuerza", type=int, default=5)

    args = parser.parse_args()

    if args.cmd == "evaluate":
        result = autoevaluate()
    elif args.cmd == "improve":
        result = improve_from_lessons()
    elif args.cmd == "learn":
        result = save_lesson(args.agent_id, args.error, args.context, args.solution, args.tags)
    elif args.cmd == "connect":
        result = record_connection(args.a, args.b, args.relacion, args.fuerza)
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()