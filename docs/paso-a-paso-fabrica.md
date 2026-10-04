# Fábrica de Maestros — Paso a Paso

## Arquitectura

```
maestro-fabrica/
├── hermes_bridge.py          # Funciones core (build/register/unregister/validate/graph)
├── fabrica_maestros.py       # CLI standalone
├── hermes-skill/maestro-fabrica/SKILL.md  # Skill conversacional
└── tests/test_neural_fellowship.py        # 10 tests TestFabricaMaestros
```

## Pasos

### 1. Crear un maestro
```bash
python3 fabrica_maestros.py build-maestro COORD \
  -d "coordinación" -v "dev" \
  -e "python,bash,terraform" -m ⚙
```

### 2. Registrar maestro existente
```python
from hermes_bridge import register_maestro, build_maestro
m = build_maestro("NUEVO", "dom", "div", ["cap1"])
register_maestro("NUEVO", m)
```

### 3. Listar maestros
```bash
python3 fabrica_maestros.py list-maestros
```

### 4. Validar red
```bash
python3 fabrica_maestros.py validate-network
# Salida: ✅ Red válida o ❌ errores + ⚠️ advertencias
```

### 5. Ver grafo de dependencias
```bash
python3 fabrica_maestros.py maestro-graph
```

### 6. Desregistrar
```bash
python3 fabrica_maestros.py unregister-maestro COORD
```

## Validación automática
- Huérfanos: especialistas sin maestro válido
- Ciclos: cross-referencias circulares (A→B→A)
- Duplicados: capacidades compartidas entre especialistas
- Sin especialistas: maestros sin asignación

## Integración con skill
Skill `maestro-fabrica` usa `skill_manage` para crear skills de maestro,
`memory()` para persistir, `cronjob_manage` para automatización.
```