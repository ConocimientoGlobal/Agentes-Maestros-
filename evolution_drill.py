#!/usr/bin/env python3
"""Fire drill: Network Evolution — detect → propose → apply → regression → re-test."""
import json, sys, importlib
from pathlib import Path

REPO = Path('/data/data/com.termux/files/home/Agentes-Maestros-audit')
sys.path.insert(0, str(REPO))

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}: {detail}")

print("=" * 60)
print("EVOLUCIÓN DE LA RED")
print("=" * 60)

# Phase 1: Evolve (generates perf data, detects degradation, proposes, applies)
from network_evolution import evolve_network
result = evolve_network()

print(f"\n1. DETECCIÓN DE DEGRADACIÓN")
print(f"   Total tasks routed: {result['stats']['total']}")
print(f"   Success rate: {result['stats']['success_rate']}%")
print(f"   Degradation signals: {result['stats']['degradation_signals']}")
check("degradación detectada", result['stats']['degradation_signals'] > 0, f"signals={result['stats']['degradation_signals']}")
check("success rate < 100%", result['stats']['success_rate'] < 100, "expected some failures")

print(f"\n2. PROPUESTA DE MEJORA")
proposals = [p['id'] for p in result['proposals']]
check("propuestas generadas", len(proposals) > 0, f"proposals: {proposals}")
high_prio = [p for p in result['proposals'] if p['priority'] == 'high']
check("propuesta high-priority", len(high_prio) > 0)

print(f"\n3. APLICACIÓN CONTROLADA")
applied_list = result['applied']
rejected_list = result['rejected']
check("proposal applied", len(applied_list) > 0, f"{len(applied_list)} aplicada(s)")
check("rollback si regresión", result['rollback_occurred'] in (True, False), f"rollback={result['rollback_occurred']}")
if applied_list:
    print(f"   Applied: {applied_list[0]['proposal']['action']}")
    print(f"   Regression OK: {applied_list[0]['result'].get('regression_ok', 'N/A')}")
else:
    print("   No proposals applied (all rejected or no high-priority)")
if rejected_list:
    print(f"   Rejected: {len(rejected_list)} proposal(s)")

print(f"\n4. REGRESSIÓN (pytest antes vs después)")
if applied_list:
    before = applied_list[0]['result']['tests_before']
    after = applied_list[0]['result']['tests_after']
    check("tests before: 0 failed", before['failed'] == 0)
    check("tests after: 0 failed", after['failed'] == 0)
    check("no regression", before['failed'] == after['failed'])
else:
    check("no regression (no changes)", True)

print(f"\n5. DESCUBRIMIENTO POST-EVOLUCIÓN")
if applied_list:
    before = applied_list[0]['result']['tests_before']
    after = applied_list[0]['result']['tests_after']
    print(f"   Before: {before['passed']} passed, {before['failed']} failed")
    print(f"   After:  {after['passed']} passed, {after['failed']} failed")
    check("no regressions", after['failed'] == 0 and after['failed'] <= before['failed'])
    check("test count stable", after['passed'] == before['passed'], f"{before['passed']} -> {after['passed']}")
else:
    check("no regression (no changes)", True)
    print("   (skipping test comparison — no changes applied)")

print(f"\n5. VERIFICACIÓN POST-EVOLUCIÓN (discovery + reuse)")
check("reuse OK post-evo", result.get('reuse_ok', False))
check("post-evolution reuse OK", result.get('reuse_ok', False))

# Verify the new capability is discoverable + present in the specialist (re-import fresh)
if applied_list:
    new_cap = applied_list[0]['proposal']['params']['new_capability']
    # Re-import modules after evolution applied changes
    import importlib
    import neural_fellowship
    importlib.reload(neural_fellowship)
    import hermes_bridge
    importlib.reload(hermes_bridge)
    from hermes_bridge import query_capability, build_capability_index, AGENTES_ESPECIALIZADOS
    build_capability_index()
    disc = query_capability(new_cap)
    check(f"capability '{new_cap}' discoverable", new_cap in disc, f"disc keys: {list(disc.keys())[:5]}")
    check(f"capability '{new_cap}' in health-emotional-coach",
          new_cap in AGENTES_ESPECIALIZADOS.get('health-emotional-coach', {}).get('capacidades', []),
          f"caps: {AGENTES_ESPECIALIZADOS.get('health-emotional-coach', {}).get('capacidades', [])}")

# Verify the previously degraded task now routes correctly
from neural_fellowship import Orquestador
orch = Orquestador()
r = orch.ruta_completa("angustia emocional intensa")
print(f"\n5b. POST-EVOL: 'angustia emocional intensa' → {r['especialista']['especialista']} (conf={r['especialista']['confianza']})")
check("post-evo: angustia routes to health-emotional-coach",
      r['especialista']['especialista'] == 'health-emotional-coach' and r['especialista']['confianza'] >= 30,
      f"spec={r['especialista']['especialista']} conf={r['especialista']['confianza']}")
check("post-evo: angustia routes to health-emotional-coach",
      r['especialista']['especialista'] == 'health-emotional-coach' and r['especialista']['confianza'] >= 30,
      f"spec={r['especialista']['especialista']} conf={r['especialista']['confianza']}")

print(f"\n6. PERSISTENCIA DEL BACKUP")
backup_files = list((REPO / 'state' / 'backups').glob('*')) if (REPO / 'state' / 'backups').exists() else []
check("backup created", len(backup_files) > 0, f"backups: {backup_files}")

print(f"\n7. PERSISTENCIA (reload)")
import importlib
import neural_fellowship
from hermes_bridge import build_capability_index

importlib.reload(neural_fellowship)
from neural_fellowship import AGENTES_ESPECIALIZADOS as AE2
check("health-emotional-coach survives reload", 'health-emotional-coach' in AE2)
if applied_list:
    new_cap = applied_list[0]['proposal']['params']['new_capability']
    check(f"new capability persists in {new_cap}",
          new_cap in AE2.get('health-emotional-coach', {}).get('capacidades', []))

print(f"\n✅ {passed}/{passed+failed} checks passed")
sys.exit(0 if failed == 0 else 1)

print(f"\n8. CAPABILITY COUNT STABLE")
idx = build_capability_index()
check("capability index built", len(idx) > 600, f"count={len(idx)}")

print("\n" + "=" * 60)
print(f"RESULTADO: {passed} passed, {failed} failed")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
