---
name: hermes-neural-fellowship
description: Use when Hermes needs to route tasks to Neural Fellowship agent network, auto-execute mechanical tasks, or learn from errors. Bridges Hermes Agent with the Neural Fellowship multi-agent system (63 maestros + 85 especialistas).
version: 1.0.0
tags: [neural-fellowship, agent-routing, auto-executor, learning-system, multi-agent]
---

# Hermes Neural Fellowship Bridge

Integration bridge between Hermes Agent and the Neural Fellowship multi-agent system. Provides intelligent task routing, auto-execution of mechanical tasks, and learning from errors.

## Trigger Conditions

- User asks to "route a task" or "find the right agent"
- User wants to auto-execute file/system operations (mkdir, git, pip, etc.)
- User reports an error that should be remembered for future reference
- User asks for "system status" of Neural Fellowship
- User wants to recall past lessons learned by an agent

## Workflow: Tarea → Neural Fellowship → Ejecución

```
┌─────────────────────────────────────────────────────────────┐
│                     HERMES AGENT                            │
│                                                             │
│  1. Recibe tarea del usuario                                │
│         │                                                   │
│         ▼                                                   │
│  2. Invoca route_task(description) via hermes_bridge.py     │
│         │                                                   │
│         ▼                                                   │
│  3. Neural Fellowship determina:                            │
│     - Maestro óptimo (NEXUS, ARCAN, AGENCY, etc.)           │
│     - Especialista (engineering-backend-architect, etc.)    │
│     - Nivel de automatización (True/False)                  │
│         │                                                   │
│         ├──► automatizable=True ──► auto_execute()          │
│         │                         → terminal/direct exec     │
│         │                                                   │
│         └──► automatizable=False ──► delegate_task()        │
│                                   → specialist prompt       │
│                                   → IA agent execution      │
└─────────────────────────────────────────────────────────────┘
```

## Step-by-Step Integration

### Step 1: Route the Task

```python
import sys
sys.path.insert(0, '/data/data/com.termux/files/home/tmp/Agentes-Maestros-')
from hermes_bridge import route_task

result = route_task("Crear landing page con React y Tailwind")
# Returns:
# {
#   "maestro": {"id": "NEXUS", "dominio": "Desarrollo", "confianza": 85, ...},
#   "especialista": {"id": "engineering-frontend-developer", "confianza": 60, ...},
#   "automatizable": True
# }
```

### Step 2: Check Lessons (pre-execution)

```python
from hermes_bridge import recall_lessons, generate_pre_execution_checklist

agent_id = result["especialista"]["id"]  # "engineering-frontend-developer"
lessons = recall_lessons(agent_id)
checklist = generate_pre_execution_checklist(agent_id, "Crear landing page con React y Tailwind")
```

### Step 3a: Auto-Execute (mechanical tasks)

If `automatizable=True` and the task is mechanical:

```python
from hermes_bridge import auto_execute

exec_result = auto_execute("crear carpeta ~/projects/landing-page")
# Returns: {"status": "success", "accion": "mkdir", ...}
```

Or use `dry_run=True` to preview without executing:
```python
preview = auto_execute("git commit Initial commit", dry_run=True)
```

### Step 3b: Delegate to IA Agent (creative/complex tasks)

If `automatizable=False`, use Hermes `delegate_task` with the specialist prompt:

```
delegate_task(
    prompt=f"""Eres el especialista {result['especialista']['id']} 
    (Maestro: {result['maestro']['id']} - {result['maestro']['dominio']}).
    
    Capacidades: {', '.join(result['especialista']['capacidades'])}
    
    Lecciones previas:
    {chr(10).join(f'- {l["error"]}: {l["solution"]}' for l in lessons)}
    
    Tarea: {description}""",
    task_type="specialist"
)
```

### Step 4: Remember Errors (post-execution)

If an error occurs during execution:

```python
from hermes_bridge import remember

remember(
    agent_id="NEXUS",
    error="ModuleNotFoundError: react-scripts",
    context="Creando proyecto React con create-react-app",
    solution="npm install react-scripts --save-dev",
    tags=["react", "npm", "dependencies"]
)
```

## Function Reference

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `route_task(description)` | str | dict | Routes task to optimal agent |
| `auto_execute(description, dry_run)` | str, bool | dict | Auto-executes mechanical tasks |
| `remember(agent_id, error, context, solution)` | str×4 | dict | Records error as lesson |
| `recall_lessons(agent_id)` | str | list | Retrieves agent's past lessons |
| `get_system_status()` | — | dict | Full system status |
| `get_warnings_for_agent(agent_id)` | str | list | Frequent errors (2+ occurrences) |
| `generate_pre_execution_checklist(agent_id, task)` | str×2 | list | Pre-execution checklist |
| `search_memory(query)` | str | list | Searches memory graph |

