"""Competitive Evolution POC - Module initialization."""

__version__ = "0.1.0"

from .utils import Neo4jLineageTracker, Solution, Task

__all__ = [
    "Neo4jLineageTracker",
    "Solution",
    "Task",
    "__version__",
]
