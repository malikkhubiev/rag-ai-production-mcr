"""
Block weight redistribution logic.

The mathematical description specifies that if a block has no criteria
(``N = 0``), its weight should be redistributed among the remaining blocks.

This module encapsulates that policy in a small, easily testable function.
"""

from __future__ import annotations

from typing import Dict, List

from .config import MANDATORY_WEIGHT, PREFERRED_WEIGHT, TASKS_WEIGHT
from .models import BlockType, Requirement


def redistribute_weights(
    mandatory: List[Requirement],
    preferred: List[Requirement],
    tasks: List[Requirement],
) -> Dict[BlockType, float]:
    """
    Redistribute block weights when some blocks are empty.

    Rules (mirroring the production Java implementation):

    - Start with base weights from ``config.py``.
    - If both preferred and tasks are empty → their weights are added to mandatory.
    - If only preferred is empty → its weight is moved to tasks.
    - If only tasks is empty → its weight is moved to preferred.
    - If the mandatory block is empty, its weight is set to 0.0
      (this situation is not expected in normal operation, but is handled defensively).
    """
    weights: Dict[BlockType, float] = {
        BlockType.MANDATORY: MANDATORY_WEIGHT,
        BlockType.PREFERRED: PREFERRED_WEIGHT,
        BlockType.TASKS: TASKS_WEIGHT,
    }

    mandatory_empty = not mandatory
    preferred_empty = not preferred
    tasks_empty = not tasks

    if mandatory_empty:
        # Defensive: in a typical configuration the mandatory block should not be empty.
        weights[BlockType.MANDATORY] = 0.0

    if preferred_empty and tasks_empty:
        # Both optional blocks are empty → all weight goes to mandatory.
        weights[BlockType.MANDATORY] = (
            weights[BlockType.MANDATORY]
            + weights[BlockType.PREFERRED]
            + weights[BlockType.TASKS]
        )
        weights[BlockType.PREFERRED] = 0.0
        weights[BlockType.TASKS] = 0.0
    elif preferred_empty:
        # Only preferred empty → its weight moves to tasks.
        weights[BlockType.TASKS] = (
            weights[BlockType.TASKS] + weights[BlockType.PREFERRED]
        )
        weights[BlockType.PREFERRED] = 0.0
    elif tasks_empty:
        # Only tasks empty → its weight moves to preferred.
        weights[BlockType.PREFERRED] = (
            weights[BlockType.PREFERRED] + weights[BlockType.TASKS]
        )
        weights[BlockType.TASKS] = 0.0

    return weights

