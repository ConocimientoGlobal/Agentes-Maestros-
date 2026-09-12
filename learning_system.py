#!/usr/bin/env python3
"""
Sistema de Aprendizaje de Errores
Cada agente aprende de sus errores y no los repite.
"""

import json
import os
from pathlib import Path
from datetime import datetime

SKILL_DIR = Path(__file__).parent.parent
LESSONS_FILE = SKILL_DIR / "references" / "learned_lessons.json"

class LearningSystem:
    """
    Sistema donde cada agente:
    - Registra errores en learned_lessons.json
    - Antes de ejecutar, consulta lecciones previas
    - Si comete un error, lo documenta con contexto
    - En futuras iteraciones, evita repetir el mismo camino
    """

    def __init__(self):
        self.lessons = self._load_lessons()

    def _load_lessons(self) -> list:
        if LESSONS_FILE.exists():
            with open(LESSONS_FILE, 'r') as f:
                return json.load(f)
        return []

    def _save_lessons(self):
        with open(LESSONS_FILE, 'w') as f:
            json.dump(self.lessons, f, indent=2, ensure_ascii=False)

    def record_error(self, agent_id: str, error: str, context: str, solution: str, tags: list = None) -> dict:
        """
        Registra un error cometido por un agente.
        """
        lesson = {
            "agent_id": agent_id,
            "error": error,
            "context": context,
            "solution": solution,
            "tags": tags or [],
            "learned_at": datetime.now().isoformat(),
            "occurrences": 1,
            "last_seen": datetime.now().isoformat()
        }
        # Si ya existe un error similar, incrementar ocurrencias
        for existing in self.lessons:
            if existing["agent_id"] == agent_id and existing["error"].lower() == error.lower():
                existing["occurrences"] += 1
                existing["last_seen"] = datetime.now().isoformat()
                self._save_lessons()
                return existing
        self.lessons.append(lesson)
        self._save_lessons()
        return lesson

    def get_warnings_for_agent(self, agent_id: str) -> list:
        """
        Obtiene advertencias para un agente basadas en errores pasados.
        Retorna lista de errores frecuentes (2+ ocurrencias).
        """
        warnings = []
        for lesson in self.lessons:
            if lesson["agent_id"] == agent_id and lesson["occurrences"] >= 2:
                warnings.append({
                    "error": lesson["error"],
                    "context": lesson["context"],
                    "solution": lesson["solution"],
                    "occurrences": lesson["occurrences"]
                })
        return sorted(warnings, key=lambda x: x["occurrences"], reverse=True)

    def get_relevant_lessons(self, agent_id: str, task_description: str) -> list:
        """
        Obtiene lecciones relevantes para una tarea específica.
        """
        relevant = []
        task_lower = task_description.lower()
        for lesson in self.lessons:
            if lesson["agent_id"] == agent_id:
                # Buscar coincidencias en el error o contexto
                if any(word in lesson["error"].lower() or word in lesson["context"].lower()
                       for word in task_lower.split() if len(word) > 3):
                    relevant.append(lesson)
        return relevant

    def get_all_lessons(self) -> list:
        """Todas las lecciones registradas."""
        return self.lessons

    def get_agent_lessons(self, agent_id: str) -> list:
        """Lecciones de un agente específico."""
        return [l for l in self.lessons if l["agent_id"] == agent_id]

    def generate_pre_execution_checklist(self, agent_id: str, task: str) -> list:
        """
        Genera una checklist de verificación antes de ejecutar.
        Basada en errores pasados del agente.
        """
        warnings = self.get_warnings_for_agent(agent_id)
        relevant = self.get_relevant_lessons(agent_id, task)
        checklist = []
        for w in warnings[:5]:  # Top 5 errores frecuentes
            checklist.append(f"⚠️ EVITAR: {w['error']} → SOLUCIÓN: {w['solution']}")
        for r in relevant[:3]:  # 3 lecciones relevantes
            checklist.append(f"📝 RECORDAR: {r['error']} en contexto '{r['context']}' → {r['solution']}")
        return checklist

    def get_stats(self) -> dict:
        """Estadísticas del sistema de aprendizaje."""
        agents = set(l["agent_id"] for l in self.lessons)
        return {
            "total_lessons": len(self.lessons),
            "agents_with_lessons": len(agents),
            "most_common_error": max(self.lessons, key=lambda x: x["occurrences"])["error"] if self.lessons else None,
            "total_occurrences": sum(l["occurrences"] for l in self.lessons)
        }


def main():
    """CLI para testing."""
    import sys
    ls = LearningSystem()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "stats":
            print(json.dumps(ls.get_stats(), indent=2, ensure_ascii=False))
        elif cmd == "record" and len(sys.argv) > 5:
            print(json.dumps(ls.record_error(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]), indent=2, ensure_ascii=False))
        elif cmd == "checklist" and len(sys.argv) > 3:
            print(json.dumps(ls.generate_pre_execution_checklist(sys.argv[2], " ".join(sys.argv[3:])), indent=2, ensure_ascii=False))
        elif cmd == "warnings" and len(sys.argv) > 2:
            print(json.dumps(ls.get_warnings_for_agent(sys.argv[2]), indent=2, ensure_ascii=False))
    else:
        print("Uso: python3 learning_system.py [stats|record|checklist|warnings] [args]")


if __name__ == "__main__":
    main()
