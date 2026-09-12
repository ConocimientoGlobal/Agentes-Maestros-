# Neural Fellowship — Red Neuronal de Agentes Autónomos

Sistema de orquestación multi-agente: **63 agentes maestros** + **243 agentes especializados** + routing engine + auto-executor + detector de tareas.

## Estructura

```
neural_fellowship.py   → Sistema completo (toda la lógica)
```

## Uso

```bash
# Escanear ecosistema y generar propuestas
python3 neural_fellowship.py

# Auto-ejecutar tareas mecánicas
python3 neural_fellowship.py --auto

# Ruta al agente correcto para una tarea
python3 neural_fellowship.py --route "Necesito hacer una campaña de email marketing"

# Listar 243 agentes especializados
python3 neural_fellowship.py --agents

# Listar 63 agentes maestros
python3 neural_fellowship.py --maestros
```

## Arquitectura

```
Tarea entrante
      │
      ▼
┌─────────────────┐
│   Orquestador   │  ← Routing Engine (keywords → maestro + especialista)
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────────┐
│Mecánica│ │  Requiere IA│
└───┬────┘ └─────┬──────┘
    │            │
    ▼            ▼
┌─────────┐ ┌──────────┐
│Auto-Exec│ │Cola IA   │
│(directo)│ │(agente)  │
└─────────┘ └──────────┘
```

## 63 Agentes Maestros

| Maestro | Dominio | División |
|---------|---------|----------|
| ARCAN | Creatividad | design |
| ORION | Investigación | research + academic |
| NEXUS | Desarrollo | engineering |
| AURUM | Finanzas | finance |
| SENTINEL | Seguridad | security |
| MERIDIAN | Productividad | project-management + product |
| AGENCY | Comercial | marketing + sales + paid-media |
| HELIOS | Web/GIS | gis + spatial-computing |
| CRONUS | Game Dev | game-development |
| MNEMOS | Memoria/Salud | healthcare + specialized |
| + 53 más... | | |

## 243 Agentes Especializados

Cada maestro contiene entre 3-15 especialistas con capacidades específicas. Ejemplos:

- **NEXUS**: Frontend Developer, Backend Architect, AI Engineer, DevOps Automator, SRE, Prompt Engineer, RAG Pipeline Engineer...
- **AGENCY**: SEO Specialist, Content Creator, Email Marketing Strategist, Growth Hacker, Proposal Strategist...
- **SENTINEL**: Penetration Tester, AppSec Engineer, Security Architect, Compliance Auditor...
- **ARCAN**: Brand Guardian, UI Designer, UX Architect, Image Prompt Engineer...

## Detección Automática de Tareas

El sistema escanea:
- `~/knowledge/_projects/*.md` — Proyectos con sección `## Pendiente`
- `~/knowledge/_active/*/task_plan.md` — Planes de tarea con `- [ ]`
- `~/knowledge/TODAY.md` — Tareas diarias

Genera propuestas con prioridad (alta/media/baja) y permite ejecución selectiva.

## Auto-Executor

Tareas mecánicas reconocidas:
- `crear carpeta/directorio <path>` → `mkdir`
- `crear archivo <path>` → `touch`
- `instalar paquete <pkg>` → `pip install`
- `copiar <src> a <dst>` → `cp`
- `mover <src> a <dst>` → `mv`
- `eliminar archivo <path>` → `rm`
- `git commit <mensaje>` → `git add . && git commit`
- `git push` → `git push`
- `ejecutar <cmd>` → subprocess
- `crear markdown <path>` → crear .md

Las tareas que no coinciden con ningún patrón se encolan para un agente IA.

## State & Queue

- `executor_state.json` — Tareas ya ejecutadas (no se repiten)
- `agent_queue.json` — Cola de tareas pendientes para agente
- `executor-YYYYMMDD.log` — Log de ejecuciones

## Integración con Hermes

Este sistema es el backend de agentes del ecosistema Hermes Agent. El orchestrator de Hermes delega tareas a este sistema para ruteo y ejecución automática.

---

**Licencia:** MIT
