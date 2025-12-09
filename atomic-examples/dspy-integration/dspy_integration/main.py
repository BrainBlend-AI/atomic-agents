"""
DSPy + Atomic Agents Integration: A Comprehensive Didactic Example

This example teaches you WHY combining DSPy with Atomic Agents is powerful
by walking through three stages with a large, challenging benchmark:

┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: Raw DSPy (Properly Implemented with Typed Signatures)              │
│ ✓ Automatic prompt optimization                                             │
│ ✓ Typed signatures with Literal constraints                                 │
│ ✗ No Pydantic validation ecosystem                                          │
│ ✗ Limited integration with structured output tools                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ STAGE 2: Raw Atomic Agents                                                  │
│ ✓ Type-safe structured outputs (Pydantic)                                   │
│ ✓ Guaranteed schema compliance                                              │
│ ✗ Manual prompt engineering - guesswork                                     │
│ ✗ No systematic way to improve                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ STAGE 3: DSPy + Atomic Agents (The Best of Both)                           │
│ ✓ Automatic prompt optimization                                             │
│ ✓ Type-safe structured outputs                                              │
│ ✓ Measurable, reproducible improvements                                     │
│ ✓ Full Pydantic ecosystem integration                                       │
└─────────────────────────────────────────────────────────────────────────────┘

Run: uv run python -m dspy_integration.main
"""

import os
import json
import time
import random
from typing import List, Literal, Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

import dspy
import instructor
import openai
from pydantic import Field
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.columns import Columns
from rich.text import Text
from rich.rule import Rule
from rich.tree import Tree
from rich import box

from atomic_agents.base.base_io_schema import BaseIOSchema
from atomic_agents.agents.atomic_agent import AtomicAgent, AgentConfig
from atomic_agents.context.system_prompt_generator import SystemPromptGenerator

load_dotenv()
console = Console()

# Set random seed for reproducibility
random.seed(42)

# ============================================================================
# THE TASK: Movie Review Classification
# ============================================================================
# We'll classify movie reviews into genres based on the review text.
# This is intentionally tricky - reviews often mention multiple genres,
# use sarcasm, or have ambiguous language.
#
# LARGE BENCHMARK: 60 training examples, 30 test examples
# ============================================================================

GENRES = ["action", "comedy", "drama", "horror", "sci-fi", "romance"]
GenreType = Literal["action", "comedy", "drama", "horror", "sci-fi", "romance"]

# ============================================================================
# TRAINING DATASET (60 examples)
# ============================================================================
# Mixed difficulty: clear examples for learning, nuanced examples for teaching
DATASET = [
    # === ACTION (10 examples) ===
    {"review": "Non-stop car chases and explosions! The hero single-handedly took down an army.", "genre": "action"},
    {"review": "Martial arts sequences were incredible. The final fight scene was epic!", "genre": "action"},
    {"review": "She trained for 10 years to avenge her family. The fight choreography was poetry in motion.", "genre": "action"},
    {"review": "Bullets flying, buildings exploding, and our hero diving through glass windows. Peak adrenaline.", "genre": "action"},
    {"review": "The heist sequence had me on the edge of my seat. Tension and gunfights galore.", "genre": "action"},
    {"review": "Wow, another chosen one saving the world with a magic sword. Groundbreaking. Still epic though.", "genre": "action"},
    {"review": "This action film broke my heart. The hero's best friend didn't make it.", "genre": "action"},
    {"review": "High-octane from start to finish. The stunt work deserves every award.", "genre": "action"},
    {"review": "A revenge thriller with some of the best choreographed fights I've ever seen.", "genre": "action"},
    {"review": "Explosions, car chases, and a hero who refuses to give up. Classic action fare done right.", "genre": "action"},

    # === COMEDY (10 examples) ===
    {"review": "I couldn't stop laughing! The jokes were hilarious and the timing was perfect.", "genre": "comedy"},
    {"review": "Witty dialogue and absurd situations had the whole theater in stitches.", "genre": "comedy"},
    {"review": "The jokes were so bad they were good. I hate that I loved this stupid movie.", "genre": "comedy"},
    {"review": "I cried watching this comedy because I related too much to the sad clown.", "genre": "comedy"},
    {"review": "A romantic comedy set during a zombie apocalypse. The jokes land even when heads don't.", "genre": "comedy"},
    {"review": "Slapstick humor meets clever wordplay. My cheeks hurt from laughing.", "genre": "comedy"},
    {"review": "The funniest movie I've seen all year. Every scene had at least one great gag.", "genre": "comedy"},
    {"review": "Dark comedy at its finest - you'll feel guilty for laughing but won't be able to stop.", "genre": "comedy"},
    {"review": "The comedic timing of the leads is impeccable. Chemistry-driven hilarity.", "genre": "comedy"},
    {"review": "Satirical genius. It skewers modern society while making you snort-laugh.", "genre": "comedy"},

    # === DRAMA (10 examples) ===
    {"review": "A heart-wrenching story of loss and redemption. I cried for hours.", "genre": "drama"},
    {"review": "A slow burn exploration of grief and family dysfunction. Beautifully acted.", "genre": "drama"},
    {"review": "Yes there's a spaceship, but this is really about the captain dealing with his father's death.", "genre": "drama"},
    {"review": "It's set in space but it's really a courtroom drama about intergalactic law.", "genre": "drama"},
    {"review": "The performances were raw and honest. A meditation on what it means to be human.", "genre": "drama"},
    {"review": "Devastating. The final scene left me emotionally wrecked for days.", "genre": "drama"},
    {"review": "A character study that unfolds like a novel. Patient storytelling at its best.", "genre": "drama"},
    {"review": "The immigrant experience portrayed with such authenticity and grace.", "genre": "drama"},
    {"review": "Three generations of trauma, finally addressed. Cathartic and powerful.", "genre": "drama"},
    {"review": "Oscar-worthy performances in a story about ordinary people facing extraordinary circumstances.", "genre": "drama"},

    # === HORROR (10 examples) ===
    {"review": "Terrifying! I slept with the lights on for a week after watching this.", "genre": "horror"},
    {"review": "Jump scares galore! The monster design was genuinely creepy.", "genre": "horror"},
    {"review": "Zombies attack! But the real horror is the breakdown of society and trust.", "genre": "horror"},
    {"review": "The horror movie made me laugh - those deaths were so creative!", "genre": "horror"},
    {"review": "Psychological terror that gets under your skin. No cheap scares, just dread.", "genre": "horror"},
    {"review": "The creature was nightmare fuel. I'm still seeing it when I close my eyes.", "genre": "horror"},
    {"review": "A haunted house movie that actually delivers. Genuinely unsettling atmosphere.", "genre": "horror"},
    {"review": "Gore-fest with a surprising amount of social commentary. Brutal and smart.", "genre": "horror"},
    {"review": "The slow build of dread was masterful. When it finally hit, I screamed.", "genre": "horror"},
    {"review": "Found footage done right. I had to keep reminding myself it wasn't real.", "genre": "horror"},

    # === SCI-FI (10 examples) ===
    {"review": "Set in 2150, the space battles and alien technology were mind-blowing.", "genre": "sci-fi"},
    {"review": "Time travel paradoxes and quantum physics made this a thinker.", "genre": "sci-fi"},
    {"review": "The robot fell in love with a human. Surprisingly touching for a sci-fi.", "genre": "sci-fi"},
    {"review": "The sci-fi premise was just an excuse for philosophical debates. Loved every second.", "genre": "sci-fi"},
    {"review": "Cyberpunk aesthetic meets thought-provoking questions about consciousness.", "genre": "sci-fi"},
    {"review": "The worldbuilding is incredible. Every detail of this future feels plausible.", "genre": "sci-fi"},
    {"review": "First contact done differently. The aliens were truly alien, not just humans with makeup.", "genre": "sci-fi"},
    {"review": "Hard sci-fi that doesn't dumb down the science. Refreshingly intelligent.", "genre": "sci-fi"},
    {"review": "Dystopian future that feels uncomfortably close to our present. Chilling and prescient.", "genre": "sci-fi"},
    {"review": "Space exploration with a philosophical bent. What does it mean to be alone in the universe?", "genre": "sci-fi"},

    # === ROMANCE (10 examples) ===
    {"review": "The chemistry between the leads was electric. A beautiful love story.", "genre": "romance"},
    {"review": "Swoon-worthy moments and a happily ever after. Pure romantic bliss.", "genre": "romance"},
    {"review": "They met during an alien invasion. The world was ending but love found a way.", "genre": "romance"},
    {"review": "Enemies to lovers done perfectly. The tension was delicious.", "genre": "romance"},
    {"review": "A sweeping love story across decades. Their connection transcended time.", "genre": "romance"},
    {"review": "Second chance romance that made me believe in love again. Tissues required.", "genre": "romance"},
    {"review": "The slow burn was worth the wait. When they finally kissed, I cheered.", "genre": "romance"},
    {"review": "A meet-cute for the ages. Charming leads and witty banter throughout.", "genre": "romance"},
    {"review": "Forbidden love with actual stakes. Their sacrifice at the end broke me.", "genre": "romance"},
    {"review": "Holiday romance that's predictable but perfectly executed. Feel-good viewing.", "genre": "romance"},
]

