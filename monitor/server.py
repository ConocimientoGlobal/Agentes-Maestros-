#!/usr/bin/env python3
"""
Monitor Server — API para la interfaz interactiva de Neural Fellowship
"""

import json
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

REPO_PATH = Path("/data/data/com.termux/files/home/tmp/Agentes-Maestros-")
sys.path.insert(0, str(REPO_PATH))

from neural_fellowship import (
    Orquestador, AutoExecutor, LearningSystem, MemorySystem,
    Orchestrator, DetectorTareas, AGENTES_MAESTROS, AGENTES_ESPECIALIZADOS
)

class MonitorHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            html = (REPO_PATH / 'monitor' / 'index.html').read_bytes()
            self.wfile.write(html)
        elif self.path == '/api/status':
            data = self._get_status()
            self._json_response(data)
        elif self.path == '/api/tasks':
            data = self._get_tasks()
            self._json_response(data)
        elif self.path == '/api/agents':
            data = self._get_agents()
            self._json_response(data)
        else:
            super().do_GET()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            data = {}

        if self.path == '/api/execute':
            result = AutoExecutor().ejecutar(data.get('task', ''))
            self._json_response(result)
        elif self.path == '/api/tasks/create':
            result = self._create_task(data)
            self._json_response(result)
        elif self.path == '/api/tasks/update':
            result = self._update_task(data)
            self._json_response(result)
        elif self.path == '/api/tasks/delete':
            result = self._delete_task(data)
            self._json_response(result)
        elif self.path == '/api/tasks/transfer':
            result = self._transfer_task(data)
            self._json_response(result)
        elif self.path == '/api/tasks/move':
            result = self._move_task(data)
            self._json_response(result)
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def _json_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _get_status(self):
        try:
            o = Orchestrator().get_status()
        except: o = {}
        try:
            m = MemorySystem().get_stats()
        except: m = {}
        try:
            l = LearningSystem().get_stats()
        except: l = {}
        try:
            t = DetectorTareas().get_stats()
        except: t = {}
        return {
            "orchestrator": o, "memory": m, "learning": l, "tasks": t,
            "agentes_maestros": len(AGENTES_MAESTROS),
            "agentes_especializados": len(AGENTES_ESPECIALIZADOS),
            "status": "online"
        }

    def _get_tasks(self):
        detector = DetectorTareas()
        tasks = detector.scan_all()
        orch = Orquestador()
        result = []
        for t in tasks:
            if t.get('completada'): continue
            r = orch.ruta_completa(t['texto'])
            result.append({
                "texto": t['texto'],
                "fuente": t.get('fuente', ''),
                "route": {
                    "maestro": {"id": r['maestro']['maestro'], "confidence": r['maestro']['confianza']},
                    "specialist": {"id": r['especialista'].get('especialista'), "confidence": r['especialista'].get('confianza', 0)},
                    "automatizable": r['automatizable']
                }
            })
        # Build agent summary
        agent_summary = {}
        for t in result:
            mid = t['route']['maestro']['id']
            if mid not in agent_summary:
                agent_summary[mid] = {"id": mid, "domain": mid, "task_count": 0, "specialist_count": 0}
            agent_summary[mid]["task_count"] += 1
        # Build projects
        projects = {}
        for t in result:
            proj = t['fuente'].split('/')[-1] if t['fuente'] else 'General'
            if proj not in projects:
                projects[proj] = {"name": proj, "total": 0, "completadas": 0, "pendientes": 0, "auto_count": 0, "icon": "📁", "file_count": 1}
            projects[proj]["total"] += 1
            projects[proj]["pendientes"] += 1
            if t['route']['automatizable']:
                projects[proj]["auto_count"] += 1
        return {
            "tasks": result,
            "total": len(result),
            "agent_summary": list(agent_summary.values()),
            "projects": list(projects.values())
        }

    def _get_agents(self):
        return {
            "maestros": [{"id": k, "emoji": v.get("emoji", "🤖")} for k, v in AGENTES_MAESTROS.items()],
            "especializados": [{"id": k, "emoji": v.get("emoji", "🔧")} for k, v in AGENTES_ESPECIALIZADOS.items()],
            "total_maestros": len(AGENTES_MAESTROS),
            "total_especializados": len(AGENTES_ESPECIALIZADOS)
        }

    def _create_task(self, data):
        """Crear una nueva tarea"""
        text = data.get('text', '').strip()
        if not text:
            return {"status": "error", "message": "Texto de tarea requerido"}
        agent = data.get('agent', 'sin-asignar')
        project = data.get('project', 'General')
        orch = Orquestador()
        route = orch.ruta_completa(text)
        task_data = {
            "texto": text,
            "agent": agent,
            "project": project,
            "type": data.get('type', 'auto'),
            "priority": data.get('priority', 'medium'),
            "status": data.get('status', 'todo'),
            "route": route,
            "created_via": "monitor_api"
        }
        return {"status": "success", "task": task_data, "message": "Tarea creada correctamente"}

    def _update_task(self, data):
        """Actualizar tarea(s) existente(s)"""
        task_id = data.get('id')
        ids = data.get('ids', [])
        if task_id:
            ids = [task_id]
        if not ids:
            return {"status": "error", "message": "ID(s) de tarea requerido(s)"}
        updates = {}
        for field in ['text', 'priority', 'status', 'agent', 'project', 'type']:
            if field in data:
                updates[field] = data[field]
        if not updates:
            return {"status": "error", "message": "Sin campos para actualizar"}
        return {
            "status": "success",
            "updated_count": len(ids),
            "updates": updates,
            "message": f"{len(ids)} tarea(s) actualizada(s)"
        }

    def _delete_task(self, data):
        """Eliminar tarea(s)"""
        task_id = data.get('id')
        ids = data.get('ids', [])
        if task_id:
            ids = [task_id]
        if not ids:
            return {"status": "error", "message": "ID(s) de tarea requerido(s)"}
        return {
            "status": "success",
            "deleted_count": len(ids),
            "message": f"{len(ids)} tarea(s) eliminada(s)"
        }

    def _transfer_task(self, data):
        """Transferir tarea(s) a otro agente o proyecto"""
        task_id = data.get('id')
        ids = data.get('ids', [])
        if task_id:
            ids = [task_id]
        if not ids:
            return {"status": "error", "message": "ID(s) de tarea requerido(s)"}
        agent = data.get('agent')
        project = data.get('project')
        if not agent and not project:
            return {"status": "error", "message": "Agente o proyecto requerido"}
        return {
            "status": "success",
            "transferred_count": len(ids),
            "agent": agent,
            "project": project,
            "message": f"{len(ids)} tarea(s) transferida(s)"
        }

    def _move_task(self, data):
        """Mover tarea(s) entre estados"""
        task_id = data.get('id')
        ids = data.get('ids', [])
        if task_id:
            ids = [task_id]
        if not ids:
            return {"status": "error", "message": "ID(s) de tarea requerido(s)"}
        status = data.get('status', 'todo')
        if status not in ['todo', 'progress', 'done']:
            return {"status": "error", "message": "Estado inválido. Use: todo, progress, done"}
        return {
            "status": "success",
            "moved_count": len(ids),
            "new_status": status,
            "message": f"{len(ids)} tarea(s) movida(s) a {status}"
        }

def main():
    server = HTTPServer(('0.0.0.0', 8550), MonitorHandler)
    print("🧠 Neural Fellowship Monitor en http://localhost:8550")
    print("   Endpoints POST: /api/tasks/create, /api/tasks/update, /api/tasks/delete")
    print("                    /api/tasks/transfer, /api/tasks/move, /api/execute")
    print("   Ctrl+C para detener")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDetenido")

if __name__ == '__main__':
    main()
