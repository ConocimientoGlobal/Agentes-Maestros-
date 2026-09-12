#!/usr/bin/env python3
"""Tests completos para Neural Fellowship — neural_fellowship.py.

Cubre: Orquestador, AutoExecutor, MemorySystem, LearningSystem,
       Orchestrator, DetectorTareas, QueueManager.
"""

import json
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from neural_fellowship import (
    Orquestador,
    AutoExecutor,
    MemorySystem,
    LearningSystem,
    Orchestrator,
    DetectorTareas,
    QueueManager,
    AGENTES_MAESTROS,
    AGENTES_ESPECIALIZADOS,
)


# ===========================================================================
# FIXTURES
# ===========================================================================

@pytest.fixture
def tmp_state_dir(tmp_path):
    """Directorio temporal para todos los archivos de estado."""
    paths = {
        'memory_index': tmp_path / 'memory_index.json',
        'lessons': tmp_path / 'learned_lessons.json',
        'queue_file': tmp_path / 'agent_queue.json',
        'orchestrator_state': tmp_path / 'orchestrator_state.json',
        'executor_state': tmp_path / 'executor_state.json',
        'projects_dir': tmp_path / '_projects',
        'active_dir': tmp_path / '_active',
        'today_file': tmp_path / 'TODAY.md',
        'knowledge_dir': tmp_path / 'knowledge',
    }
    paths['projects_dir'].mkdir()
    paths['active_dir'].mkdir()
    paths['knowledge_dir'].mkdir()
    paths['queue_file'].parent.mkdir(parents=True, exist_ok=True)
    paths['orchestrator_state'].parent.mkdir(parents=True, exist_ok=True)
    paths['executor_state'].parent.mkdir(parents=True, exist_ok=True)
    return paths


@pytest.fixture
def router():
    """Orquestador es logica pura — no requiere monkeypatch."""
    return Orquestador()


@pytest.fixture
def executor(tmp_state_dir, monkeypatch):
    """AutoExecutor con HOME temporal."""
    monkeypatch.setattr('neural_fellowship.HOME', tmp_state_dir['knowledge_dir'])
    return AutoExecutor()


@pytest.fixture
def memory(tmp_state_dir, monkeypatch):
    """MemorySystem con archivo temporal."""
    monkeypatch.setattr('neural_fellowship.MEMORY_INDEX', tmp_state_dir['memory_index'])
    return MemorySystem()


@pytest.fixture
def learner(tmp_state_dir, monkeypatch):
    """LearningSystem con archivo temporal."""
    monkeypatch.setattr('neural_fellowship.LESSONS_FILE', tmp_state_dir['lessons'])
    return LearningSystem()


@pytest.fixture
def orch(tmp_state_dir, monkeypatch):
    """Orchestrator con archivo temporal."""
    monkeypatch.setattr('neural_fellowship.ORCHESTRATOR_STATE', tmp_state_dir['orchestrator_state'])
    return Orchestrator()


@pytest.fixture
def detector(tmp_state_dir, monkeypatch):
    """DetectorTareas con directorios temporales."""
    monkeypatch.setattr('neural_fellowship.PROJECTS_DIR', tmp_state_dir['projects_dir'])
    monkeypatch.setattr('neural_fellowship.ACTIVE_DIR', tmp_state_dir['active_dir'])
    monkeypatch.setattr('neural_fellowship.TODAY_FILE', tmp_state_dir['today_file'])
    return DetectorTareas()


@pytest.fixture
def queue(tmp_state_dir, monkeypatch):
    """QueueManager con archivo temporal."""
    monkeypatch.setattr('neural_fellowship.QUEUE_FILE', tmp_state_dir['queue_file'])
    return QueueManager()


# ===========================================================================
# ORQUESTADOR TESTS
# ===========================================================================

