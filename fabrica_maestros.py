#!/usr/bin/env python3
"""Fábrica de Maestros — CLI independiente para crear/registrar/validar maestros."""

import argparse
import json
import sys
from pathlib import Path

REPO_PATH = Path(__file__).parent.resolve()


def load_maestros():
    agent_dir = REPO_PATH / "agent_directory.json"
    return json.loads(agent_dir.read_text(encoding="utf-8"))


def save_maestros(data):
    agent_dir = REPO_PATH / "agent_directory.json"
    agent_dir.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_maestro(maestro_id, dominio, division, especialidades, emoji="❓", automatizable=False):
    return {
        "emoji": emoji,
        "dominio": dominio,
        "division": division,
        "especialidades": especialidades,
        "automatizable": automatizable,
    }


def register_maestro(maestro_id, maestro_data):
    data = load_maestros()
    data["maestros"][maestro_id] = maestro_data
    save_maestros(data)
    return data["maestros"]


def unregister_maestro(maestro_id):
    data = load_maestros()
    removed = data["maestros"].pop(maestro_id, None)
    if removed is None:
        raise KeyError(f"Maestro '{maestro_id}' not found")
    save_maestros(data)
    return removed


def list_maestros():
    data = load_maestros()
    return data.get("maestros", {})


def validate_network():
    data = load_maestros()
    maestros = data.get("maestros", {})
    especialistas = data.get("especialistas", {})

    errors = []
    warnings = []
    maestro_ids = set(maestros.keys())
    esp_ids = set(especialistas.keys())

    # 1. Every especialista must reference a valid maestro
    for esp_id, esp_data in especialistas.items():
        m = esp_data.get("maestro", "")
        if m not in maestro_ids:
            errors.append(f"especialista '{esp_id}' references unknown maestro '{m}'")

    # 2. Every maestro must have at least one especialista
    maestros_with_esps = {esp_data.get("maestro") for esp_data in especialistas.values()}
    for m_id in maestro_ids:
        if m_id not in maestros_with_esps:
            warnings.append(f"maestro '{m_id}' has no especialistas assigned")

    # 3. Circular cross-references (A→B→A)
    cross_refs = {}
    for m_id, m_data in maestros.items():
        div = m_data.get("division", "")
        if "→" in div:
            target = div.split("→")[1].strip().replace("usa ", "")
            cross_refs[m_id] = target

    for a, b in cross_refs.items():
        if b in cross_refs and cross_refs[b] == a:
            errors.append(f"circular cross-ref: {a} ↔ {b}")

    # 5. Duplicate capabilities
    cap_owners = {}
    for esp_id, esp_data in especialistas.items():
        for cap in esp_data.get("capacidades", []):
            cap = cap.lower().strip()
            if cap in cap_owners:
                warnings.append(f"capability '{cap}' owned by both '{cap_owners[cap]}' and '{esp_id}'")
            else:
                cap_owners[cap] = esp_id

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "maestros": len(maestro_ids),
        "especialistas": len(esp_ids),
    }


def get_maestro_graph():
    data = load_maestros()
    maestros = data.get("maestros", {})
    especialistas = data.get("especialistas", {})

    graph = {}
    for m_id, m_data in maestros.items():
        esp_list = [e for e, ed in especialistas.items() if ed.get("maestro") == m_id]
        cross = []
        div = m_data.get("division", "")
        if "→" in div:
            target = div.split("→")[1].strip().replace("usa ", "")
            cross = [target]

        graph[m_id] = {
            "dominio": m_data.get("dominio", ""),
            "division": div,
            "emoji": m_data.get("emoji", "❓"),
            "automatizable": m_data.get("automatizable", False),
            "especialistas": esp_list,
            "cross_refs": cross,
        }
    return graph


def main():
    parser = argparse.ArgumentParser(
        description="Fábrica de Maestros — Crear, registrar, validar la red de Agentes-Maestros"
    )
    sub = parser.add_subparsers(dest="cmd")

    # build-maestro
    bm = sub.add_parser("build-maestro", help="Register a new maestro")
    bm.add_argument("maestro_id", help="Maestro ID (e.g. COORD)")
    bm.add_argument("--dominio", "-d", required=True)
    bm.add_argument("--division", "-v", required=True)
    bm.add_argument("--especialidades", "-e", required=True, help="Comma-separated")
    bm.add_argument("--emoji", "-m", default="❓")
    bm.add_argument("--automatizable", "-a", action="store_true")

    # unregister-maestro
    rm = sub.add_parser("unregister-maestro", help="Remove a maestro")
    rm.add_argument("maestro_id")

    # list-maestros
    sub.add_parser("list-maestros", help="List all maestros")

    # validate-network
    sub.add_parser("validate-network", help="Validate network integrity")

    # maestro-graph
    sub.add_parser("maestro-graph", help="Show maestro dependency graph")

    args = parser.parse_args()

    if args.cmd == "build-maestro":
        data = build_maestro(
            args.maestro_id, args.dominio, args.division,
            [e.strip() for e in args.especialidades.split(",")],
            args.emoji, args.automatizable,
        )
        register_maestro(args.maestro_id, data)
        print(f"✅ Maestro '{args.maestro_id}' registrado ({args.dominio}/{args.division})")

    elif args.cmd == "unregister-maestro":
        removed = unregister_maestro(args.maestro_id)
        print(f"🗑️ Maestro '{args.maestro_id}' removido")

    elif args.cmd == "list-maestros":
        maestros = list_maestros()
        for mid, mdata in sorted(maestros.items()):
            esps = [e for e, ed in load_maestros().get("especialistas", {}).items() if ed.get("maestro") == mid]
            print(f"  {mdata.get('emoji','❓')} {mid} — {mdata.get('dominio')}/{mdata.get('division')} ({len(esps)} especialistas)")

    elif args.cmd == "validate-network":
        result = validate_network()
        if result["ok"]:
            print(f"✅ Red válida: {result['maestros']} maestros, {result['especialistas']} especialistas")
        else:
            print(f"❌ Red inválida: {len(result['errors'])} errores, {len(result['warnings'])} advertencias")
        for e in result["errors"]:
            print(f"  ❌ {e}")
        for w in result["warnings"]:
            print(f"  ⚠️  {w}")
        sys.exit(0 if result["ok"] else 1)

    elif args.cmd == "maestro-graph":
        graph = get_maestro_graph()
        for mid, gdata in sorted(graph.items()):
            cross = " → " + ", ".join(gdata["cross_refs"]) if gdata["cross_refs"] else ""
            print(f"  {gdata['emoji']} {mid} [{gdata['dominio']}/{gdata['division']}]{cross}")
            for esp in gdata["especialistas"]:
                print(f"      └─ {esp}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()