## Real-World Examples

### Example 1: Web Development Task

**User:** "Crear API REST con FastAPI y PostgreSQL"

**Hermes workflow:**
1. `route_task("Crear API REST con FastAPI y PostgreSQL")` → NEXUS, engineering-backend-architect
2. `recall_lessons("engineering-backend-architect")` → check for past DB connection errors
3. Since `automatizable=True` for NEXUS → delegate to backend architect agent with context
4. Agent creates the API code
5. If error: `remember("NEXUS", "psycopg2 compile error", "DB connection", "apt install libpq-dev")`

### Example 2: Marketing Campaign

**User:** "Crear campaña de email marketing para lanzamiento de producto"

**Hermes workflow:**
1. `route_task("email marketing lanzamiento")` → AGENCY, marketing-email-marketing-strategist
2. `automatizable=False` → delegate to AGENCY specialist agent
3. Agent creates campaign strategy, copy, and sequence

### Example 3: File System Automation

**User:** "Preparar estructura de proyecto Python"

**Hermes workflow:**
1. `auto_execute("crear carpeta ~/projects/mi-proyecto")` → mkdir success
2. `auto_execute("crear carpeta ~/projects/mi-proyecto/src")` → mkdir success
3. `auto_execute("crear archivo ~/projects/mi-proyecto/README.md")` → touch success

### Example 4: Error Recovery

**User:** "Tuve un error de CORS al conectar frontend con backend"

**Hermes workflow:**
1. `remember("NEXUS", "CORS error", "Frontend→Backend connection", "Add CORSMiddleware to FastAPI")`
2. Next time `route_task("frontend backend connection")` will include this lesson in context

## File Locations

- **Bridge module:** `~/tmp/Agentes-Maestros-/hermes_bridge.py`
- **Neural Fellowship core:** `~/tmp/Agentes-Maestros-/neural_fellowship.py`
- **Agent directory:** `~/tmp/Agentes-Maestros-/agent_directory.json`
- **Lessons DB:** `~/tmp/Agentes-Maestros-/references/learned_lessons.json`
- **Memory index:** `~/tmp/Agentes-Maestros-/references/memory_index.json`

## Agent Architecture

The Neural Fellowship system consists of:

- **63 Maestros** (domain nodes): NEXUS, ARCAN, AGENCY, ORION, AURUM, SENTINEL, MERIDIAN, HELIOS, CRONUS, MNEMOS, etc.
- **85 Especialistas** (leaf nodes): engineering-frontend-developer, marketing-seo-specialist, etc.
- **Orquestador**: Routes tasks to optimal agents using keyword scoring
- **AutoExecutor**: Safely executes mechanical tasks (file ops, git, pip, npm)
- **MemorySystem**: Graph-based knowledge storage with connections and tags
- **LearningSystem**: Error recording with pre-execution checklists

## Auto-Executable Patterns

The AutoExecutor recognizes these patterns:

| Pattern | Action |
|---------|--------|
| `crear carpeta/directorio X` | mkdir |
| `crear archivo X` | touch |
| `crear archivo md X` | create_md |
| `copiar X a Y` | cp |
| `mover X a Y` | mv |
| `eliminar archivo/carpeta X` | rm |
| `git commit MSG` | git_commit |
| `git push` / `git pull` | git_push/pull |
| `pip install PKG` | pip_install |
| `npm install PKG` | npm_install |
| `ejecutar CMD` | run_cmd (restricted) |

## Troubleshooting

**Issue:** `ModuleNotFoundError: No module named 'neural_fellowship'`
**Fix:** The bridge adds `~/tmp/Agentes-Maestros-` to sys.path automatically.

**Issue:** Lessons not persisting
**Fix:** Check write permissions on `~/tmp/Agentes-Maestros-/references/`

**Issue:** Route returns PHOENIX (default)
**Fix:** Task description is too generic; add domain-specific keywords (design, code, research, etc.)

## CLI Testing

Test the bridge directly from terminal:

```bash
cd ~/tmp/Agentes-Maestros-

python3 hermes_bridge.py route -d "Crear API REST con FastAPI"
python3 hermes_bridge.py auto -d "crear carpeta ~/test-bridge" --dry-run
python3 hermes_bridge.py remember -a NEXUS -e "CORS error" -c "Frontend connection" -s "Add CORSMiddleware"
python3 hermes_bridge.py recall -a NEXUS
python3 hermes_bridge.py status
python3 hermes_bridge.py checklist -a NEXUS -d "Crear API REST"
python3 hermes_bridge.py memory -q "cors"
```