class TestOrquestador:
    def test_determinar_maestro_diseno(self, router):
        """Routing a ARCAN por keywords de diseno."""
        result = router.determinar_maestro("Disenar branding y logo para empresa")
        assert result['maestro'] == 'ARCAN'
        assert result['confianza'] > 0

    def test_determinar_maestro_desarrollo(self, router):
        """Routing a NEXUS por keywords de codigo."""
        result = router.determinar_maestro("Programar API REST en Python")
        assert result['maestro'] == 'NEXUS'

    def test_determinar_maestro_seguridad(self, router):
        """Routing a SENTINEL por keywords de seguridad."""
        result = router.determinar_maestro("Pentesting y auditoria de vulnerabilidades")
        assert result['maestro'] == 'SENTINEL'

    def test_determinar_maestro_finanzas(self, router):
        """Routing a AURUM por keywords de finanzas."""
        result = router.determinar_maestro("valuacion DCF y finanzas")
        assert result['maestro'] == 'AURUM'

    def test_determinar_maestro_marketing(self, router):
        """Routing a AGENCY por keywords de marketing."""
        result = router.determinar_maestro("Campania SEO y contenido para redes")
        assert result['maestro'] == 'AGENCY'

    def test_determinar_maestro_sin_match(self, router):
        """Fallback a PHOENIX cuando no hay match."""
        result = router.determinar_maestro("xyzabc123456789")
        assert result['maestro'] == 'PHOENIX'
        assert result['confianza'] == 0

    def test_determinar_maestro_nombre_exacto(self, router):
        """Match exacto por nombre de maestro da score alto."""
        result = router.determinar_maestro("ORION debe encargarse del estudio")
        assert result['maestro'] == 'ORION'
        assert result['confianza'] >= 50

    def test_determinar_especialista_por_capacidad(self, router):
        """Match de especialista por capacidades dentro de un maestro."""
        result = router.determinar_especialista(
            "identidad-marca guia-estilo branding", maestro="ARCAN"
        )
        assert result['especialista'] is not None
        assert result['maestro'] == 'ARCAN'
        assert result['confianza'] > 0

    def test_determinar_especialista_con_maestro_filtro(self, router):
        """Filtra especialistas por maestro especifico."""
        result = router.determinar_especialista(
            "Crear react component", maestro="NEXUS"
        )
        assert result['maestro'] == 'NEXUS'
        assert result['especialista'] is not None

    def test_determinar_especialista_sin_match(self, router):
        """Sin match retorna None."""
        result = router.determinar_especialista("xyzabc123", maestro="NONEXIST")
        assert result['especialista'] is None
        assert result['confianza'] == 0

    def test_ruta_completa_estructura(self, router):
        """ruta_completa retorna estructura completa."""
        result = router.ruta_completa("Investigar papers de machine learning")
        assert 'tarea' in result
        assert 'maestro' in result
        assert 'especialista' in result
        assert 'automatizable' in result
        assert result['tarea'] == "Investigar papers de machine learning"

    def test_ruta_completa_automatizable_nexus(self, router):
        """Flag automatizable correcto para NEXUS."""
        result = router.ruta_completa("Programar backend con API")
        assert result['automatizable'] is True

    def test_ruta_completa_automatizable_prophet(self, router):
        """Flag automatizable correcto para PROPHET."""
        result = router.ruta_completa("Entrenar modelo de IA con fine-tuning")
        assert result['automatizable'] is True

    def test_ruta_completa_no_automatizable_aurum(self, router):
        """Flag automatizable correcto para AURUM (falso)."""
        result = router.ruta_completa("valuacion DCF finanzas")
        assert result['automatizable'] is False


# ===========================================================================
# AUTO-EXECUTOR TESTS
# ===========================================================================

