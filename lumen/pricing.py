"""Pure price estimation used by dry-run and paid providers."""

from __future__ import annotations

from lumen.contracts import BudgetConfig


def estimate_video_cost(
    config: BudgetConfig,
    model: str,
    resolution: str,
    duration: float,
) -> float:
    try:
        per_second = config.pricing.video_cny_per_second[model][resolution]
    except KeyError as exc:
        raise ValueError(f"no video price configured for {model} at {resolution}") from exc
    return round(per_second * duration * config.pricing.discount_multiplier, 2)


def estimate_image_cost(config: BudgetConfig, count: int = 1) -> float:
    if count < 0:
        raise ValueError("image count must be non-negative")
    return round(
        config.pricing.image_cny_each * count * config.pricing.discount_multiplier,
        2,
    )
