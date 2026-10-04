#!/usr/bin/env python3
"""Tests for Network Evolution — detection, proposal, application, regression."""
import json, sys, shutil, subprocess, re, importlib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from hermes_bridge import build_capability_index, validate_network
from neural_fellowship import Orquestador, AGENTES_ESPECIALIZADOS, STATE_DIR


@pytest.fixture
def fresh_state(tmp_path, monkeypatch):
    """Isolated state dir + agent_directory for evolution tests."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    monkeypatch.setattr("network_evolution.STATE_DIR", state_dir)
    monkeypatch.setattr("network_evolution.PERF_HISTORY", state_dir / "perf_history.json")
    # Copy real agent_directory.json
    target = tmp_path / "agent_directory.json"
    shutil.copy2(REPO / "agent_directory.json", target)
    monkeypatch.setattr("network_evolution.REPO_PATH", tmp_path)
    return tmp_path


class TestPerformanceTracker:
    def test_record_and_detect_low_confidence(self, fresh_state, monkeypatch):
        from network_evolution import PerformanceTracker
        t = PerformanceTracker()
        t.record("angustia emocional intensa", False, 18, "specialized-customer-success-manager", "MNEMOS")
        signals = t.get_degradation_signals()
        assert any(s["type"] == "low_confidence" for s in signals)

    def test_record_and_detect_failure(self, fresh_state, monkeypatch):
        from network_evolution import PerformanceTracker
        t = PerformanceTracker()
        t.record("duelo no resuelto", False, 0, None, "PHOENIX")
        signals = t.get_degradation_signals()
        assert any(s["type"] == "failed_routing" for s in signals)

    def test_stats(self, fresh_state, monkeypatch):
        from network_evolution import PerformanceTracker
        t = PerformanceTracker()
        t.record("task a", True, 80, "health-emotional-coach", "MNEMOS")
        t.record("task b", False, 10, None, "PHOENIX")
        stats = t.get_stats()
        assert stats["total"] == 2
        assert stats["success_rate"] == 50.0


class TestEvolutionProposer:
    def test_proposes_capability_from_low_confidence(self, fresh_state, monkeypatch):
        from network_evolution import PerformanceTracker, EvolutionProposer
        t = PerformanceTracker()
        t.record("angustia emocional intensa", False, 18, None, "MNEMOS")
        proposer = EvolutionProposer(t)
        proposals = proposer.propose()
        high = [p for p in proposals if p["priority"] == "high"]
        assert len(high) > 0
        assert any("add_especialista_capability" in p["action"] for p in high)

    def test_proposes_consolidation_for_duplicates(self, fresh_state, monkeypatch):
        from network_evolution import PerformanceTracker, EvolutionProposer
        t = PerformanceTracker()
        # validate_network will find existing duplicates
        proposer = EvolutionProposer(t)
        proposals = proposer.propose()
        assert any(p["id"] == "consolidate_capabilities" for p in proposals)


class TestEvolutionApplier:
    def test_apply_add_capability_no_regression(self, fresh_state, monkeypatch):
        from network_evolution import EvolutionApplier
        applier = EvolutionApplier(repo_path=fresh_state)
        proposal = {
            "action": "add_especialista_capability",
            "priority": "high",
            "params": {
                "especialista": "health-emotional-coach",
                "new_capability": "test-capability-evolution",
            },
        }
        result = applier.apply(proposal)
        assert result["status"] == "success"
        assert result["regression_ok"] is True

    def test_apply_add_capability_already_exists(self, fresh_state, monkeypatch):
        from network_evolution import EvolutionApplier
        applier = EvolutionApplier(repo_path=fresh_state)
        # health-emotional-coach already has 'ansiedad'
        proposal = {
            "action": "add_especialista_capability",
            "priority": "high",
            "params": {
                "especialista": "health-emotional-coach",
                "new_capability": "ansiedad",
            },
        }
        result = applier.apply(proposal)
        assert result["status"] == "success"

    def test_apply_unknown_action(self, fresh_state, monkeypatch):
        from network_evolution import EvolutionApplier
        applier = EvolutionApplier(repo_path=fresh_state)
        result = applier.apply({"action": "nonexistent", "priority": "high", "params": {}})
        assert result["status"] == "unknown_action"


class TestRegression:
    def test_evolution_does_not_reduce_test_count(self, fresh_state, monkeypatch):
        """Evolution must not reduce passing test count — regression is checked inside EvolutionApplier.apply()."""
        from network_evolution import EvolutionApplier
        applier = EvolutionApplier(repo_path=fresh_state)
        proposal = {
            "action": "add_especialista_capability",
            "priority": "high",
            "params": {
                "especialista": "health-emotional-coach",
                "new_capability": "test-regression-cap",
            },
        }
        result = applier.apply(proposal)
        assert result["regression_ok"] is True
        assert result["tests_before"]["failed"] == 0
        assert result["tests_after"]["failed"] == 0