class TestAutoExecutor:
    def test_detectar_tipo_crear_carpeta(self, executor):
        """Detecta patron mkdir."""
        action, params = executor.detectar_tipo("crear carpeta test_dir")
        assert action == "mkdir"
        assert params == ("test_dir",)

    def test_detectar_tipo_crear_directorio(self, executor):
        """Detecta patron crear directorio."""
        action, params = executor.detectar_tipo("crear directorio mi_dir")
        assert action == "mkdir"

    def test_detectar_tipo_crear_archivo(self, executor):
        """Detecta patron touch."""
        action, params = executor.detectar_tipo("crear archivo test.txt")
        assert action == "touch"
        assert params == ("test.txt",)

    def test_detectar_tipo_git_commit(self, executor):
        """Detecta patron git_commit."""
        action, params = executor.detectar_tipo("git commit mensaje de prueba")
        assert action == "git_commit"
        assert params == ("mensaje de prueba",)

    def test_detectar_tipo_pip_install(self, executor):
        """Detecta patron pip_install."""
        action, params = executor.detectar_tipo("pip install requests")
        assert action == "pip_install"
        assert params == ("requests",)

    def test_detectar_tipo_npm_install(self, executor):
        """Detecta patron npm_install."""
        action, params = executor.detectar_tipo("npm install express")
        assert action == "npm_install"

    def test_detectar_tipo_git_push(self, executor):
        """Detecta patron git_push."""
        action, params = executor.detectar_tipo("git push")
        assert action == "git_push"

    def test_detectar_tipo_git_pull(self, executor):
        """Detecta patron git_pull."""
        action, params = executor.detectar_tipo("git pull")
        assert action == "git_pull"

    def test_detectar_tipo_no_match(self, executor):
        """Sin match retorna None."""
        action, params = executor.detectar_tipo("Hacer investigacion de mercado")
        assert action is None
        assert params is None

    def test_ejecutar_dry_run_mkdir(self, executor):
        """Dry run no ejecuta, solo reporta."""
        result = executor.ejecutar("crear carpeta test_dry", dry_run=True)
        assert result['status'] == 'dry_run'
        assert result['dry_run'] is True
        assert result['accion'] == 'mkdir'

    def test_ejecutar_dry_run_git(self, executor):
        """Dry run para git_commit."""
        result = executor.ejecutar("git commit mensaje test", dry_run=True)
        assert result['status'] == 'dry_run'
        assert result['accion'] == 'git_commit'

    def test_ejecutar_dry_run_pip(self, executor):
        """Dry run para pip_install."""
        result = executor.ejecutar("pip install flask", dry_run=True)
        assert result['status'] == 'dry_run'
        assert result['accion'] == 'pip_install'

    def test_ejecutar_no_automatizable(self, executor):
        """Tarea no automatizable retorna status especial."""
        result = executor.ejecutar("Hacer investigacion cualitativa", dry_run=False)
        assert result['status'] == 'no_automatizable'

    def test_ejecutar_mkdir_real(self, executor, tmp_state_dir):
        """Ejecuta mkdir y crea directorio."""
        target = tmp_state_dir['knowledge_dir'] / 'nueva_carpeta'
        result = executor.ejecutar(f"crear carpeta {target}")
        assert result['status'] == 'success'
        assert target.exists()
        assert target.is_dir()

    def test_ejecutar_touch_real(self, executor, tmp_state_dir):
        """Ejecuta touch y crea archivo."""
        target = tmp_state_dir['knowledge_dir'] / 'nuevo_archivo.txt'
        result = executor.ejecutar(f"crear archivo {target}")
        assert result['status'] == 'success'
        assert target.exists()

    def test_ejecutar_create_md_real(self, executor, tmp_state_dir):
        """Ejecuta create_md via touch pattern (pattern ordering)."""
        target = tmp_state_dir['knowledge_dir'] / 'nueva_notas.md'
        # "crear archivo md X" matches "crear archivo (\S+)" first (pattern order)
        result = executor.ejecutar(f"crear archivo {target}")
        assert result['status'] == 'success'
        assert target.exists()


# ===========================================================================
# MEMORY SYSTEM TESTS
# ===========================================================================