# ============================================================================
# TEST DATASET (30 examples)
# ============================================================================
# INTENTIONALLY CHALLENGING: sarcasm, multi-genre, misleading language,
# subverted expectations, subtle signals, cultural references
TEST_SET = [
    # === SARCASM & IRONY (5 examples) ===
    {"review": "Oh great, another movie where the hero walks away from explosions in slow motion. How original. Still watched it twice though.", "genre": "action"},
    {"review": "Groundbreaking stuff: man punches bad guys, gets the girl, saves the day. Revolutionary cinema. Loved every predictable second.", "genre": "action"},
    {"review": "I laughed so hard I cried. Then I just cried. Then I laughed again. What even was this movie?", "genre": "comedy"},
    {"review": "Wow, they really subverted my expectations by doing exactly what I expected. The jokes were so obvious they circled back to funny.", "genre": "comedy"},
    {"review": "Another 'scary' movie where the characters make terrible decisions. At least the kills were creative. Actually terrifying creature design though.", "genre": "horror"},

    # === MULTI-GENRE / PRIMARY GENRE DETECTION (6 examples) ===
    {"review": "The robot's sacrifice to save humanity made me sob uncontrollably. Beautiful storytelling set against a dystopian future.", "genre": "sci-fi"},
    {"review": "A serial killer falls in love with his next victim, but she's also a serial killer. Bloody and romantic.", "genre": "horror"},
    {"review": "Two detectives solve crimes while slowly falling for each other. The mystery was okay but I shipped them so hard.", "genre": "romance"},
    {"review": "It's technically a war movie but really it's about two soldiers finding love in the trenches. The battle scenes support the love story.", "genre": "romance"},
    {"review": "Space opera with a love triangle at its core. The laser battles are cool but I'm here for the drama between the three leads.", "genre": "sci-fi"},
    {"review": "Post-apocalyptic survival with a found family. The zombies are almost secondary to the human connections.", "genre": "drama"},

    # === MISLEADING GENRE SIGNALS (5 examples) ===
    {"review": "My heart was RACING the entire time! The courtroom scenes were absolutely EXPLOSIVE! Justice was served!", "genre": "drama"},
    {"review": "The alien invasion was just a backdrop for the family reconciliation story. Dad finally said he was proud.", "genre": "drama"},
    {"review": "Terrifyingly funny. The ghost just wanted to do stand-up comedy but kept accidentally scaring people.", "genre": "comedy"},
    {"review": "Action-packed emotional journey! By action I mean arguments, and by packed I mean I cried the whole time.", "genre": "drama"},
    {"review": "A thriller where the biggest twist was how much I ended up caring about these characters' relationships.", "genre": "romance"},

    # === SUBVERTED EXPECTATIONS (5 examples) ===
    {"review": "Everyone dies at the end. Like, EVERYONE. But somehow it was the most romantic film I've ever seen.", "genre": "romance"},
    {"review": "The monster wasn't scary at all - it just wanted friends. I cried when they finally accepted it.", "genre": "drama"},
    {"review": "Started as a slasher, ended as a meditation on trauma and healing. The horror serves the character development.", "genre": "horror"},
    {"review": "What seemed like a rom-com setup became a profound exploration of self-love and independence. She didn't need him after all.", "genre": "drama"},
    {"review": "The funniest parts were unintentional. This action movie's dialogue is so bad it's become a comedy classic in my friend group.", "genre": "action"},

    # === SUBTLE / AMBIGUOUS (5 examples) ===
    {"review": "Set in 2087, but really it's about loneliness. The AI companion understood him better than any human ever did.", "genre": "sci-fi"},
    {"review": "Quiet film about two people sharing a meal. Nothing happens and everything happens. Deeply moving.", "genre": "drama"},
    {"review": "The laughs come from pain, the pain comes from truth. A comedy that understands sadness intimately.", "genre": "comedy"},
    {"review": "Is it a horror movie if the monster is capitalism? Genuinely unsettling corporate satire.", "genre": "horror"},
    {"review": "They never say 'I love you' but every frame screams it. Visual storytelling at its most romantic.", "genre": "romance"},

    # === CULTURAL CONTEXT / SPECIFIC REFERENCES (4 examples) ===
    {"review": "John Wick energy but make it about a retired chef defending his restaurant. Knife fights choreographed like ballet.", "genre": "action"},
    {"review": "Hereditary meets Little Miss Sunshine. Family dysfunction with supernatural undertones played for dark laughs.", "genre": "comedy"},
    {"review": "Blade Runner questions wrapped in a Her-style relationship. What is real, and does it matter?", "genre": "sci-fi"},
    {"review": "Pride and Prejudice but in space. The Darcy character is an alien prince and it absolutely works.", "genre": "romance"},
]


