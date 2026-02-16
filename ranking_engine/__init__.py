"""
Modular implementation of a two-phase multi-block ranking algorithm.

This package provides:
- data models for requirements and block scores,
- pure scoring functions for individual blocks,
- weight redistribution logic for empty blocks,
- a high-level ranking function for collections of items.

The mathematical definition of the algorithm is described in ``math.md``.
The code here follows the same structure, but is completely domain-agnostic:
it talks about generic "items" evaluated against several blocks of criteria.
"""

from .models import (
    BlockType,
    Requirement,
    RequirementDetail,
    BlockScore,
    ItemInput,
    ItemScore,
)
from .config import (
    GREEN_THRESHOLD,
    YELLOW_THRESHOLD,
    GREEN_WEIGHT,
    YELLOW_WEIGHT,
    RED_WEIGHT,
    MANDATORY_WEIGHT,
    PREFERRED_WEIGHT,
    TASKS_WEIGHT,
    EPSILON,
)
from .ranking import rank_items

__all__ = [
    # Models
    "BlockType",
    "Requirement",
    "RequirementDetail",
    "BlockScore",
    "ItemInput",
    "ItemScore",
    # Config constants
    "GREEN_THRESHOLD",
    "YELLOW_THRESHOLD",
    "GREEN_WEIGHT",
    "YELLOW_WEIGHT",
    "RED_WEIGHT",
    "MANDATORY_WEIGHT",
    "PREFERRED_WEIGHT",
    "TASKS_WEIGHT",
    "EPSILON",
    # Top-level API
    "rank_items",
]