class TestMemorySystem:
    def test_conectar_nuevo(self, memory):
        """Crea conexion nueva."""
        result = memory.conectar("python", "programacion", "relacionado", 7)
        assert result['a'] == "python"
        assert result['b'] == "programacion"
        assert result['fuerza'] == 7
        assert 'creada_en' in result

    def test_conectar_actualiza_existente(self, memory):
        """Actualiza fuerza en conexion duplicada."""
        memory.conectar("a", "b", "rel", 5)
        result = memory.conectar("a", "b", "rel", 8)
        assert result['fuerza'] == 8
        assert len(memory.index['conexiones']) == 1

    def test_conectar_fuerza_clamp_alto(self, memory):
        """Fuerza maxima es 10."""
        result = memory.conectar("a", "b", "rel", 99)
        assert result['fuerza'] == 10

    def test_conectar_fuerza_clamp_bajo(self, memory):
        """Fuerza minima es 1."""
        result = memory.conectar("a", "b", "rel", -5)
        assert result['fuerza'] == 1

    def test_buscar_conexiones_fuerza_desc(self, memory):
        """Busca conexiones ordenadas por fuerza descendente."""
        memory.conectar("python", "django", "fw", 8)
        memory.conectar("python", "flask", "fw", 5)
        memory.conectar("java", "spring", "fw", 6)

        results = memory.buscar_conexiones("python")
        assert len(results) == 2
        assert results[0]['fuerza'] >= results[1]['fuerza']
        assert results[0]['concepto'] == 'django'

    def test_buscar_conexiones_min_fuerza(self, memory):
        """Filtra por fuerza minima."""
        memory.conectar("a", "b", "rel", 3)
        memory.conectar("a", "c", "rel", 7)
        memory.conectar("a", "d", "rel", 5)

        results = memory.buscar_conexiones("a", min_fuerza=5)
        assert len(results) == 2
        assert all(r['fuerza'] >= 5 for r in results)

    def test_buscar_conexiones_sin_resultados(self, memory):
        """Sin resultados retorna lista vacia."""
        results = memory.buscar_conexiones("noexiste")
        assert results == []

    def test_buscar_conexiones_bidireccional(self, memory):
        """Busca en ambas direcciones (a y b)."""
        memory.conectar("python", "flask", "fw", 5)
        results_a = memory.buscar_conexiones("python")
        results_b = memory.buscar_conexiones("flask")
        assert len(results_a) == 1
        assert len(results_b) == 1
        assert results_a[0]['concepto'] == 'flask'
        assert results_b[0]['concepto'] == 'python'

    def test_agregar_leccion_nueva(self, memory):
        """Agrega leccion nueva."""
        result = memory.agregar_leccion(
            "NEXUS", "Error de sintaxis", "Python",
            "Usar verificacion de tipos", ["python", "syntax"]
        )
        assert result['agent_id'] == "NEXUS"
        assert result['error'] == "Error de sintaxis"
        assert result['solucion'] == "Usar verificacion de tipos"
        assert result['tags'] == ["python", "syntax"]
        assert result['usada'] == 0

    def test_agregar_leccion_sin_tags(self, memory):
        """Leccion sin tags usa lista vacia."""
        result = memory.agregar_leccion("NEXUS", "err", "ctx", "sol")
        assert result['tags'] == []

    def test_agregar_leccion_actualizar_duplicada(self, memory):
        """Duplicado incrementa usada."""
        memory.agregar_leccion("NEXUS", "Error X", "ctx", "sol")
        result = memory.agregar_leccion("NEXUS", "Error X", "ctx2", "sol2")
        assert result['usada'] == 1
        assert 'ultima_uso' in result

    def test_buscar_lecciones_por_agente(self, memory):
        """Busca lecciones filtradas por agente."""
        memory.agregar_leccion("NEXUS", "Error A", "ctx", "sol")
        memory.agregar_leccion("ARCAN", "Error B", "ctx", "sol")
        memory.agregar_leccion("NEXUS", "Error C", "ctx", "sol")

        results = memory.buscar_lecciones(agent_id="NEXUS")
        assert len(results) == 2

    def test_buscar_lecciones_por_tag(self, memory):
        """Busca lecciones por tag."""
        memory.agregar_leccion("NEXUS", "Error A", "ctx", "sol", tags=["python", "ml"])
        memory.agregar_leccion("NEXUS", "Error B", "ctx", "sol", tags=["java"])

        results = memory.buscar_lecciones(tag="python")
        assert len(results) == 1
        assert results[0]['error'] == "Error A"

    def test_buscar_lecciones_por_error(self, memory):
        """Busca lecciones por texto en error."""
        memory.agregar_leccion("NEXUS", "Connection timeout", "ctx", "sol")
        memory.agregar_leccion("NEXUS", "Syntax error", "ctx", "sol")

        results = memory.buscar_lecciones(error="timeout")
        assert len(results) == 1

    def test_tag_crear(self, memory):
        """Crea tag con descripcion e items."""
        memory.tag("python", "Todo sobre python", ["item1", "item2"])
        assert "python" in memory.index['tags']
        assert memory.index['tags']['python']['descripcion'] == "Todo sobre python"
        assert memory.index['tags']['python']['items'] == ["item1", "item2"]

    def test_tag_sin_items(self, memory):
        """Tag sin items usa lista vacia."""
        memory.tag("empty", "tag vacio")
        assert memory.index['tags']['empty']['items'] == []

    def test_get_stats(self, memory):
        """Estadisticas correctas."""
        memory.conectar("a", "b", "rel")
        memory.agregar_leccion("NEXUS", "err", "ctx", "sol")
        memory.tag("tag1", "desc")

        stats = memory.get_stats()
        assert stats['conexiones'] == 1
        assert stats['lecciones'] == 1
        assert stats['tags'] == 1
        assert stats['agentes_con_contexto'] == 0

    def test_guardar_y_obtener_contexto(self, memory):
        """Guarda y recupera contexto de agente."""
        memory.guardar_contexto("NEXUS", "ultima_tarea", "completada")
        ctx = memory.obtener_contexto("NEXUS")
        assert "ultima_tarea" in ctx
        assert ctx["ultima_tarea"]["value"] == "completada"

    def test_buscar_en_memoria(self, memory):
        """Busqueda completa en memoria."""
        memory.tag("database", "DB related", ["postgres", "mysql"])
        memory.conectar("sql", "database", "type", 5)
        results = memory.buscar_en_memoria("database")
        assert len(results) >= 1


