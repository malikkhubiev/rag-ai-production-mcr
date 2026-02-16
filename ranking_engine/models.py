"""
Core data models for the ranking algorithm.

All models are intentionally domain-agnostic:
they work with abstract "items" evaluated against several blocks of criteria.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class BlockType(str, Enum):
    """
    Logical blocks of criteria.

    In the mathematical description these are typically:
    - Mandatory
    - Preferred
    - Tasks
    """

    MANDATORY = "mandatory"
    PREFERRED = "preferred"
    TASKS = "tasks"


@dataclass
class Requirement:
    """
    Atomic criterion within a block.

    Attributes:
        name: Human-readable description of the requirement.
        match_percent: Confidence (0–100) that the item satisfies this requirement.
        evidence: Optional free-text evidence supporting the score.
        difference_comment: Optional explanation of gaps or nuances.
    """

    name: str
    match_percent: int
    evidence: str = ""
    difference_comment: str = ""


@dataclass
class RequirementDetail:
    """
    Normalised representation of a requirement used inside scoring.

    It keeps both the original percentage value and the derived
    categorical label ("GREEN" / "YELLOW" / "RED").
    """

    name: str
    percent: int
    color: str
    evidence: str
    comment: str


@dataclass
class BlockScore:
    """
    Score for a single block of criteria.

    Attributes:
        color_score: Primary score (coverage-based), Phase 1.
        percent_score: Refined score (percentages-aware), Phase 2.
        g, y, r: Counts of requirements in green / yellow / red categories.
        g_avg, y_avg, r_avg: Mean percentages within each category
                             (useful for diagnostics and tie-breaking logic).
        details: Per-requirement breakdown of contributions.
    """

    color_score: float
    percent_score: float
    g: int
    y: int
    r: int
    details: List[RequirementDetail] = field(default_factory=list)
    g_avg: float = 0.0
    y_avg: float = 0.0
    r_avg: float = 0.0

    @property
    def n(self) -> int:
        """Total number of requirements in this block."""
        return self.g + self.y + self.r

    @property
    def coverage(self) -> float:
        """
        Structural coverage: fraction of requirements that are at least partially met.

        This corresponds to (g + y) / N in the mathematical description.
        """
        total = self.n
        if total == 0:
            return 0.0
        return float(self.g + self.y) / float(total)


@dataclass
class ItemInput:
    """
    Input data for a single item to be ranked.

    Attributes:
        item_id: Stable identifier of the item (string or numeric identifier).
        mandatory: List of requirements in the "mandatory" block.
        preferred: List of requirements in the "preferred" block.
        tasks: List of requirements in the "tasks" block.
        metadata: Optional arbitrary payload associated with the item
                  (e.g. external IDs, textual description, etc.).
    """

    item_id: str
    mandatory: List[Requirement] = field(default_factory=list)
    preferred: List[Requirement] = field(default_factory=list)
    tasks: List[Requirement] = field(default_factory=list)
    metadata: Optional[dict] = None


@dataclass
class ItemScore:
    """
    Full scoring result for a single item.

    Attributes:
        item_id: Identifier copied from the input.
        mandatory, preferred, tasks: Block-level scores.
        final_color_score: Aggregated ColorScore over blocks (Phase 1).
        final_percent_score: Aggregated PercentScore over blocks (Phase 2).
        used_weights: Effective weights used for each block, after
                      potential redistribution for empty blocks.
        rank: Optional rank position after global sorting (1 = best).
    """

    item_id: str
    mandatory: BlockScore
    preferred: BlockScore
    tasks: BlockScore
    final_color_score: float
    final_percent_score: float
    used_weights: Dict[BlockType, float] = field(default_factory=dict)
    rank: Optional[int] = None

    @property
    def mandatory_coverage(self) -> float:
        """Convenience accessor for coverage within the mandatory block."""
        return self.mandatory.coverage if self.mandatory is not None else 0.0

    @property
    def average_coverage(self) -> float:
        """
        Average coverage over all non-empty blocks.

        This is a diagnostic metric and is not used in the primary ranking.
        """
        coverages: List[float] = []
        for block in (self.mandatory, self.preferred, self.tasks):
            if block is not None and block.n > 0:
                coverages.append(block.coverage)
        if not coverages:
            return 0.0
        return sum(coverages) / float(len(coverages))

