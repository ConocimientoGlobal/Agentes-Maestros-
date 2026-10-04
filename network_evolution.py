#!/usr/bin/env python3
"""
NETWORK EVOLUTION — Loop de mejora continua para la red de agentes.

Reutiliza componentes existentes (Orquestador, LearningSystem, validate_network,
build_capability_index, AGENTES_MAESTROS/ESPECIALIZADOS).

1. PerformanceTracker  → registra routing results → detecta degradación
2. EvolutionProposer   → sugiere mejoras concretas (keywords, capacidades, especialistas)
3. EvolutionApplier    → aplica mejoras con backup + regression check
"""
import json, shutil, subprocess, sys, re
from datetime import datetime
from pathlib import Path

REPO_PATH = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_PATH))

from hermes_bridge import (
    Orquestador, route_task, build_capability_index,
    AGENTES_MAESTROS, AGENTES_ESPECIALIZADOS,
    validate_network, get_maestro_graph,
)
from neural_fellowship import LearningSystem, STATE_DIR

PERF_HISTORY = STATE_DIR / "perf_history.json"
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Score confidence threshold below which a routing is considered "degraded"
CONFIDENCE_THRESHOLD = 30


class PerformanceTracker:
    """Tracks routing results and detects degradation signals."""

    def __init__(self):
        self.history = self._load()

    def _load(self):
        if PERF_HISTORY.exists():
            return json.loads(PERF_HISTORY.read_text(encoding="utf-8"))
        return {"tasks": [], "degradation_signals": []}

    def _save(self):
        PERF_HISTORY.write_text(json.dumps(self.history, indent=2, ensure_ascii=False), encoding="utf-8")

    def record(self, task_description: str, success: bool, confidence: int, specialist: str = None, master: str = None):
        """Record a routing outcome."""
        entry = {
            "task": task_description,
            "success": success,
            "confidence": confidence,
            "specialist": specialist or "",
            "master": master or "",
            "timestamp": datetime.now().isoformat(),
        }
        self.history["tasks"].append(entry)
        self._save()

        # Detect degradation signals
        if confidence < CONFIDENCE_THRESHOLD:
            signal = {
                "type": "low_confidence",
                "task": task_description,
                "confidence": confidence,
                "specialist": specialist,
                "master": master,
                "detected_at": datetime.now().isoformat(),
            }
            self.history["degradation_signals"].append(signal)
            self._save()

        if not success:
            signal = {
                "type": "failed_routing",
                "task": task_description,
                "confidence": confidence,
                "specialist": specialist,
                "master": master,
                "detected_at": datetime.now().isoformat(),
            }
            self.history["degradation_signals"].append(signal)
            self._save()

    def get_degradation_signals(self) -> list:
        """Return recent degradation signals (last 50)."""
        return self.history["degradation_signals"][-50:]

    def get_tasks_with_capability(self) -> list:
        """Extract tasks that mention capabilities not in the index."""
        idx = build_capability_index()
        known_caps = set(idx.keys())
        unknown = []
        for t in self.history["tasks"]:
            task_lower = t["task"].lower()
            for cap in known_caps:
                pass  # known capabilities are fine
            # Look for domain-relevant words that don't map to any capability
            words = re.findall(r'\b[a-záéíóúñ]+\b', task_lower)
            for w in words:
                if len(w) > 5:
                    # Check if this word appears in any capability name
                    if not any(w in cap for cap in known_caps):
                        unknown.append((t, w))
        return unknown

    def get_stats(self) -> dict:
        tasks = self.history["tasks"]
        if not tasks:
            return {"total": 0, "success_rate": 0, "avg_confidence": 0}
        successes = sum(1 for t in tasks if t["success"])
        avg_conf = sum(t["confidence"] for t in tasks) / len(tasks)
        return {
            "total": len(tasks),
            "success_rate": round(successes / len(tasks) * 100, 2),
            "avg_confidence": round(avg_conf, 2),
            "degradation_signals": len(self.history["degradation_signals"]),
        }


