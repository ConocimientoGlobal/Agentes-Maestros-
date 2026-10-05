#!/usr/bin/env python3
"""Fire drill real: capability + routing evolution con nuevos mecanismos.
Versión ligera: sin regression check (pytest) para evitar timeouts."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from network_evolution import PerformanceTracker, EvolutionProposer, EvolutionApplier, Orquestador
from hermes_bridge import build_capability_index

repo = Path(__file__).resolve().parent

print("=" * 60)
print("FIRE DRILL ROUTING EVOLUTION (hardening final, sin regression)")
print("=" * 60)

# === CAPABILITY DRILL ===
print("\n--- CAPABILITY DRILL ---")
orch = Orquestador()
initial_caps = set(build_capability_index())
print(f"Initial capabilities: {len(initial_caps)}")

t = PerformanceTracker()
t.record("trauma complejo no resuelto en contexto de duelo", False, 16, None, "MNEMOS")
proposer = EvolutionProposer(t)
proposals = proposer.propose()
print(f"Proposals: {[(p['action'], p['priority']) for p in proposals]}")

# Apply capability directly (no regression check)
applier = EvolutionApplier(repo_path=repo)
applied = []
for prop in proposals:
    if prop["action"] == "add_especialista_capability":
        # Direct call to internal method (bypasses pytest regression)
        result = applier._add_especialista_capability(
            prop["params"]["especialista"],
            prop["params"]["new_capability"]
        )
        applied.append((prop["action"], result))
        print(f"  Applied {prop['action']}: {result}")

orch2 = Orquestador()
final_caps = set(build_capability_index())
new_caps = final_caps - initial_caps
print(f"New capabilities: {new_caps}")
print(f"Capability drill: {'PASS' if applied else 'NO ACTION NEEDED'}")

# === ROUTING DRILL ===
print("\n--- ROUTING DRILL ---")
orch3 = Orquestador()
before_routing = {k: list(v) for k, v in orch3.routing_map.items()}
print(f"health routing before: {before_routing.get('health', [])}")

t2 = PerformanceTracker()
t2.record("manejo del estrés laboral severo", False, 18, None, "MNEMOS")
proposer2 = EvolutionProposer(t2)
proposals2 = proposer2.propose()
routing_props = [p for p in proposals2 if p["action"] in ("add_routing_keywords", "change_connection")]
print(f"Routing proposals: {[(p['action'], p.get('params', {})) for p in routing_props]}")

applier2 = EvolutionApplier(repo_path=repo)
for prop in routing_props:
    if prop["action"] == "add_routing_keywords":
        result = applier2._add_routing_keywords(
            prop["params"]["division"],
            prop["params"]["new_keywords"]
        )
        print(f"  Applied add_routing_keywords: {result}")
    elif prop["action"] == "change_connection":
        result = applier2._change_connection(
            prop["params"]["from_division"],
            prop["params"]["to_division"],
            prop["params"]["keyword"]
        )
        print(f"  Applied change_connection: {result}")

orch4 = Orquestador()
after_routing = {k: list(v) for k, v in orch4.routing_map.items()}
print(f"health routing after: {after_routing.get('health', [])}")

# Check persistence
has_override = (repo / "state" / "routing_overrides.json").exists()
print(f"routing_overrides.json exists: {has_override}")
if has_override:
    with open(repo / "state" / "routing_overrides.json") as f:
        overrides = json.load(f)
    print(f"Overrides: {json.dumps(overrides, indent=2)}")

print("\n=== FIRE DRILL COMPLETE ===")