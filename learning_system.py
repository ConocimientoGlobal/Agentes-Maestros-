#!/usr/bin/env python3
"""
Sistema de Aprendizaje de Errores — SHIM de compatibilidad.
===========================================================
La implementación canónica vive en neural_fellowship.LearningSystem (consolidada).
Este módulo se conserva únicamente para no romper imports externos
(`from learning_system import LearningSystem`).

Histórico: la versión previa duplicaba la clase y leía de
`~/references/learned_lessons.json` (ruta inexistente) → no persistía.
Ahora re-exporta la clase consolidada, que escribe en <repo>/state/.
"""

from neural_fellowship import LearningSystem  # noqa: F401

__all__ = ["LearningSystem"]


def main():
    """CLI de conveniencia — delega en la implementación consolidada."""
    import json
    import sys

    ls = LearningSystem()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "stats":
            print(json.dumps(ls.get_stats(), indent=2, ensure_ascii=False))
        elif cmd == "warnings" and len(sys.argv) > 2:
            print(json.dumps(ls.get_warnings_for_agent(sys.argv[2]), indent=2, ensure_ascii=False))
    else:
        print("Uso: python3 learning_system.py [stats|warnings] [args]")


if __name__ == "__main__":
    main()