# ============================================================================
# SCHEMA DEFINITIONS
# ============================================================================

class MovieGenreOutput(BaseIOSchema):
    """Output schema for movie genre classification with structured results."""

    genre: Literal["action", "comedy", "drama", "horror", "sci-fi", "romance"] = Field(
        ...,
        description="The primary genre of the movie based on the review.",
    )
    confidence: float = Field(
        ...,
        description="Confidence score between 0.0 and 1.0",
        ge=0.0,
        le=1.0,
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation for why this genre was chosen.",
    )


class MovieReviewInput(BaseIOSchema):
    """Input schema for movie review classification."""

    review: str = Field(
        ...,
        description="The movie review text to classify.",
    )


# ============================================================================
# EVALUATION UTILITIES
# ============================================================================

@dataclass
class EvalResult:
    """Stores evaluation results for comparison."""
    correct: int
    total: int
    accuracy: float
    predictions: List[Dict[str, Any]]
    avg_time: float


def evaluate_predictions(predictions: List[Dict], test_set: List[Dict]) -> EvalResult:
    """Calculate accuracy and gather stats."""
    correct = 0
    results = []

    for pred, truth in zip(predictions, test_set):
        is_correct = pred.get("genre", "").lower() == truth["genre"].lower()
        if is_correct:
            correct += 1
        results.append({
            "review": truth["review"][:50] + "...",
            "expected": truth["genre"],
            "predicted": pred.get("genre", "ERROR"),
            "correct": is_correct,
            "confidence": pred.get("confidence", 0),
            "reasoning": pred.get("reasoning", "N/A")[:60],
        })

    return EvalResult(
        correct=correct,
        total=len(test_set),
        accuracy=correct / len(test_set) if test_set else 0,
        predictions=results,
        avg_time=0,
    )


# ============================================================================
# STAGE 1: RAW DSPy (Properly Implemented with Typed Signatures)
# ============================================================================

# Define a proper typed DSPy signature with Literal constraints
class MovieGenreSignature(dspy.Signature):
    """Classify a movie review into its primary genre based on the review text.

    Consider the overall focus and tone of the review, not just individual keywords.
    A review mentioning 'explosions' might be a drama if the focus is on characters.
    A 'scary' movie might be a comedy if played for laughs.
    """

    review: str = dspy.InputField(desc="The movie review text to classify")
    genre: GenreType = dspy.OutputField(desc="The primary genre: action, comedy, drama, horror, sci-fi, or romance")
    confidence: float = dspy.OutputField(desc="Confidence score between 0.0 and 1.0")
    reasoning: str = dspy.OutputField(desc="Brief explanation for the classification")


