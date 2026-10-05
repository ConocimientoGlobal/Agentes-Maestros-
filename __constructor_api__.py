#!/usr/bin/env python3
"""API mínima del Constructor/Arquitecto — punto de entrada para propuestas.

Uso:
    from __constructor_api__ import Constructor
    c = Constructor()
    proposal = c.receive_gap({"task": "X", "reason": "Y"})
    print(json.dumps(proposal, indent=2))

El Constructor:
- No modifica la red automáticamente
- Siempre marca requires_human_approval=True
- Analiza reutilización antes de proponer creación
- Puede investigar cuando el problema lo requiere
- Produce propuesta estructurada que va a la cola
"""

import json
import sys
from pathlib import Path

REPO_PATH = Path(__file__).parent.resolve()
STATE_DIR = REPO_PATH / "state"
PROPOSALS_DIR = STATE_DIR / "proposals"

# ============================================================================
# Importar desde fabrica_maestros.py (mismo repo)
# ============================================================================

sys.path.insert(0, str(REPO_PATH))
from fabrica_maestros import Fabricadora


class Constructor(Fabricadora):
    """Maestro especializado en Arquitectura, investigación y construcción
    de nuevas capacidades para la red de agentes.

    Contrato del Maestro (mínimo compatible con arquitectura existente):
    ├── identidad: "constructor" / "Constructor/Arquitecto"
    ├── dominio: "arquitectura + investigación + capacidades"
    ├── capacidades: diseño, análisis de reutilización, investigación
    ├── especialistas asociados: según necesidad
    ├── herramientas disponibles: herramientas Hermes estándar
    ├── criterios de decisión: política de preferencia de reutilización
    ├── entrada: capability gap (tarea + razón)
    ├── proceso: analizar → investigar → diseñar → proponer → validar → registrar
    └── salida: propuesta estructurada con requires_human_approval=True
    """

    def __init__(self, repo_path: Path = None):
        super().__init__(repo_path)
        self.identity = "constructor"
        self.name = "Constructor/Arquitecto"
        self.domains = ["arquitectura", "investigación", "construcción de capacidades"]
        self.capabilities = [
            "analizar_reutilización",
            "diseñar_arquitectura",
            "investigar_problema",
            "generar_propuesta",
            "validar_propuesta",
            "registrar_propuesta",
        ]

    def receive_gap(self, gap: dict) -> dict:
        """Recibe un capability gap y produce propuesta completa.

        Flujo:
        1. Analizar reutilización (política de preferencia)
        2. Investigar si es necesario
        3. Generar propuesta estructurada
        4. Marcar requires_human_approval=True
        5. Guardar en cola de construcción

        NO modifica la red automáticamente.
        """
        task = gap.get("task", "")
        reason = gap.get("reason", "")

        # 1. Análisis de reutilización
        analysis = self.analyze_reuse(task)

        # 2. Investigación si es necesario (cuando no hay reutilización clara)
        research = []
        if not analysis.get("existing_capabilities") and not analysis.get("existing_specialists"):
            research = self.research(task)

        # 3. Generar propuesta
        proposal = self.propose(gap, analysis)
        proposal["research"] = research

        # 4. Validación interna del Constructor
        validation = self._validate_proposal(proposal)
        proposal["validation"] = validation

        # 5. Guardar en cola (aprobación humana requerida)
        proposal_id = self.queue_proposal(proposal)

        return {
            "status": "proposal",
            "proposal_id": proposal_id,
            "proposal": proposal,
        }

    def _validate_proposal(self, proposal: dict) -> dict:
        """Validación interna: verifica completitud de la propuesta."""
        required_fields = [
            "problem", "reuse_analysis", "reuse_decision",
            "proposed_solution", "requires_human_approval",
        ]
        missing = [f for f in required_fields if not proposal.get(f)]

        return {
            "complete": len(missing) == 0,
            "missing_fields": missing,
            "requires_human_approval": proposal.get("requires_human_approval", True),
        }

    def get_proposal(self, proposal_id: str) -> dict:
        """Recupera una propuesta por ID."""
        proposals = self.get_all_proposals()
        for p in proposals:
            if p.get("id") == proposal_id:
                return p
        return None

    def get_all_proposals(self) -> list:
        """Recupera todas las propuestas almacenadas."""
        if not PROPOSALS_DIR.exists():
            return []
        proposals = []
        for f in sorted(PROPOSALS_DIR.glob("*.json")):
            proposals.append(json.loads(f.read_text(encoding="utf-8")))
        return proposals

    def save_proposal(self, proposal: dict) -> str:
        """Guarda una propuesta en state/proposals/."""
        PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
        path = PROPOSALS_DIR / f"{proposal['id']}.json"
        path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2), encoding="utf-8")
        return proposal["id"]


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI para el Constructor."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Constructor/Arquitecto — analiza gaps, genera propuestas"
    )
    sub = parser.add_subparsers(dest="cmd")

    # receive-gap
    rg = sub.add_parser("receive-gap", help="Recibir capability gap")
    rg.add_argument("task", help="Tarea que no es ejecutable")
    rg.add_argument("--reason", "-r", default="", help="Razón del gap")

    # queue
    sub.add_parser("queue", help="Ver cola de construcción")

    # proposals
    sub.add_parser("proposals", help="Listar propuestas")

    args = parser.parse_args()

    c = Constructor()

    if args.cmd == "receive-gap":
        gap = {"task": args.task, "reason": args.reason or "sin handler ejecutable"}
        result = c.receive_gap(gap)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "queue":
        queue = c.get_queue()
        print(json.dumps(queue, ensure_ascii=False, indent=2))

    elif args.cmd == "proposals":
        proposals = c.get_all_proposals()
        for p in proposals:
            print(f"  {p['id']} — {p.get('problem', '?')} — approved={p.get('status')}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()