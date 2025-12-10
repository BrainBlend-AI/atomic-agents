"""
Stages package for DSPy + Atomic Agents integration demo.

Each stage demonstrates a different approach:
- Stage 1: Raw DSPy with typed signatures
- Stage 2: Raw Atomic Agents with manual prompts
- Stage 3: Combined DSPy + Atomic Agents

Following Single Responsibility Principle: each stage module handles
one approach completely, from setup to evaluation.
"""

from dspy_integration.stages.stage1_dspy import run_stage1_raw_dspy
from dspy_integration.stages.stage2_atomic import run_stage2_raw_atomic_agents
from dspy_integration.stages.stage3_combined import run_stage3_combined

__all__ = [
    "run_stage1_raw_dspy",
    "run_stage2_raw_atomic_agents",
    "run_stage3_combined",
]
