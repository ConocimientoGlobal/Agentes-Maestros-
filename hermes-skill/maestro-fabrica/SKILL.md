---
name: maestro-fabrica
description: Crea, registra, valida y orquesta la red de maestros de Agentes-Maestros. Use para agregar maestros nuevos, validar la red, listar, graficar dependencias.
triggers:
  - crear maestro
  - registrar maestro
  - validar red
  - listar maestros
  - maestro graph
  - fabrica de maestros
---

# Fábrica de Maestros — Skill de orquestación

## Uso

### Crear maestro
```
Crea un maestro con dominio "{{DOMINIO}}", división "{{DIVISION}}", especialidades [{{ESPECIALIDADES}}]
```
→ Llama a `hermes_bridge.build_maestro()` + `register_maestro()`.

### Validar red
```
Validá la red de maestros
```
→ `hermes_bridge.validate_network()`. Reporta errores y advertencias.

### Listar maestros
```
Listá todos los maestros
```
→ `hermes_bridge.list_maestros()`.

### Grafo de dependencias
```
Mostrá el grafo de maestros
```
→ `hermes_bridge.get_maestro_graph()`.

### Remover maestro
```
Remové el maestro {{MAESTRO_ID}}
```
→ `hermes_bridge.unregister_maestro()`.

## Funciones bridge (hermes_bridge.py)

- `build_maestro(id, dominio, division, especialidades, emoji, automatizable)` → dict
- `register_maestro(id, data)` → dict (persiste en agent_directory.json)
- `unregister_maestro(id)` → dict (remueve de agent_directory.json)
- `list_maestros()` → dict
- `validate_network()` → {ok, errors, warnings, maestros, especialistas}
- `get_maestro_graph()` → {maestro_id: {division, dominio, emoji, automatizable, especialistas, cross_refs}}

## Validación de red

La función `validate_network()` verifica:
1. Cada especialista referencia un maestro existente
2. Cada maestro tiene al menos un especialista
3. No hay referencias circulares (A→B→A)
4. No hay especialistas huérfanos
5. No hay capacidades duplicadas entre especialistas

## Flujo de creación

1. `build_maestro()` construye el dict
2. `register_maestro()` persiste en `agent_directory.json`
3. Opcional: `validate_network()` verifica integridad
4. Opcional: `skill_manage` crea skill individual del maestro

## Integración con neural_fellowship.py

```bash
python3 neural_fellowship.py --build-maestro NUEVO --dominio "dev" --division "coordinación" --especialidades "espec1,espec2" --emoji "⚙"
python3 neural_fellowship.py --validate-network
python3 neural_fellowship.py --list-maestros
python3 neural_fellowship.py --maestro-graph
```
