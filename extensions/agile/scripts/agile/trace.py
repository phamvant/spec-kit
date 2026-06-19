"""Structured Product Traceability Markdown and sidecar synchronization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .errors import DomainError
from .io import atomic_write_json, safe_path
from .models import FeatureTrace

START = "<!-- PRODUCT TRACEABILITY START -->"
END = "<!-- PRODUCT TRACEABILITY END -->"
FIELDS = ("implements", "refines", "impacts", "unaffected")


def render_section(trace: FeatureTrace) -> str:
    lines = ["## Product Traceability", START]
    for field in FIELDS:
        values = getattr(trace, field)
        lines.append(f"- {field}: {', '.join(values) if values else 'none'}")
    lines.append(END)
    return "\n".join(lines)


def section_digest(section: str) -> str:
    return hashlib.sha256(section.strip().encode("utf-8")).hexdigest()


def parse_section(markdown: str, feature: str) -> tuple[FeatureTrace, str]:
    if markdown.count(START) != 1 or markdown.count(END) != 1:
        raise DomainError("spec.md must contain exactly one Product Traceability section")
    start = markdown.index(START)
    end = markdown.index(END, start) + len(END)
    section_start = markdown.rfind("## Product Traceability", 0, start)
    if section_start < 0:
        raise DomainError("Product Traceability heading is missing")
    section = markdown[section_start:end]
    values: dict[str, list[str]] = {}
    for field in FIELDS:
        prefix = f"- {field}:"
        matches = [line for line in section.splitlines() if line.startswith(prefix)]
        if len(matches) != 1:
            raise DomainError(f"Malformed Product Traceability field: {field}")
        raw = matches[0][len(prefix):].strip()
        values[field] = [] if raw == "none" else sorted({part.strip() for part in raw.split(",") if part.strip()})
    return FeatureTrace(feature=feature, **values), section


def write_trace(project_root: Path, feature_dir: Path, trace: FeatureTrace) -> list[Path]:
    feature_dir = safe_path(project_root, feature_dir)
    spec_path = safe_path(project_root, feature_dir / "spec.md")
    sidecar_path = safe_path(project_root, feature_dir / "feature-trace.json")
    current = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""
    section = render_section(trace)
    if START in current and END in current:
        parsed, old_section = parse_section(current, trace.feature)
        del parsed
        updated = current.replace(old_section, section)
    else:
        updated = current.rstrip() + ("\n\n" if current.strip() else "") + section + "\n"
    trace.trace_digest = section_digest(section)
    from .io import _atomic_write
    _atomic_write(spec_path, updated)
    atomic_write_json(sidecar_path, trace.to_dict())
    return [spec_path, sidecar_path]


def validate_trace_pair(project_root: Path, feature_dir: Path) -> FeatureTrace:
    feature_dir = safe_path(project_root, feature_dir, must_exist=True)
    spec_path = safe_path(project_root, feature_dir / "spec.md", must_exist=True)
    sidecar_path = safe_path(project_root, feature_dir / "feature-trace.json", must_exist=True)
    from .io import load_json
    sidecar = FeatureTrace.from_dict(load_json(sidecar_path))
    parsed, section = parse_section(spec_path.read_text(encoding="utf-8"), sidecar.feature)
    for field in FIELDS:
        if getattr(parsed, field) != getattr(sidecar, field):
            raise DomainError(f"Product Traceability drift in {field}: {feature_dir.name}")
    if sidecar.trace_digest != section_digest(section):
        raise DomainError(f"Product Traceability digest mismatch: {feature_dir.name}")
    return sidecar

