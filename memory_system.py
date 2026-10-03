#!/usr/bin/env python3
"""
Sistema de Memoria Neuronal — SHIM de compatibilidad.
=====================================================
La implementación canónica vive en neural_fellowship.MemorySystem (consolidada).
Este módulo se conserva únicamente para no romper imports externos
(`from memory_system import MemorySystem`).

Histórico: la versión previa duplicaba la clase y leía de
`~/references/memory_index.json` (ruta inexistente) → no persistía.
Ahora re-exporta la clase consolidada, que escribe en <repo>/state/.
"""

from neural_fellowship import MemorySystem  # noqa: F401

__all__ = ["MemorySystem"]


def main():
    """CLI de conveniencia — delega en la implementación consolidada."""
    import json
    import sys

    mem = MemorySystem()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "stats":
            print(json.dumps(mem.get_stats(), indent=2, ensure_ascii=False))
        elif cmd == "search" and len(sys.argv) > 2:
            print(json.dumps(mem.buscar_en_memoria(" ".join(sys.argv[2:])), indent=2, ensure_ascii=False))
    else:
        print("Uso: python3 memory_system.py [stats|search] [args]")


if __name__ == "__main__":
    main()