# ===========================================================================
# LEARNING SYSTEM TESTS
# ===========================================================================

class TestLearningSystem:
    def test_record_error_nuevo(self, learner):
        """Registra error nuevo."""
        result = learner.record_error("NEXUS", "Timeout error", "API call", "Add retry", ["api"])
        assert result['agent_id'] == "NEXUS"
        assert result['error'] == "Timeout error"
        assert result['occurrences'] == 1
        assert result['tags'] == ["api"]

    def test_record_error_incrementar_ocurrencias(self, learner):
        """Incrementa ocurrencias en error duplicado."""
        learner.record_error("NEXUS", "Timeout error", "ctx", "sol")
        result = learner.record_error("NEXUS", "Timeout error", "ctx", "sol")
        assert result['occurrences'] == 2

    def test_record_error_case_insensitive(self, learner):
        """Matching de error es case-insensitive."""
        learner.record_error("NEXUS", "Timeout error", "ctx", "sol")
        result = learner.record_error("NEXUS", "timeout error", "ctx", "sol")
        assert result['occurrences'] == 2

    def test_record_error_sin_tags(self, learner):
        """Sin tags usa lista vacia."""
        result = learner.record_error("NEXUS", "err", "ctx", "sol")
        assert result['tags'] == []

    def test_get_warnings_sin_warnings(self, learner):
        """Sin warnings cuando occurrences < 2."""
        learner.record_error("NEXUS", "Error raro", "ctx", "sol")
        warnings = learner.get_warnings_for_agent("NEXUS")
        assert warnings == []

    def test_get_warnings_con_warnings(self, learner):
        """Retorna warnings cuando occurrences >= 2."""
        learner.record_error("NEXUS", "Common error", "ctx", "sol")
        learner.record_error("NEXUS", "Common error", "ctx", "sol")
        learner.record_error("NEXUS", "Common error", "ctx", "sol")

        warnings = learner.get_warnings_for_agent("NEXUS")
        assert len(warnings) == 1
        assert warnings[0]['occurrences'] == 3
        assert warnings[0]['error'] == "Common error"

    def test_get_warnings_ordenado_por_ocurrencias(self, learner):
        """Warnings ordenados por ocurrencias descendentes."""
        learner.record_error("NEXUS", "Frequent", "ctx", "sol")
        learner.record_error("NEXUS", "Frequent", "ctx", "sol")
        learner.record_error("NEXUS", "Frequent", "ctx", "sol")
        learner.record_error("NEXUS", "Less freq", "ctx", "sol")
        learner.record_error("NEXUS", "Less freq", "ctx", "sol")

        warnings = learner.get_warnings_for_agent("NEXUS")
        assert len(warnings) == 2
        assert warnings[0]['occurrences'] >= warnings[1]['occurrences']

    def test_get_warnings_agente_sin_lecciones(self, learner):
        """Agente sin lecciones retorna vacio."""
        warnings = learner.get_warnings_for_agent("INEXISTENTE")
        assert warnings == []

    def test_generate_pre_execution_checklist(self, learner):
        """Genera checklist con warnings y lecciones relevantes."""
        learner.record_error("NEXUS", "DB timeout", "query lenta", "add index")
        learner.record_error("NEXUS", "DB timeout", "query lenta", "add index")
        learner.record_error("NEXUS", "DB timeout", "query lenta", "add index")
        learner.record_error("NEXUS", "Auth fail", "token expired", "refresh token")
        learner.record_error("NEXUS", "Auth fail", "token expired", "refresh token")

        checklist = learner.generate_pre_execution_checklist("NEXUS", "DB query optimization")
        assert len(checklist) >= 1
        assert any("EVITAR" in item for item in checklist)

    def test_generate_checklist_sin_warnings(self, learner):
        """Checklist vacio cuando no hay warnings."""
        learner.record_error("NEXUS", "One time error", "ctx", "sol")
        checklist = learner.generate_pre_execution_checklist("NEXUS", "random task")
        assert checklist == []

    def test_get_relevant_lessons(self, learner):
        """Busca lecciones relevantes por descripcion de tarea."""
        learner.record_error("NEXUS", "Error en query SQL", "database", "optimize")
        learner.record_error("NEXUS", "UI glitch", "frontend", "fix css")

        relevant = learner.get_relevant_lessons("NEXUS", "Optimize database query performance")
        assert len(relevant) >= 1

    def test_get_stats_vacio(self, learner):
        """Stats con cero lecciones."""
        stats = learner.get_stats()
        assert stats['total_lessons'] == 0
        assert stats['agents_with_lessons'] == 0
        assert stats['most_common_error'] is None
        assert stats['total_occurrences'] == 0

    def test_get_stats_con_datos(self, learner):
        """Stats con lecciones registradas."""
        learner.record_error("NEXUS", "Error A", "ctx", "sol")
        learner.record_error("NEXUS", "Error A", "ctx", "sol")
        learner.record_error("ARCAN", "Error B", "ctx", "sol")

        stats = learner.get_stats()
        assert stats['total_lessons'] == 2
        assert stats['agents_with_lessons'] == 2
        assert stats['most_common_error'] == "Error A"
        assert stats['total_occurrences'] == 3

    def test_get_agent_lessons(self, learner):
        """Filtra lecciones por agente."""
        learner.record_error("NEXUS", "err1", "ctx", "sol")
        learner.record_error("ARCAN", "err2", "ctx", "sol")
        learner.record_error("NEXUS", "err3", "ctx", "sol")

        lessons = learner.get_agent_lessons("NEXUS")
        assert len(lessons) == 2


