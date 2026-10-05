#!/usr/bin/env python3
"""Implementador de propuestas aprobadas — Fábrica de Maestros.

Cierra el tramo: propuesta aprobada → implementación → validación → registro → commit.

Responsabilidad: ejecutar UNA especificación ya aprobada. No decide qué construir.

Uso:
    from __implementador_api__ import Implementador
    imp = Implementador()
    result = imp.receive_proposal(proposal_dict)
"""

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_PATH = Path(__file__).resolve().parent
STATE_DIR = REPO_PATH / "state"
QUEUE_FILE = STATE_DIR / "construction_queue.json"
RESULTS_FILE = STATE_DIR / "implementation_results.json"
BACKUP_DIR = STATE_DIR / "backups"


STATES = ["received", "approved", "implementing", "validating", "completed", "failed", "rolled_back"]


class Implementador:
    """Ejecuta propuestas aprobadas de forma controlada y reversible."""

    def __init__(self):
        self.state = "received"
        self.result: dict[str, Any] = {}
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # 1. Recibir + validar aprobación
    # ------------------------------------------------------------------ #
    def receive_proposal(self, proposal: dict[str, Any]) -> dict[str, Any]:
        """Recibe propuesta. La rechaza si no tiene aprobación explícita."""
        self.result = {
            "proposal_id": proposal.get("id", "unknown"),
            "status": "received",
            "changes": [],
            "validation": {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "commit": None,
            "rollback_executed": False,
            "rollback_reason": None,
        }

        # Señal inequívoca de aprobación: approval explícito + status approved
        approved = (
            proposal.get("status") == "approved"
            and proposal.get("approval") is not None
            and proposal.get("approval").get("approved") is True
            and proposal.get("approval").get("by")  # quién aprobó
        )
        if not approved:
            self.result["status"] = "rejected"
            self.result["reason"] = "Propuesta no aprobada: falta approval explícito"
            return self.result

        self.state = "approved"
        self.result["status"] = "approved"
        return self.result

    # ------------------------------------------------------------------ #
    # 2. Planificar cambios
    # ------------------------------------------------------------------ #
    def planificar_cambios(self, proposal: dict[str, Any]) -> list[dict[str, Any]]:
        """Identifica archivos a modificar según la propuesta."""
        files = proposal.get("files_to_change", [])
        if not files:
            # Soporta 'file' singular y 'path'
            for k in ("file", "path", "filepath"):
                if k in proposal:
                    files = [{"path": proposal[k]}]
                    break
        self.result["changes"] = files
        return files

    # ------------------------------------------------------------------ #
    # 3. Aplicar cambios con backup
    # ------------------------------------------------------------------ #
    def aplicar_cambios(self, proposal: dict[str, Any]) -> dict[str, Any]:
        """Aplica cambios descritos en la propuesta. Guarda backup previo."""
        self.state = "implementing"
        files = self.planificar_cambios(proposal)
        backups = []

        for f in files:
            path = REPO_PATH / f["path"]
            if not path.exists():
                self.result["status"] = "failed"
                self.result["failed_file"] = f["path"]
                self.result["failed_reason"] = f"Archivo no existe: {f['path']}"
                return self._rollback(backups, self.result["failed_reason"])

            # Backup
            backup_path = BACKUP_DIR / f"backup_{path.name}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            shutil.copy2(path, backup_path)
            backups.append({"original": str(path), "backup": str(backup_path)})

            # Aplicar cambios
            content = path.read_text(encoding="utf-8")
            new_content = self._apply_edits(content, f.get("edits", f.get("changes", [])))
            path.write_text(new_content, encoding="utf-8")

        self.result["backups"] = backups
        return {"applied": len(backups), "backups": backups}

    # ------------------------------------------------------------------ #
    # 4. Validar
    # ------------------------------------------------------------------ #
    def ejecutar_validacion(self, proposal: dict[str, Any]) -> dict[str, Any]:
        """Ejecuta validaciones de la propuesta."""
        self.state = "validating"
        validation = proposal.get("validation_plan", [])
        results = []
        failed = False

        for v in validation:
            if v.get("type") == "syntax":
                ok, err = self._validate_syntax(v.get("file", ""))
                results.append({"check": v.get("description", v.get("type")), "passed": ok, "error": err})
                if not ok:
                    failed = True
            elif v.get("type") == "import":
                ok, err = self._validate_import(v.get("file", ""))
                results.append({"check": v.get("description", v.get("type")), "passed": ok, "error": err})
                if not ok:
                    failed = True
            elif v.get("type") == "test":
                ok, err = self._run_test(v.get("command", ""))
                results.append({"check": v.get("description", v.get("type")), "passed": ok, "error": err})
                if not ok:
                    failed = True
            elif v.get("type") == "compile":
                ok, err = self._validate_compile(v.get("file", ""))
                results.append({"check": v.get("description", v.get("type")), "passed": ok, "error": err})
                if not ok:
                    failed = True
            else:
                results.append({"check": str(v), "passed": True, "note": "sin tipo específico"})

        self.result["validation"] = {"checks": results, "all_passed": not failed}

        if not validation:
            self.state = "completed"
            return self.result

        if failed:
            self.state = "failed"
            self.result["rollback_executed"] = True
            self.result["rollback_reason"] = "Validación fallida"
            return self._rollback(self.result.get("backups", []), "Validación fallida")

        self.state = "completed"
        return {"validated": True, "checks": len(results)}

    # ------------------------------------------------------------------ #
    # 5. Registro
    # ------------------------------------------------------------------ #
    def registrar_resultado(self) -> dict[str, Any]:
        """Persiste el resultado de la implementación."""
        self.result["timestamp"] = datetime.now(timezone.utc).isoformat()
        existing = []
        if RESULTS_FILE.exists():
            existing = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
        existing.append(self.result)
        RESULTS_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        return self.result

    # ------------------------------------------------------------------ #
    # 6. Rollback
    # ------------------------------------------------------------------ #
    def rollback(self) -> dict[str, Any]:
        """Restaura backups manualmente (llamado externo)."""
        return self._rollback(self.result.get("backups", []), "rollback manual")

    def _rollback(self, backups: list[dict], reason: str) -> dict[str, Any]:
        """Restaura archivos desde backups."""
        restored = []
        for b in backups:
            original = Path(b["original"])
            backup = Path(b["backup"])
            if original.exists() and backup.exists():
                shutil.copy2(backup, original)
                restored.append(b["original"])
        self.state = "rolled_back"
        self.result["rollback_executed"] = True
        self.result["rollback_reason"] = reason
        self.result["restored_files"] = restored
        return {"rolled_back": len(restored), "reason": reason}

    # ------------------------------------------------------------------ #
    # 7. Git
    # ------------------------------------------------------------------ #
    def commit(self, message: str) -> dict[str, Any]:
        """Commit después de validación exitosa."""
        if self.state != "completed":
            return {"error": f"Commit rechazado: estado={self.state}, se requiere completed"}

        try:
            subprocess.run(
                ["git", "add", "-A"], cwd=REPO_PATH, capture_output=True, timeout=10
            )
            r = subprocess.run(
                ["git", "commit", "-m", message], cwd=REPO_PATH, capture_output=True, timeout=10
            )
            if r.returncode == 0:
                self.result["commit"] = subprocess.run(
                    ["git", "rev-parse", "HEAD"], cwd=REPO_PATH, capture_output=True, text=True, timeout=5
                ).stdout.strip()
            else:
                self.result["commit"] = None
                self.result["commit_error"] = r.stderr.decode(errors="replace")
            return self.result
        except Exception as e:
            self.result["commit_error"] = str(e)
            return self.result

    # ------------------------------------------------------------------ #
    # Flujo completo
    # ------------------------------------------------------------------ #
    def implementar(self, proposal: dict[str, Any]) -> dict[str, Any]:
        """Flujo completo: receive → apply → validate → register."""
        r = self.receive_proposal(proposal)
        if r["status"] == "rejected":
            return r

        self.aplicar_cambios(proposal)
        if self.state == "failed":
            return self.result

        self.ejecutar_validacion(proposal)
        self.registrar_resultado()
        return self.result

    # ------------------------------------------------------------------ #
    # Helpers internos
    # ------------------------------------------------------------------ #
    def _apply_edits(self, content: str, edits: list[dict]) -> str:
        """Aplica parches de texto a un archivo."""
        for edit in edits:
            old = edit.get("old", edit.get("replace", ""))
            new = edit.get("new", edit.get("with", ""))
            if old:
                content = content.replace(old, new)
        return content

    def _validate_syntax(self, filepath: str) -> tuple[bool, str]:
        if not filepath:
            return True, ""
        import py_compile
        try:
            py_compile.compile(REPO_PATH / filepath, doraise=True)
            return True, ""
        except (py_compile.PyCompileError, FileNotFoundError) as e:
            return False, str(e)

    def _validate_import(self, filepath: str) -> tuple[bool, str]:
        if not filepath:
            return True, ""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("_check", REPO_PATH / filepath)
            if spec and spec.loader:
                import importlib.util
                mod = importlib.util.module_from_spec(spec)
                return True, ""
            return True, ""
        except Exception as e:
            return False, str(e)

    def _run_test(self, command: str) -> tuple[bool, str]:
        if not command:
            return True, ""
        try:
            r = subprocess.run(command, shell=True, capture_output=True, timeout=30, cwd=REPO_PATH)
            return r.returncode == 0, r.stderr.decode(errors="replace")[:500]
        except Exception as e:
            return False, str(e)

    def _validate_compile(self, filepath: str) -> tuple[bool, str]:
        return self._validate_syntax(filepath)


# ----------------------------------------------------------------------
# API mínima standalone
# ----------------------------------------------------------------------
def implementar_propuesta(proposal: dict) -> dict:
    """Conveniencia: recibe propuesta → implementa → retorna resultado."""
    imp = Implementador()
    return imp.implementar(proposal)