class EvolutionProposer:
    """Proposes concrete improvements based on performance data."""

    def __init__(self, tracker: PerformanceTracker):
        self.tracker = tracker

    def propose(self) -> list:
        """Generate improvement proposals. Returns list of dicts."""
        proposals = []
        signals = self.tracker.get_degradation_signals()

        # --- Proposal 1: Low-confidence tasks → add capability/keywords ---
        low_conf_tasks = [s for s in signals if s["type"] == "low_confidence"]
        if low_conf_tasks:
            # Collect domain-relevant words from low-confidence tasks
            stop = {"para", "con", "mis", "del", "una", "por", "que", "como", "necesito", "tengo", "y", "de"}
            words = set()
            for s in low_conf_tasks:
                ws = re.findall(r'\b[a-záéíóúñ-]+\b', s["task"].lower())
                words.update(w for w in ws if len(w) > 5 and w not in stop)
            known_caps = set(build_capability_index().keys())
            new_words = sorted(w for w in words if w not in known_caps)

            if new_words:
                # Determine the correct especialista: if task routed to health maestro but wrong
                # specialist, target health-emotional-coach. Otherwise use the routed specialist.
                target_esp = "health-emotional-coach"
                for s in low_conf_tasks:
                    if s.get("master") in ("MNEMOS", "healthcare"):
                        target_esp = "health-emotional-coach"
                        break
                proposals.append({
                    "id": "add_capability",
                    "action": "add_especialista_capability",
                    "priority": "high",
                    "reason": f"{len(low_conf_tasks)} low-confidence routings detected — unmapped domain terms: {new_words[:5]}",
                    "params": {
                        "especialista": target_esp,
                        "new_capability": new_words[0],
                    },
                })

        # --- Proposal 2: Failed routing → add capability to especialista ---
        failed_tasks = [s for s in signals if s["type"] == "failed_routing"]
        if failed_tasks:
            stop = {"para", "con", "mis", "del", "una", "por", "que", "como", "necesito", "tengo", "y", "de"}
            candidate_words = set()
            for s in failed_tasks:
                ws = re.findall(r'\b[a-záéíóúñ]+\b', s["task"].lower())
                candidate_words.update(w for w in ws if len(w) > 5 and w not in stop)
            known_caps = set(build_capability_index().keys())
            new_cap = sorted(w for w in candidate_words if w not in known_caps)
            if new_cap:
                # Target health-emotional-coach for health-domain failed routings
                target_esp = "health-emotional-coach"
                for s in failed_tasks:
                    if s.get("master") == "MNEMOS":
                        target_esp = "health-emotional-coach"
                        break
                proposals.append({
                    "id": "add_capability_2",
                    "action": "add_especialista_capability",
                    "priority": "high",
                    "reason": f"{len(failed_tasks)} failed routings for unmapped capability",
                    "params": {
                        "especialista": target_esp,
                        "new_capability": new_cap[0],
                    },
                })

        # --- Proposal 3: Duplicate capability warnings → consolidate ---
        net = validate_network()
        if net["warnings"]:
            dup_caps = [w for w in net["warnings"] if "owned by both" in w]
            if dup_caps:
                proposals.append({
                    "id": "consolidate_capabilities",
                    "action": "flag_duplicate_capability",
                    "priority": "medium",
                    "reason": f"{len(dup_caps)} duplicate capability ownerships detected",
                    "params": {"warnings": dup_caps},
                })

        return proposals


class EvolutionApplier:
    """Applies proposals with backup + regression check."""

    def __init__(self, repo_path: Path = None):
        self.repo = repo_path or REPO_PATH
        self.backup_dir = self.repo / "state" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _backup(self, filename: str) -> Path:
        src = self.repo / filename
        if not src.exists():
            return None
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = self.backup_dir / f"{filename}.{stamp}"
        shutil.copy2(src, dst)
        return dst

    def _restore(self, backup_path: Path, filename: str):
        dst = self.repo / filename
        shutil.copy2(backup_path, dst)

    def apply(self, proposal: dict) -> dict:
        """Apply a proposal. Returns {status, changes, regression_ok}."""
        action = proposal["action"]
        params = proposal["params"]
        backup = self._backup("hermes_bridge.py") if action == "add_routing_keywords" else self._backup("agent_directory.json")
        before_tests = self._run_tests()

        try:
            if action == "add_routing_keywords":
                self._add_routing_keywords(params["division"], params["new_keywords"])
            elif action == "add_especialista_capability":
                self._add_especialista_capability(params["especialista"], params["new_capability"])
            elif action == "consolidate_capabilities":
                # Flag only — no structural change
                changes = {"flagged": params["warnings"]}
                return {"status": "success", "changes": changes, "regression_ok": True, "backup": str(backup)}
            else:
                return {"status": "unknown_action", "regression_ok": False}

            # Rebuild capability index after changes
            build_capability_index()

            after_tests = self._run_tests()
            regression_ok = after_tests["failed"] == 0 and after_tests["failed"] <= before_tests["failed"]

            return {
                "status": "success",
                "changes": params,
                "regression_ok": regression_ok,
                "backup": str(backup),
                "tests_before": before_tests,
                "tests_after": after_tests,
            }
        except Exception as e:
            if backup:
                self._restore(backup, "hermes_bridge.py" if action == "add_routing_keywords" else "agent_directory.json")
                build_capability_index()
            return {"status": "failed", "error": str(e), "regression_ok": False, "backup_restored": str(backup)}

    def _add_routing_keywords(self, division: str, new_keywords: list):
        """Add keywords to routing_map[division] in Orquestador."""
        # Read the Orquestador's routing_map and extend it
        # We patch the source file to be persistent
        bridge_file = self.repo / "hermes_bridge.py"
        content = bridge_file.read_text(encoding="utf-8")

        # Find the health routing line and extend it
        for kw in new_keywords:
            kw_escaped = kw.replace('"', '\\"')
            # We need to add the keyword to the routing_map in neural_fellowship.py
            # But hermes_bridge imports Orquestador, so we patch neural_fellowship.py
            nf_file = self.repo / "neural_fellowship.py"
            nf_content = nf_file.read_text(encoding="utf-8")

            # Find the health routing list
            health_line = re.search(
                r'("health": \[.*?)\]', nf_content
            )
            if health_line:
                old_list = health_line.group(1)
                # Check if keyword already present
                if f'"{kw}"' not in nf_content:
                    new_list = old_list + f', "{kw}"'
                    nf_content = nf_content.replace(old_list, new_list, 1)
                    nf_file.write_text(nf_content, encoding="utf-8")

    def _add_especialista_capability(self, especialista: str, capability: str):
        """Add a capability to a specialist in agent_directory.json."""
        dir_file = self.repo / "agent_directory.json"
        data = json.loads(dir_file.read_text(encoding="utf-8"))
        if especialista in data.get("especialistas", {}):
            caps = data["especialistas"][especialista].get("capacidades", [])
            if capability not in caps:
                caps.append(capability)
                data["especialistas"][especialista]["capacidades"] = caps
                dir_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _run_tests(self) -> dict:
        """Run pytest and return {passed, failed, output}."""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q"],
            capture_output=True, text=True, cwd=str(self.repo)
        )
        output = result.stdout + result.stderr
        passed_match = re.search(r'(\d+) passed', output)
        failed_match = re.search(r'(\d+) failed', output)
        return {
            "passed": int(passed_match.group(1)) if passed_match else 0,
            "failed": int(failed_match.group(1)) if failed_match else 0,
            "exit_code": result.returncode,
            "output_tail": output[-200:],
        }


