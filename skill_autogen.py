#!/usr/bin/env python3
"""Skill Autogenerada — auto-crea skills Hermes para especialistas."""

import argparse
import json
import sys
from pathlib import Path

REPO_PATH = Path(__file__).resolve().parent
AGENT_DIR = REPO_PATH / "agent_directory.json"
CAP_INDEX = REPO_PATH / "state" / "capability_index.json"
SKILLS_DIR = REPO_PATH / "hermes-skill"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def get_specialist_info(specialist_id: str) -> dict | None:
    """Get full info for a specialist from agent_directory.json."""
    agent_dir = load_json(AGENT_DIR)
    specialists = agent_dir.get("especialistas", {})
    if specialist_id in specialists:
        spec = specialists[specialist_id]
        spec["id"] = specialist_id
        return spec
    return None


def get_maestro_for_specialist(specialist_id: str) -> dict | None:
    """Get maestro info for a specialist."""
    agent_dir = load_json(AGENT_DIR)
    specialists = agent_dir.get("especialistas", {})
    maestros = agent_dir.get("maestros", {})
    if specialist_id not in specialists:
        return None
    maestro_id = specialists[specialist_id].get("maestro")
    if maestro_id in maestros:
        m = maestros[maestro_id]
        m["id"] = maestro_id
        return m
    return None


def generate_skill_content(specialist: dict, maestro: dict | None = None) -> str:
    """Generate SKILL.md content for a specialist."""
    spec_id = specialist.get("id", "unknown")
    name = specialist.get("nombre", spec_id)
    capacidades = specialist.get("capacidades", [])
    tags = specialist.get("tags", [])
    capabilities = specialist.get("capacidades", [])
    maestro_name = maestro.get("nombre", maestro.get("id", "?")) if maestro else "unknown"
    dominio = maestro.get("dominio", "") if maestro else ""
    emoji = maestro.get("emoji", "⚙") if maestro else "⚙"

    lines = [
        "---",
        f"name: {spec_id}",
        f"description: {name} — especialista automatizable",
        f"trigger: {', '.join(capacidades[:5])}",
        f"version: \"0.1.0\"",
        "---",
        "",
        f"# {name}",
        "",
        f"Especialista de {maestro_name} ({dominio}).",
        "",
        "## Info",
        "",
        f"- **Maestro**: {maestro_name}",
        f"- **Capacidades**: {', '.join(capacidades)}",
        f"- **Tags**: {', '.join(tags)}",
        f"- **Capacidades**: {', '.join(capacidades)}",
        "",
        "## Uso",
        "",
        f"Esta skill es autogenerada para {name}.",
        "Usá `orquestar.py orquestar \"<task>\"` para activar automáticamente.",
        "",
        "## Acciones",
        "",
    ]
    for c in capacidades:
        lines.append(f"- `{c}`: usar capacidad {c}")

    return "\n".join(lines) + "\n"


def create_skill(specialist_id: str, overwrite: bool = False) -> dict:
    """Create a skill directory for a specialist."""
    specialist = get_specialist_info(specialist_id)
    if not specialist:
        return {"error": f"Especialista '{specialist_id}' no encontrado"}

    capabilities = specialist.get("capacidades", [])
    if not capabilities:
        return {"error": f"Especialista '{specialist_id}' sin capacidades"}

    maestro = get_maestro_for_specialist(specialist_id)
    content = generate_skill_content(specialist, maestro)

    skill_dir = SKILLS_DIR / specialist_id.replace("-", "_")
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"

    if skill_file.exists() and not overwrite:
        return {"error": f"Skill ya existe: {skill_dir}", "path": str(skill_file)}

    skill_file.write_text(content, encoding="utf-8")
    return {
        "created": True,
        "specialist": specialist_id,
        "skill_path": str(skill_file),
        "maestro": maestro.get("id") if maestro else None,
        "capacidades": capabilities,
    }


def list_automatizable() -> list:
    """List all specialists that can have skills auto-generated."""
    agent_dir = load_json(AGENT_DIR)
    specialists = agent_dir.get("especialistas", {})
    auto = []
    for sid, data in specialists.items():
        if data.get("capacidades"):
            m = get_maestro_for_specialist(sid)
            auto.append({
                "id": sid,
                "nombre": data.get("nombre", sid),
                "maestro": m.get("id") if m else None,
                "capacidades": data.get("capacidades", []),
            })
    return auto


def main():
    parser = argparse.ArgumentParser(description="Skill Autogenerada")
    sub = parser.add_subparsers(dest="cmd")

    p_create = sub.add_parser("create", help="Crear skill para un especialista")
    p_create.add_argument("specialist_id")
    p_create.add_argument("--overwrite", action="store_true")

    p_list = sub.add_parser("list", help="Listar especialistas automatizables")

    p_bulk = sub.add_parser("bulk-create", help="Crear skills para todos los automatizables")

    args = parser.parse_args()

    if args.cmd == "create":
        result = create_skill(args.specialist_id, overwrite=args.overwrite)
    elif args.cmd == "list":
        result = {"automatizable": list_automatizable(), "count": len(list_automatizable())}
    elif args.cmd == "bulk-create":
        auto = list_automatizable()
        created, errors = [], []
        for s in auto:
            r = create_skill(s["id"])
            if r.get("created"):
                created.append(s["id"])
            else:
                errors.append({"id": s["id"], "error": r.get("error")})
        result = {"created": created, "errors": errors, "total": len(auto)}
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()