import os
from typing import List
import wget
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn

from rag_chatbot.agents.query_agent import query_agent, RAGQueryAgentInputSchema, RAGQueryAgentOutputSchema
from rag_chatbot.agents.qa_agent import qa_agent, RAGQuestionAnsweringAgentInputSchema, RAGQuestionAnsweringAgentOutputSchema
from rag_chatbot.context_providers import RAGContextProvider, ChunkItem
from rag_chatbot.services.chroma_db import ChromaDBService
from rag_chatbot.config import CHUNK_SIZE, CHUNK_OVERLAP, NUM_CHUNKS_TO_RETRIEVE, CHROMA_PERSIST_DIR


console = Console()

WELCOME_MESSAGE = """
Welcome to the RAG Chatbot! I can help you find information from the State of the Union address.
Ask me any questions about the speech and I'll use my knowledge base to provide accurate answers.

I'll show you my thought process:
1. First, I'll generate a semantic search query from your question
2. Then, I'll retrieve relevant chunks of text from the speech
3. Finally, I'll analyze these chunks to provide you with an answer
"""

STARTER_QUESTIONS = [
    "What were the main points about the economy?",
    "What did the president say about healthcare?",
    "How did he address foreign policy?",
]


def download_document() -> str:
    """Download the sample document if it doesn't exist."""
    url = "https://raw.githubusercontent.com/IBM/watson-machine-learning-samples/master/cloud/data/foundation_models/state_of_the_union.txt"
    output_path = "downloads/state_of_the_union.txt"

    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    if not os.path.exists(output_path):
        console.print("\n[bold yellow]📥 Downloading sample document...[/bold yellow]")
        wget.download(url, output_path)
        console.print("\n[bold green]✓ Download complete![/bold green]")

    return output_path


