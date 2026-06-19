"""Relationship graph validation and deterministic normalization."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .errors import DomainError
from .models import Relationship, RelationshipType


def build_graph(requirement_ids: Iterable[str], relationships: Iterable[Relationship]) -> list[Relationship]:
    known = set(requirement_ids)
    normalized: dict[tuple[str, str, str], Relationship] = {}
    for edge in relationships:
        if edge.source not in known or edge.target not in known:
            raise DomainError(f"Unknown relationship endpoint: {edge.source} -> {edge.target}")
        if edge.source == edge.target:
            raise DomainError(f"Self relationship is not allowed: {edge.source}")
        source, target = edge.source, edge.target
        if edge.type is RelationshipType.CONFLICTS_WITH and target < source:
            source, target = target, source
        key = (source, edge.type.value, target)
        if key in normalized:
            raise DomainError(f"Duplicate relationship: {key}")
        normalized[key] = Relationship(source, edge.type, target)
    edges = sorted(normalized.values(), key=lambda item: (item.source, item.type.value, item.target))
    for edge_type in (RelationshipType.PARENT_OF, RelationshipType.DEPENDS_ON):
        _assert_acyclic(edges, edge_type)
    for edge in edges:
        if edge.type is RelationshipType.SUPERSEDES:
            reverse = (edge.target, edge.type.value, edge.source)
            if reverse in normalized:
                raise DomainError(f"Mutual supersedes relationship: {edge.source}, {edge.target}")
    return edges


def _assert_acyclic(edges: list[Relationship], edge_type: RelationshipType) -> None:
    adjacency: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        if edge.type is edge_type:
            adjacency[edge.source].append(edge.target)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise DomainError(f"{edge_type.value} cycle includes {node}")
        if node in visited:
            return
        visiting.add(node)
        for target in sorted(adjacency[node]):
            visit(target)
        visiting.remove(node)
        visited.add(node)

    for node in sorted(adjacency):
        visit(node)

