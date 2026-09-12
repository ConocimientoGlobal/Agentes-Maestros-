#!/usr/bin/env python3
"""
Sistema de Memoria Neuronal
Navega la memoria estándar de Hermes y conecta información estratégicamente.
"""

import json
import os
from pathlib import Path
from datetime import datetime

SKILL_DIR = Path(__file__).parent.parent
MEMORY_INDEX_FILE = SKILL_DIR / "references" / "memory_index.json"

class MemorySystem:
    """
    Sistema de memoria que:
    1. Navega la memoria estándar de Hermes (tool `memory`)
    2. Conecta información estratégicamente (grafo de relaciones)
    3. Almacena lecciones aprendidas (errores y soluciones)
    4. Comparte contexto entre agentes (estado compartido)
    """

    def __init__(self):
        self.index = self._load_index()

    def _load_index(self) -> dict:
        if MEMORY_INDEX_FILE.exists():
            with open(MEMORY_INDEX_FILE, 'r') as f:
                return json.load(f)
        return {
            "conexiones": [],  # Grafo de relaciones entre conceptos
            "lecciones": [],   # Lecciones aprendidas
            "contexto": {},   # Contexto compartido por agente
            "tags": {}        # Tags para búsqueda rápida
        }

    def _save_index(self):
        with open(MEMORY_INDEX_FILE, 'w') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)

    def conectar(self, concepto_a: str, concepto_b: str, relacion: str, fuerza: int = 5):
        """
        Crea una conexión estratégica entre dos conceptos.
        fuerza: 1-10 (10 = muy relacionada)
        """
        conexion = {
            "a": concepto_a,
            "b": concepto_b,
            "relacion": relacion,
            "fuerza": fuerza,
            "creada_en": datetime.now().isoformat()
        }
        # Evitar duplicados
        for c in self.index["conexiones"]:
            if c["a"] == concepto_a and c["b"] == concepto_b:
                c["fuerza"] = max(c["fuerza"], fuerza)
                self._save_index()
                return c
        self.index["conexiones"].append(conexion)
        self._save_index()
        return conexion

    def buscar_conexiones(self, concepto: str, min_fuerza: int = 1) -> list:
        """Busca conexiones de un concepto ordenadas por fuerza."""
        resultados = []
        for c in self.index["conexiones"]:
            if c["a"] == concepto or c["b"] == concepto:
                if c["fuerza"] >= min_fuerza:
                    otro = c["b"] if c["a"] == concepto else c["a"]
                    resultados.append({
                        "concepto": otro,
                        "relacion": c["relacion"],
                        "fuerza": c["fuerza"]
                    })
        return sorted(resultados, key=lambda x: x["fuerza"], reverse=True)

    def agregar_leccion(self, agent_id: str, error: str, contexto: str, solucion: str, tags: list = None):
        """
        Registra una lección aprendida por un agente.
        """
        leccion = {
            "agent_id": agent_id,
            "error": error,
            "contexto": contexto,
            "solucion": solucion,
            "tags": tags or [],
            "creada_en": datetime.now().isoformat(),
            "usada": 0
        }
        # Evitar duplicados por error similar
        for l in self.index["lecciones"]:
            if l["agent_id"] == agent_id and l["error"] == error:
                l["usada"] += 1
                l["ultima_uso"] = datetime.now().isoformat()
                self._save_index()
                return l
        self.index["lecciones"].append(leccion)
        self._save_index()
        return leccion

    def buscar_lecciones(self, agent_id: str = None, tag: str = None, error: str = None) -> list:
        """
        Busca lecciones aprendidas por agente, tag o error.
        """
        resultados = self.index["lecciones"]
        if agent_id:
            resultados = [l for l in resultados if l["agent_id"] == agent_id]
        if tag:
            resultados = [l for l in resultados if tag in l.get("tags", [])]
        if error:
            resultados = [l for l in resultados if error.lower() in l["error"].lower()]
        return sorted(resultados, key=lambda x: x["usada"], reverse=True)

    def obtener_contexto(self, agent_id: str) -> dict:
        """Obtiene el contexto compartido de un agente."""
        return self.index["contexto"].get(agent_id, {})

    def guardar_contexto(self, agent_id: str, key: str, value: str):
        """Guarda contexto para un agente."""
        if agent_id not in self.index["contexto"]:
            self.index["contexto"][agent_id] = {}
        self.index["contexto"][agent_id][key] = {
            "value": value,
            "updated_at": datetime.now().isoformat()
        }
        self._save_index()

    def buscar_en_memoria(self, query: str) -> list:
        """
        Busca en el índice de memoria por tags, errores o conceptos.
        """
        query_lower = query.lower()
        resultados = []
        # Buscar en tags
        for tag, items in self.index.get("tags", {}).items():
            if query_lower in tag.lower():
                resultados.extend(items)
        # Buscar en lecciones
        for leccion in self.index["lecciones"]:
            if any(query_lower in v.lower() for v in leccion.values() if isinstance(v, str)):
                resultados.append(leccion)
        # Buscar en conexiones
        for conexion in self.index["conexiones"]:
            if query_lower in conexion["a"].lower() or query_lower in conexion["b"].lower():
                resultados.append(conexion)
        return resultados

    def tag(self, nombre: str, descripcion: str, items: list = None):
        """
        Crea un tag para organizar información.
        """
        self.index["tags"][nombre] = {
            "descripcion": descripcion,
            "items": items or [],
            "creado_en": datetime.now().isoformat()
        }
        self._save_index()

    def get_stats(self) -> dict:
        """Estadísticas del sistema de memoria."""
        return {
            "conexiones": len(self.index["conexiones"]),
            "lecciones": len(self.index["lecciones"]),
            "agentes_con_contexto": len(self.index["contexto"]),
            "tags": len(self.index["tags"])
        }


def main():
    """CLI para testing."""
    import sys
    mem = MemorySystem()
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "stats":
            print(json.dumps(mem.get_stats(), indent=2, ensure_ascii=False))
        elif cmd == "connect" and len(sys.argv) > 4:
            print(json.dumps(mem.conectar(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]) if len(sys.argv) > 5 else 5), indent=2, ensure_ascii=False))
        elif cmd == "lesson" and len(sys.argv) > 5:
            print(json.dumps(mem.agregar_leccion(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]), indent=2, ensure_ascii=False))
        elif cmd == "search" and len(sys.argv) > 2:
            print(json.dumps(mem.buscar_en_memoria(" ".join(sys.argv[2:])), indent=2, ensure_ascii=False))
    else:
        print("Uso: python3 memory_system.py [stats|connect|lesson|search] [args]")


if __name__ == "__main__":
    main()
