"""
High-level ranking API.

Given a collection of items with per-block requirement assessments,
this module:

1. Computes block-level scores (ColorScore and PercentScore) for each item.
2. Adjusts block weights if some blocks are empty.
3. Aggregates block scores into final scores.
4. Sorts items lexicographically:
   - primary key: FinalColorScore (Phase 1),
   - tie-breaker: FinalPercentScore (Phase 2).
"""

from __future__ import annotations

from functools import cmp_to_key
from typing import Iterable, List

from .config import EPSILON
from .models import BlockType, ItemInput, ItemScore
from .scoring import calculate_block_score
from .weights import redistribute_weights


def rank_items(items: Iterable[ItemInput]) -> List[ItemScore]:
    """
    Rank input items using the two-phase multi-block algorithm.

    The function is pure: for a fixed collection of inputs it always
    produces the same outputs and does not perform any I/O.
    """
    scores: List[ItemScore] = []

    for item in items:
        # 1) Compute block-level scores
        mandatory_score = calculate_block_score(item.mandatory, BlockType.MANDATORY)
        preferred_score = calculate_block_score(item.preferred, BlockType.PREFERRED)
        tasks_score = calculate_block_score(item.tasks, BlockType.TASKS)

        # 2) Redistribute weights for empty blocks
        weights = redistribute_weights(
            mandatory=item.mandatory,
            preferred=item.preferred,
            tasks=item.tasks,
        )

        # 3) Aggregate into final scores (Phase 1 and Phase 2)
        final_color_score = (
            weights[BlockType.MANDATORY] * mandatory_score.color_score
            + weights[BlockType.PREFERRED] * preferred_score.color_score
            + weights[BlockType.TASKS] * tasks_score.color_score
        )

        final_percent_score = (
            weights[BlockType.MANDATORY] * mandatory_score.percent_score
            + weights[BlockType.PREFERRED] * preferred_score.percent_score
            + weights[BlockType.TASKS] * tasks_score.percent_score
        )

        scores.append(
            ItemScore(
                item_id=item.item_id,
                mandatory=mandatory_score,
                preferred=preferred_score,
                tasks=tasks_score,
                final_color_score=final_color_score,
                final_percent_score=final_percent_score,
                used_weights=weights,
            )
        )

    # 4) Two-phase lexicographic sorting with epsilon-aware comparison,
    #    mirroring the Java implementation:
    #    - if FinalColorScore differs by more than EPSILON → use it;
    #    - otherwise → fall back to FinalPercentScore.

    def _compare(a: ItemScore, b: ItemScore) -> int:
        color_diff = b.final_color_score - a.final_color_score
        if abs(color_diff) > EPSILON:
            return -1 if color_diff > 0 else 1

        percent_diff = b.final_percent_score - a.final_percent_score
        if percent_diff > 0:
            return -1
        if percent_diff < 0:
            return 1
        return 0

    scores.sort(key=cmp_to_key(_compare))

    # Assign ranks (1 = best), preserving order after sorting
    for idx, score in enumerate(scores, start=1):
        score.rank = idx

    return scores

