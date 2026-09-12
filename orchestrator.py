#!/usr/bin/env python3
"""
Orquestador Central — Coordina la ejecución de agentes en paralelo.
Maneja delegación, estado compartido, y loop hasta objetivo.
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime

SKILL_DIR = Path(__file__).parent.parent
STATE_FILE = SKILL_DIR / "references" / "orchestrator_state.json"
LESSONS_FILE = SKILL_DIR / "references" / "learned_lessons.json"

class Orchestrator:
    def __init__(self):
        self.state = self._load_state()
        self.max_iterations = 10
        self.timeout_minutes = 30

    def _load_state(self) -> dict:
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        return {
            "active_agents": {},
            "completed_tasks": [],
            "failed_tasks": [],
            "shared_context": {},
            "iteration": 0,
            "started_at": None
        }

    def _save_state(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def register_agent(self, agent_id: str, goal: str, context: str, maestro: str = None):
        """Registra un agente activo."""
        self.state["active_agents"][agent_id] = {
            "goal": goal,
            "context": context,
            "maestro": maestro,
            "status": "active",
            "started_at": datetime.now().isoformat(),
            "iterations": 0,
            "progress": []
        }
        self._save_state()

    def update_progress(self, agent_id: str, message: str):
        """Actualiza el progreso de un agente."""
        if agent_id in self.state["active_agents"]:
            self.state["active_agents"][agent_id]["progress"].append({
                "time": datetime.now().isoformat(),
                "message": message
            })
            self._save_state()

    def complete_task(self, agent_id: str, result: str):
        """Marca una tarea como completada."""
        if agent_id in self.state["active_agents"]:
            self.state["active_agents"][agent_id]["status"] = "completed"
            self.state["active_agents"][agent_id]["result"] = result
            self.state["completed_tasks"].append({
                "agent_id": agent_id,
                "result": result,
                "completed_at": datetime.now().isoformat()
            })
            self._save_state()

    def fail_task(self, agent_id: str, error: str):
        """Marca una tarea como fallida."""
        if agent_id in self.state["active_agents"]:
            self.state["active_agents"][agent_id]["status"] = "failed"
            self.state["active_agents"][agent_id]["error"] = error
            self.state["failed_tasks"].append({
                "agent_id": agent_id,
                "error": error,
                "failed_at": datetime.now().isoformat()
            })
            self._save_state()

    def delegate_to(self, from_agent: str, to_agent: str, task: str, reason: str):
        """Registra una delegación entre agentes."""
        if "delegations" not in self.state:
            self.state["delegations"] = []
        self.state["delegations"].append({
            "from": from_agent,
            "to": to_agent,
            "task": task,
            "reason": reason,
            "delegated_at": datetime.now().isoformat()
        })
        self._save_state()

    def get_shared_context(self, key: str = None) -> dict:
        """Obtiene contexto compartido entre agentes."""
        if key:
            return self.state["shared_context"].get(key)
        return self.state["shared_context"]

    def set_shared_context(self, key: str, value: str):
        """Establece contexto compartido."""
        self.state["shared_context"][key] = value
        self._save_state()

    def should_continue(self) -> bool:
        """Determina si el loop debe continuar."""
        # Hay agentes activos?
        active = [a for a in self.state["active_agents"].values() if a["status"] == "active"]
        if not active:
            return False
        # Límite de iteraciones?
        if self.state["iteration"] >= self.max_iterations:
            return False
        # Timeout?
        if self.state["started_at"]:
            started = datetime.fromisoformat(self.state["started_at"])
            elapsed = (datetime.now() - started).total_seconds() / 60
            if elapsed >= self.timeout_minutes:
                return False
        return True

    def get_status(self) -> dict:
        """Retorna el estado actual del orquestador."""
        active_count = sum(1 for a in self.state["active_agents"].values() if a["status"] == "active")
        completed_count = len(self.state["completed_tasks"])
        failed_count = len(self.state["failed_tasks"])
        return {
            "active_agents": active_count,
            "completed_tasks": completed_count,
            "failed_tasks": failed_count,
            "total_agents": len(self.state["active_agents"]),
            "iteration": self.state["iteration"],
            "should_continue": self.should_continue()
        }

    def reset(self):
        """Resetea el estado."""
        self.state = {
            "active_agents": {},
            "completed_tasks": [],
            "failed_tasks": [],
            "shared_context": {},
            "iteration": 0,
            "started_at": datetime.now().isoformat()
        }
        self._save_state()


def main():
    """CLI para testing."""
    import sys
    orch = Orchestrator()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "status":
            print(json.dumps(orch.get_status(), indent=2, ensure_ascii=False))
        elif cmd == "reset":
            orch.reset()
            print("Orquestador reseteado.")
        elif cmd == "register" and len(sys.argv) > 3:
            orch.register_agent(sys.argv[2], sys.argv[3], " ".join(sys.argv[4:]))
            print(f"Agente {sys.argv[2]} registrado.")
    else:
        print("Uso: python3 orchestrator.py [status|reset|register] [args]")


if __name__ == "__main__":
    main()
