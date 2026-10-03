#!/usr/bin/env python3
"""
Orquestador Central — SHIM de compatibilidad.
=============================================
La implementación canónica vive en neural_fellowship.Orchestrator (consolidada).
Este módulo se conserva únicamente para no romper imports externos
(`from orchestrator import Orchestrator`).

Histórico: la versión previa duplicaba la clase y leía/escribía de
`~/references/orchestrator_state.json` (ruta inexistente) → no persistía.
Ahora re-exporta la clase consolidada, que escribe en <repo>/state/.
"""

from neural_fellowship import Orchestrator  # noqa: F401

__all__ = ["Orchestrator"]


def main():
    """CLI de conveniencia — delega en la implementación consolidada."""
    import json
    import sys

    orch = Orchestrator()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "status":
            print(json.dumps(orch.get_status(), indent=2, ensure_ascii=False))
        elif cmd == "reset":
            orch.reset()
            print("Orquestador reseteado.")
    else:
        print("Uso: python3 orchestrator.py [status|reset]")


if __name__ == "__main__":
    main()