# ===========================================================================
# ORCHESTRATOR TESTS
# ===========================================================================

class TestOrchestrator:
    def test_register_agent(self, orch):
        """Registra agente con campos correctos."""
        orch.register_agent("agent_1", "Build API", "Context here", "NEXUS")
        assert "agent_1" in orch.state['active_agents']
        agent = orch.state['active_agents']['agent_1']
        assert agent['status'] == 'active'
        assert agent['goal'] == 'Build API'
        assert agent['context'] == 'Context here'
        assert agent['maestro'] == 'NEXUS'
        assert 'started_at' in agent

    def test_complete_task(self, orch):
        """Marca tarea como completada."""
        orch.register_agent("agent_1", "goal", "ctx")
        orch.complete_task("agent_1", "Done!")
        assert orch.state['active_agents']['agent_1']['status'] == 'completed'
        assert orch.state['active_agents']['agent_1']['result'] == "Done!"
        assert len(orch.state['completed_tasks']) == 1

    def test_fail_task(self, orch):
        """Marca tarea como fallida."""
        orch.register_agent("agent_1", "goal", "ctx")
        orch.fail_task("agent_1", "Error occurred")
        assert orch.state['active_agents']['agent_1']['status'] == 'failed'
        assert orch.state['active_agents']['agent_1']['error'] == "Error occurred"
        assert len(orch.state['failed_tasks']) == 1

    def test_should_continue_con_activos(self, orch):
        """Continua si hay agentes activos."""
        orch.register_agent("agent_1", "goal", "ctx")
        assert orch.should_continue() is True

    def test_should_continue_sin_activos(self, orch):
        """No continua si no hay agentes activos."""
        assert orch.should_continue() is False

    def test_should_continue_max_iterations(self, orch):
        """No continua al alcanzar max_iterations."""
        orch.register_agent("agent_1", "goal", "ctx")
        orch.state['iteration'] = 10
        assert orch.should_continue() is False

    def test_should_continue_iteration_9(self, orch):
        """Continua en iteration 9 de 10."""
        orch.register_agent("agent_1", "goal", "ctx")
        orch.state['iteration'] = 9
        assert orch.should_continue() is True

    def test_get_status(self, orch):
        """Estado correcto del sistema."""
        orch.register_agent("agent_1", "goal", "ctx")
        orch.register_agent("agent_2", "goal2", "ctx2")

        status = orch.get_status()
        assert status['active_agents'] == 2
        assert status['completed_tasks'] == 0
        assert status['failed_tasks'] == 0
        assert status['total_agents'] == 2

    def test_reset(self, orch):
        """Resetea el estado completamente."""
        orch.register_agent("agent_1", "goal", "ctx")
        orch.complete_task("agent_1", "done")
        orch.reset()
        assert len(orch.state['active_agents']) == 0
        assert len(orch.state['completed_tasks']) == 0
        assert len(orch.state['failed_tasks']) == 0
        assert orch.state['iteration'] == 0
        assert orch.state['started_at'] is not None

    def test_shared_context(self, orch):
        """Contexto compartido set/get."""
        orch.set_shared_context("key1", "value1")
        assert orch.get_shared_context("key1") == "value1"
        assert orch.get_shared_context() == {"key1": "value1"}

    def test_delegate_to(self, orch):
        """Registra delegacion entre agentes."""
        orch.register_agent("agent_1", "goal", "ctx")
        orch.register_agent("agent_2", "goal2", "ctx2")
        orch.delegate_to("agent_1", "agent_2", "subtask", "reason")

        assert 'delegations' in orch.state
        assert len(orch.state['delegations']) == 1
        deleg = orch.state['delegations'][0]
        assert deleg['from'] == "agent_1"
        assert deleg['to'] == "agent_2"
        assert deleg['task'] == "subtask"

    def test_update_progress(self, orch):
        """Actualiza progreso del agente."""
        orch.register_agent("agent_1", "goal", "ctx")
        orch.update_progress("agent_1", "Paso completado")
        assert len(orch.state['active_agents']['agent_1']['progress']) == 1


