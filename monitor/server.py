#!/usr/bin/env python3
"""
Monitor Server — Neural Fellowship
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

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write((REPO_PATH / 'monitor' / 'index.html').read_bytes())
        elif self.path == '/api/status':
            self._json(self._status())
        elif self.path == '/api/tasks':
            self._json(self._tasks())
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/api/execute':
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length))
            result = AutoExecutor().ejecutar(data.get('task', ''))
            self._json(result)
        elif self.path == '/api/tasks/delete':
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length))
            ids = data.get('ids', [])
            self._json({"status": "ok", "deleted": len(ids)})
        elif self.path == '/api/tasks/create':
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length))
            self._json({"status": "ok", "created": 1})
        else:
            self.send_error(404)

    def _json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _status(self):
        try: o = Orchestrator().get_status()
        except: o = {}
        try: m = MemorySystem().get_stats()
        except: m = {}
        try: l = LearningSystem().get_stats()
        except: l = {}
        try: t = DetectorTareas().get_stats()
        except: t = {}
        
        # Get projects
        projects = []
        proj_dir = Path.home() / 'knowledge' / '_projects'
        if proj_dir.exists():
            for f in proj_dir.glob('*.md'):
                tasks_in_file = self._scan_file_tasks(f)
                if tasks_in_file:
                    completed = sum(1 for t in tasks_in_file if t.get('completada'))
                    projects.append({
                        "name": f.stem.replace('-', ' ').title(),
                        "icon": "📁",
                        "total": len(tasks_in_file),
                        "completadas": completed
                    })
        
        return {
            "orchestrator": o, "memory": m, "learning": l, "tasks": t,
            "agentes_maestros": len(AGENTES_MAESTROS),
            "agentes_especializados": len(AGENTES_ESPECIALIZADOS),
            "projects": projects,
            "status": "online"
        }

    def _tasks(self):
        detector = DetectorTareas()
        raw_tasks = detector.scan_all()
        orch = Orquestador()
        result = []
        for t in raw_tasks:
            if t.get('completada'): continue
            r = orch.ruta_completa(t['texto'])
            # Extract project name from source
            fuente = t.get('fuente', '')
            project = None
            if '_projects/' in fuente:
                project = fuente.split('_projects/')[1].split('/')[0] if '/' in fuente else fuente.split('_projects/')[1].split('.')[0]
            
            result.append({
                "id": str(hash(t['texto']))[:10],
                "texto": t['texto'],
                "fuente": fuente,
                "project": project,
                "route": {
                    "maestro": {"id": r['maestro']['maestro'], "confidence": r['maestro']['confianza']},
                    "specialist": {"id": r['especialista'].get('especialista'), "confidence": r['especialista'].get('confianza', 0)},
                    "automatizable": r['automatizable']
                }
            })
        return {"tasks": result, "total": len(result)}

    def _scan_file_tasks(self, filepath):
        tasks = []
        try:
            content = filepath.read_text()
            for line in content.split('\n'):
                if line.strip().startswith('- [ ]'):
                    tasks.append({"texto": line.strip()[5:], "completada": False})
                elif line.strip().startswith('- [x]'):
                    tasks.append({"texto": line.strip()[5:], "completada": True})
        except: pass
        return tasks

def main():
    server = HTTPServer(('0.0.0.0', 8550), Handler)
    print("🧠 Neural Fellowship en http://localhost:8550")
    try: server.serve_forever()
    except KeyboardInterrupt: print("\nDetenido")

if __name__ == '__main__':
    main()
