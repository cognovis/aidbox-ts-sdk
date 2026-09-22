#!/usr/bin/env -S uv run python
"""Admit Repository Delivery implementation from a claim-bead envelope.

The live claim entrypoint is `skills/executive-pack/scripts/claim-bead.py`.
This module invokes that CLI wrapper and branches on its typed JSON envelope,
never on its process exit code. `claim-bead.py` exits 0 on almost every error.

First claim and same-owner resume authorize dispatch. A foreign in-progress
claim is a typed `FOREIGN_CLAIM` refusal. This gate never launches an
implementation session; the caller keeps the envelope as delivery state.

`admit` is the only public path that may set dispatch_authorized true, and it
does so only after the live claim-bead CLI reports ownership. Caller-authored
envelope files are not dispatch authority.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from claim import DefaultCommandRunner, _probe_bead

CONTRACT = "cognovis.claim-admission.v1"
CLAIM_PRODUCERS = frozenset({"claim.py", "claim-bead.py"})
CLAIM_ENTRYPOINT = "skills/executive-pack/scripts/claim-bead.py"
CLAIM_BEAD_SCRIPT = _SCRIPT_DIR / "claim-bead.py"


def extract_last_json_object(raw: str) -> dict[str, Any] | None:
    """Return the last JSON object in claim-bead stdout (human line + envelope)."""
    decoder = json.JSONDecoder()
    last: dict[str, Any] | None = None
    index = 0
    while index < len(raw):
        brace = raw.find("{", index)
        if brace < 0:
            break
        try:
            obj, end = decoder.raw_decode(raw, brace)
        except json.JSONDecodeError:
            index = brace + 1
            continue
        if isinstance(obj, dict):
            last = obj
        index = end
    return last


def authorize_implementation_dispatch(
    envelope: dict[str, Any] | None,
    *,
    bead_id: str,
    owner: str,
) -> dict[str, Any]:
    """Classify a claim envelope. Does not grant live dispatch authority."""
    if not str(owner or "").strip():
        return _result(
            dispatch_authorized=False,
            code="CLAIM_OWNER_MISSING",
            envelope=envelope if isinstance(envelope, dict) else None,
            bead_id=bead_id,
            owner=owner,
            summary="Claim owner is empty; implementation dispatch is refused.",
        )
    if not str(bead_id or "").strip():
        return _result(
            dispatch_authorized=False,
            code="CLAIM_BEAD_MISSING",
            envelope=envelope if isinstance(envelope, dict) else None,
            bead_id=bead_id,
            owner=owner,
            summary="Bead id is empty; implementation dispatch is refused.",
        )
    if not isinstance(envelope, dict) or not envelope:
        return _result(
            dispatch_authorized=False,
            code="CLAIM_ENVELOPE_MISSING",
            envelope=envelope if isinstance(envelope, dict) else None,
            bead_id=bead_id,
            owner=owner,
            summary="No claim envelope was supplied; implementation dispatch is refused.",
        )

    if not _is_claim_envelope(envelope):
        return _result(
            dispatch_authorized=False,
            code="CLAIM_ENVELOPE_MISMATCH",
            envelope=envelope,
            bead_id=bead_id,
            owner=owner,
            summary="Envelope is not a claim-bead.py / claim.py claim envelope.",
        )

    data = envelope.get("data") if isinstance(envelope.get("data"), dict) else {}
    envelope_bead = str(data.get("bead_id") or "").strip()
    envelope_owner = _envelope_owner(data)
    if envelope_bead != bead_id:
        return _result(
            dispatch_authorized=False,
            code="CLAIM_ENVELOPE_MISMATCH",
            envelope=envelope,
            bead_id=bead_id,
            owner=owner,
            summary=(
                f"Claim envelope bead_id={envelope_bead!r} owner={envelope_owner!r} "
                f"does not match requested bead_id={bead_id!r} owner={owner!r}."
            ),
        )

    if envelope.get("status") != "ok":
        return _result(
            dispatch_authorized=False,
            code="CLAIM_UNSUCCESSFUL",
            envelope=envelope,
            bead_id=bead_id,
            owner=owner,
            summary=str(envelope.get("summary") or "Claim envelope is not successful."),
        )

    if envelope_owner != owner:
        return _result(
            dispatch_authorized=False,
            code="CLAIM_ENVELOPE_MISMATCH",
            envelope=envelope,
            bead_id=bead_id,
            owner=owner,
            summary=(
                f"Claim envelope bead_id={envelope_bead!r} owner={envelope_owner!r} "
                f"does not match requested bead_id={bead_id!r} owner={owner!r}."
            ),
        )

    code = "RESUMED" if data.get("resume") else "CLAIMED"
    return _result(
        dispatch_authorized=False,
        claim_verified=False,
        code=code,
        envelope=envelope,
        bead_id=bead_id,
        owner=owner,
        summary=str(envelope.get("summary") or f"Bead {bead_id} claimed by {owner}"),
    )


def admit_claim(*, bead_id: str, owner: str) -> dict[str, Any]:
    """Run claim-bead.py and admit first claim or same-owner resume."""
    bead_id = str(bead_id or "").strip()
    owner = str(owner or "").strip()
    if not owner:
        return _result(
            dispatch_authorized=False,
            code="CLAIM_OWNER_MISSING",
            envelope=None,
            bead_id=bead_id,
            owner=owner,
            summary="Claim owner is empty; implementation dispatch is refused.",
        )
    if not bead_id:
        return _result(
            dispatch_authorized=False,
            code="CLAIM_BEAD_MISSING",
            envelope=None,
            bead_id=bead_id,
            owner=owner,
            summary="Bead id is empty; implementation dispatch is refused.",
        )

    envelope = _invoke_claim_bead_cli(bead_id=bead_id, owner=owner)
    classified = authorize_implementation_dispatch(
        envelope, bead_id=bead_id, owner=owner
    )
    if classified["code"] in ("CLAIMED", "RESUMED"):
        return _verified_admission(classified)

    if _error_code(envelope) != "ALREADY_CLAIMED":
        return classified

    _status, bead = _probe_bead(bead_id, DefaultCommandRunner())
    current_owner = _bead_owner(bead)
    if current_owner == owner:
        resume = _resume_envelope(bead_id, owner, bead)
        return _verified_admission(
            authorize_implementation_dispatch(
                resume, bead_id=bead_id, owner=owner
            )
        )

    return _result(
        dispatch_authorized=False,
        code="FOREIGN_CLAIM",
        envelope=envelope,
        bead_id=bead_id,
        owner=owner,
        summary=(
            f"Bead {bead_id} is claimed by {current_owner or 'another session'}; "
            f"owner {owner} is refused"
        ),
    )


def _invoke_claim_bead_cli(*, bead_id: str, owner: str) -> dict[str, Any] | None:
    completed = subprocess.run(
        [
            sys.executable,
            str(CLAIM_BEAD_SCRIPT),
            bead_id,
            "--json-only",
            "--session-id",
            owner,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    # Branch on the envelope. claim-bead.py exits 0 on almost every error and
    # exits 1 for BEAD_BODY_INCOMPLETE; neither code is the admission decision.
    return extract_last_json_object(completed.stdout) or extract_last_json_object(
        completed.stderr or ""
    )


def _is_claim_envelope(envelope: dict[str, Any]) -> bool:
    meta = envelope.get("meta")
    if not isinstance(meta, dict):
        return False
    return str(meta.get("producer") or "") in CLAIM_PRODUCERS


def _envelope_owner(data: dict[str, Any]) -> str:
    assignee = str(data.get("assignee") or "").strip()
    if assignee:
        return assignee
    claim = data.get("claim") if isinstance(data.get("claim"), dict) else {}
    return str(claim.get("claimed_by") or "").strip()


def _bead_owner(bead: dict[str, Any] | None) -> str:
    if not bead:
        return ""
    assignee = str(bead.get("assignee") or "").strip()
    if assignee:
        return assignee
    metadata = bead.get("metadata") if isinstance(bead.get("metadata"), dict) else {}
    claim = metadata.get("claim") if isinstance(metadata.get("claim"), dict) else {}
    return str(claim.get("claimed_by") or "").strip()


def _error_code(envelope: dict[str, Any] | None) -> str | None:
    if not isinstance(envelope, dict):
        return None
    errors = envelope.get("errors") if isinstance(envelope.get("errors"), list) else []
    for item in errors:
        if isinstance(item, dict) and item.get("code"):
            return str(item["code"])
    return None


def _resume_envelope(bead_id: str, owner: str, bead: dict[str, Any]) -> dict[str, Any]:
    metadata = bead.get("metadata") if isinstance(bead.get("metadata"), dict) else {}
    claim_meta = metadata.get("claim") if isinstance(metadata.get("claim"), dict) else {}
    claim = dict(claim_meta)
    claim.setdefault("claimed_by", owner)
    return {
        "status": "ok",
        "summary": f"Bead {bead_id} already claimed by {owner} — resuming",
        "data": {
            "bead_id": bead_id,
            "current_status": "in_progress",
            "assignee": owner,
            "claim": claim,
            "resume": True,
        },
        "errors": [],
        "next_steps": [],
        "open_items": [],
        "meta": {
            "contract_version": "1",
            "producer": "claim-bead.py",
            "schema": "core/contracts/execution-result.schema.json",
        },
    }


def _verified_admission(classified: dict[str, Any]) -> dict[str, Any]:
    """Mark live admit_claim output. Classifier results must not look like this."""
    admitted = dict(classified)
    admitted["dispatch_authorized"] = True
    admitted["claim_verified"] = True
    admitted["outcome"] = "admitted"
    return admitted


def _result(
    *,
    dispatch_authorized: bool,
    code: str,
    envelope: dict[str, Any] | None,
    bead_id: str,
    owner: str,
    summary: str,
    claim_verified: bool = False,
) -> dict[str, Any]:
    verified = bool(claim_verified) and bool(dispatch_authorized)
    return {
        "contract": CONTRACT,
        "dispatch_authorized": bool(dispatch_authorized) and verified,
        "claim_verified": verified,
        "implementation_launched": False,
        "outcome": "admitted" if verified else "refused",
        "code": code,
        "bead_id": bead_id,
        "owner": owner,
        "envelope": envelope if envelope is not None else {},
        "summary": summary,
        "claim_entrypoint": CLAIM_ENTRYPOINT,
    }


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="claim_admission.py",
        description=(
            "Admit Repository Delivery implementation after "
            f"{CLAIM_ENTRYPOINT} reports ownership."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    admit_parser = sub.add_parser(
        "admit",
        help="Run claim-bead.py and admit first claim or same-owner resume.",
    )
    admit_parser.add_argument("--bead-id", required=True)
    admit_parser.add_argument("--owner", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = admit_claim(bead_id=args.bead_id, owner=args.owner)
    print(json.dumps(result))
    return 0 if result["dispatch_authorized"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