def stage1_raw_dspy(api_key: str) -> tuple[EvalResult, dict]:
    """
    Demonstrate raw DSPy with PROPER typed signatures.

    This shows DSPy at its best: typed signatures with Literal constraints,
    automatic optimization, and chain-of-thought reasoning.
    """
    console.print(Rule("[bold blue]STAGE 1: Raw DSPy (Properly Implemented)[/bold blue]", style="blue"))

    console.print(Panel(
        "[green]DSPy STRENGTHS:[/green]\n"
        "• Typed signatures with Literal constraints (genre MUST be valid)\n"
        "• Automatic prompt optimization via BootstrapFewShot\n"
        "• Chain-of-thought reasoning for complex decisions\n"
        "• Systematic few-shot example selection\n\n"
        "[yellow]LIMITATIONS vs Atomic Agents:[/yellow]\n"
        "• No Pydantic ecosystem (validators, serializers, etc.)\n"
        "• Less integration with structured output tools like Instructor\n"
        "• Type hints are enforced by DSPy, not Python runtime",
        title="Stage 1 Overview",
        border_style="blue"
    ))

    # Configure DSPy
    lm = dspy.LM("openai/gpt-4o-mini", api_key=api_key)
    dspy.configure(lm=lm)

    # Show the proper typed signature
    console.print("\n[bold]Step 1.1: Define Typed DSPy Signature[/bold]")
    console.print("DSPy supports class-based signatures with Python type hints:\n")

    signature_code = '''from typing import Literal

# DSPy Signature WITH proper type constraints
class MovieGenreSignature(dspy.Signature):
    """Classify a movie review into its primary genre."""

    review: str = dspy.InputField(desc="The movie review text")

    # Literal type constrains output to valid genres only!
    genre: Literal["action", "comedy", "drama", "horror", "sci-fi", "romance"] = \\
        dspy.OutputField(desc="The primary genre")

    confidence: float = dspy.OutputField(desc="Confidence 0.0-1.0")
    reasoning: str = dspy.OutputField(desc="Brief explanation")

# DSPy enforces the Literal constraint - no more "dramedy" or "thriller"!
classify = dspy.ChainOfThought(MovieGenreSignature)'''

    console.print(Syntax(signature_code, "python", theme="monokai", line_numbers=True))

    # Create the classifier with typed signature
    classify = dspy.ChainOfThought(MovieGenreSignature)

    # Show what the UNOPTIMIZED prompt looks like
    console.print("\n[bold]Step 1.2: Unoptimized Prompt (What DSPy Generates)[/bold]")

    # Run once to see the prompt
    with dspy.context(lm=lm):
        _ = classify(review=DATASET[0]["review"])

    # Get the last prompt from history
    unoptimized_prompt = None
    if lm.history:
        last_call = lm.history[-1]
        unoptimized_prompt = last_call.get("messages", [{}])

        console.print(Panel(
            "[dim]Notice how DSPy includes the Literal type constraint in the prompt:[/dim]\n\n" +
            json.dumps(unoptimized_prompt, indent=2)[:2000] + "...",
            title="Unoptimized DSPy Prompt (With Type Constraints)",
            border_style="yellow"
        ))

    # Now let's OPTIMIZE with BootstrapFewShot
    console.print("\n[bold]Step 1.3: DSPy Optimization (BootstrapFewShot)[/bold]")
    console.print(Panel(
        "[cyan]What BootstrapFewShot does:[/cyan]\n\n"
        "1. Takes your labeled training examples\n"
        "2. Runs the LLM on each to generate 'traces' (reasoning chains)\n"
        "3. Filters traces that produce correct answers\n"
        "4. Selects the best traces as few-shot demonstrations\n"
        "5. Injects these into future prompts automatically\n\n"
        "[yellow]Key insight:[/yellow] DSPy doesn't just use your examples verbatim.\n"
        "It generates NEW reasoning and picks what actually works!",
        title="How DSPy Optimization Works",
        border_style="cyan"
    ))

    # Create training set from our larger dataset
    # Use 30 examples for training (half the dataset)
    train_examples = DATASET[:30]
    trainset = [
        dspy.Example(
            review=ex["review"],
            genre=ex["genre"],
            confidence=0.85,  # Reasonable default
            reasoning=f"This review demonstrates typical {ex['genre']} characteristics."
        ).with_inputs("review")
        for ex in train_examples
    ]

    # Define metric for optimization
    def genre_match(example, prediction, trace=None):
        pred_genre = str(prediction.genre).lower().strip()
        expected_genre = str(example.genre).lower().strip()
        return pred_genre == expected_genre

    # Optimize with more demos for better learning
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Running DSPy optimization (30 training examples)...", total=None)

        optimizer = dspy.BootstrapFewShot(
            metric=genre_match,
            max_bootstrapped_demos=4,
            max_labeled_demos=4,
            max_rounds=1,
        )
        optimized_classify = optimizer.compile(classify, trainset=trainset)
        progress.remove_task(task)

    console.print("[green]✓ Optimization complete![/green]\n")

    # Show what the OPTIMIZED prompt looks like
    console.print("[bold]Step 1.4: Optimized Prompt (After DSPy Magic)[/bold]")

    with dspy.context(lm=lm):
        _ = optimized_classify(review=TEST_SET[0]["review"])

    optimized_prompt = None
    if lm.history:
        last_call = lm.history[-1]
        optimized_prompt = last_call.get("messages", [{}])

        # Show the prompt
        prompt_str = json.dumps(optimized_prompt, indent=2)

        console.print(Panel(
            "[dim]Notice the auto-selected few-shot examples with reasoning:[/dim]\n\n" +
            prompt_str[:3500] + ("\n..." if len(prompt_str) > 3500 else ""),
            title="Optimized DSPy Prompt (With Auto-Selected Examples)",
            border_style="green"
        ))

    # Show which demos were selected
    console.print("\n[bold]Step 1.5: Few-Shot Examples DSPy Selected[/bold]")

    if hasattr(optimized_classify, 'demos') and optimized_classify.demos:
        tree = Tree("[bold]Selected Demonstrations[/bold]")
        for i, demo in enumerate(optimized_classify.demos[:4]):
            demo_branch = tree.add(f"[cyan]Example {i+1}[/cyan]")
            review_text = str(getattr(demo, 'review', 'N/A'))
            demo_branch.add(f"Review: {review_text[:70]}...")
            demo_branch.add(f"Genre: [green]{getattr(demo, 'genre', 'N/A')}[/green]")
            if hasattr(demo, 'reasoning'):
                reasoning = str(getattr(demo, 'reasoning', ''))[:80]
                demo_branch.add(f"Reasoning: [dim]{reasoning}...[/dim]")
        console.print(tree)
    else:
        console.print("[dim]Demo inspection not available for this predictor type[/dim]")

    # Evaluate on test set
    console.print(f"\n[bold]Step 1.6: Evaluation on Test Set ({len(TEST_SET)} challenging examples)[/bold]")

    predictions = []
    start_time = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Running predictions...", total=len(TEST_SET))

        for test_ex in TEST_SET:
            try:
                result = optimized_classify(review=test_ex["review"])
                # DSPy with typed signatures should return valid genres
                genre_val = str(result.genre).strip().lower()
                # Normalize any edge cases
                if genre_val not in GENRES:
                    genre_val = "error"  # Mark invalid outputs

                predictions.append({
                    "genre": genre_val,
                    "confidence": float(result.confidence) if hasattr(result, 'confidence') else 0.5,
                    "reasoning": str(result.reasoning) if hasattr(result, 'reasoning') else "N/A",
                })
            except Exception as e:
                predictions.append({
                    "genre": "error",
                    "confidence": 0,
                    "reasoning": str(e),
                })
            progress.advance(task)

    elapsed = time.time() - start_time

    eval_result = evaluate_predictions(predictions, TEST_SET)
    eval_result.avg_time = elapsed / len(TEST_SET)

    # Show results
    console.print("\n[bold]Step 1.7: Results[/bold]")

    # Show DSPy's strengths AND remaining limitations
    invalid_genres = [p["genre"] for p in predictions if p["genre"] not in GENRES]

    console.print(Panel(
        "[green]DSPy TYPED SIGNATURE BENEFITS:[/green]\n"
        f"• Genre constrained to valid options (invalid outputs: {len(invalid_genres)})\n"
        "• Automatic few-shot example selection\n"
        "• Chain-of-thought reasoning included\n\n"
        "[yellow]REMAINING LIMITATIONS:[/yellow]\n"
        "• No Pydantic validation ecosystem\n"
        "• Confidence not guaranteed to be 0-1 (no ge/le constraints)\n"
        "• Can't use Instructor's retry mechanisms\n"
        "• Type enforcement is DSPy-specific, not Python-native",
        title="DSPy Typed Signatures Assessment",
        border_style="blue"
    ))

    # Results table
    table = Table(title=f"Stage 1 Results: {eval_result.accuracy:.1%} Accuracy ({eval_result.correct}/{eval_result.total})", box=box.ROUNDED)
    table.add_column("Review", style="cyan", max_width=40)
    table.add_column("Expected", style="green")
    table.add_column("Predicted", style="yellow")
    table.add_column("✓/✗", justify="center")

    for pred in eval_result.predictions:
        table.add_row(
            pred["review"],
            pred["expected"],
            pred["predicted"],
            "[green]✓[/green]" if pred["correct"] else "[red]✗[/red]"
        )

    console.print(table)

    behind_scenes = {
        "unoptimized_prompt_sample": str(unoptimized_prompt)[:500] if unoptimized_prompt else "N/A",
        "optimized_prompt_sample": str(optimized_prompt)[:500] if optimized_prompt else "N/A",
        "num_demos_selected": len(optimized_classify.demos) if hasattr(optimized_classify, 'demos') else "N/A",
        "training_examples": len(trainset),
        "invalid_genre_outputs": len(invalid_genres),
    }

    return eval_result, behind_scenes


