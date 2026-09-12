---
name: hermes-neural-fellowship
description: "Hermes Neural Fellowship Bridge — Integración completa con Hermes Agent"
version: 2.0.0
tags: [neural-fellowship, agent-routing, delegate-task, auto-executor, learning-system]
---

# Hermes Neural Fellowship Bridge

Puente de integración real entre Hermes Agent y Neural Fellowship. Permite routing inteligente, auto-ejecución y delegación de tareas a especialistas vía `delegate_task`.

## Cuándo usar

- El usuario pide ejecutar una tarea compleja y necesita saber qué agente es el mejor
- El usuario quiere auto-ejecutar operaciones mecánicas (mkdir, git, pip, etc.)
- El usuario reporta un error y quiere registrarlo para no repetirlo
- Se necesita estado del sistema neuronal

## Flujo de Integración

```
Tarea → route_task()
         ↓
    automatizable? → True → auto_execute() → terminal
         ↓
    False → run_task() → delegate_task() con prompt del especialista
         ↓
    Especialista ejecuta vía subagente
```

## Cómo invocar desde Hermes

### 1. Obtener routing de una tarea

```python
import sys
sys.path.insert(0, '/data/data/com.termux/files/home/tmp/Agentes-Maestros-')
from hermes_bridge import route_task

result = route_task("Crear landing page con SEO")
# → {"maestro": {"id": "AGENCY", "emoji": "📢", ...}, 
#    "specialist": {"id": "marketing-seo-specialist", ...},
#    "automatizable": False}
```

### 2. Ejecutar flujo completo

```python
from hermes_bridge import run_task

result = run_task("crear carpeta ~/projects/nueva")
# Si es automatizable → ejecuta directamente
# Si no → retorna dict con 'type': 'delegate' y el prompt listo

# Si result['execution']['type'] == 'delegate':
#   Delegar a Hermes delegate_task con el prompt
```

### 3. Auto-ejecutar directamente

```python
from hermes_bridge import auto_execute

result = auto_execute("pip install fastapi")
# → {"status": "success", "mensaje": "..."}
```

### 4. Registrar error/lección

```python
from hermes_bridge import remember

remember("NEXUS", "ModuleNotFoundError", "FastAPI sin instalar", "pip install fastapi")
# → registra la lección para no repetir el error
```

### 5. Consultar estado

```python
from hermes_bridge import get_system_status
status = get_system_status()
# → estado completo: orchestrator, memory, learning, tasks
```

## Ejemplo real: Flujo completo con Hermes

```python
# Paso 1: Route
import sys
sys.path.insert(0, '/data/data/com.termux/files/home/tmp/Agentes-Maestros-')
from hermes_bridge import route_task

routing = route_task("Crear landing page con SEO")
print(f"Maestro: {routing['maestro']['id']}")
print(f"Especialista: {routing['specialist']['id']}")
print(f"Automatizable: {routing['automatizable']}")

# Paso 2: Según resultado
if routing['automatizable']:
    from hermes_bridge import auto_execute
    result = auto_execute("crear landing page")
    print(f"Resultado: {result}")
else:
    # Delegar a subagente con el prompt del especialista
    specialist = routing['specialist']
    maestro = routing['maestro']
    
    delegation_context = f"""
Eres {specialist['id']}, especialista en {maestro['domain']}.
Capacidades: {', '.join(specialist.get('capabilities', []))}

Tarea: Crear landing page con SEO

Instrucciones:
1. Consulta lecciones previas antes de ejecutar
2. Ejecuta la tarea
3. Reporta resultados
"""
    # Luego: delegate_task con delegation_context
    print(f"Delegar: {specialist['id']}")
```

## Comandos CLI

```bash
# Route
python3 ~/tmp/Agentes-Maestros-/hermes_bridge.py route "crear API REST"

# Run (full flow)
python3 ~/tmp/Agentes-Maestros-/hermes_bridge.py run "pip install fastapi"
python3 ~/tmp/Agentes-Maestros-/hermes_bridge.py run "crear landing" --dry-run

# Auto-execute
python3 ~/tmp/Agentes-Maestros-/hermes_bridge.py auto "crear carpeta ~/test"
python3 ~/tmp/Agentes-Maestros-/hermes_bridge.py auto "pip install fastapi" --dry-run

# Remember
python3 ~/tmp/Agentes-Maestros-/hermes_bridge.py remember \
  --agent NEXUS \
  --error "ModuleNotFoundError" \
  --context "FastAPI no instalado" \
  --solution "pip install fastapi"

# Recall
python3 ~/tmp/Agentes-Maestros-/hermes_bridge.py recall --agent NEXUS

# Warnings
python3 ~/tmp/Agentes-Maestros-/hermes_bridge.py warnings --agent NEXUS

# Checklist
python3 ~/tmp/Agentes-Maestros-/hermes_bridge.py checklist --agent NEXUS --task "deploy app"

# Memory
python3 ~/tmp/Agentes-Maestros-/hermes_bridge.py memory --query "error timeout"

# Status
python3 ~/tmp/Agentes-Maestros-/hermes_bridge.py status
```

## Componentes Neural Fellowship

| Componente | Archivo | Función |
|------------|---------|---------|
| Routing | `neural_fellowship.py` (Orquestador) | Scoring keywords → agente óptimo |
| Auto-Execute | `neural_fellowship.py` (AutoExecutor) | Ejecutar tareas mecánicas (whitelist) |
| Memory | `neural_fellowship.py` (MemorySystem) | Grafo + lecciones + contexto |
| Learning | `neural_fellowship.py` (LearningSystem) | Errores → checklists |
| Orchestrator | `neural_fellowship.py` (Orchestrator) | Estado compartido entre agentes |
| Detector | `neural_fellowship.py` (DetectorTareas) | Escanear tareas pendientes |
| Bridge | `hermes_bridge.py` | API para Hermes Agent |

## Reglas

1. **Siempre route antes de ejecutar** — no adivinar el agente
2. **Consultar lecciones** antes de tareas similares (recall_lessons)
3. **Registrar errores** después de resolverlos (remember)
4. **Automatizar lo mecánico** — AutoExecutor para mkdir, git, pip, etc.
5. **Delegar lo complejo** — delegate_task para tareas que requieren IA
6. **Verificar estado** — get_system_status para monitoreo