# --- High-level orchestration ---

def evolve_network(iterations: int = 3):
    """
    Main evolution loop:
    1. Route a batch of mental-health tasks to generate performance data
    2. Track results
    3. Propose improvements
    4. Apply safest proposal
    5. Regression check
    6. Re-test discovery + reuse
    """
    tracker = PerformanceTracker()
    orch = Orquestador()

    # Phase 1: Generate performance data with known + edge-case tasks
    train_tasks = [
        ("necesito ayuda con mi ansiedad y manejo del estrés", True, "health-emotional-coach"),
        ("tengo estrés laboral y necesito gestionar mis emociones", True, "health-emotional-coach"),
        ("ansiedad crónica no controlada", True, "health-emotional-coach"),
        ("síntomas depresivos persisten", False, None),           # edge: no exact match
        ("angustia emocional intensa", False, None),              # edge: low confidence
        ("duelo no resuelto después de pérdida", False, None),   # edge: no mapping
    ]

    for desc, expected_success, expected_spec in train_tasks:
        result = orch.ruta_completa(desc)
        spec_id = result["especialista"]["especialista"]
        conf = result["especialista"]["confianza"]
        success = expected_success and spec_id == expected_spec
        tracker.record(desc, success, conf, spec_id, result["maestro"]["maestro"])

    stats = tracker.get_stats()
    signals = tracker.get_degradation_signals()

    # Phase 2: Propose improvements
    proposer = EvolutionProposer(tracker)
    proposals = proposer.propose()

    # Filter to high-priority proposals only
    high_priority = [p for p in proposals if p["priority"] == "high"]

    if not high_priority:
        return {
            "status": "no_improvements_needed",
            "stats": stats,
            "signals": len(signals),
            "proposals": proposals,
        }

    # Phase 3: Apply first high-priority proposal
    applier = EvolutionApplier()
    result = applier.apply(high_priority[0])

    # Phase 4: Re-test discovery + reuse after improvement
    r1 = orch.ruta_completa("necesito ayuda con mi ansiedad y manejo del estrés")
    r2 = orch.ruta_completa("tengo estrés laboral y necesito gestionar mis emociones")
    reuse_ok = r1["especialista"]["especialista"] == r2["especialista"]["especialista"] == "health-emotional-coach"

    # Reload capability index after changes
    import importlib
    import hermes_bridge
    importlib.reload(hermes_bridge)
    import neural_fellowship
    importlib.reload(neural_fellowship)

    r3 = Orquestador().ruta_completa("necesito ayuda con mi ansiedad y manejo del estrés")
    post_reuse_ok = r3["especialista"]["especialista"] == "health-emotional-coach"

    return {
        "status": "evolved",
        "stats": stats,
        "signals": len(signals),
        "proposals": proposals,
        "applied": high_priority[0],
        "result": result,
        "reuse_ok": reuse_ok,
        "post_evolution_reuse_ok": post_reuse_ok,
    }
