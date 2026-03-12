"""
Learner Agent: The conversational AI that acts as a curious student.
"""

from typing import List, Dict, Tuple
from anthropic import Anthropic

from .knowledge_graph import KnowledgeGraph
from .prompts import get_learner_system_prompt


class LearnerAgent:
    """The agent that learns from the student."""

    def __init__(self, client: Anthropic, topic_name: str, language: str = "en"):
        self.client = client
        self.topic_name = topic_name
        self.language = language
        self.model = "claude-sonnet-4-20250514"
        self.conversation_history: List[Dict[str, str]] = []
        self.turn_count = 0

    def get_system_prompt(self, knowledge_graph: KnowledgeGraph) -> str:
        """Generate the system prompt with current context."""
        concept_list = knowledge_graph.get_concepts_list()

        return get_learner_system_prompt(
            topic_name=self.topic_name,
            turn_count=self.turn_count,
            concept_list=concept_list,
            language=self.language
        )

    def generate_response(self, student_message: str, knowledge_graph: KnowledgeGraph) -> Tuple[str, int, int]:
        """
        Generate the learner agent's response to the student's message.

        Args:
            student_message: What the student said
            knowledge_graph: Current state of knowledge (for context)

        Returns:
            Tuple of (agent_response, input_tokens, output_tokens)
        """
        # Add student message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": student_message
        })

        # Generate system prompt with current context
        system_prompt = self.get_system_prompt(knowledge_graph)

        try:
            # Call Claude Sonnet
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.7,  # Some creativity for natural conversation
                system=system_prompt,
                messages=self.conversation_history
            )

            agent_response = response.content[0].text

            # Extract token usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            # Add agent response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": agent_response
            })

            self.turn_count += 1

            return agent_response, input_tokens, output_tokens

        except Exception as e:
            print(f"[ERROR] Failed to generate learner response: {e}")
            return "Lo siento, tuve un problema. ¿Puedes repetir eso? / Sorry, I had a problem. Can you repeat that?", 0, 0

    def get_initial_greeting(self) -> str:
        """Get the initial greeting from the agent."""
        # Use static greetings to ensure consistent language
        # LLM-generated greetings can be unpredictable with language mixing
        if self.language == "es":
            greeting = f"¡Hola! Estoy muy emocionado de aprender sobre {self.topic_name}. Tengo que admitir que no sé absolutamente nada del tema, así que empiezo completamente en blanco. ¡Estoy listo y ansioso por absorber todo lo que puedas enseñarme!"
        else:
            greeting = f"Hello! I'm absolutely thrilled to meet you and learn about {self.topic_name}! I have to admit, I know practically nothing about this topic, so I'm starting completely fresh. I'm so ready and eager to soak up everything you can teach me - please share away!"

        # Add greeting to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": greeting
        })

        return greeting

    def reset(self):
        """Reset the conversation history."""
        self.conversation_history = []
        self.turn_count = 0
