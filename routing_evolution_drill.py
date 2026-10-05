"""
routing_evolution_drill.py — Fire drill para Evolución del Routing.

Caso: query con routing degradado → proponer change_connection o add_routing_keywords
→ aplicar → verificar routing ANTES/DEPUÉS → persistencia → regresión.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent
BACKUP_DIR = REPO / "state" / "backups"

def run_tests():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q"],
        capture_output=True, text=True, cwd=str(REPO)
    )
    return result.stdout + result.stderr

def get_routing_map():
    """Get current routing map from Orquestador."""
    sys.path.insert(0, str(REPO))
    from network_evolution import Orquestador
    orch = Orquestador()
    return {k: list(v) for k, v in orch.routing_map.items()}

def route_query(query):
    """Route a query through Orquestador."""
    sys.path.insert(0, str(REPO))
    from network_evolution import Orquestador
    orch = Orquestador()
    return orch.ruta_completa(query)

def backup_file(filename):
    """Backup a file before modification."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    src = REPO / filename
    if not src.exists():
        return None
    stamp = subprocess.run(
        ["date", "+%Y%m%d_%H%M%S"],
        capture_output=True, text=True
    ).stdout.strip()
    dst = BACKUP_DIR / f"{filename}.{stamp}"
    shutil.copy2(str(src), str(dst))
    return dst

def restore_file(backup_path, filename):
    """Restore a file from backup."""
    src = REPO / filename
    shutil.copy2(str(backup_path), str(src))

def main():
    print("=" * 60)
    print("FIRE DRILL: Evolución del Routing")
    print("=" * 60)

    # --- ANTES ---
    print("\n--- ROUTING ANTES ---")
    routing_before = get_routing_map()
    for division, kws in routing_before.items():
        print(f"  {division}: {kws}")

    # Route a test query
    test_query = "necesito ayuda con manejo del estrés"
    result_before = route_query(test_query)
    print(f"\nQuery: '{test_query}'")
    print(f"  Especialista: {result_before.get('especialista', {}).get('especialista', 'N/A')}")
    print(f"  Confianza: {result_before.get('especialista', {}).get('confianza', 'N/A')}")
    print(f"  Maestro: {result_before.get('maestro', {}).get('maestro', 'N/A')}")

    # --- PROPOSAL: add_routing_keywords ---
    print("\n--- PROPUESTA ---")
    print("  Acción: add_routing_keywords")
    print("  Division: health")
    print("  Keywords: ['estrés', 'manejo']")
    print("  Motivo: 'estrés' no está en routing_map['health'], degrada el routing")

    # --- APPLY ---
    print("\n--- APLICANDO ---")
    from network_evolution import EvolutionApplier, EvolutionProposer, PerformanceTracker

    applier = EvolutionApplier()
    proposal = {
        "id": "add_routing_kw_health_estrés",
        "action": "add_routing_keywords",
        "priority": "high",
        "reason": "Query con 'estrés' no tiene keyword en routing_map['health']",
        "params": {
            "division": "health",
            "new_keywords": ["estrés", "manejo"],
            "task": test_query,
        }
    }

    # Backup before apply
    backup = backup_file("hermes_bridge.py")
    print(f"  Backup: {backup}")

    result = applier.apply(proposal)
    print(f"  Status: {result['status']}")
    print(f"  Regression OK: {result.get('regression_ok', 'N/A')}")

    # --- DESPUÉS ---
    print("\n--- ROUTING DESPUÉS ---")
    routing_after = get_routing_map()
    for division, kws in routing_after.items():
        print(f"  {division}: {kws}")

    # Route same query again
    result_after = route_query(test_query)
    print(f"\nQuery: '{test_query}'")
    print(f"  Especialista: {result_after.get('especialista', {}).get('especialista', 'N/A')}")
    print(f"  Confianza: {result_after.get('especialista', {}).get('confianza', 'N/A')}")
    print(f"  Maestro: {result_after.get('maestro', {}).get('maestro', 'N/A')}")

    # --- PERSISTENCE CHECK ---
    print("\n--- PERSISTENCIA ---")
    # Re-import to force fresh load
    import importlib
    import network_evolution
    importlib.reload(network_evolution)
    from network_evolution import Orquestador
    orch_fresh = Orquestador()
    fresh_routing = {k: list(v) for k, v in orch_fresh.routing_map.items()}
    print(f"  Routing después de reload: {fresh_routing.get('health', [])}")
    has_keywords = "estrés" in fresh_routing.get("health", []) or "manejo" in fresh_routing.get("health", [])
    print(f"  Keywords persistidas: {has_keywords}")

    # --- TESTS ---
    print("\n--- TESTS ---")
    test_output = run_tests()
    print(test_output[-300:] if len(test_output) > 300 else test_output)

    # --- SUMMARY ---
    print("\n--- RESUMEN ---")
    print(f"  Routing ANTES: {routing_before.get('health', [])}")
    print(f"  Routing DESPUÉS: {routing_after.get('health', [])}")
    print(f"  Keywords añadidas: {'estrés' in routing_after.get('health', [])}")
    print(f"  Persistencia OK: {has_keywords}")
    print(f"  Regresión OK: {result.get('regression_ok', False)}")

    # --- RESTORE BACKUP ---
    if backup:
        restore_file(backup, "hermes_bridge.py")
        print(f"\n  Backup restaurado: {backup}")

    return result

if __name__ == "__main__":
    main()
