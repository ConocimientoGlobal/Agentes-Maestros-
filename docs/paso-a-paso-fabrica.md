# Fábrica de Maestros — Paso a Paso

## Arquitectura

```
Agentes-Maestros-/
├── agent_directory.json         # Fuente de verdad (65 maestros, 243 especialistas)
├── state/
│   ├── capability_index.json    # Índice unificado de capacidades (681)
│   ├── learned_lessons.json     # Lecciones aprendidas (FASE 5)
│   └── memory_index.json        # Conexiones entre componentes (FASE 5)
├── hermes_bridge.py             # Funciones core FASE 1-bis a 5
├── neural_fellowship.py         # CLI principal (65 maestros + 243 especialistas)
├── orquestar.py                 # Orquestador dinámico FASE 3
├── autoeval.py                  # Autoevaluación FASE 5
├── skill_autogen.py             # Autogeneración de skills FASE 4
├── hermes-skill/                # 245 skills autogeneradas
│   └── <specialist_id>/SKILL.md
├── tests/test_neural_fellowship.py  # 112 tests
└── docs/paso-a-paso-fabrica.md      # Este documento
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

### 7. Consultar capacidades
```bash
python3 neural_fellowship.py --capabilities --build-cap-index
python3 neural_fellowship.py --cap-query "identidad-marca"
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