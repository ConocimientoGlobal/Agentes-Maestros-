#!/usr/bin/env python3
"""Orquestador Dinámico — task → capability → especialista → maestro."""

import argparse
import json
import sys
from pathlib import Path

REPO_PATH = Path(__file__).resolve().parent
AGENT_DIR = REPO_PATH / "agent_directory.json"
CAP_INDEX = REPO_PATH / "state" / "capability_index.json"


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


def main():
    parser = argparse.ArgumentParser(description="Orquestador Dinámico")
    sub = parser.add_subparsers(dest="cmd")

    p_orch = sub.add_parser("orquestar", help="Route task to master/especialista")
    p_orch.add_argument("task", help="Task description")
    p_orch.add_argument("--top", type=int, default=3, help="Top capabilities")

    p_cap = sub.add_parser("query-cap", help="Query capability index")
    p_cap.add_argument("text", help="Search text")
    p_cap.add_argument("--top", type=int, default=5)

    p_master = sub.add_parser("routing", help="Find master for a capability")
    p_master.add_argument("capability", help="Capability name")

    args = parser.parse_args()
    if args.cmd == "orquestar":
        result = orquestar(args.task, args.top)
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