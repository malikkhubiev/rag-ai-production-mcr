"""
Configuration constants for the ranking algorithm.

The values here mirror the mathematical description in ``math.md``:
they define thresholds for confidence categories, per-category weights,
and default importance weights for the three blocks of criteria.
"""

# Category thresholds (see "Confidence categories" in math.md)
# High (green):   >= 70%
# Partial (yellow): 30–69%
# Low (red):       < 30%
GREEN_THRESHOLD: int = 70
YELLOW_THRESHOLD: int = 30


# Category contribution weights (see "Contribution of categories" in math.md)
GREEN_WEIGHT: float = 1.0
YELLOW_WEIGHT: float = 0.5
RED_WEIGHT: float = 0.01


# Default block weights (see "Block weights" / "Strategy modes" in math.md)
# Here we use a flexible profile configuration as the default:
# base block is important, but additional blocks can also have impact.
MANDATORY_WEIGHT: float = 1.0
PREFERRED_WEIGHT: float = 0.2
TASKS_WEIGHT: float = 0.2


# Numerical tolerance for comparing floating point scores in sorting
EPSILON: float = 1e-6

