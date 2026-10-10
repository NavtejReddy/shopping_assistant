import asyncio
from datetime import datetime, timezone
import operator
from time import monotonic
from typing import Protocol

import httpx
from openai import AsyncOpenAI

from .config import Settings, load_settings
from .decisions import DecisionsEvaluator, failed_criteria
from .extraction import Extraction, fetch_products, validate_url
from .models import CriterionResult, FilterSpec, Product, ProductResult, SearchRequest, SearchResult


class Evaluator(Protocol):
    async def evaluate(self, product: Product, spec: FilterSpec) -> list[CriterionResult]: ...


def price_results(product: Product, spec: FilterSpec) -> list[CriterionResult]:
    operations = {"lt": operator.lt, "lte": operator.le, "gt": operator.gt, "gte": operator.ge}
    results = []
    for i, condition in enumerate(spec.price):
        if product.price is None or product.currency != condition.currency:
            outcome = "insufficient_information"
            note = "Price is missing or its currency cannot be compared; no currency conversion was performed."
        else:
            outcome = "match" if operations[condition.operator](product.price, condition.amount) else "no_match"
            note = f"Listed price is {product.price} {product.currency}; excludes unlisted taxes and shipping."
        results.append(CriterionResult(
            name=f"price_{i}", criterion=f"Price {condition.operator} {condition.amount} {condition.currency}",
            mandatory=True, outcome=outcome, source="code", note=note,
        ))
    return results


def combine(product: Product, criteria: list[CriterionResult]) -> ProductResult:
    required = [c.outcome for c in criteria if c.mandatory]
    if "no_match" in required:
        status = "no_match"
    elif "error" in required or (not required and any(c.outcome == "error" for c in criteria)):
        status = "error"
    elif "insufficient_information" in required:
        status = "insufficient_information"
    elif not required and not any(c.outcome == "match" for c in criteria):
        status = "insufficient_information"
    else:
        status = "match"
    return ProductResult(product=product, status=status, criteria=criteria,
                         preference_matches=sum(not c.mandatory and c.outcome == "match" for c in criteria))


async def evaluate_products(extraction: Extraction, request: SearchRequest, settings: Settings,
                            evaluator: Evaluator, fetched_at: str, started: float) -> SearchResult:
    selected = extraction.products[:settings.max_products]
    semaphore = asyncio.Semaphore(settings.concurrency)

    async def evaluate(product: Product) -> ProductResult:
        criteria = price_results(product, request.filter)
        if any(c.outcome == "no_match" for c in criteria):
            return combine(product, criteria)
        async with semaphore:
            criteria += await evaluator.evaluate(product, request.filter)
        return combine(product, criteria)

    tasks = [asyncio.create_task(evaluate(p)) for p in selected]
    remaining = max(0, settings.search_timeout - (monotonic() - started))
    try:
        _, pending = await asyncio.wait(tasks, timeout=remaining)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        results = []
        for product, task in zip(selected, tasks):
            if task.cancelled():
                criteria = price_results(product, request.filter)
                criteria += failed_criteria(request.filter, "Search deadline reached before this product's evaluation completed.")
                results.append(combine(product, criteria))
            else:
                results.append(task.result())
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    # Equal-weight preference count; preserve listing order for ties.
    results.sort(key=lambda result: -result.preference_matches)
    groups = {status: [r for r in results if r.status == status]
              for status in ("match", "no_match", "insufficient_information", "error")}
    unchecked = len(extraction.products) - len(selected)
    errors = sum(any(c.outcome == "error" for c in r.criteria) for r in results)
    warnings = ["Demo catalog only. Prices and descriptions are listing snapshots, not verified current offers."]
    if unchecked:
        warnings.append(f"Product cap reached: only the first {len(selected)} of {len(extraction.products)} extracted products were checked.")
    if extraction.skipped:
        warnings.append(f"Skipped {extraction.skipped} malformed product cards.")
    if errors:
        warnings.append(f"{errors} products have evaluation errors; these are not evidence of a mismatch.")
    if not request.filter.price and not request.filter.requirements:
        warnings.append("Only preferences were provided. Matches indicate at least one supported preference, not mandatory eligibility.")
    return SearchResult(
        source_url=validate_url(request.url), fetched_at=fetched_at, applied_filter=request.filter,
        products_found=len(extraction.products), products_checked=len(selected), products_not_checked=unchecked,
        extraction_skipped=extraction.skipped, counts={k: len(v) for k, v in groups.items()},
        matches=groups["match"][:request.result_limit], uncertain=groups["insufficient_information"][:request.result_limit],
        errors=groups["error"][:request.result_limit], excluded=groups["no_match"][:request.result_limit],
        results_truncated=any(len(v) > request.result_limit for v in groups.values()),
        complete=not (unchecked or extraction.skipped or errors), elapsed_seconds=round(monotonic() - started, 3),
        warnings=warnings,
    )


async def search(request: SearchRequest, settings: Settings | None = None) -> SearchResult:
    settings = settings or load_settings()
    url = validate_url(request.url)
    needs_ai = bool(request.filter.requirements or request.filter.preferences)
    if needs_ai and not settings.api_key.get_secret_value():
        raise ValueError("OPENAI_API_KEY is required for semantic filtering. Set it in the project's .env file.")
    started = monotonic()
    async with httpx.AsyncClient(timeout=settings.request_timeout, trust_env=False) as http:
        extraction = await fetch_products(url, http)
    fetched_at = datetime.now(timezone.utc).isoformat()
    # Price-only searches don't send API requests or require an API key.
    async with AsyncOpenAI(api_key=settings.api_key.get_secret_value() or "unused",
                           timeout=settings.request_timeout, max_retries=1) as client:
        return await evaluate_products(extraction, request, settings,
                                       DecisionsEvaluator(client, settings.concurrency), fetched_at, started)
