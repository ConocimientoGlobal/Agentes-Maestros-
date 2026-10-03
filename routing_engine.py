#!/usr/bin/env python3
"""
Routing Engine — SHIM de compatibilidad.
========================================
La implementación canónica del routing vive en neural_fellowship.Orquestador.
Este módulo se conserva únicamente para no romper imports externos
(`from routing_engine import RoutingEngine`).

Histórico: la versión previa duplicaba la lógica de scoring y leía el catálogo
desde `~/references/agent_directory.json` (ruta inexistente) → catálogo vacío.
Ahora envuelve el Orquestador consolidado, que lee el catálogo real.
"""

from neural_fellowship import Orquestador, AGENTES_ESPECIALIZADOS  # noqa: F401

__all__ = ["RoutingEngine"]


class RoutingEngine:
    """Fachada fina sobre Orquestador para compatibilidad de API."""

    def __init__(self):
        self._orch = Orquestador()

    def find_best_agent(self, task_description: str, required_capabilities: list = None) -> dict:
        """Compatibilidad: devuelve {maestro, especialista, confianza, motivo}."""
        ruta = self._orch.ruta_completa(task_description)
        esp = ruta["especialista"]
        return {
            "maestro": ruta["maestro"]["maestro"],
            "especialista": esp.get("especialista"),
            "confianza": esp.get("confianza", ruta["maestro"]["confianza"]),
            "motivo": ruta["maestro"]["motivo"],
        }

    def get_maestro_for_task(self, task_description: str) -> str:
        return self._orch.determinar_maestro(task_description)["maestro"]

    def get_parallel_routes(self, tasks: list) -> list:
        return [
            {**self.find_best_agent(t.get("description", ""), t.get("capabilities")), "task": t}
            for t in tasks
        ]


def main():
    """CLI de conveniencia."""
    import json
    import sys

    if len(sys.argv) > 1:
        print(json.dumps(RoutingEngine().find_best_agent(" ".join(sys.argv[1:])), indent=2, ensure_ascii=False))
    else:
        print("Uso: python3 routing_engine.py <descripción de tarea>")


if __name__ == "__main__":
    main()
