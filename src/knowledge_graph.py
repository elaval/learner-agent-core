"""
In-memory knowledge graph for storing concepts, relationships, and evidence.
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class Concept:
    """A concept extracted from student teaching."""
    name: str
    definition: str
    category: str  # "entity", "process", "property", etc.
    confidence: float
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    definition_history: List[str] = field(default_factory=list)

    def update_definition(self, new_definition: str, new_confidence: float):
        """Update the definition and track history."""
        self.definition_history.append(self.definition)
        self.definition = new_definition
        self.confidence = new_confidence
        self.updated_at = datetime.now().isoformat()


@dataclass
class Relationship:
    """A relationship between two concepts."""
    source: str
    target: str
    type: str  # "functional", "spatial", "hierarchical", "causal"
    label: str
    confidence: float
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Evidence:
    """A quote from the student linked to a concept."""
    concept: str
    quote: str
    type: str  # "definition", "example", "explanation", "correction"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class KnowledgeGraph:
    """In-memory knowledge graph."""

    def __init__(self):
        self.concepts: Dict[str, Concept] = {}
        self.relationships: List[Relationship] = []
        self.evidence: List[Evidence] = []

    def add_concept(self, name: str, definition: str, category: str, confidence: float) -> Concept:
        """Add a new concept to the graph."""
        concept = Concept(
            name=name,
            definition=definition,
            category=category,
            confidence=confidence
        )
        self.concepts[name.lower()] = concept
        return concept

    def update_concept(self, name: str, definition: str, confidence: float) -> Optional[Concept]:
        """Update an existing concept's definition."""
        key = name.lower()
        if key in self.concepts:
            self.concepts[key].update_definition(definition, confidence)
            return self.concepts[key]
        return None

    def get_concept(self, name: str) -> Optional[Concept]:
        """Get a concept by name (case-insensitive)."""
        return self.concepts.get(name.lower())

    def has_concept(self, name: str) -> bool:
        """Check if a concept exists."""
        return name.lower() in self.concepts

    def add_relationship(self, source: str, target: str, rel_type: str, label: str, confidence: float) -> Relationship:
        """Add a relationship between two concepts."""
        relationship = Relationship(
            source=source,
            target=target,
            type=rel_type,
            label=label,
            confidence=confidence
        )
        self.relationships.append(relationship)
        return relationship

    def add_evidence(self, concept: str, quote: str, evidence_type: str) -> Evidence:
        """Add evidence (student quote) linked to a concept."""
        ev = Evidence(
            concept=concept,
            quote=quote,
            type=evidence_type
        )
        self.evidence.append(ev)
        return ev

    def get_concepts_list(self) -> List[str]:
        """Get a list of all concept names."""
        return list(self.concepts.keys())

    def get_relationships_for_concept(self, concept_name: str) -> List[Relationship]:
        """Get all relationships involving a concept (as source or target)."""
        name_lower = concept_name.lower()
        return [
            r for r in self.relationships
            if r.source.lower() == name_lower or r.target.lower() == name_lower
        ]

    def get_evidence_for_concept(self, concept_name: str) -> List[Evidence]:
        """Get all evidence for a specific concept."""
        name_lower = concept_name.lower()
        return [e for e in self.evidence if e.concept.lower() == name_lower]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the graph to a dictionary."""
        return {
            "concepts": {name: asdict(concept) for name, concept in self.concepts.items()},
            "relationships": [asdict(r) for r in self.relationships],
            "evidence": [asdict(e) for e in self.evidence]
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert the graph to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the graph."""
        return {
            "concepts": len(self.concepts),
            "relationships": len(self.relationships),
            "evidence": len(self.evidence)
        }

    def is_empty(self) -> bool:
        """Check if the graph has no content."""
        return len(self.concepts) == 0 and len(self.relationships) == 0
