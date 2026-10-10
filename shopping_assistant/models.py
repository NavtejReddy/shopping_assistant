from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Outcome = Literal["match", "no_match", "insufficient_information", "error"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PriceConstraint(StrictModel):
    operator: Literal["lt", "lte", "gt", "gte"]
    amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: Literal["USD"] = "USD"


class FilterSpec(StrictModel):
    price: list[PriceConstraint] = Field(default_factory=list, max_length=2)
    requirements: list[Text] = Field(default_factory=list, max_length=8)
    preferences: list[Text] = Field(default_factory=list, max_length=4)

    @model_validator(mode="after")
    def valid_filter(self):
        if not (self.price or self.requirements or self.preferences):
            raise ValueError("Supply at least one price condition, requirement, or preference.")
        for items in (self.requirements, self.preferences):
            if len(set(items)) != len(items):
                raise ValueError("Duplicate criteria are not allowed.")
        lower = [p for p in self.price if p.operator in ("gt", "gte")]
        upper = [p for p in self.price if p.operator in ("lt", "lte")]
        if lower and upper:
            lo, hi = lower[0], upper[0]
            if lo.amount > hi.amount or (lo.amount == hi.amount and (lo.operator == "gt" or hi.operator == "lt")):
                raise ValueError("Price conditions describe an empty range.")
        return self


class SearchRequest(StrictModel):
    url: str = Field(max_length=2048)
    filter: FilterSpec
    result_limit: int = Field(default=10, ge=1, le=50)


class Product(StrictModel):
    id: str
    name: str
    url: str
    description: str
    price: Decimal | None = None
    currency: str | None = None


class CriterionResult(StrictModel):
    name: str
    criterion: str
    mandatory: bool
    outcome: Outcome
    source: Literal["code", "decisions"]
    note: str


class ProductResult(StrictModel):
    product: Product
    status: Outcome
    criteria: list[CriterionResult]
    preference_matches: int = 0


class SearchResult(StrictModel):
    source_url: str
    fetched_at: str
    applied_filter: FilterSpec
    products_found: int
    products_checked: int
    products_not_checked: int
    extraction_skipped: int
    counts: dict[str, int]
    matches: list[ProductResult]
    uncertain: list[ProductResult]
    errors: list[ProductResult]
    excluded: list[ProductResult]
    results_truncated: bool
    complete: bool
    elapsed_seconds: float
    warnings: list[str]
