"""Typed models for product-governance artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class RequirementType(StrEnum):
    GOAL = "goal"
    CAPABILITY = "capability"
    FUNCTIONAL = "functional"
    QUALITY = "quality"
    CONSTRAINT = "constraint"


class RequirementStatus(StrEnum):
    PROPOSED = "proposed"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    IMPLEMENTING = "implementing"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class Priority(StrEnum):
    MUST = "must"
    SHOULD = "should"
    COULD = "could"
    WONT = "wont"


class RelationshipType(StrEnum):
    PARENT_OF = "parent_of"
    DEPENDS_ON = "depends_on"
    CONFLICTS_WITH = "conflicts_with"
    SUPERSEDES = "supersedes"


@dataclass(slots=True)
class VerificationPolicy:
    method: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "VerificationPolicy":
        return cls(method=str(value["method"]).strip())


@dataclass(slots=True)
class Requirement:
    id: str
    title: str
    description: str
    type: RequirementType
    capability: str
    status: RequirementStatus
    priority: Priority
    owner: str
    source: str
    verification: VerificationPolicy
    depends_on: list[str] = field(default_factory=list)
    supersedes: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Requirement":
        return cls(
            id=str(value["id"]),
            title=str(value["title"]).strip(),
            description=str(value["description"]).strip(),
            type=RequirementType(value["type"]),
            capability=str(value["capability"]).strip(),
            status=RequirementStatus(value["status"]),
            priority=Priority(value["priority"]),
            owner=str(value["owner"]).strip(),
            source=str(value["source"]).strip(),
            verification=VerificationPolicy.from_dict(value["verification"]),
            depends_on=sorted(set(value.get("depends_on", []))),
            supersedes=sorted(set(value.get("supersedes", []))),
            tags=sorted(set(value.get("tags", []))),
        )

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["type"] = self.type.value
        value["status"] = self.status.value
        value["priority"] = self.priority.value
        return value


@dataclass(slots=True, frozen=True)
class Relationship:
    source: str
    type: RelationshipType
    target: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Relationship":
        return cls(str(value["from"]), RelationshipType(value["type"]), str(value["to"]))

    def to_dict(self) -> dict[str, str]:
        return {"from": self.source, "type": self.type.value, "to": self.target}


@dataclass(slots=True)
class FeatureTrace:
    feature: str
    implements: list[str] = field(default_factory=list)
    refines: list[str] = field(default_factory=list)
    impacts: list[str] = field(default_factory=list)
    unaffected: list[str] = field(default_factory=list)
    trace_digest: str | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "FeatureTrace":
        return cls(
            feature=str(value["feature"]),
            implements=sorted(set(value.get("implements", []))),
            refines=sorted(set(value.get("refines", []))),
            impacts=sorted(set(value.get("impacts", []))),
            unaffected=sorted(set(value.get("unaffected", []))),
            trace_digest=value.get("trace_digest"),
        )

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema_version": "1.0",
            "feature": self.feature,
            "implements": self.implements,
            "refines": self.refines,
            "impacts": self.impacts,
            "unaffected": self.unaffected,
        }
        if self.trace_digest:
            value["trace_digest"] = self.trace_digest
        return value

