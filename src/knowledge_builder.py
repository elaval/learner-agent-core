"""
Knowledge Builder: Extracts concepts, relationships, and evidence from student messages.
"""

import json
from typing import Dict, Any
from anthropic import Anthropic

from .knowledge_graph import KnowledgeGraph
from .prompts import get_knowledge_extraction_prompt


class KnowledgeBuilder:
    """Extracts structured knowledge from student messages using Claude Haiku."""

    def __init__(self, client: Anthropic, topic_name: str):
        self.client = client
        self.topic_name = topic_name
        self.model = "claude-haiku-4-5-20251001"

    def extract_from_message(self, student_message: str, knowledge_graph: KnowledgeGraph) -> Dict[str, Any]:
        """
        Extract concepts, relationships, and evidence from a student message.

        Returns:
            Dict with keys: new_concepts, updated_concepts, new_relationships, evidence
        """
        # Build the extraction prompt
        current_graph_json = knowledge_graph.to_json(indent=None) if not knowledge_graph.is_empty() else "{}"

        prompt = get_knowledge_extraction_prompt(
            topic_name=self.topic_name,
            student_message=student_message,
            current_graph_json=current_graph_json
        )

        try:
            # Call Claude Haiku for extraction
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.0,  # We want deterministic extraction
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse the JSON response
            response_text = response.content[0].text.strip()

            # Sometimes the model wraps JSON in markdown code blocks
            if response_text.startswith("```"):
                # Extract JSON from code block
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])  # Remove first and last lines

            extraction = json.loads(response_text)

            # Validate structure
            required_keys = ["new_concepts", "updated_concepts", "new_relationships", "evidence"]
            for key in required_keys:
                if key not in extraction:
                    extraction[key] = []

            return extraction

        except json.JSONDecodeError as e:
            print(f"[WARNING] Failed to parse extraction JSON: {e}")
            print(f"Response was: {response_text[:200]}...")
            return {
                "new_concepts": [],
                "updated_concepts": [],
                "new_relationships": [],
                "evidence": []
            }
        except Exception as e:
            print(f"[ERROR] Extraction failed: {e}")
            return {
                "new_concepts": [],
                "updated_concepts": [],
                "new_relationships": [],
                "evidence": []
            }

    def update_knowledge_graph(self, extraction: Dict[str, Any], knowledge_graph: KnowledgeGraph) -> None:
        """
        Update the knowledge graph with extracted information.
        """
        # Add new concepts
        for concept in extraction.get("new_concepts", []):
            if not knowledge_graph.has_concept(concept["name"]):
                knowledge_graph.add_concept(
                    name=concept["name"],
                    definition=concept["definition"],
                    category=concept["category"],
                    confidence=concept["confidence"]
                )

        # Update existing concepts
        for concept in extraction.get("updated_concepts", []):
            knowledge_graph.update_concept(
                name=concept["name"],
                definition=concept["definition"],
                confidence=concept["confidence"]
            )

        # Add relationships
        for rel in extraction.get("new_relationships", []):
            knowledge_graph.add_relationship(
                source=rel["source"],
                target=rel["target"],
                rel_type=rel["type"],
                label=rel["label"],
                confidence=rel["confidence"]
            )

        # Add evidence
        for ev in extraction.get("evidence", []):
            knowledge_graph.add_evidence(
                concept=ev["concept"],
                quote=ev["quote"],
                evidence_type=ev["type"]
            )

    def process_student_message(self, student_message: str, knowledge_graph: KnowledgeGraph) -> Dict[str, Any]:
        """
        Process a student message: extract knowledge and update the graph.

        Returns:
            The extraction dict (for debugging/logging)
        """
        extraction = self.extract_from_message(student_message, knowledge_graph)
        self.update_knowledge_graph(extraction, knowledge_graph)
        return extraction
