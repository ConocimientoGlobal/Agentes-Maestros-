# Agente Maestros — Neural Fellowship

> Sistema neuronal de agentes autónomos: 65 maestros + 243 especialistas con routing inteligente, memoria compartida y aprendizaje de errores.

## 🧠 Arquitectura

```
Tarea → Orquestador (routing scoring) → Maestro → Especialista
                                    ↓
                              Automatizable? → AutoExecutor
                              Requiere IA?    → QueueManager (cola Hermes)
                              
Memoria: Grafo de conexiones + Lecciones + Contexto por agente
Aprendizaje: Registro de errores → Checklists pre-ejecución
Orquestador: Estado compartido + delegación entre agentes
```

## 📊 Estado Actual

| Componente | Estado | Notas |
|------------|--------|-------|
| Orquestador (routing) | ✅ Consolidado | Scoring mejorado, 65 maestros, ve los 243 especialistas del JSON |
| AutoExecutor | ✅ Consolidado | Whitelist de comandos seguros (sin `rm`) |
| Memory System | ✅ Consolidado | Grafo + lecciones + contexto. **Persiste en `<repo>/state/`** |
| Learning System | ✅ Consolidado | Checklists pre-ejecución |
| Orchestrator | ✅ Consolidado | Estado compartido + delegación |
| Detector de Tareas | ✅ Consolidado | Scans proyectos activos + TODAY |
| Queue Manager | ✅ Consolidado | Cola persistente en JSON |

## 🩹 Fase 1 — Fixes críticos (2026-10-03)

Auditoría (FASE 0) → corrección de bugs que rompían el sistema en producción:

1. **Persistencia rota** — las rutas de estado resolvían a `~/references/`
   (inexistente), así que cada guardado lanzaba `FileNotFoundError` y
   memoria/aprendizaje **nunca persistían**. Ahora escriben en `<repo>/state/`
   (creado al importar, git-ignored).
2. **Divergencia catálogo código↔JSON** — el código embebía un esquema viejo de
   96 especialistas; `agent_directory.json` tiene 243. El routing solo veía ~39%
   del catálogo. Ahora `AGENTES_ESPECIALIZADOS` **se carga desde el JSON**
   (fuente de verdad única), con el dict embebido solo como fallback offline.
3. **Seguridad** — `AutoExecutor` ya no expone `rm -rf` en su whitelist.
4. **Deuda muerta** — `orchestrator.py`, `routing_engine.py`, `memory_system.py`
   y `learning_system.py` eran copias viejas con las rutas rotas. Ahora son
   **shims** que re-exportan las clases consolidadas (compatibilidad de imports,
   una sola fuente de verdad).
5. **Tests** — +7 tests de regresión (97 total).

## 🔧 Consolidación Realizada

1. **4 archivos de routing → 1** (`neural_fellowship.py`)
   - `orchestrator.py` → clase `Orchestrator` dentro del archivo principal
   - `routing_engine.py` → clase `Orquestador` dentro del archivo principal  
   - `memory_system.py` → clase `MemorySystem` dentro del archivo principal
   - `learning_system.py` → clase `LearningSystem` dentro del archivo principal

2. **Typo fix**: `capcidades` → `capacidades` en `agent_directory.json`

3. **Seguridad**: `AutoExecutor` ahora usa whitelist de comandos + validación de paths

4. **Paths**: De `/data/data/com.termux/files/home` a `Path.home()` portable

5. **Requirements**: Agregado `requirements.txt` (stdlib only)

## 🚀 Uso

```bash
# Ver estado general
python3 neural_fellowship.py

# Listar agentes
python3 neural_fellowship.py --maestros
python3 neural_fellowship.py --agents

# Ruta una tarea
python3 neural_fellowship.py --route "crear componente React"

# Escanear tareas pendientes
python3 neural_fellowship.py --scan

# Auto-ejecutar (dry-run)
python3 neural_fellowship.py --auto

# Estado del sistema
python3 neural_fellowship.py --status

# Buscar en memoria
python3 neural_fellowship.py --memory "error timeout"

# Registrar lección
python3 neural_fellowship.py --lesson "AGENT:ERROR:CONTEXT:SOLUTION"
```

## 🗺️ Pendiente / Próxima Iteración

- [ ] Integración real con Hermes (`delegate_task`, `memory()`, `cronjob_manage`)
- [ ] Tests automatizados
- [ ] CI/CD para validar sintaxis
- [ ] Interfaz web/monitor del sistema
- [ ] Más especialistas (actual: 85, meta original: 243)

## 📝 Changelog

- **2026-09-12**: Consolidación — 4 archivos de routing → 1. Fix typos. Seguridad + portabilidad.