# ============================================================================
# STAGE 2: RAW ATOMIC AGENTS
# ============================================================================

def stage2_raw_atomic_agents(api_key: str) -> tuple[EvalResult, dict]:
    """
    Demonstrate raw Atomic Agents: beautiful structured outputs, but manual prompts.
    """
    console.print(Rule("[bold magenta]STAGE 2: Raw Atomic Agents[/bold magenta]", style="magenta"))

    console.print(Panel(
        "[green]ATOMIC AGENTS STRENGTHS:[/green]\n"
        "• Full Pydantic ecosystem (validators, serializers, Field constraints)\n"
        "• Instructor integration for robust structured output\n"
        "• Python-native type safety with runtime validation\n"
        "• ge/le constraints on confidence (guaranteed 0-1)\n\n"
        "[yellow]LIMITATIONS:[/yellow]\n"
        "• Manual prompt engineering - no automatic optimization\n"
        "• No systematic few-shot example selection\n"
        "• Prompt improvements require guesswork and iteration",
        title="Stage 2 Overview",
        border_style="magenta"
    ))

    console.print("\n[bold]Step 2.1: Define Pydantic Schema[/bold]")
    console.print("Atomic Agents uses Pydantic for type-safe outputs:\n")

    schema_code = '''class MovieGenreOutput(BaseIOSchema):
    """Output schema for movie genre classification."""

    genre: Literal["action", "comedy", "drama", "horror", "sci-fi", "romance"] = Field(
        ...,
        description="The primary genre of the movie.",
    )
    confidence: float = Field(
        ...,
        ge=0.0, le=1.0,  # VALIDATED! Must be between 0 and 1
        description="Confidence score between 0.0 and 1.0",
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation for the classification.",
    )

# The LLM output MUST match this schema or it fails validation.
# No more parsing "high" vs "0.85" vs "85%" - it's always a float!'''

    console.print(Syntax(schema_code, "python", theme="monokai", line_numbers=True))

    console.print("\n[bold]Step 2.2: Manual System Prompt (The Guesswork)[/bold]")

    # This is our manually crafted prompt - we're guessing what works!
    manual_system_prompt = SystemPromptGenerator(
        background=[
            "You are a movie genre classification expert.",
            "You analyze movie reviews and determine the primary genre.",
            f"Valid genres are: {', '.join(GENRES)}",
        ],
        steps=[
            "Read the review carefully.",
            "Identify key genre indicators (action words, emotional language, etc.).",
            "Consider the overall tone and subject matter.",
            "Select the single most appropriate genre.",
            "Provide a confidence score based on how clear the genre signals are.",
        ],
        output_instructions=[
            "Be decisive - pick ONE primary genre even if multiple could apply.",
            "Confidence should be 0.7-1.0 for clear cases, 0.5-0.7 for ambiguous ones.",
            "Keep reasoning brief but specific to the review.",
        ],
    )

    generated_prompt = manual_system_prompt.generate_prompt()

    console.print(Panel(
        "[dim]This is the system prompt WE WROTE BY HAND:[/dim]\n\n" +
        generated_prompt,
        title="Manual System Prompt (Our Best Guess)",
        border_style="yellow"
    ))

    console.print(Panel(
        "[red]THE PROBLEM:[/red]\n\n"
        "We wrote this prompt based on intuition. Questions we can't answer:\n\n"
        "• Is 'Be decisive' helping or hurting accuracy?\n"
        "• Should we add few-shot examples? Which ones?\n"
        "• Is the step-by-step instruction actually useful?\n"
        "• Would different wording improve results?\n\n"
        "[yellow]Without DSPy, we're just guessing![/yellow]",
        title="The Manual Prompt Engineering Problem",
        border_style="red"
    ))

    # Create Atomic Agent
    console.print("\n[bold]Step 2.3: Create Atomic Agent[/bold]")

    client = instructor.from_openai(openai.OpenAI(api_key=api_key))

    agent = AtomicAgent[MovieReviewInput, MovieGenreOutput](
        config=AgentConfig(
            client=client,
            model="gpt-4o-mini",
            system_prompt_generator=manual_system_prompt,
        )
    )

    console.print("[green]✓ Agent created with schema validation[/green]")

    # Show how Instructor enforces the schema
    console.print("\n[bold]Step 2.4: Schema Enforcement in Action[/bold]")

    console.print(Panel(
        "[cyan]What happens under the hood:[/cyan]\n\n"
        "1. Atomic Agents sends your prompt + Pydantic schema to the LLM\n"
        "2. Instructor (the library) converts schema to JSON Schema for the LLM\n"
        "3. LLM generates output attempting to match the schema\n"
        "4. Instructor validates the response against Pydantic\n"
        "5. If validation fails, Instructor retries with error feedback\n"
        "6. You get a guaranteed-valid Pydantic object or an exception\n\n"
        "[green]Result:[/green] genre is ALWAYS one of our 6 options,\n"
        "confidence is ALWAYS a float between 0 and 1!",
        title="How Schema Enforcement Works",
        border_style="cyan"
    ))

    # Evaluate
    console.print("\n[bold]Step 2.5: Evaluation on Test Set[/bold]")

    predictions = []
    start_time = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[magenta]Running predictions...", total=len(TEST_SET))

        for test_ex in TEST_SET:
            try:
                result = agent.run(MovieReviewInput(review=test_ex["review"]))
                predictions.append({
                    "genre": result.genre,  # Already validated!
                    "confidence": result.confidence,  # Already a float!
                    "reasoning": result.reasoning,
                })
            except Exception as e:
                predictions.append({
                    "genre": "error",
                    "confidence": 0,
                    "reasoning": str(e),
                })
            progress.advance(task)

    elapsed = time.time() - start_time

    eval_result = evaluate_predictions(predictions, TEST_SET)
    eval_result.avg_time = elapsed / len(TEST_SET)

    # Show the BENEFIT - structured outputs
    console.print("\n[bold]Step 2.6: The Benefit - Type-Safe Outputs[/bold]")

    console.print(Panel(
        "[green]ATOMIC AGENTS ADVANTAGE:[/green]\n\n"
        "Look at these outputs - perfectly structured:\n" +
        "\n".join([
            f"  • genre='{predictions[i]['genre']}' (Literal) confidence={predictions[i]['confidence']:.2f} (float)"
            for i in range(min(3, len(predictions)))
        ]) + "\n\n"
        "[cyan]Benefits:[/cyan]\n"
        "• genre is guaranteed to be one of our 6 valid options\n"
        "• confidence is always a float between 0.0 and 1.0\n"
        "• No parsing needed - direct attribute access\n"
        "• IDE autocomplete works perfectly\n"
        "• Downstream code can trust the types",
        title="Structured Output Benefits",
        border_style="green"
    ))

    # Results table
    table = Table(title=f"Stage 2 Results: {eval_result.accuracy:.1%} Accuracy", box=box.ROUNDED)
    table.add_column("Review", style="cyan", max_width=35)
    table.add_column("Expected", style="green")
    table.add_column("Predicted", style="yellow")
    table.add_column("Confidence", justify="right")
    table.add_column("✓/✗", justify="center")

    for pred in eval_result.predictions:
        table.add_row(
            pred["review"],
            pred["expected"],
            pred["predicted"],
            f"{pred['confidence']:.2f}",
            "[green]✓[/green]" if pred["correct"] else "[red]✗[/red]"
        )

    console.print(table)

    behind_scenes = {
        "system_prompt": generated_prompt,
        "schema_enforced": True,
        "manual_engineering": True,
    }

    return eval_result, behind_scenes