def chunk_document(file_path: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split the document into chunks with overlap."""
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()

    # Split into paragraphs first
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    current_size = 0

    for i, paragraph in enumerate(paragraphs):
        if current_size + len(paragraph) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # Include some overlap from the previous chunk
            if overlap > 0 and chunks:
                last_chunk = chunks[-1]
                overlap_text = " ".join(last_chunk.split()[-overlap:])
                current_chunk = overlap_text + "\n\n" + paragraph
            else:
                current_chunk = paragraph
            current_size = len(current_chunk)
        else:
            current_chunk += "\n\n" + paragraph if current_chunk else paragraph
            current_size += len(paragraph)

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def initialize_system() -> tuple[ChromaDBService, RAGContextProvider]:
    """Initialize the RAG system components."""
    console.print("\n[bold magenta]🚀 Initializing RAG Chatbot System...[/bold magenta]")

    try:
        # Download and chunk document
        doc_path = download_document()
        chunks = chunk_document(doc_path)
        console.print(f"[dim]• Created {len(chunks)} document chunks[/dim]")

        # Initialize ChromaDB
        console.print("[dim]• Initializing vector database...[/dim]")
        chroma_db = ChromaDBService(
            collection_name="state_of_union", persist_directory=CHROMA_PERSIST_DIR, recreate_collection=True
        )

        # Add chunks to ChromaDB
        console.print("[dim]• Adding document chunks to vector database...[/dim]")
        chunk_ids = chroma_db.add_documents(
            documents=chunks, metadatas=[{"source": "state_of_union", "chunk_index": i} for i in range(len(chunks))]
        )
        console.print(f"[dim]• Added {len(chunk_ids)} chunks to vector database[/dim]")

        # Initialize context provider
        console.print("[dim]• Creating context provider...[/dim]")
        rag_context = RAGContextProvider("RAG Context")

        # Register context provider with agents
        console.print("[dim]• Registering context provider with agents...[/dim]")
        query_agent.register_context_provider("rag_context", rag_context)
        qa_agent.register_context_provider("rag_context", rag_context)

        console.print("[bold green]✨ System initialized successfully![/bold green]\n")
        return chroma_db, rag_context

    except Exception as e:
        console.print(f"\n[bold red]Error during initialization:[/bold red] {str(e)}")
        raise


def display_welcome() -> None:
    """Display welcome message and starter questions."""
    welcome_panel = Panel(WELCOME_MESSAGE, title="[bold blue]RAG Chatbot[/bold blue]", border_style="blue", padding=(1, 2))
    console.print("\n")
    console.print(welcome_panel)

    table = Table(
        show_header=True, header_style="bold cyan", box=box.ROUNDED, title="[bold]Example Questions to Get Started[/bold]"
    )
    table.add_column("№", style="dim", width=4)
    table.add_column("Question", style="green")

    for i, question in enumerate(STARTER_QUESTIONS, 1):
        table.add_row(str(i), question)

    console.print("\n")
    console.print(table)
    console.print("\n" + "─" * 80 + "\n")


def display_chunks(chunks: List[ChunkItem]) -> None:
    """Display the retrieved chunks in a formatted way."""
    console.print("\n[bold cyan]📚 Retrieved Text Chunks:[/bold cyan]")

    for i, chunk in enumerate(chunks, 1):
        chunk_panel = Panel(
            Markdown(chunk.content),
            title=f"[bold]Chunk {i} (Distance: {chunk.metadata['distance']:.4f})[/bold]",
            border_style="blue",
            padding=(1, 2),
        )
        console.print(chunk_panel)
        console.print()


def display_query_info(query_output: RAGQueryAgentOutputSchema) -> None:
    """Display information about the generated query."""
    query_panel = Panel(
        f"[yellow]Generated Query:[/yellow] {query_output.query}\n\n" f"[yellow]Reasoning:[/yellow] {query_output.reasoning}",
        title="[bold]🔍 Semantic Search Strategy[/bold]",
        border_style="yellow",
        padding=(1, 2),
    )
    console.print("\n")
    console.print(query_panel)


def display_answer(qa_output: RAGQuestionAnsweringAgentOutputSchema) -> None:
    """Display the reasoning and answer from the QA agent."""
    # Display reasoning
    reasoning_panel = Panel(
        Markdown(qa_output.reasoning),
        title="[bold]🤔 Analysis & Reasoning[/bold]",
        border_style="green",
        padding=(1, 2),
    )
    console.print("\n")
    console.print(reasoning_panel)

    # Display answer
    answer_panel = Panel(
        Markdown(qa_output.answer),
        title="[bold]💡 Answer[/bold]",
        border_style="blue",
        padding=(1, 2),
    )
    console.print("\n")
    console.print(answer_panel)


def chat_loop(chroma_db: ChromaDBService, rag_context: RAGContextProvider) -> None:
    """Main chat loop."""
    display_welcome()

    while True:
        try:
            user_message = console.input("\n[bold blue]Your question:[/bold blue] ").strip()

            if user_message.lower() == "exit":
                console.print("\n[bold]👋 Goodbye! Thanks for using the RAG Chatbot.[/bold]")
                break

            console.print("\n" + "─" * 80)
            console.print("\n[bold magenta]🔄 Processing your question...[/bold magenta]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                # Generate search query
                task = progress.add_task("[cyan]Generating semantic search query...", total=None)
                query_output = query_agent.run(RAGQueryAgentInputSchema(user_message=user_message))
                progress.remove_task(task)

                # Display query information
                display_query_info(query_output)

                # Perform vector search
                task = progress.add_task("[cyan]Searching knowledge base...", total=None)
                search_results = chroma_db.query(query_text=query_output.query, n_results=NUM_CHUNKS_TO_RETRIEVE)

                # Update context with retrieved chunks
                rag_context.chunks = [
                    ChunkItem(content=doc, metadata={"chunk_id": id, "distance": dist})
                    for doc, id, dist in zip(search_results["documents"], search_results["ids"], search_results["distances"])
                ]
                progress.remove_task(task)

                # Display retrieved chunks
                display_chunks(rag_context.chunks)

                # Generate answer
                task = progress.add_task("[cyan]Analyzing chunks and generating answer...", total=None)
                qa_output = qa_agent.run(RAGQuestionAnsweringAgentInputSchema(question=user_message))
                progress.remove_task(task)

                # Display answer
                display_answer(qa_output)

            console.print("\n" + "─" * 80)

        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
            console.print("[dim]Please try again or type 'exit' to quit.[/dim]")


if __name__ == "__main__":
    try:
        chroma_db, rag_context = initialize_system()
        chat_loop(chroma_db, rag_context)
    except KeyboardInterrupt:
        console.print("\n[bold]👋 Goodbye! Thanks for using the RAG Chatbot.[/bold]")
    except Exception as e:
        console.print(f"\n[bold red]Fatal error:[/bold red] {str(e)}")
