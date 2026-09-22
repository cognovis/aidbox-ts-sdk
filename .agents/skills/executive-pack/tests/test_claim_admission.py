"""Claim admission gate for Repository Delivery (clc-7leq).

Seam A authorizes implementation dispatch only from a successful claim
envelope for the requested Bead and current owner. Seam B drives the live
claim-bead.py gate through a mocked bd fixture: first claim, same-owner
resume, and foreign refusal. The gate never launches an implementation
session.
"""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "skills" / "executive-pack" / "scripts"
ADMISSION_SCRIPT = SCRIPTS / "claim_admission.py"
CLAIM_BEAD_ENTRYPOINT = "skills/executive-pack/scripts/claim-bead.py"

sys.path.insert(0, str(SCRIPTS))

from claim import MockCommandRunner, claim_bead  # noqa: E402


def _load_admission():
    spec = importlib.util.spec_from_file_location("claim_admission", ADMISSION_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _completed(stdout: str, returncode: int = 0) -> subprocess.CompletedProcess:
    result = subprocess.CompletedProcess(args=[], returncode=returncode)
    result.stdout = stdout
    result.stderr = ""
    return result


def _bd_show_json(
    status: str,
    bead_id: str,
    assignee: str = "",
    claimed_by: str = "",
) -> str:
    metadata: dict[str, Any] = {}
    if claimed_by:
        metadata["claim"] = {"claimed_by": claimed_by}
    return json.dumps(
        [
            {
                "id": bead_id,
                "status": status,
                "assignee": assignee,
                "metadata": metadata,
            }
        ]
    )


def _ok_envelope(bead_id: str = "clc-1", owner: str = "session-a") -> dict[str, Any]:
    return {
        "status": "ok",
        "summary": f"Bead {bead_id} claimed by {owner}",
        "data": {
            "bead_id": bead_id,
            "current_status": "in_progress",
            "assignee": owner,
            "claim": {"claimed_by": owner, "claimed_at": "2026-01-01T00:00:00Z"},
        },
        "errors": [],
        "next_steps": [],
        "open_items": [],
        "meta": {
            "contract_version": "1",
            "producer": "claim.py",
            "schema": "core/contracts/execution-result.schema.json",
        },
    }


def _error_envelope(
    bead_id: str = "clc-1",
    code: str = "ALREADY_CLAIMED",
    assignee: str = "",
) -> dict[str, Any]:
    return {
        "status": "error",
        "summary": f"Bead {bead_id} is already in_progress — refusing claim",
        "data": {
            "bead_id": bead_id,
            "current_status": "in_progress",
            "assignee": assignee,
        },
        "errors": [
            {
                "code": code,
                "message": f"Bead {bead_id} is already in_progress.",
                "retryable": False,
                "suggested_fix": f"bd update {bead_id} --status=open",
            }
        ],
        "next_steps": [],
        "open_items": [],
        "meta": {
            "contract_version": "1",
            "producer": "claim.py",
            "schema": "core/contracts/execution-result.schema.json",
        },
    }


def _in_progress_runner(bead_id: str, assignee: str) -> MockCommandRunner:
    return MockCommandRunner(
        responses={
            f"bd show {bead_id} --json": _completed(
                _bd_show_json("in_progress", bead_id, assignee=assignee)
            ),
        }
    )


def _install_fake_tracker(
    tmp_path: Path,
    *,
    bead_id: str,
    status: str,
    assignee: str = "",
    title: str = "Fix it",
    description: str = "body",
) -> dict[str, Path]:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    show_path = tmp_path / "bead.json"
    show_path.write_text(
        json.dumps(
            [
                {
                    "id": bead_id,
                    "status": status,
                    "assignee": assignee,
                    "title": title,
                    "description": description,
                    "metadata": (
                        {"claim": {"claimed_by": assignee}} if assignee else {}
                    ),
                }
            ]
        ),
        encoding="utf-8",
    )
    log_path = tmp_path / "bd.log"
    bd = bindir / "bd"
    bd.write_text(
        (
            "#!/bin/sh\n"
            f'printf "%s\\n" "$*" >> "{log_path}"\n'
            'if [ "$1" = "show" ]; then\n'
            f'  cat "{show_path}"\n'
            "  exit 0\n"
            "fi\n"
            "exit 0\n"
        ),
        encoding="utf-8",
    )
    bd.chmod(bd.stat().st_mode | stat.S_IXUSR)
    ccore = bindir / "ccore"
    ccore.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    ccore.chmod(ccore.stat().st_mode | stat.S_IXUSR)
    return {"bindir": bindir, "log": log_path, "show": show_path}


def _cli_calls_claim_bead(cmd: list[str] | tuple[str, ...] | str) -> bool:
    parts = cmd if isinstance(cmd, (list, tuple)) else [cmd]
    return any(str(part).endswith("claim-bead.py") for part in parts)


# --- Seam A: authorize from envelope -----------------------------------------


def test_missing_envelope_refuses_dispatch_before_launch() -> None:
    admission = _load_admission()

    result = admission.authorize_implementation_dispatch(
        None, bead_id="clc-1", owner="session-a"
    )

    assert result["dispatch_authorized"] is False
    assert result["implementation_launched"] is False
    assert result["code"] == "CLAIM_ENVELOPE_MISSING"


def test_empty_envelope_refuses_dispatch() -> None:
    admission = _load_admission()

    result = admission.authorize_implementation_dispatch(
        {}, bead_id="clc-1", owner="session-a"
    )

    assert result["dispatch_authorized"] is False
    assert result["implementation_launched"] is False
    assert result["code"] == "CLAIM_ENVELOPE_MISSING"


def test_wrong_bead_envelope_is_mismatch() -> None:
    admission = _load_admission()

    result = admission.authorize_implementation_dispatch(
        _ok_envelope(bead_id="clc-other"), bead_id="clc-1", owner="session-a"
    )

    assert result["dispatch_authorized"] is False
    assert result["implementation_launched"] is False
    assert result["code"] == "CLAIM_ENVELOPE_MISMATCH"


def test_wrong_owner_envelope_is_mismatch() -> None:
    admission = _load_admission()

    result = admission.authorize_implementation_dispatch(
        _ok_envelope(owner="session-other"), bead_id="clc-1", owner="session-a"
    )

    assert result["dispatch_authorized"] is False
    assert result["implementation_launched"] is False
    assert result["code"] == "CLAIM_ENVELOPE_MISMATCH"


def test_non_claim_envelope_is_mismatch() -> None:
    admission = _load_admission()
    foreign = {
        "status": "ok",
        "data": {"bead_id": "clc-1", "assignee": "session-a"},
        "meta": {"producer": "landing_policy.py"},
    }

    result = admission.authorize_implementation_dispatch(
        foreign, bead_id="clc-1", owner="session-a"
    )

    assert result["dispatch_authorized"] is False
    assert result["implementation_launched"] is False
    assert result["code"] == "CLAIM_ENVELOPE_MISMATCH"


def test_unsuccessful_envelope_refuses_even_when_ids_match() -> None:
    admission = _load_admission()

    result = admission.authorize_implementation_dispatch(
        _error_envelope(assignee="session-a"), bead_id="clc-1", owner="session-a"
    )

    assert result["dispatch_authorized"] is False
    assert result["implementation_launched"] is False
    assert result["code"] == "CLAIM_UNSUCCESSFUL"
    assert result["envelope"]["status"] == "error"


def test_successful_matching_envelope_is_not_live_dispatch_authority() -> None:
    admission = _load_admission()
    envelope = _ok_envelope()

    result = admission.authorize_implementation_dispatch(
        envelope, bead_id="clc-1", owner="session-a"
    )

    assert result["dispatch_authorized"] is False
    assert result.get("claim_verified") is not True
    assert result["implementation_launched"] is False
    assert result["code"] == "CLAIMED"
    assert result["envelope"] is envelope


def test_authorization_ignores_process_exit_code() -> None:
    """claim-bead.py exits 0 on almost every error; the envelope is the decision."""
    admission = _load_admission()
    assert "returncode" not in admission.authorize_implementation_dispatch.__code__.co_varnames
    assert "exit_code" not in admission.authorize_implementation_dispatch.__code__.co_varnames


def test_cli_has_no_authorize_or_envelope_file_command() -> None:
    help_text = subprocess.run(
        [sys.executable, str(ADMISSION_SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    unknown = subprocess.run(
        [
            sys.executable,
            str(ADMISSION_SCRIPT),
            "authorize",
            "--bead-id",
            "clc-1",
            "--owner",
            "session-a",
            "--envelope-file",
            "stale.json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    combined_help = f"{help_text.stdout}\n{help_text.stderr}"
    assert "admit" in combined_help
    assert "authorize" not in combined_help
    assert "envelope-file" not in combined_help
    assert unknown.returncode != 0
    assert "invalid choice" in unknown.stderr.lower()
    assert "authorize" in unknown.stderr
    assert not unknown.stdout.strip().startswith("{")


def test_empty_owner_is_refused_without_claiming(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    admission = _load_admission()
    tools = _install_fake_tracker(tmp_path, bead_id="clc-1", status="open")
    monkeypatch.setenv("PATH", str(tools["bindir"]) + os.pathsep + os.environ.get("PATH", ""))

    result = admission.admit_claim(bead_id="clc-1", owner="  ")

    assert result["dispatch_authorized"] is False
    assert result["implementation_launched"] is False
    assert result["code"] == "CLAIM_OWNER_MISSING"
    assert not tools["log"].exists()


def test_empty_bead_id_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    admission = _load_admission()
    tools = _install_fake_tracker(tmp_path, bead_id="clc-1", status="open")
    monkeypatch.setenv("PATH", str(tools["bindir"]) + os.pathsep + os.environ.get("PATH", ""))

    result = admission.admit_claim(bead_id="", owner="session-a")

    assert result["dispatch_authorized"] is False
    assert result["code"] == "CLAIM_BEAD_MISSING"
    assert not tools["log"].exists()


# --- Seam B: disposable mocked-bd fixture ------------------------------------


def test_first_claim_admits_and_does_not_launch_implementation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    admission = _load_admission()
    tools = _install_fake_tracker(tmp_path, bead_id="clc-fix", status="open")
    monkeypatch.setenv("PATH", str(tools["bindir"]) + os.pathsep + os.environ.get("PATH", ""))

    result = admission.admit_claim(bead_id="clc-fix", owner="session-a")

    log = tools["log"].read_text(encoding="utf-8")
    assert result["dispatch_authorized"] is True
    assert result["claim_verified"] is True
    assert result["implementation_launched"] is False
    assert result["code"] == "CLAIMED"
    assert result["envelope"]["status"] == "ok"
    assert result["envelope"]["data"]["assignee"] == "session-a"
    assert "update" in log
    assert "implement" not in log


def test_same_owner_replay_is_idempotent_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    admission = _load_admission()
    runner = _in_progress_runner("clc-fix", assignee="session-a")
    first = claim_bead(
        bead_id="clc-fix", session_id="session-a", command_runner=runner
    )
    assert first["status"] == "error"
    assert first["errors"][0]["code"] == "ALREADY_CLAIMED"

    tools = _install_fake_tracker(
        tmp_path, bead_id="clc-fix", status="in_progress", assignee="session-a"
    )
    monkeypatch.setenv("PATH", str(tools["bindir"]) + os.pathsep + os.environ.get("PATH", ""))

    result = admission.admit_claim(bead_id="clc-fix", owner="session-a")

    log = tools["log"].read_text(encoding="utf-8")
    assert result["dispatch_authorized"] is True
    assert result["claim_verified"] is True
    assert result["implementation_launched"] is False
    assert result["code"] == "RESUMED"
    assert result["envelope"]["status"] == "ok"
    assert result["envelope"]["data"]["assignee"] == "session-a"
    assert "update" not in log


def test_foreign_owner_is_typed_refusal_without_implementation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    admission = _load_admission()
    tools = _install_fake_tracker(
        tmp_path, bead_id="clc-fix", status="in_progress", assignee="session-other"
    )
    monkeypatch.setenv("PATH", str(tools["bindir"]) + os.pathsep + os.environ.get("PATH", ""))

    result = admission.admit_claim(bead_id="clc-fix", owner="session-a")

    log = tools["log"].read_text(encoding="utf-8")
    assert result["dispatch_authorized"] is False
    assert result.get("claim_verified") is not True
    assert result["implementation_launched"] is False
    assert result["code"] == "FOREIGN_CLAIM"
    assert result["envelope"]["status"] == "error"
    assert "session-other" in result["summary"]
    assert "update" not in log
    assert "implement" not in log


def test_admit_invokes_claim_bead_entrypoint_not_retired_loop() -> None:
    source = ADMISSION_SCRIPT.read_text(encoding="utf-8")
    tests = Path(__file__).read_text(encoding="utf-8")
    retired_contract = "execution_contract" + ".py"
    retired_worker = "bead-loop-" + "implementer"

    assert CLAIM_BEAD_ENTRYPOINT in source
    assert CLAIM_BEAD_ENTRYPOINT in tests
    assert retired_contract not in source
    assert retired_worker not in source
    assert retired_contract not in tests
    assert retired_worker not in tests


def test_admit_executes_claim_bead_cli_and_ignores_exit_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    admission = _load_admission()
    tools = _install_fake_tracker(
        tmp_path,
        bead_id="clc-fix",
        status="open",
        title="[DISCOVERED] note only",
        description="no criteria",
    )
    monkeypatch.setenv("PATH", str(tools["bindir"]) + os.pathsep + os.environ.get("PATH", ""))
    calls: list[Any] = []
    real_run = subprocess.run

    def spy(cmd, *args, **kwargs):  # noqa: ANN001
        calls.append(cmd)
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", spy)
    if hasattr(admission, "subprocess"):
        monkeypatch.setattr(admission.subprocess, "run", spy)

    result = admission.admit_claim(bead_id="clc-fix", owner="session-a")

    assert any(_cli_calls_claim_bead(cmd) for cmd in calls)
    assert result["dispatch_authorized"] is False
    assert result["code"] == "CLAIM_UNSUCCESSFUL"
    assert result["envelope"].get("errors", [{}])[0].get("code") == "BEAD_BODY_INCOMPLETE"
