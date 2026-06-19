"""Append-only, locked product change ledger."""

from __future__ import annotations

import hashlib
import json
import os
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from .errors import DomainError, InfrastructureError


def idempotency_key(feature: str, requirements: list[str], commit: str, event_type: str) -> str:
    payload = json.dumps(
        {"event_type": event_type, "feature": feature, "requirements": sorted(requirements), "commit": commit},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_ledger(path: Path) -> list[dict]:
    if not path.exists():
        return []
    events: list[dict] = []
    previous = 0
    seen_ids: set[str] = set()
    seen_keys: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            raise DomainError(f"Blank ledger line at {line_number}")
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DomainError(f"Malformed ledger line {line_number}: {exc.msg}") from exc
        event_id = event.get("event_id", "")
        try:
            number = int(event_id.removeprefix("CHG-"))
        except ValueError as exc:
            raise DomainError(f"Invalid ledger event ID: {event_id}") from exc
        if number <= previous:
            raise DomainError(f"Non-monotonic ledger event ID: {event_id}")
        if event_id in seen_ids or event.get("idempotency_key") in seen_keys:
            raise DomainError(f"Duplicate ledger event: {event_id}")
        if event.get("corrects_event") and event["corrects_event"] not in seen_ids:
            raise DomainError(f"Correction references unknown prior event: {event['corrects_event']}")
        previous = number
        seen_ids.add(event_id)
        seen_keys.add(event.get("idempotency_key"))
        events.append(event)
    return events


@contextmanager
def _locked(handle, timeout: float = 5.0) -> Iterator[None]:
    started = time.monotonic()
    if os.name == "nt":
        import msvcrt
        while True:
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError as exc:
                if time.monotonic() - started >= timeout:
                    raise InfrastructureError("Timed out acquiring ledger lock") from exc
                time.sleep(0.05)
        try:
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError as exc:
                if time.monotonic() - started >= timeout:
                    raise InfrastructureError("Timed out acquiring ledger lock") from exc
                time.sleep(0.05)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def append_event(
    path: Path,
    *,
    feature: str,
    requirements: list[str],
    commit: str,
    evidence: list[str],
    event_type: str = "feature_verified",
    corrects_event: str | None = None,
    actor: str = "product-governance",
) -> tuple[dict, bool]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    with path.open("r+", encoding="utf-8", newline="\n") as handle, _locked(handle):
        events = read_ledger(path)
        key = idempotency_key(feature, requirements, commit, event_type)
        existing = next((event for event in events if event.get("idempotency_key") == key), None)
        if existing:
            return existing, False
        if corrects_event and corrects_event not in {event["event_id"] for event in events}:
            raise DomainError(f"Correction references unknown event: {corrects_event}")
        event = {
            "schema_version": "1.0",
            "event_id": f"CHG-{len(events) + 1:06d}",
            "occurred_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "event_type": event_type,
            "feature": feature,
            "requirements": sorted(set(requirements)),
            "commit": commit,
            "evidence": sorted(set(evidence)),
            "actor": actor,
            "idempotency_key": key,
        }
        if corrects_event:
            event["corrects_event"] = corrects_event
        handle.seek(0, os.SEEK_END)
        handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
        read_ledger(path)
        return event, True


def render_changelog(events: list[dict]) -> str:
    lines = ["# Product Change Log", ""]
    for event in events:
        lines.extend([
            f"## {event['event_id']} — {event['feature']}",
            f"- Type: {event['event_type']}",
            f"- Commit: {event['commit']}",
            f"- Requirements: {', '.join(event['requirements']) or 'none'}",
            f"- Occurred: {event['occurred_at']}",
            "",
        ])
    return "\n".join(lines)

