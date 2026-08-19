from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PricingSnapshot(BaseModel):
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    timestamp_utc: datetime
    currency: str = Field(default="USD", min_length=3, max_length=3)

    input_price_per_million_tokens: float = Field(ge=0)
    output_price_per_million_tokens: float = Field(ge=0)

    cached_input_price_per_million_tokens: float | None = Field(
        default=None,
        ge=0,
    )

    reasoning_price_per_million_tokens: float | None = Field(
        default=None,
        ge=0,
    )

    source_reference: str | None = None
