"""
Learner Agent: The conversational AI that acts as a curious student.
"""

from typing import List, Dict
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

    def generate_response(self, student_message: str, knowledge_graph: KnowledgeGraph) -> str:
        """
        Generate the learner agent's response to the student's message.

        Args:
            student_message: What the student said
            knowledge_graph: Current state of knowledge (for context)

        Returns:
            The agent's response
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

            # Add agent response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": agent_response
            })

            self.turn_count += 1

            return agent_response

        except Exception as e:
            print(f"[ERROR] Failed to generate learner response: {e}")
            return "Lo siento, tuve un problema. ¿Puedes repetir eso? / Sorry, I had a problem. Can you repeat that?"

    def get_initial_greeting(self) -> str:
        """Get the initial greeting from the agent."""
        if self.language == "es":
            initial_prompt = f"""Estás conociendo a un estudiante que te va a enseñar sobre {self.topic_name}.
Preséntate con entusiasmo en ESPAÑOL. Dile:
1. Que estás emocionado de aprender de él/ella
2. Que no sabes absolutamente nada sobre {self.topic_name}
3. Que estás listo para que te enseñe

Mantén la respuesta CORTA (2-3 oraciones). Sé cálido y alentador.
IMPORTANTE: Responde 100% en español, sin palabras en inglés."""
        else:
            initial_prompt = f"""You are meeting a student who will teach you about {self.topic_name}.
Introduce yourself enthusiastically in ENGLISH. Tell them:
1. You're excited to learn from them
2. You know absolutely nothing about {self.topic_name}
3. You're ready for them to teach you

Keep it SHORT (2-3 sentences). Be warm and encouraging.
IMPORTANT: Respond 100% in English, no Spanish words."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=256,
                temperature=0.8,
                messages=[
                    {"role": "user", "content": initial_prompt}
                ]
            )

            greeting = response.content[0].text

            # Add greeting to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": greeting
            })

            return greeting

        except Exception as e:
            print(f"[ERROR] Failed to generate greeting: {e}")
            # Fallback greeting based on language
            if self.language == "es":
                return f"¡Hola! Soy tu estudiante y estoy listo para aprender. Me dijeron que tú sabes mucho sobre {self.topic_name}. ¿Me puedes enseñar? ¡No sé nada del tema!"
            else:
                return f"Hi! I'm your student and I'm ready to learn. I heard you know a lot about {self.topic_name}. Can you teach me? I don't know anything about it!"

    def reset(self):
        """Reset the conversation history."""
        self.conversation_history = []
        self.turn_count = 0