# ===========================================================================
# DETECTOR TAREAS TESTS
# ===========================================================================

class TestDetectorTareas:
    def test_scan_con_checkboxes(self, detector, tmp_state_dir):
        """Detecta checkboxes marcados y sin marcar."""
        md = tmp_state_dir['projects_dir'] / 'tasks.md'
        md.write_text("- [ ] Tarea pendiente 1\n- [x] Tarea completada\n")

        tasks = detector.scan_all()
        pending = [t for t in tasks if not t['completada']]
        done = [t for t in tasks if t['completada']]
        assert len(pending) == 1
        assert len(done) == 1

    def test_scan_con_bullets(self, detector, tmp_state_dir):
        """Detecta bullets simples como tareas."""
        md = tmp_state_dir['projects_dir'] / 'bullets.md'
        md.write_text("- bullet task 1\n- bullet task 2\n")

        tasks = detector.scan_all()
        bullet_tasks = [t for t in tasks if t['tipo'] == 'bullet']
        assert len(bullet_tasks) == 2

    def test_scan_directorio_vacio(self, detector, tmp_state_dir):
        """Directorio sin archivos retorna vacio."""
        tasks = detector.scan_all()
        assert tasks == []

    def test_scan_incluye_today(self, detector, tmp_state_dir):
        """TODAY.md se incluye en el scan."""
        tmp_state_dir['today_file'].write_text("- [ ] Tarea del dia actual\n")

        tasks = detector.scan_all()
        assert len(tasks) >= 1

    def test_get_stats(self, detector, tmp_state_dir):
        """Estadisticas correctas."""
        md = tmp_state_dir['projects_dir'] / 'stats.md'
        md.write_text("- [ ] Pendiente 1\n- [ ] Pendiente 2\n- [x] Completada 1\n")

        stats = detector.get_stats()
        assert stats['total'] == 3
        assert stats['pendientes'] == 2
        assert stats['completadas'] == 1
        assert stats['fuentes_escaneadas'] >= 1

    def test_scan_multiples_archivos(self, detector, tmp_state_dir):
        """Escanea multiples archivos."""
        (tmp_state_dir['projects_dir'] / 'a.md').write_text("- [ ] Tarea A\n")
        (tmp_state_dir['projects_dir'] / 'b.md').write_text("- [ ] Tarea B\n")
        (tmp_state_dir['projects_dir'] / 'c.md').write_text("- [x] Tarea C\n")

        tasks = detector.scan_all()
        assert len(tasks) == 3


