#!/usr/bin/env python3
"""Fire drill: crear health-emotional-coach y probar routing end-to-end."""
import json, sys
from pathlib import Path

REPO = Path('/data/data/com.termux/files/home/Agentes-Maestros-audit')
sys.path.insert(0, str(REPO))

# Step 1: Crear especialista
dir_file = REPO / 'agent_directory.json'
d = json.loads(dir_file.read_text(encoding='utf-8'))
d['especialistas']['health-emotional-coach'] = {
    'maestro': 'MNEMOS',
    'capacidades': ['gestion-emocional', 'mental-health', 'terapia']
}
dir_file.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
print('1. CREADO health-emotional-coach con capacidades: gestion-emocional, mental-health, terapia')

# Step 2: Reconstruir capability index
from hermes_bridge import build_capability_index, query_capability
idx = build_capability_index()
print(f'\n2. CAPABILITY INDEX: {len(idx)} capacidades')
print(f'   gestion-emocional in idx: {"gestion-emocional" in idx}')
if 'gestion-emocional' in idx:
    print(f'   agentes: {list(idx["gestion-emocional"]["agentes"].keys())}')

# Step 3: Verificar descubrimiento
q = query_capability('gestion-emocional')
print(f'\n3. DESCUBRIMIENTO: {json.dumps(q, ensure_ascii=False)}')

# Step 4: Routing end-to-end
from neural_fellowship import Orquestador
o = Orquestador()
result = o.ruta_completa('necesito ayuda con mi ansiedad y manejo del estrés')
print(f'\n4. ROUTING:')
print(f'   Maestro: {result["maestro"]["maestro"]} (confianza: {result["maestro"]["confianza"]})')
print(f'   Especialista: {result["especialista"]["especialista"]} (confianza: {result["especialista"]["confianza"]})')
print(f'   Capacidades: {result["especialista"]["capacidades"]}')

# Step 5: Reutilización - segunda tarea con misma capacidad
result2 = o.ruta_completa('tengo estrés laboral y necesito gestionar mis emociones')
print(f'\n5. REUTILIZACIÓN:')
print(f'   Maestro: {result2["maestro"]["maestro"]} (confianza: {result2["maestro"]["confianza"]})')
print(f'   Especialista: {result2["especialista"]["especialista"]} (confianza: {result2["especialista"]["confianza"]})')
print(f'   Capacidades: {result2["especialista"]["capacidades"]}')

# Step 6: Persistencia
d2 = json.loads(dir_file.read_text(encoding='utf-8'))
print(f'\n6. PERSISTENCIA:')
print(f'   health-emotional-coach en directory: {"health-emotional-coach" in d2["especialistas"]}')
idx2 = build_capability_index()
print(f'   gestion-emocional sobrevive reload: {"gestion-emocional" in idx2}')

# Step 7: Tests
import subprocess
r = subprocess.run(['python3', '-m', 'pytest', 'tests/', '-q'], capture_output=True, text=True, cwd=str(REPO))
print(f'\n7. TESTS: {r.stdout.strip()}')
print(f'   Exit: {r.returncode}')

print(f'\n{"=" * 60}')
print('FIRE DRILL COMPLETADO')
print(f'{"=" * 60}')