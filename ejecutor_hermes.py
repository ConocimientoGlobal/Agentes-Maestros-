#!/usr/bin/env python3
"""Ejecutor flexible para Neural Fellowship que delega a Hermes runtime real.

Este ejecutor permite:
1. Delegar tareas complejas al agente Hermes real (via hermes CLI)
2. Mantener la selección de Maestro normal de Neural Fellowship  
3. Registrar el resultado como feedback en el sistema de aprendizaje
4. Usar el flujo normal de ejecución con estados completos (completed/error_ejecucion/no_ejecutable)

Implementa el handler "hermes_agent" en EXECUTION_STRATEGIES y se conecta desde resolve_execution()
"""

import subprocess
import json
import sys
import tempfile
from pathlib import Path


def _ejecutar_con_hermes(task: str, routing: dict) -> dict:
    """Delega ejecución a Hermes runtime real para tareas abiertas."""
    
    # Verificaciones iniciales
    if not task or not isinstance(task, str):
        return {
            "status": "error_ejecucion",
            "tipo": "hermes_agent",
            "error": "Tarea inválida: debe ser string no vacío",
        }
    
    # Verificar que la tarea sea abierta (no solo script de Python)
    # Ejemplos aceptables: "escribir un script para calcular estadísticas", "buscar información sobre X"
    if 'python:' in task.lower() and not ('crear' in task.lower() or 'escribir' in task.lower()):
        # Si parece solo ejecutar python sin contexto, usar ejecutor real
        # Pero el sistema actual ya tiene otro mecanismo para eso
        pass
    
    # Ejecutar en modo oneshot (directo)
    try:
        # La ejecución en modo oneshot es la forma más limpia de usar Hermes
        result = subprocess.run(
            ["hermes", "--oneshot", task],
            capture_output=True,
            text=True,
            timeout=60,  # 60s timeout para evitar bloqueos
            cwd=Path(__file__).parent  # Asegurar contexto
        )
        
        salida = result.stdout.strip() if result.stdout.strip() else None
        stderr = result.stderr.strip() if result.stderr.strip() else None
        
        return {
            "status": "completed" if result.returncode == 0 else "error_ejecucion",
            "tipo": "hermes_agent",
            "salida": salida,
            "stderr": stderr,
            "returncode": result.returncode,
            "codigo_ejecutado": task,
            "hermes_output": result.stdout,
        }
    
    except subprocess.TimeoutExpired:
        return {
            "status": "error_ejecucion",
            "tipo": "hermes_agent", 
            "error": "Timeout: Hermes no respondió en 60 segundos",
        }
    
    except Exception as e:
        return {
            "status": "error_ejecucion",
            "tipo": "hermes_agent",
            "error": f"Error ejecutando Hermes: {type(e).__name__}: {e}",
        }


# Exportar para que orquestar.py pueda importarlo
__all__ = ["_ejecutar_con_hermes"]