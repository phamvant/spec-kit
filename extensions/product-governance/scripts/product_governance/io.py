"""Safe artifact loading, schema validation, and atomic writes."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from . import SUPPORTED_SCHEMA_VERSION
from .errors import InfrastructureError, SchemaError


def discover_project_root(start: Path | str | None = None) -> Path:
    current = Path(start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".specify").exists() or (candidate / ".git").exists():
            return candidate
    return current


def safe_path(root: Path, value: Path | str, *, must_exist: bool = False) -> Path:
    root = root.resolve()
    path = Path(value)
    resolved = (root / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise InfrastructureError(f"Path escapes project root: {value}") from exc
    if must_exist and not resolved.exists():
        raise InfrastructureError(f"Path does not exist: {resolved}")
    return resolved


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SchemaError(f"Unable to parse YAML: {path}", details={"error": str(exc)}) from exc
    if not isinstance(value, dict):
        raise SchemaError(f"Expected a YAML object: {path}")
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaError(f"Unable to parse JSON: {path}", details={"error": str(exc)}) from exc
    if not isinstance(value, dict):
        raise SchemaError(f"Expected a JSON object: {path}")
    return value


def guard_schema_version(value: dict[str, Any], path: Path | None = None) -> None:
    version = value.get("schema_version")
    if version != SUPPORTED_SCHEMA_VERSION:
        location = f" in {path}" if path else ""
        raise SchemaError(
            f"Unsupported schema_version{location}: {version!r}; expected {SUPPORTED_SCHEMA_VERSION!r}"
        )


def validate_schema(value: dict[str, Any], schema_path: Path, *, artifact_path: Path | None = None) -> None:
    guard_schema_version(value, artifact_path)
    schema = load_json(schema_path)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: list(item.path))
    if errors:
        details = [
            {"path": ".".join(str(p) for p in error.path), "message": error.message}
            for error in errors
        ]
        raise SchemaError(f"Schema validation failed: {artifact_path or schema_path}", details={"errors": details})


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise InfrastructureError(f"Atomic write failed: {path}", details={"error": str(exc)}) from exc


def atomic_write_json(path: Path, value: Any) -> None:
    _atomic_write(path, json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def atomic_write_yaml(path: Path, value: Any) -> None:
    _atomic_write(path, yaml.safe_dump(value, sort_keys=False, allow_unicode=True))

