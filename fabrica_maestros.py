#!/usr/bin/env python3
"""Fábrica de Maestros — CLI + API para crear/registrar/validar maestros.

Extensión Fábrica de Maestros (FASE 2):
- Fabricadora: analiza gaps, genera propuestas de construcción
- Constructor/Arquitecto: analiza reutilización, investiga, diseña soluciones
- Registro de constructor en agent_directory.json
- Cola de construcción con aprobación humana
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

REPO_PATH = Path(__file__).parent.resolve()
AGENT_DIR = REPO_PATH / "agent_directory.json"
STATE_DIR = REPO_PATH / "state"
QUEUE_FILE = STATE_DIR / "construction_queue.json"

# ============================================================================
# POLÍTICA DE PREFERENCIA — Orden de reutilización vs creación
# ============================================================================

POLITICA_PREFERENCIA = [
    "reuse_capability",       # 1. Reutilizar capability existente
    "reuse_specialist",       # 2. Reutilizar especialista existente
    "reuse_maestro",          # 3. Reutilizar Maestro existente
    "combine_capabilities",   # 4. Combinar capacidades existentes
    "extend_capability",      # 5. Extender capability existente
    "create_capability",      # 6. Crear nueva capability
    "create_specialist",      # 7. Crear especialista
    "create_maestro",         # 8. Crear Maestro
    "create_fabrica",         # 9. Crear nueva fábrica
]


# ============================================================================
# UTILIDADES EXISTENTES (preservadas)
# ============================================================================

def load_maestros():
    return json.loads(AGENT_DIR.read_text(encoding="utf-8"))


def save_maestros(data):
    AGENT_DIR.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_maestro(maestro_id, dominio, division, especialidades, emoji="❓", automatizable=False):
    return {
        "emoji": emoji,
        "dominio": dominio,
        "division": division,
        "especialidades": especialidades,
        "automatizable": automatizable,
    }


def register_maestro(maestro_id, maestro_data):
    data = load_maestros()
    data["maestros"][maestro_id] = maestro_data
    save_maestros(data)
    return data["maestros"]


def unregister_maestro(maestro_id):
    data = load_maestros()
    removed = data["maestros"].pop(maestro_id, None)
    if removed is None:
        raise KeyError(f"Maestro '{maestro_id}' not found")
    save_maestros(data)
    return removed


def list_maestros():
    data = load_maestros()
    return data.get("maestros", {})


def validate_network():
    data = load_maestros()
    maestros = data.get("maestros", {})
    especialistas = data.get("especialistas", {})

    errors = []
    warnings = []
    maestro_ids = set(maestros.keys())
    esp_ids = set(especialistas.keys())

    for esp_id, esp_data in especialistas.items():
        m = esp_data.get("maestro", "")
        if m not in maestro_ids:
            errors.append(f"especialista '{esp_id}' references unknown maestro '{m}'")

    maestros_with_esps = {esp_data.get("maestro") for esp_data in especialistas.values()}
    for m_id in maestro_ids:
        if m_id not in maestros_with_esps:
            warnings.append(f"maestro '{m_id}' has no especialistas assigned")

    cross_refs = {}
    for m_id, m_data in maestros.items():
        div = m_data.get("division", "")
        if "→" in div:
            target = div.split("→")[1].strip().replace("usa ", "")
            cross_refs[m_id] = target

    for a, b in cross_refs.items():
        if b in cross_refs and cross_refs[b] == a:
            errors.append(f"circular cross-ref: {a} ↔ {b}")

    cap_owners = {}
    for esp_id, esp_data in especialistas.items():
        for cap in esp_data.get("capacidades", []):
            cap = cap.lower().strip()
            if cap in cap_owners:
                warnings.append(f"capability '{cap}' owned by both '{cap_owners[cap]}' and '{esp_id}'")
            else:
                cap_owners[cap] = esp_id

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "maestros": len(maestro_ids),
        "especialistas": len(esp_ids),
    }


def get_maestro_graph():
    data = load_maestros()
    maestros = data.get("maestros", {})
    especialistas = data.get("especialistas", {})

    graph = {}
    for m_id, m_data in maestros.items():
        esp_list = [e for e, ed in especialistas.items() if ed.get("maestro") == m_id]
        cross = []
        div = m_data.get("division", "")
        if "→" in div:
            target = div.split("→")[1].strip().replace("usa ", "")
            cross = [target]

        graph[m_id] = {
            "dominio": m_data.get("dominio", ""),
            "division": div,
            "emoji": m_data.get("emoji", "❓"),
            "automatizable": m_data.get("automatizable", False),
            "especialistas": esp_list,
            "cross_refs": cross,
        }
    return graph


def main():
    parser = argparse.ArgumentParser(
        description="Fábrica de Maestros — Crear, registrar, validar la red de Agentes-Maestros"
    )
    sub = parser.add_subparsers(dest="cmd")

    # build-maestro
    bm = sub.add_parser("build-maestro", help="Register a new maestro")
    bm.add_argument("maestro_id", help="Maestro ID (e.g. COORD)")
    bm.add_argument("--dominio", "-d", required=True)
    bm.add_argument("--division", "-v", required=True)
    bm.add_argument("--especialidades", "-e", required=True, help="Comma-separated")
    bm.add_argument("--emoji", "-m", default="❓")
    bm.add_argument("--automatizable", "-a", action="store_true")

    # unregister-maestro
    rm = sub.add_parser("unregister-maestro", help="Remove a maestro")
    rm.add_argument("maestro_id")

    # list-maestros
    sub.add_parser("list-maestros", help="List all maestros")

    # validate-network
    sub.add_parser("validate-network", help="Validate network integrity")

    # maestro-graph
    sub.add_parser("maestro-graph", help="Show maestro dependency graph")

    args = parser.parse_args()

    if args.cmd == "build-maestro":
        data = build_maestro(
            args.maestro_id, args.dominio, args.division,
            [e.strip() for e in args.especialidades.split(",")],
            args.emoji, args.automatizable,
        )
        register_maestro(args.maestro_id, data)
        print(f"✅ Maestro '{args.maestro_id}' registrado ({args.dominio}/{args.division})")

    elif args.cmd == "unregister-maestro":
        removed = unregister_maestro(args.maestro_id)
        print(f"🗑️ Maestro '{args.maestro_id}' removido")

    elif args.cmd == "list-maestros":
        maestros = list_maestros()
        for mid, mdata in sorted(maestros.items()):
            esps = [e for e, ed in load_maestros().get("especialistas", {}).items() if ed.get("maestro") == mid]
            print(f"  {mdata.get('emoji','❓')} {mid} — {mdata.get('dominio')}/{mdata.get('division')} ({len(esps)} especialistas)")

    elif args.cmd == "validate-network":
        result = validate_network()
        if result["ok"]:
            print(f"✅ Red válida: {result['maestros']} maestros, {result['especialistas']} especialistas")
        else:
            print(f"❌ Red inválida: {len(result['errors'])} errores, {len(result['warnings'])} advertencias")
        for e in result["errors"]:
            print(f"  ❌ {e}")
        for w in result["warnings"]:
            print(f"  ⚠️  {w}")
        sys.exit(0 if result["ok"] else 1)

    elif args.cmd == "maestro-graph":
        graph = get_maestro_graph()
        for mid, gdata in sorted(graph.items()):
            cross = " → " + ", ".join(gdata["cross_refs"]) if gdata["cross_refs"] else ""
            print(f"  {gdata['emoji']} {mid} [{gdata['dominio']}/{gdata['division']}]{cross}")
            for esp in gdata["especialistas"]:
                print(f"      └─ {esp}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()


# ============================================================================
# FÁBRICA DE MAESTROS — Fabricadora + Constructor/Arquitecto
# ============================================================================


class Fabricadora:
    """Analiza gaps de capacidad y genera propuestas de construcción.

    No modifica la red. Producción: propuestas con requires_human_approval=True.
    """

    def __init__(self, repo_path: Path = None):
        self.repo_path = repo_path or REPO_PATH
        self.agent_dir = self.repo_path / "agent_directory.json"
        self.state_dir = self.repo_path / "state"
        self.queue_file = self.state_dir / "construction_queue.json"
        self.state_dir.mkdir(exist_ok=True)

    def load_agents(self) -> dict:
        return json.loads(self.agent_dir.read_text(encoding="utf-8"))

    def save_agents(self, data: dict):
        self.agent_dir.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_capability_index(self) -> dict:
        """Lee state/capability_index.json si existe."""
        idx_file = self.state_dir / "capability_index.json"
        if idx_file.exists():
            return json.loads(idx_file.read_text(encoding="utf-8"))
        return {}

    def detect_gaps(self, tasks_attempted: list) -> list:
        """Detecta capability gaps a partir de tareas que fallaron en ejecución."""
        gaps = []
        for task_info in tasks_attempted:
            status = task_info.get("status", "")
            if status == "no_ejecutable":
                gaps.append({
                    "type": "capability_gap",
                    "task": task_info.get("task", ""),
                    "reason": task_info.get("reason", "sin handler ejecutable"),
                    "master": task_info.get("master", ""),
                    "specialist": task_info.get("specialist", ""),
                })
        return gaps

    def analyze_reuse(self, gap_task: str, data: dict = None) -> dict:
        """Analiza qué se puede reutilizar antes de proponer creación nueva.

        Aplica la política de preferencia en orden.
        """
        data = data or self.load_agents()
        maestros = data.get("maestros", {})
        especialistas = data.get("especialistas", {})
        cap_index = self.get_capability_index()

        analysis = {
            "existing_capabilities": [],
            "existing_specialists": [],
            "existing_maestros": [],
            "recommended_reuse": None,
        }

        # 1. Buscar capabilities existentes relacionadas
        task_tokens = set(gap_task.lower().replace("-", " ").split())
        for cap_id, cap_data in cap_index.items():
            cap_name = cap_id.lower()
            if any(t in cap_name for t in task_tokens):
                analysis["existing_capabilities"].append({
                    "id": cap_id,
                    "name": cap_data.get("nombre", cap_id),
                    "score": self._token_overlap(task_tokens, cap_name),
                })

        # 2. Buscar especialistas cuyas capacidades se relacionen
        for esp_id, esp_data in especialistas.items():
            for cap in esp_data.get("capacidades", []):
                cap_lower = cap.lower()
                if any(t in cap_lower for t in task_tokens):
                    analysis["existing_specialists"].append({
                        "id": esp_id,
                        "maestro": esp_data.get("maestro", ""),
                        "capacidades": esp_data.get("capacidades", []),
                    })
                    break

        # 3. Buscar maestros relevantes
        for m_id, m_data in maestros.items():
            dom = m_data.get("dominio", "").lower()
            if any(t in dom for t in task_tokens):
                analysis["existing_maestros"].append({
                    "id": m_id,
                    "dominio": m_data.get("dominio", ""),
                    "division": m_data.get("division", ""),
                })

        # Ordenar por relevancia y recomendar mejor opción
        analysis["existing_capabilities"].sort(key=lambda x: x["score"], reverse=True)
        if analysis["existing_capabilities"]:
            analysis["recommended_reuse"] = {
                "type": "capability",
                "id": analysis["existing_capabilities"][0]["id"],
                "name": analysis["existing_capabilities"][0]["name"],
            }

        return analysis

    def propose(self, gap: dict, analysis: dict = None) -> dict:
        """Genera una propuesta de construcción a partir de un capability gap.

        No modifica la red. La propuesta requiere aprobación humana.
        """
        data = self.load_agents()
        analysis = analysis or self.analyze_reuse(gap.get("task", ""), data)

        # Decidir: reutilizar vs construir
        reuse_decision = self._decide_reuse(analysis)

        proposal = {
            "id": f"prop-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "status": "proposal",
            "problem": gap.get("task", ""),
            "reason": gap.get("reason", ""),
            "reuse_analysis": analysis,
            "reuse_decision": reuse_decision,
            "research": [],
            "proposed_solution": "",
            "architecture": [],
            "required_capabilities": [],
            "required_specialists": [],
            "required_tools": [],
            "files_to_change": [],
            "validation_plan": [],
            "risks": [],
            "acceptance_criteria": [],
            "requires_human_approval": True,
        }

        # Si hay reutilización viable, proponer eso
        if reuse_decision["action"] in ("reuse_capability", "reuse_specialist", "reuse_maestro", "combine_capabilities", "extend_capability"):
            proposal["proposed_solution"] = reuse_decision["rationale"]
        else:
            # Necesita construcción nueva
            proposal["proposed_solution"] = f"Requiere creación de nueva capability para: {gap.get('task', '')}"
            proposal["required_capabilities"].append({
                "name": gap.get("task", ""),
                "reason": gap.get("reason", ""),
            })

        return proposal

    def _decide_reuse(self, analysis: dict) -> dict:
        """Aplica la política de preferencia para decidir reutilización vs creación."""
        caps = analysis.get("existing_capabilities", [])
        esps = analysis.get("existing_specialists", [])
        ms = analysis.get("existing_maestros", [])

        # Política de preferencia en orden
        if caps:
            return {
                "action": "reuse_capability",
                "target": caps[0]["id"],
                "rationale": f"Reutilizar capability existente: {caps[0]['name']} (score: {caps[0]['score']})",
                "priority": 1,
            }
        if esps:
            return {
                "action": "reuse_specialist",
                "target": esps[0]["id"],
                "rationale": f"Reutilizar especialista existente: {esps[0]['id']} → {esps[0]['maestro']}",
                "priority": 2,
            }
        if ms:
            return {
                "action": "reuse_maestro",
                "target": ms[0]["id"],
                "rationale": f"Reutilizar Maestro existente: {ms[0]['id']} — {ms[0]['dominio']}",
                "priority": 3,
            }

        return {
            "action": "create_capability",
            "target": None,
            "rationale": "No hay capacidades existentes que cubran el gap — se requiere creación nueva",
            "priority": 6,
        }

    def _token_overlap(self, tokens1: set, text2: str) -> int:
        """Cuenta tokens en común entre dos conjuntos de palabras."""
        tokens2 = set(text2.lower().split())
        return len(tokens1 & tokens2)

    def queue_proposal(self, proposal: dict) -> str:
        """Guarda la propuesta en la cola de construcción para aprobación humana."""
        queue = self.get_queue()
        queue.append(proposal)
        self.state_dir.mkdir(exist_ok=True)
        self.queue_file.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
        return proposal["id"]

    def get_queue(self) -> list:
        """Lee la cola de construcción pendiente."""
        if self.queue_file.exists():
            return json.loads(self.queue_file.read_text(encoding="utf-8"))
        return []

    def approve_proposal(self, proposal_id: str) -> dict:
        """Marca una propuesta como aprobada (requiere implementación manual por ahora)."""
        queue = self.get_queue()
        for p in queue:
            if p["id"] == proposal_id:
                p["status"] = "approved"
                p["approved_at"] = datetime.now().isoformat()
                break
        self.queue_file.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"proposal_id": proposal_id, "status": "approved"}

    def research(self, topic: str, sources: list = None) -> list:
        """Genera plan de investigación estructurado.

        No ejecuta búsqueda automáticamente — devuelve plan para ejecución humana.
        """
        plan = [
            {
                "step": "pregunta",
                "description": f"Definir pregunta precisa para: {topic}",
                "status": "pending",
            },
            {
                "step": "fuentes",
                "description": f"Consultar fuentes: {sources or ['documentación existente', 'agent_directory.json']}",
                "status": "pending",
            },
            {
                "step": "contraste",
                "description": "Contrastar información entre fuentes",
                "status": "pending",
            },
            {
                "step": "síntesis",
                "description": "Sintetizar hallazgos sin modificar identidad del Maestro",
                "status": "pending",
            },
        ]
        return plan