# ===========================================================================
# QUEUE MANAGER TESTS
# ===========================================================================

class TestQueueManager:
    def test_enqueue(self, queue):
        """Agrega tarea a la cola."""
        task = {"id": "task_1", "type": "research", "description": "Investigar"}
        queue.enqueue(task)
        assert len(queue.queue) == 1
        assert queue.queue[0]['status'] == 'queued'
        assert 'enqueued_at' in queue.queue[0]

    def test_dequeue_primero(self, queue):
        """Desencola la primera tarea queued."""
        queue.enqueue({"id": "task_1", "type": "a"})
        queue.enqueue({"id": "task_2", "type": "b"})

        task = queue.dequeue()
        assert task is not None
        assert task['id'] == 'task_1'
        assert task['status'] == 'processing'

    def test_dequeue_vacio(self, queue):
        """Cola vacia retorna None."""
        task = queue.dequeue()
        assert task is None

    def test_complete(self, queue):
        """Marca tarea como completada en cola."""
        queue.enqueue({"id": "task_1", "type": "a"})
        queue.complete("task_1", "Success!")

        assert queue.queue[0]['status'] == 'completed'
        assert queue.queue[0]['result'] == "Success!"
        assert 'completed_at' in queue.queue[0]

    def test_get_queued(self, queue):
        """Filtra solo tareas en cola."""
        queue.enqueue({"id": "task_1", "type": "a"})
        queue.enqueue({"id": "task_2", "type": "b"})
        queue.dequeue()

        queued = queue.get_queued()
        assert len(queued) == 1
        assert queued[0]['id'] == 'task_2'

    def test_persistencia_entre_instancias(self, queue, tmp_state_dir, monkeypatch):
        """Estado persiste a archivo y se carga en nueva instancia."""
        queue.enqueue({"id": "persist_test", "type": "test"})

        monkeypatch.setattr('neural_fellowship.QUEUE_FILE', tmp_state_dir['queue_file'])
        new_queue = QueueManager()
        assert len(new_queue.queue) == 1
        assert new_queue.queue[0]['id'] == 'persist_test'

    def test_orden_fifo(self, queue):
        """Cola mantiene orden FIFO."""
        queue.enqueue({"id": "first", "type": "a"})
        queue.enqueue({"id": "second", "type": "b"})
        queue.enqueue({"id": "third", "type": "c"})

        assert queue.dequeue()['id'] == 'first'
        assert queue.dequeue()['id'] == 'second'
        assert queue.dequeue()['id'] == 'third'

    def test_complete_no_existente(self, queue):
        """Complete en task inexistente no falla."""
        queue.enqueue({"id": "task_1", "type": "a"})
        queue.complete("no_existe", "result")
        assert queue.queue[0]['status'] == 'queued'

    def test_estados_transicion(self, queue):
        """Transicion de estados: queued -> processing -> completed."""
        queue.enqueue({"id": "task_1", "type": "a"})
        assert queue.queue[0]['status'] == 'queued'

        task = queue.dequeue()
        assert task['status'] == 'processing'

        queue.complete("task_1", "done")
        assert queue.queue[0]['status'] == 'completed'
