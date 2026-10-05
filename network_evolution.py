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

    def record(self, task_description: str, success: bool, confidence: float, specialist: str = None, master: str = "unknown"):
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
        low_conf_tasks = [s for s in signals if s["type"] == "low_confidence"]
        failed_tasks = [s for s in signals if s["type"] == "failed_routing"]

        stop = {
            "para", "con", "mis", "del", "una", "por", "que", "como",
            "necesito", "tengo", "quiero", "siento", "me", "mi", "mis",
            "el", "la", "los", "las", "un", "una", "y", "de", "en", "al",
            "después", "resuelto", "intensa", "emocional",
        }
        domain_stems = ("angust", "duelo", "pérdid", "estrés", "ansiedad", "depres")
        known_caps = set(build_capability_index().keys())
        orch = Orquestador()

        # --- Proposal 1: Low-confidence → add capability or routing keywords ---
        if low_conf_tasks:
            candidate_words = set()
            for s in low_conf_tasks:
                ws = re.findall(r'\b[a-záéíóúñ]+\b', s["task"].lower())
                for w in ws:
                    if len(w) > 4 and w not in stop:
                        if any(w.startswith(stem) for stem in domain_stems):
                            candidate_words.add(w)
            new_words = sorted(w for w in candidate_words if w not in known_caps)
            if new_words:
                proposals.append({
                    "id": "add_capability",
                    "action": "add_especialista_capability",
                    "priority": "high",
                    "reason": f"{len(low_conf_tasks)} low-confidence routings — unmapped domain terms: {new_words[:5]}",
                    "params": {"especialista": "health-emotional-coach", "new_capability": new_words[0]},
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

        # --- Proposal 4: Routing keywords missing → add to routing_map ---
        orch = Orquestador()
        # the routing_map for that domain lacks those keywords.
        for s in low_conf_tasks + failed_tasks:
            task_lower = s["task"].lower()
            for division, kw_list in orch.routing_map.items():
                # Check if any domain keyword is in the task
                division_match = any(div_kw in task_lower for div_kw in kw_list)
                if division_match:
                    # Find words in the task not covered by any routing_map entry
                    words = re.findall(r'\b[a-záéíóúñ]{4,}\b', task_lower)
                    missing = []
                    for w in words:
                        if w not in stop and not any(w.startswith(stem) for stem in domain_stems):
                            # Check if this word is NOT already in any routing_map list
                            all_routing_kws = set()
                            for dl in orch.routing_map.values():
                                all_routing_kws.update(dl)
                            if w not in all_routing_kws and w not in known_caps:
                                missing.append(w)
                    if missing:
                        proposals.append({
                            "id": f"add_routing_kw_{division}_{missing[0]}",
                            "action": "add_routing_keywords",
                            "priority": "high",
                            "reason": f"Task '{s['task'][:40]}...' has '{missing[0]}' not in routing_map[{division}]",
                            "params": {
                                "division": division,
                                "new_keywords": missing[:3],
                                "task": s["task"],
                                "confidence": s["confidence"],
                            },
                        })
                        break  # One proposal per task is enough

        # --- Proposal 5: Wrong specialist → change connection ---
        # If a task routed to specialist X with low confidence, but specialist Y
        # in the same maestro has a capability matching the task, propose changing.
        for s in low_conf_tasks:
            task_lower = s["task"].lower()
            current_spec = s.get("specialist", "")
            current_maestro = s.get("master", "")
            # Find a better specialist in the same maestro
            for agent_id, info in AGENTES_ESPECIALIZADOS.items():
                if info["maestro"] != current_maestro:
                    continue
                if agent_id == current_spec:
                    continue
                for cap in info.get("capacidades", []):
                    if cap.lower().replace("-", " ") in task_lower:
                        proposals.append({
                            "id": f"change_conn_{current_spec}_to_{agent_id}",
                            "action": "change_connection",
                            "priority": "high",
                            "reason": f"Task '{s['task'][:40]}...' routed to {current_spec} (conf={s['confidence']}), but {agent_id} has matching capability '{cap}'",
                            "params": {
                                "from_division": s.get("master", "unknown"),
                                "to_division": current_maestro,
                                "keyword": cap,
                                "from_specialist": current_spec,
                                "to_specialist": agent_id,
                                "task": s["task"],
                                "capability": cap,
                                "confidence": s["confidence"],
                            },
                        })
                        break
                else:
                    continue
                break

        # --- Proposal 6: No capability exists → create new one ---
        # If a degraded task has words that don't match ANY capability,
        # and no existing capability covers the domain, propose creating one.
        for s in low_conf_tasks:
            task_lower = s["task"].lower()
            # Check if any existing capability matches
            idx = build_capability_index()
            caps_text = " ".join(idx.keys()).lower()
            has_cap_match = any(
                w in caps_text for w in re.findall(r'\b[a-záéíóúñ]{4,}\b', task_lower)
            )
            if not has_cap_match:
                proposals.append({
                    "id": f"create_cap_{s['task'][:20]}",
                    "action": "create_capability",
                    "priority": "high",
                    "reason": f"Task '{s['task'][:40]}...' has no matching capability in index",
                    "params": {
                        "task": s["task"],
                        "confidence": s["confidence"],
                        "specialist": s.get("specialist", ""),
                    },
                })

        # --- Proposal 7: No change needed ---
        # If routing is already correct (high confidence), flag as no_change.
        for s in signals:
            if s["confidence"] >= CONFIDENCE_THRESHOLD and s.get("specialist"):
                proposals.append({
                    "id": f"no_change_{s['task'][:20]}",
                    "action": "no_change",
                    "priority": "low",
                    "reason": f"Task '{s['task'][:40]}...' already correctly routed (conf={s['confidence']})",
                    "params": {
                        "task": s["task"],
                        "specialist": s["specialist"],
                        "confidence": s["confidence"],
                    },
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

    def _reload_orquestador(self, orch=None):
        """Force-reload Orquestador module to persist routing changes.
        If orch is provided, use it directly (avoids re-import side effects)."""
        import importlib
        if orch is None:
            import neural_fellowship
            importlib.reload(neural_fellowship)
        else:
            # Ensure the Orquestador's routing_map is saved to disk
            orch.save_routing_overrides()

    def _restore(self, backup_path: Path, filename: str):
        dst = self.repo / filename
        shutil.copy2(backup_path, dst)

    def apply(self, proposal: dict) -> dict:
        """Apply a proposal. Returns {status, changes, regression_ok}."""
        action = proposal["action"]
        params = proposal["params"]

        # Determine backup file based on action
        if action in ("add_routing_keywords", "change_connection"):
            backup = self._backup("state/routing_overrides.json")
            target_file = "state/routing_overrides.json"
        elif action in ("add_especialista_capability", "consolidate_capabilities"):
            backup = self._backup("agent_directory.json")
            target_file = "agent_directory.json"
        else:
            backup = None
            target_file = None

        before_tests = self._run_tests()

        try:
            if action == "add_routing_keywords":
                self._add_routing_keywords(params["division"], params["new_keywords"])
            elif action == "change_connection":
                self._change_connection(params["from_division"], params["to_division"], params["keyword"])
            elif action == "add_especialista_capability":
                self._add_especialista_capability(params["especialista"], params["new_capability"])
            elif action == "consolidate_capabilities":
                # Flag only — no structural change
                changes = {"flagged": params["warnings"]}
                return {"status": "success", "changes": changes, "regression_ok": True, "backup": str(backup)}
            elif action == "no_change":
                changes = {"reason": params["reason"], "note": "No routing improvement possible"}
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
            if backup and target_file:
                self._restore(backup, target_file)
                build_capability_index()
            return {"status": "failed", "error": str(e), "regression_ok": False, "backup_restored": str(backup)}

    def _change_connection(self, from_division: str, to_division: str, keyword: str):
        """Move a keyword from one division's routing to another via persistent overrides."""
        orch = Orquestador()
        # Remove from source division if present
        if from_division in orch.routing_map and keyword in orch.routing_map[from_division]:
            orch.routing_map[from_division].remove(keyword)
        # Add to target division (no duplicates)
        if to_division in orch.routing_map and keyword not in orch.routing_map[to_division]:
            orch.routing_map[to_division].append(keyword)
        orch.save_routing_overrides()
        # Reload Orquestador to persist changes
        self._reload_orquestador(orch)

    def _add_routing_keywords(self, division: str, new_keywords: list):
        """Add keywords to routing_map[division] via persistent overrides."""
        orch = Orquestador()
        if division not in orch.routing_map:
            return
        existing = set(orch.routing_map[division])
        for kw in new_keywords:
            if kw not in existing:
                orch.routing_map[division].append(kw)
                existing.add(kw)
        orch.save_routing_overrides()
        self._reload_orquestador(orch)

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

def evolve_network(max_iterations: int = 3):
    """
    Main evolution loop — multi-proposal high-priority with rollback:
    1. Route a batch of mental-health tasks to generate performance data
    2. Track results
    3. Propose improvements
    4. For each high-priority proposal: apply → regression check → keep or rollback
    5. If regression fails: revert only that modification, continue with next proposal
    6. Stop when: no proposals left, max_iterations reached, or regression failure without rollback possible
    7. Re-test discovery + reuse after all changes
    """
    tracker = PerformanceTracker()
    orch = Orquestador()

    # Phase 1: Generate performance data with known + edge-case tasks
    train_tasks = [
        ("necesito ayuda con mi ansiedad y manejo del estrés", True, "health-emotional-coach"),
        ("tengo estrés laboral y necesito gestionar mis emociones", True, "health-emotional-coach"),
        ("ansiedad crónica no controlada", True, "health-emotional-coach"),
        ("síntomas depresivos persisten", False, None),
        ("angustia emocional intensa", False, None),
        ("duelo no resuelto después de pérdida", False, None),
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

    # Phase 3: Process high-priority proposals sequentially with rollback
    applier = EvolutionApplier()
    applied = []
    rejected = []
    rollback_occurred = False

    for proposal in high_priority[:max_iterations]:
        result = applier.apply(proposal)

        if result.get("regression_ok"):
            # Validation passed — keep the change
            # Re-test discovery + reuse for this specific change
            r1 = Orquestador().ruta_completa("necesito ayuda con mi ansiedad y manejo del estrés")
            r2 = Orquestador().ruta_completa("tengo estrés laboral y necesito gestionar mis emociones")
            reuse_ok = r1["especialista"]["especialista"] == r2["especialista"]["especialista"] == "health-emotional-coach"
            result["post_apply_reuse_ok"] = reuse_ok
            applied.append({"proposal": proposal, "result": result})
        else:
            # Regression detected — rollback this modification only
            backup = result.get("backup")
            if backup and Path(backup).exists():
                applier._restore(Path(backup), "agent_directory.json")
                build_capability_index()
                rollback_occurred = True
            rejected.append({
                "proposal": proposal,
                "result": result,
                "rollback": bool(backup and Path(backup).exists()),
            })

    # Reload modules after all changes
    import importlib
    import hermes_bridge
    importlib.reload(hermes_bridge)
    import neural_fellowship
    importlib.reload(neural_fellowship)

    # Phase 4: Final re-test discovery + reuse
    r3 = Orquestador().ruta_completa("necesito ayuda con mi ansiedad y manejo del estrés")
    post_reuse_ok = r3["especialista"]["especialista"] == "health-emotional-coach"

    return {
        "status": "evolved" if applied else "no_changes_applied",
        "stats": stats,
        "signals": len(signals),
        "proposals": proposals,
        "applied": applied,
        "rejected": rejected,
        "rollback_occurred": rollback_occurred,
        "reuse_ok": post_reuse_ok,
    }
