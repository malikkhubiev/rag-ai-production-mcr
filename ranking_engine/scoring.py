"""
Block-level scoring logic.

This module implements the per-block scoring functions described in ``math.md``:

- Phase 1: ``ColorScore_B`` — structural coverage with color categories.
- Phase 2: ``PercentScore_B`` — refinement by mean percentages inside categories.

The implementation closely follows the production-proven Java version, while
remaining completely domain-agnostic and focused solely on the mathematics.
"""

from __future__ import annotations

from typing import Iterable, List

from .config import (
    GREEN_THRESHOLD,
    YELLOW_THRESHOLD,
    GREEN_WEIGHT,
    YELLOW_WEIGHT,
    RED_WEIGHT,
)
from .models import BlockScore, BlockType, Requirement, RequirementDetail


def _clamp(value: int, min_value: int, max_value: int) -> int:
    """Clamp an integer to the inclusive range [min_value, max_value]."""
    return max(min_value, min(max_value, value))


def _determine_color(percent: int) -> str:
    """
    Map a percentage to a color category according to the thresholds.

    Returns one of: ``"GREEN"``, ``"YELLOW"``, ``"RED"``.
    """
    if percent >= GREEN_THRESHOLD:
        return "GREEN"
    if percent >= YELLOW_THRESHOLD:
        return "YELLOW"
    return "RED"


def _average(values: Iterable[float]) -> float:
    """Safely compute the arithmetic mean; return 0.0 for an empty collection."""
    values_list = list(values)
    if not values_list:
        return 0.0
    return sum(values_list) / float(len(values_list))


def calculate_block_score(requirements: List[Requirement], block_type: BlockType) -> BlockScore:
    """
    Compute ColorScore and PercentScore for a single block of criteria.

    The logic mirrors the Java implementation:

    - If the block is empty, scores are zero.
    - Percentages are clamped to [0, 100].
    - Requirements are bucketed into GREEN / YELLOW / RED according to thresholds.
    - Phase 1 (ColorScore):
        * If there are no GREEN and no YELLOW items → 0.0.
        * For the "mandatory" block: quadratic-like form in (g, y) with a small
          additive contribution from reds. The result is normalised by N.
        * For other blocks: linear aggregation over (g, y, r) with normalisation by N.
    - Phase 2 (PercentScore):
        * Mean percentages G_avg, Y_avg, R_avg are computed within each color.
        * They are normalised to [0, 1] by dividing by 100.
        * A linear form in (G_norm, Y_norm, R_norm) is multiplied by ColorScore_B.
        * Invalid numerical results (NaN/inf) are safely replaced by 0.0.
    """
    # Rule 1: empty block → all zeros
    if not requirements:
        return BlockScore(
            color_score=0.0,
            percent_score=0.0,
            g=0,
            y=0,
            r=0,
            details=[],
            g_avg=0.0,
            y_avg=0.0,
            r_avg=0.0,
        )

    g = y = r = 0
    green_percents: List[float] = []
    yellow_percents: List[float] = []
    red_percents: List[float] = []
    details: List[RequirementDetail] = []

    for req in requirements:
        percent = _clamp(req.match_percent, 0, 100)
        color = _determine_color(percent)

        details.append(
            RequirementDetail(
                name=req.name,
                percent=percent,
                color=color,
                evidence=req.evidence,
                comment=req.difference_comment,
            )
        )

        if color == "GREEN":
            g += 1
            green_percents.append(float(percent))
        elif color == "YELLOW":
            y += 1
            yellow_percents.append(float(percent))
        else:
            r += 1
            red_percents.append(float(percent))

    n = g + y + r
    if n == 0:
        # Defensive: should not happen if we counted correctly,
        # but we keep the guard to preserve the semantics.
        return BlockScore(
            color_score=0.0,
            percent_score=0.0,
            g=0,
            y=0,
            r=0,
            details=[],
            g_avg=0.0,
            y_avg=0.0,
            r_avg=0.0,
        )

    # ========= Phase 1: ColorScore_B =========
    if g + y == 0:
        # "If a block has no g and no y → block score = 0"
        color_score = 0.0
    else:
        n_float = float(n)
        if block_type is BlockType.MANDATORY:
            # Quadratic form for the mandatory block:
            # (g + 0.5*y) * (g + y) + 0.01*r
            g_plus_half_y = g + YELLOW_WEIGHT * y
            g_plus_y = float(g + y)
            numerator = g_plus_half_y * g_plus_y + RED_WEIGHT * r
            color_score = numerator / (n_float * n_float)
        else:
            # Linear aggregation for preferred / tasks blocks:
            # g + 0.5*y + 0.01*r
            numerator = float(g) + YELLOW_WEIGHT * y + RED_WEIGHT * r
            color_score = numerator / n_float

    # ========= Phase 2: PercentScore_B =========
    g_avg = _average(green_percents)
    y_avg = _average(yellow_percents)
    r_avg = _average(red_percents)

    g_norm = g_avg / 100.0
    y_norm = y_avg / 100.0
    r_norm = r_avg / 100.0

    percent_score = (g_norm + YELLOW_WEIGHT * y_norm + RED_WEIGHT * r_norm) * color_score

    # Numerical safety
    if percent_score != percent_score or percent_score in (float("inf"), float("-inf")):
        percent_score = 0.0

    return BlockScore(
        color_score=color_score,
        percent_score=percent_score,
        g=g,
        y=y,
        r=r,
        details=details,
        g_avg=g_avg,
        y_avg=y_avg,
        r_avg=r_avg,
    )

