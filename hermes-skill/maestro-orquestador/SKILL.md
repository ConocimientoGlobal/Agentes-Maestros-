---
name: maestro-orquestador
description: Orquesta la red de maestros y especialistas Hermes para tareas en lenguaje natural
trigger: "orquesta", "routing", "encuentra el maestro", "asigna tarea", "orquestar"
version: "0.1.0"
---

# Maestro Orquestador

Orquestación dinámica: task → capability_index → especialista → maestro.

## Uso

1. Recibir task en lenguaje natural
2. Consultar capability_index.json vía query_capability()
3. Encontrar especialista con mayor peso para la capability
4. Resolver maestro del especialista
5. Crear skill del especialista si no existe (skill_manage)
6. Ejecutar y retornar resultado

## Flujo

```
Task → orquestar.py orquestar "<task>"
     → capability_index.json (match)
     → agent_directory.json (routing)
     → skill del especialista (o crear)
     → output
```

## Comandos CLI

```bash
python3 orquestar.py orquestar "<task>" --top 3
python3 orquestar.py query-cap "optimizar SQL" --top 5
python3 orquestar.py routing "sql"
```

## Validación

- Sin capacidades match → feedback al usuario
- Múltiples matches → ranking por score + peso
- Especialista sin maestro → advertencia
- Skill no existe → crear vía skill_manage

## Integración

- hermes_bridge.py: query_capability(), build_capability_index()
- capability_index.json: 681 capacidades
- agent_directory.json: 243 especialistas, 65 maestros