# ============================================================================
# STAGE 3: DSPy + ATOMIC AGENTS (THE BEST OF BOTH)
# ============================================================================

def stage3_combined(api_key: str) -> tuple[EvalResult, dict]:
    """
    Demonstrate the combined approach: DSPy optimization + Atomic Agents structure.
    """
    console.print(Rule("[bold green]STAGE 3: DSPy + Atomic Agents[/bold green]", style="green"))

    console.print(Panel(
        "[green]THE SOLUTION:[/green]\n"
        "Combine DSPy's automatic optimization with Atomic Agents' type safety!\n\n"
        "[cyan]WHAT WE GET:[/cyan]\n"
        "• DSPy automatically finds the best prompts and examples\n"
        "• Atomic Agents guarantees output structure\n"
        "• Measurable improvements through optimization\n"
        "• Production-ready typed outputs\n\n"
        "[yellow]THE BEST OF BOTH WORLDS[/yellow]",
        title="Stage 3 Overview",
        border_style="green"
    ))

    # Import our bridge
    from dspy_integration.bridge import (
        DSPyAtomicModule,
        create_dspy_example,
        create_dspy_signature_from_schemas,
    )

    console.print("\n[bold]Step 3.1: The Bridge - DSPyAtomicModule[/bold]")

    bridge_code = '''# The bridge combines both frameworks:
module = DSPyAtomicModule(
    input_schema=MovieReviewInput,    # Pydantic input validation
    output_schema=MovieGenreOutput,   # Pydantic output structure
    instructions="Classify the movie review into a genre.",
    use_chain_of_thought=True,        # DSPy's reasoning capability
)

# Behind the scenes:
# 1. Pydantic schemas are converted to DSPy signatures
# 2. DSPy handles prompt construction and optimization
# 3. Outputs are validated against Pydantic schemas
# 4. You get type-safe results that DSPy optimized!'''

    console.print(Syntax(bridge_code, "python", theme="monokai", line_numbers=True))

    # Configure DSPy
    lm = dspy.LM("openai/gpt-4o-mini", api_key=api_key)
    dspy.configure(lm=lm)

    # Create the module
    module = DSPyAtomicModule(
        input_schema=MovieReviewInput,
        output_schema=MovieGenreOutput,
        instructions="Classify the movie review into its primary genre. Be accurate and provide reasoning.",
        use_chain_of_thought=True,
    )

    console.print("\n[bold]Step 3.2: Schema-to-Signature Conversion[/bold]")

    # Show the generated signature
    console.print(Panel(
        f"[cyan]Pydantic Schema → DSPy Signature:[/cyan]\n\n"
        f"Input fields: review (str)\n"
        f"Output fields: genre (Literal), confidence (float), reasoning (str)\n\n"
        f"[dim]The bridge automatically converts Pydantic field descriptions\n"
        f"into DSPy field descriptors, preserving all metadata.[/dim]",
        title="Automatic Conversion",
        border_style="cyan"
    ))

    # Create typed training examples
    console.print("\n[bold]Step 3.3: Type-Safe Training Examples[/bold]")

    console.print(Panel(
        "[cyan]Creating training examples with validation:[/cyan]\n\n"
        "Each example is validated against our Pydantic schemas!\n"
        "If you accidentally put confidence=1.5 or genre='thriller',\n"
        "you get an immediate error - not a silent failure later.",
        title="Validated Training Data",
        border_style="cyan"
    ))

    # Create training set with our helper - use more examples for better optimization
    train_examples = DATASET[:40]  # Use 40 examples for training
    trainset = []
    for ex in train_examples:
        trainset.append(
            create_dspy_example(
                MovieReviewInput,
                MovieGenreOutput,
                {"review": ex["review"]},
                {
                    "genre": ex["genre"],
                    "confidence": 0.85,  # Reasonable default
                    "reasoning": f"The review shows typical {ex['genre']} characteristics.",
                },
            )
        )

    console.print(f"[green]✓ Created {len(trainset)} validated training examples[/green]")

    # Define metric
    def typed_genre_match(example, prediction, trace=None):
        """Metric that works with our typed outputs."""
        pred_genre = str(prediction.genre).lower().strip()
        expected_genre = str(example.genre).lower().strip()
        return pred_genre == expected_genre

    # Optimize
    console.print("\n[bold]Step 3.4: DSPy Optimization (With Schema Awareness)[/bold]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"[green]Running optimization ({len(trainset)} training examples)...", total=None)

        optimizer = dspy.BootstrapFewShot(
            metric=typed_genre_match,
            max_bootstrapped_demos=4,
            max_labeled_demos=4,
            max_rounds=1,
        )
        optimized_module = optimizer.compile(module, trainset=trainset)
        progress.remove_task(task)

    console.print("[green]✓ Optimization complete![/green]")

    # Show the optimized prompt
    console.print("\n[bold]Step 3.5: The Optimized Prompt (Exposed!)[/bold]")

    # Run once to capture the prompt
    with dspy.context(lm=lm):
        _ = optimized_module(review=TEST_SET[0]["review"])

    if lm.history:
        last_call = lm.history[-1]
        optimized_prompt = last_call.get("messages", [{}])
        prompt_str = json.dumps(optimized_prompt, indent=2)

        console.print(Panel(
            "[dim]This is what DSPy + Atomic Agents sends to the LLM:[/dim]\n\n" +
            prompt_str[:2500] + ("\n..." if len(prompt_str) > 2500 else ""),
            title="Final Optimized Prompt",
            border_style="green"
        ))

    # Evaluate with type-safe outputs
    console.print("\n[bold]Step 3.6: Evaluation with Type-Safe Outputs[/bold]")

    predictions = []
    raw_outputs = []
    start_time = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[green]Running predictions...", total=len(TEST_SET))

        for test_ex in TEST_SET:
            try:
                # Get raw DSPy output
                raw_result = optimized_module(review=test_ex["review"])

                # Convert to validated Pydantic
                validated_result = optimized_module.run_validated(review=test_ex["review"])

                predictions.append({
                    "genre": validated_result.genre,  # Guaranteed Literal type!
                    "confidence": validated_result.confidence,  # Guaranteed 0-1 float!
                    "reasoning": validated_result.reasoning,
                })
                raw_outputs.append({
                    "raw_genre": str(raw_result.genre),
                    "validated_genre": validated_result.genre,
                })
            except Exception as e:
                predictions.append({
                    "genre": "error",
                    "confidence": 0,
                    "reasoning": str(e),
                })
            progress.advance(task)

    elapsed = time.time() - start_time

    eval_result = evaluate_predictions(predictions, TEST_SET)
    eval_result.avg_time = elapsed / len(TEST_SET)

    # Show the combined benefits
    console.print("\n[bold]Step 3.7: The Combined Benefits[/bold]")

    console.print(Panel(
        "[green]✓ DSPy BENEFITS:[/green]\n"
        "• Automatic few-shot example selection\n"
        "• Optimized prompt instructions\n"
        "• Chain-of-thought reasoning\n"
        "• Measurable improvement through metrics\n\n"
        "[green]✓ ATOMIC AGENTS BENEFITS:[/green]\n"
        "• genre is Literal['action','comedy',...] - always valid\n"
        "• confidence is float with ge=0, le=1 - always in range\n"
        "• Full IDE autocomplete and type checking\n"
        "• Pydantic validation catches any LLM mistakes\n\n"
        "[yellow]COMBINED:[/yellow] Optimized prompts + Guaranteed structure!",
        title="The Best of Both Worlds",
        border_style="green"
    ))

    # Results table
    table = Table(title=f"Stage 3 Results: {eval_result.accuracy:.1%} Accuracy", box=box.ROUNDED)
    table.add_column("Review", style="cyan", max_width=35)
    table.add_column("Expected", style="green")
    table.add_column("Predicted", style="yellow")
    table.add_column("Confidence", justify="right")
    table.add_column("✓/✗", justify="center")

    for pred in eval_result.predictions:
        table.add_row(
            pred["review"],
            pred["expected"],
            pred["predicted"],
            f"{pred['confidence']:.2f}",
            "[green]✓[/green]" if pred["correct"] else "[red]✗[/red]"
        )

    console.print(table)

    behind_scenes = {
        "optimized_prompt_sample": prompt_str[:1000] if 'prompt_str' in dir() else "N/A",
        "schema_enforced": True,
        "dspy_optimized": True,
    }

    return eval_result, behind_scenes


# ============================================================================
# FINAL COMPARISON
# ============================================================================

def show_final_comparison(
    stage1_result: EvalResult,
    stage2_result: EvalResult,
    stage3_result: EvalResult,
):
    """Show side-by-side comparison of all three approaches."""

    console.print(Rule("[bold yellow]FINAL COMPARISON[/bold yellow]", style="yellow"))

    # Summary table
    table = Table(title="Approach Comparison", box=box.DOUBLE_EDGE)
    table.add_column("Metric", style="bold")
    table.add_column("Stage 1\nRaw DSPy", justify="center", style="blue")
    table.add_column("Stage 2\nRaw Atomic Agents", justify="center", style="magenta")
    table.add_column("Stage 3\nDSPy + Atomic", justify="center", style="green")

    table.add_row(
        "Accuracy",
        f"{stage1_result.accuracy:.1%}",
        f"{stage2_result.accuracy:.1%}",
        f"[bold]{stage3_result.accuracy:.1%}[/bold]",
    )
    table.add_row(
        "Correct / Total",
        f"{stage1_result.correct}/{stage1_result.total}",
        f"{stage2_result.correct}/{stage2_result.total}",
        f"[bold]{stage3_result.correct}/{stage3_result.total}[/bold]",
    )
    table.add_row(
        "Avg Time/Query",
        f"{stage1_result.avg_time:.2f}s",
        f"{stage2_result.avg_time:.2f}s",
        f"{stage3_result.avg_time:.2f}s",
    )
    table.add_row(
        "Prompt Optimization",
        "[green]✓ Auto[/green]",
        "[red]✗ Manual[/red]",
        "[green]✓ Auto[/green]",
    )
    table.add_row(
        "Type Safety",
        "[yellow]~ DSPy Literal[/yellow]",
        "[green]✓ Pydantic[/green]",
        "[green]✓ Pydantic[/green]",
    )
    table.add_row(
        "Output Validation",
        "[yellow]~ Basic[/yellow]",
        "[green]✓ Full[/green]",
        "[green]✓ Full[/green]",
    )
    table.add_row(
        "Pydantic Ecosystem",
        "[red]✗ No[/red]",
        "[green]✓ Full[/green]",
        "[green]✓ Full[/green]",
    )
    table.add_row(
        "Few-Shot Selection",
        "[green]✓ Auto[/green]",
        "[red]✗ Manual[/red]",
        "[green]✓ Auto[/green]",
    )
    table.add_row(
        "IDE Support",
        "[yellow]~ Partial[/yellow]",
        "[green]✓ Full[/green]",
        "[green]✓ Full[/green]",
    )

    console.print(table)

    # Key takeaways
    console.print(Panel(
        "[bold yellow]KEY TAKEAWAYS[/bold yellow]\n\n"

        "[blue]RAW DSPy (with typed signatures):[/blue]\n"
        "• Excellent optimization with Literal type constraints\n"
        "• Great for experimentation and iteration\n"
        "• Missing Pydantic ecosystem (validators, Field constraints)\n\n"

        "[magenta]RAW ATOMIC AGENTS:[/magenta]\n"
        "• Full Pydantic ecosystem with runtime validation\n"
        "• Instructor integration for robust outputs\n"
        "• Manual prompt engineering limits optimization\n\n"

        "[green]DSPy + ATOMIC AGENTS:[/green]\n"
        "• Automatic optimization finds the best prompts\n"
        "• Full Pydantic validation and serialization\n"
        "• Measurable improvements + production-ready types\n"
        "• [bold]The best of both worlds![/bold]",
        title="Summary",
        border_style="yellow"
    ))

    # When to use what
    console.print(Panel(
        "[bold]WHEN TO USE EACH APPROACH[/bold]\n\n"

        "[blue]Use Raw DSPy when:[/blue]\n"
        "• Quick prototyping and experimentation\n"
        "• Output format doesn't matter much\n"
        "• You'll post-process outputs anyway\n\n"

        "[magenta]Use Raw Atomic Agents when:[/magenta]\n"
        "• You need guaranteed output structure NOW\n"
        "• You don't have training data for optimization\n"
        "• The task is simple enough that manual prompts work\n\n"

        "[green]Use DSPy + Atomic Agents when:[/green]\n"
        "• You have labeled data and want to optimize\n"
        "• Production systems need type-safe outputs\n"
        "• You want measurable, reproducible improvements\n"
        "• Both accuracy AND structure matter",
        title="Decision Guide",
        border_style="cyan"
    ))


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the complete didactic example with a comprehensive benchmark."""

    console.print(Panel.fit(
        "[bold]DSPy + Atomic Agents: A Comprehensive Didactic Example[/bold]\n\n"
        "This example teaches you WHY combining these frameworks is powerful\n"
        "by walking through three stages with full transparency.\n\n"
        "[dim]Large benchmark: 60 training examples, 30 challenging test cases\n"
        "We'll expose the prompts, show the optimizations,\n"
        "and compare measurable results.[/dim]",
        border_style="bold white",
    ))

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[red]Error: OPENAI_API_KEY environment variable required[/red]")
        return

    console.print(f"\n[dim]Using model: gpt-4o-mini[/dim]")
    console.print(f"[dim]Training set: {len(DATASET)} examples (balanced across 6 genres)[/dim]")
    console.print(f"[dim]Test set: {len(TEST_SET)} challenging examples (sarcasm, multi-genre, etc.)[/dim]\n")

    # Run all three stages
    try:
        stage1_result, stage1_behind = stage1_raw_dspy(api_key)
        console.print("\n")

        stage2_result, stage2_behind = stage2_raw_atomic_agents(api_key)
        console.print("\n")

        stage3_result, stage3_behind = stage3_combined(api_key)
        console.print("\n")

        # Final comparison
        show_final_comparison(stage1_result, stage2_result, stage3_result)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    main()
