#!/usr/bin/env python3
"""
Monitor Server — API para la interfaz de Neural Fellowship
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
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/api/execute':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            data = json.loads(body)
            result = AutoExecutor().ejecutar(data.get('task', ''))
            self._json_response(result)
        else:
            self.send_error(404)
    
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
        return {"tasks": result, "total": len(result)}

def main():
    server = HTTPServer(('0.0.0.0', 8550), MonitorHandler)
    print("🧠 Neural Fellowship Monitor en http://localhost:8550")
    print("   Ctrl+C para detener")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDetenido")

if __name__ == '__main__':
    main()
