"""Stable errors and exit codes for Agile governance."""

from __future__ import annotations


class GovernanceError(Exception):
    code = "governance_error"
    exit_code = 1

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def as_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "details": self.details}


class SchemaError(GovernanceError):
    code = "schema_error"


class DomainError(GovernanceError):
    code = "domain_error"


class InvocationError(GovernanceError):
    code = "invalid_invocation"
    exit_code = 2


class InfrastructureError(GovernanceError):
    code = "infrastructure_error"
    exit_code = 2

