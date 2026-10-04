#!/usr/bin/env python3
"""Fire drill end-to-end: gestion-emocional capability."""
import json, sys, importlib, re, subprocess
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
print("FUEGO END-TO-END: gestion-emocional")
print("=" * 60)

# Step 1: Crear especialista health-emotional-coach
print("\n1. CREANDO health-emotional-coach...")
import neural_fellowship
from neural_fellowship import AGENTES_MAESTROS, AGENTES_ESPECIALIZADOS
from hermes_bridge import register_maestro, build_maestro, build_capability_index, query_capability, route_task

# Update agent_directory.json with improved capabilities
with open(REPO / 'agent_directory.json') as f:
    ad = json.load(f)

ad['especialistas']['health-emotional-coach'] = {
    'maestro': 'MNEMOS',
    'capacidades': ['gestion-emocional', 'mental-health', 'terapia', 'salud-emocional', 'ansiedad', 'estrés', 'bienestar-mental']
}
with open(REPO / 'agent_directory.json', 'w') as f:
    json.dump(ad, f, indent=2, ensure_ascii=False)

# Rebuild everything
build_capability_index()
print("  ✅ health-emotional-coach creado con capacidades actualizadas")

# Step 2: Capability index
print("\n2. CAPABILITY INDEX...")
with open(REPO / 'state/capability_index.json') as f:
    idx = json.load(f)
check("gestion-emocional in index", 'gestion-emocional' in idx)
if 'gestion-emocional' in idx:
    agents = idx['gestion-emocional'].get('agentes', {})
    check("health-emotional-coach in agents", 'health-emotional-coach' in agents, f"agents: {agents}")

# Step 3: Discovery
print("\n3. DESCUBRIMIENTO...")
disc = query_capability('gestion-emocional')
check("discovery finds gestion-emocional", 'gestion-emocional' in disc, f"disc keys: {list(disc.keys())[:3]}")

# Step 4: Routing
print("\n4. RUTEANDO tareas de salud mental...")
r1 = route_task('necesito ayuda con mi ansiedad y manejo del estrés')
check("r1 maestro=MNEMOS", r1['maestro']['id'] == 'MNEMOS', f"got {r1['maestro']['id']}")
check("r1 especialista=health-emotional-coach", r1['specialist']['id'] == 'health-emotional-coach', f"got {r1['specialist']['id']}")
check("r1 confianza>=50", r1['maestro']['confidence'] >= 50, f"confianza={r1['maestro']['confidence']}")

r2 = route_task('tengo estrés laboral y necesito gestionar mis emociones')
check("r2 maestro=MNEMOS", r2['maestro']['id'] == 'MNEMOS', f"got {r2['maestro']['id']}")
check("r2 especialista=health-emotional-coach", r2['specialist']['id'] == 'health-emotional-coach', f"got {r2['specialist']['id']}")

# Step 5: Reutilización
print("\n5. REUTILIZACIÓN...")
r3 = route_task('ansiedad crónica')
check("r3 especialista=health-emotional-coach", r3['specialist']['id'] == 'health-emotional-coach', f"got {r3['specialist']['id']}")

# Step 6: Persistencia
print("\n6. PERSISTENCIA...")
importlib.reload(neural_fellowship)
from neural_fellowship import AGENTES_ESPECIALIZADOS as AE2
check("health-emotional-coach survives reload", 'health-emotional-coach' in AE2)

# Step 7: No duplicación
print("\n7. NO DUPLICACIÓN...")
cap_idx_before = len(idx)
build_capability_index()
with open(REPO / 'state/capability_index.json') as f:
    idx2 = json.load(f)
check("capability count stable", len(idx2) == cap_idx_before, f"before={cap_idx_before}, after={len(idx2)}")

# Step 8: Tests finales
print("\n8. TESTS FINALES...")
result = subprocess.run(['python3', '-m', 'pytest', 'tests/', '-q'], 
                       capture_output=True, text=True, cwd=str(REPO))
output = result.stdout + result.stderr
match = re.search(r'(\d+) passed', output)
if match and 'failed' not in output.lower():
    check(f"pytest {match.group(1)} passing", True)
else:
    check("pytest all passing", False, output[:300])

print("\n" + "=" * 60)
print(f"RESULTADO: {passed} passed, {failed} failed")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)