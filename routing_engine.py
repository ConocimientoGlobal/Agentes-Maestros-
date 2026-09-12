#!/usr/bin/env python3
"""
Routing Engine — Motor de Delegación Inteligente
Identifica al agente más eficiente para cada tarea.
"""

import json
import os
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
AGENT_DIR = SKILL_DIR / "references" / "agent_directory.json"
LESSONS_FILE = SKILL_DIR / "references" / "learned_lessons.json"

class RoutingEngine:
    def __init__(self):
        self.agents = self._load_agents()
        self.lessons = self._load_lessons()

    def _load_agents(self):
        if AGENT_DIR.exists():
            with open(AGENT_DIR, 'r') as f:
                return json.load(f)
        return {"maestros": {}, "especialistas": {}}

    def _load_lessons(self):
        if LESSONS_FILE.exists():
            with open(LESSONS_FILE, 'r') as f:
                return json.load(f)
        return []

    def save_lessons(self):
        with open(LESSONS_FILE, 'w') as f:
            json.dump(self.lessons, f, indent=2, ensure_ascii=False)

    def find_best_agent(self, task_description: str, required_capabilities: list = None) -> dict:
        """
        Encuentra el agente más eficiente para una tarea.
        Retorna: {maestro, especialista, confianza, motivo}
        """
        task_lower = task_description.lower()
        best_match = None
        best_score = 0
        motivo = ""

        for agent_id, info in self.agents.get("especialistas", {}).items():
            score = 0
            # Match por capacidades
            for cap in info.get("capacidades", []):
                if cap.lower().replace("-", " ") in task_lower:
                    score += 30
            # Match por nombre de agente
            if agent_id.lower().replace("-", " ") in task_lower:
                score += 20
            # Match por capacidades requeridas
            if required_capabilities:
                for req_cap in required_capabilities:
                    if req_cap in info.get("capacidades", []):
                        score += 25
            # Penalizar si tiene lecciones de error en esta área
            for lesson in self.lessons:
                if lesson.get("agent_id") == agent_id:
                    if any(cap in lesson.get("error", "") for cap in info.get("capacidades", [])):
                        score -= 10

            if score > best_score:
                best_score = score
                best_match = {
                    "maestro": info["maestro"],
                    "especialista": agent_id,
                    "confianza": min(score, 100),
                    "motivo": f"Match por capacidades: {', '.join(info.get('capacidades', [])[:3])}"
                }

        if best_match and best_match["confianza"] < 40:
            # Buscar por maestro como fallback
            for maestro_id, info in self.agents.get("maestros", {}).items():
                if maestro_id.lower() in task_lower:
                    best_match = {
                        "maestro": maestro_id,
                        "especialista": None,
                        "confianza": 50,
                        "motivo": f"Fallback por maestro: {maestro_id}"
                    }
                    break

        return best_match or {"maestro": "PHOENIX", "especialista": None, "confianza": 0, "motivo": "No se encontró match — usa orquestador"}

    def get_parallel_routes(self, tasks: list) -> list:
        """
        Para múltiples tareas independientes, retorna rutas en paralelo.
        """
        routes = []
        for task in tasks:
            route = self.find_best_agent(task.get("description", ""), task.get("capabilities", []))
            route["task"] = task
            routes.append(route)
        return routes

    def get_maestro_for_task(self, task_description: str) -> str:
        """Identifica el maestro correcto para una tarea."""
        task_lower = task_description.lower()
        routing_map = {
            "design": ["diseño", "ui", "ux", "marca", "visual", "css", "estilo"],
            "engineering": ["código", "programar", "app", "web", "api", "base de datos", "software"],
            "research": ["investigar", "estudio", "paper", "académico", "científico"],
            "finance": ["finanzas", "inversión", "presupuesto", "contabilidad", "impuestos"],
            "security": ["seguridad", "pentest", "vulnerabilidad", "auditoría", "brecha"],
            "marketing": ["marketing", "seo", "contenido", "redes", "campaña", "publicidad"],
            "sales": ["venta", "propuesta", "cliente", "prospecto", "lead"],
            "product": ["producto", "roadmap", "feature", "priorización"],
            "game": ["juego", "game", "minecraft", "pokemon", "videojuego"],
            "health": ["salud", "médico", "bienestar", "fitness"],
            "memory": ["memoria", "conocimiento", "lección", "aprendizaje"],
        }
        for maestro, keywords in routing_map.items():
            if any(kw in task_lower for kw in keywords):
                return maestro
        return "PHOENIX"

    def add_lesson(self, agent_id: str, error: str, context: str, solution: str):
        """Registra una lección aprendida."""
        lesson = {
            "agent_id": agent_id,
            "error": error,
            "context": context,
            "solution": solution,
            "learned_at": str(Path.cwd())
        }
        self.lessons.append(lesson)
        self.save_lessons()
        return lesson

    def get_lessons_for_agent(self, agent_id: str) -> list:
        """Obtiene lecciones aprendidas para un agente."""
        return [l for l in self.lessons if l.get("agent_id") == agent_id]


def main():
    """CLI para testing."""
    import sys
    engine = RoutingEngine()
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        result = engine.find_best_agent(task)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Uso: python3 routing_engine.py <descripción de tarea>")
        print("Ejemplo: python3 routing_engine.py crear componente React con TypeScript")


if __name__ == "__main__":
    main()
