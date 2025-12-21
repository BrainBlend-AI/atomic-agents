"""RAG Context Provider example for document-based Q&A."""

from typing import List, Optional
from dataclasses import dataclass

from atomic_agents.lib.components.system_prompt_generator import BaseDynamicContextProvider


@dataclass
class Document:
    """A retrieved document chunk."""

    content: str
    source: str
    score: float
    metadata: Optional[dict] = None


class RAGContextProvider(BaseDynamicContextProvider):
    """
    Context provider for Retrieval-Augmented Generation.

    Provides retrieved document chunks to the agent's system prompt,
    enabling it to answer questions based on specific documents.

    Usage:
        provider = RAGContextProvider()
        agent.register_context_provider("documents", provider)

        # Before each query, set relevant documents
        documents = vector_db.search(query, top_k=5)
        provider.set_documents(documents)

        # Run agent - it now has document context
        response = agent.run(query_input)
    """

    def __init__(self, max_documents: int = 5, include_scores: bool = False):
        """
        Initialize the RAG context provider.

        Args:
            max_documents: Maximum documents to include in context
            include_scores: Whether to show relevance scores
        """
        super().__init__(title="Retrieved Documents")
        self.documents: List[Document] = []
        self.max_documents = max_documents
        self.include_scores = include_scores

    def set_documents(self, documents: List[Document]) -> None:
        """
        Set the documents to include in context.

        Args:
            documents: List of retrieved documents, sorted by relevance
        """
        self.documents = documents[:self.max_documents]

    def clear(self) -> None:
        """Clear all documents from context."""
        self.documents = []

    def get_info(self) -> str:
        """
        Format documents for inclusion in system prompt.

        Returns:
            Formatted string with document contents and sources
        """
        if not self.documents:
            return "No relevant documents found. Answer based on general knowledge only."

        sections = []
        for i, doc in enumerate(self.documents, 1):
            header = f"Document {i}"
            if self.include_scores:
                header += f" (relevance: {doc.score:.2f})"

            section = f"### {header}\n"
            section += f"Source: {doc.source}\n"
            section += f"Content:\n{doc.content}"

            sections.append(section)

        return "\n\n".join(sections)


class SessionContextProvider(BaseDynamicContextProvider):
    """
    Context provider for session-specific information.

    Tracks user preferences, conversation context, and other
    session-specific data that should inform agent responses.
    """

    def __init__(self):
        super().__init__(title="Session Context")
        self._data: dict = {}

    def set(self, key: str, value: str) -> None:
        """Set a session value."""
        self._data[key] = value

    def get(self, key: str, default: str = "") -> str:
        """Get a session value."""
        return self._data.get(key, default)

    def update(self, data: dict) -> None:
        """Update multiple session values."""
        self._data.update(data)

    def clear(self) -> None:
        """Clear all session data."""
        self._data = {}

    def get_info(self) -> str:
        if not self._data:
            return "No session context available."

        lines = [f"- {key}: {value}" for key, value in self._data.items()]
        return "Current session information:\n" + "\n".join(lines)


# ============================================================
# Example Usage
# ============================================================

if __name__ == "__main__":
    import os
    import instructor
    import openai
    from dotenv import load_dotenv

    from atomic_agents.agents.base_agent import AtomicAgent, AgentConfig
    from atomic_agents.lib.base.base_io_schema import BaseIOSchema
    from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
    from atomic_agents.lib.components.chat_history import ChatHistory
    from pydantic import Field

    load_dotenv()

    # Define schemas
    class QuestionInput(BaseIOSchema):
        question: str = Field(..., description="Question to answer from documents")

    class AnswerOutput(BaseIOSchema):
        answer: str = Field(..., description="Answer based on documents")
        sources_used: List[str] = Field(default_factory=list, description="Document sources cited")

    # Create agent
    client = instructor.from_openai(openai.OpenAI())

    config = AgentConfig(
        client=client,
        model="gpt-4o-mini",
        history=ChatHistory(),
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are a helpful assistant that answers questions based on provided documents.",
                "Only use information from the documents to answer.",
                "If the documents don't contain the answer, say so clearly.",
            ],
            steps=[
                "1. Read the provided documents carefully.",
                "2. Find information relevant to the question.",
                "3. Synthesize an answer from the documents.",
                "4. List which document sources you used.",
            ],
            output_instructions=[
                "Base your answer only on the provided documents.",
                "Cite the sources you used.",
                "If no relevant information exists, acknowledge it.",
            ],
        ),
    )

    agent = AtomicAgent[QuestionInput, AnswerOutput](config=config)

    # Create and register context provider
    rag_provider = RAGContextProvider(max_documents=3, include_scores=True)
    agent.register_context_provider("rag", rag_provider)

    # Simulate retrieved documents
    sample_docs = [
        Document(
            content="The Atomic Agents framework uses Pydantic for schema validation. All input and output schemas should inherit from BaseIOSchema.",
            source="atomic-agents-docs/schemas.md",
            score=0.95
        ),
        Document(
            content="AtomicAgent is the core class for LLM interactions. It handles structured input/output, conversation history, and system prompt management.",
            source="atomic-agents-docs/agents.md",
            score=0.89
        ),
        Document(
            content="Context providers dynamically inject information into system prompts at runtime.",
            source="atomic-agents-docs/context.md",
            score=0.82
        ),
    ]

    # Set documents before running
    rag_provider.set_documents(sample_docs)

    # Run agent
    response = agent.run(QuestionInput(
        question="How do I define schemas in Atomic Agents?"
    ))

    print(f"Answer: {response.answer}")
    print(f"Sources: {response.sources_used}")
