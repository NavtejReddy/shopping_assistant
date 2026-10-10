import asyncio
from decimal import Decimal
from pathlib import Path
from time import monotonic
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from fastmcp import Client
import httpx
from openai import AsyncOpenAI
from pydantic import ValidationError

from shopping_assistant.config import Settings
from shopping_assistant.decisions import DecisionsEvaluator
from shopping_assistant.extraction import DEFAULT_URL, Extraction, ExtractionError, fetch_products, parse_products, validate_url
from shopping_assistant.models import CriterionResult, FilterSpec, Product, SearchRequest
from shopping_assistant.pipeline import combine, evaluate_products, price_results
from shopping_assistant.server import mcp

FIXTURE = Path(__file__).parent / "fixtures/laptops.html"


def product(price="500.00", currency="USD"):
    return Product(id="1", name="Test laptop", url="https://webscraper.io/test-sites/e-commerce/allinone/product/1",
                   description="8GB RAM, 128GB SSD", price=price, currency=currency)


def outcome(name="requirement_0", value="match", mandatory=True):
    return CriterionResult(name=name, criterion="Has SSD", mandatory=mandatory,
                           outcome=value, source="decisions", note="Test classification")


class ExtractionTests(unittest.TestCase):
    def test_real_fixture(self):
        extracted = parse_products(FIXTURE.read_text(), DEFAULT_URL)
        self.assertEqual(len(extracted.products), 117)
        self.assertEqual(extracted.skipped, 0)
        first = extracted.products[0]
        self.assertEqual(first.name, "Asus VivoBook X441NA-GA190")
        self.assertEqual(first.price, Decimal("295.99"))
        self.assertEqual(first.currency, "USD")
        self.assertIn("4GB", first.description)
        self.assertTrue(first.url.endswith("/product/60"))

    def test_reject_untrusted_urls(self):
        for url in ["http://127.0.0.1/", DEFAULT_URL + "?redirect=x", DEFAULT_URL + "#x",
                    DEFAULT_URL.replace("webscraper.io", "webscraper.io.evil.com"),
                    DEFAULT_URL.replace("https://", "https://user@"),
                    DEFAULT_URL.replace("webscraper.io", "webscraper.io:8443"),
                    DEFAULT_URL + "/../private", "file:///etc/passwd"]:
            with self.subTest(url=url), self.assertRaises(ExtractionError):
                validate_url(url)

    def test_missing_price_duplicate_and_hostile_links(self):
        card = '<div class="thumbnail"><a class="title" href="/test-sites/e-commerce/allinone/product/1">Laptop</a></div>'
        bad = '<div class="thumbnail"><a class="title" href="https://evil.test/">Bad</a></div>'
        result = parse_products(card + card + bad, DEFAULT_URL)
        self.assertEqual(len(result.products), 1)
        self.assertIsNone(result.products[0].price)
        self.assertIsNone(result.products[0].currency)
        self.assertEqual(result.skipped, 1)

    def test_layout_change(self):
        with self.assertRaises(ExtractionError):
            parse_products("<html>No products</html>", DEFAULT_URL)


class FilterTests(unittest.TestCase):
    def test_strict_price_boundary(self):
        for op, expected in [("lt", "no_match"), ("lte", "match"), ("gt", "no_match"), ("gte", "match")]:
            spec = FilterSpec(price=[{"operator": op, "amount": "500.00"}])
            self.assertEqual(price_results(product(), spec)[0].outcome, expected)

    def test_missing_or_wrong_currency_is_unknown(self):
        spec = FilterSpec(price=[{"operator": "lt", "amount": "800"}])
        for item in [product(price=None), product(currency=None), product(currency="INR")]:
            self.assertEqual(price_results(item, spec)[0].outcome, "insufficient_information")

    def test_invalid_filters(self):
        for data in [{}, {"requirements": [" "]}, {"requirements": ["SSD", "SSD"]},
                     {"price": [{"operator": "lt", "amount": "NaN"}]},
                     {"price": [{"operator": "lt", "amount": "800", "currency": "INR"}]},
                     {"price": [{"operator": "gt", "amount": "800"}, {"operator": "lte", "amount": "800"}]}]:
            with self.subTest(data=data), self.assertRaises(ValidationError):
                FilterSpec.model_validate(data)

    def test_preferences_cannot_override_requirements(self):
        result = combine(product(), [outcome(value="no_match"), outcome("preference_0", "match", False)])
        self.assertEqual(result.status, "no_match")

    def test_preference_failure_does_not_exclude(self):
        result = combine(product(), [outcome(), outcome("preference_0", "no_match", False)])
        self.assertEqual(result.status, "match")

    def test_unknown_and_error_are_separate(self):
        self.assertEqual(combine(product(), [outcome(value="insufficient_information")]).status, "insufficient_information")
        self.assertEqual(combine(product(), [outcome(value="error")]).status, "error")


class AsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_redirect_not_followed(self):
        requests = []
        def handler(request):
            requests.append(request)
            return httpx.Response(302, headers={"location": "http://127.0.0.1/"})
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with self.assertRaises(ExtractionError):
                await fetch_products(DEFAULT_URL, client)
        self.assertEqual(len(requests), 1)

    async def test_actual_http_fetch_parser_integration(self):
        async with httpx.AsyncClient(transport=httpx.MockTransport(
            lambda _: httpx.Response(200, text=FIXTURE.read_text(), headers={"content-type": "text/html"})
        )) as client:
            result = await fetch_products(DEFAULT_URL, client)
        self.assertEqual(len(result.products), 117)

    async def test_price_rejection_skips_ai(self):
        evaluator = SimpleNamespace(evaluate=AsyncMock())
        request = SearchRequest(url=DEFAULT_URL, filter={"price": [{"operator": "lt", "amount": "400"}], "requirements": ["SSD"]})
        result = await evaluate_products(Extraction([product()], 0), request, Settings(), evaluator, "now", monotonic())
        evaluator.evaluate.assert_not_awaited()
        self.assertEqual(result.counts["no_match"], 1)

    async def test_cap_counts_and_return_limit(self):
        evaluator = SimpleNamespace(evaluate=AsyncMock(return_value=[outcome()]))
        request = SearchRequest(url=DEFAULT_URL, filter={"requirements": ["SSD"]}, result_limit=1)
        result = await evaluate_products(Extraction([product()] * 4, 0), request, Settings(max_products=2), evaluator, "now", monotonic())
        self.assertEqual(result.products_checked, 2)
        self.assertEqual(result.products_not_checked, 2)
        self.assertEqual(result.counts["match"], 2)
        self.assertEqual(len(result.matches), 1)
        self.assertTrue(result.results_truncated)
        self.assertFalse(result.complete)

    async def test_deadline_cancels_and_marks_errors(self):
        async def slow(*args):
            await asyncio.sleep(5)
        evaluator = SimpleNamespace(evaluate=slow)
        request = SearchRequest(url=DEFAULT_URL, filter={"requirements": ["SSD"]})
        result = await evaluate_products(Extraction([product()], 0), request,
                                         Settings(search_timeout=0.01), evaluator, "now", monotonic())
        self.assertEqual(result.counts["error"], 1)
        self.assertFalse(result.complete)

    async def test_decisions_maps_answers_by_name(self):
        response = SimpleNamespace(model_dump=lambda: {"answers": [
            {"type": "choice", "name": "preference_0", "choice": "no_match"},
            {"type": "choice", "name": "requirement_0", "choice": "match"},
        ]})
        create = AsyncMock(return_value=response)
        evaluator = DecisionsEvaluator(SimpleNamespace(decisions=SimpleNamespace(create=create)), 2)
        values = await evaluator.evaluate(product(), FilterSpec(requirements=["SSD"], preferences=["Black"]))
        self.assertEqual([v.outcome for v in values], ["match", "no_match"])
        self.assertEqual(create.call_args.kwargs["model"], "gpt-6-luna")

    async def test_invalid_decisions_are_errors(self):
        for answers in [[], [{"name": "requirement_0", "type": "refusal"}],
                        [{"name": "requirement_0", "type": "choice", "choice": "invented"}],
                        [{"name": "requirement_0", "type": "choice", "choice": "match"}] * 2]:
            create = AsyncMock(return_value=SimpleNamespace(model_dump=lambda: {"answers": answers}))
            evaluator = DecisionsEvaluator(SimpleNamespace(decisions=SimpleNamespace(create=create)), 1)
            values = await evaluator.evaluate(product(), FilterSpec(requirements=["SSD"]))
            self.assertEqual(values[0].outcome, "error")

    async def test_sdk_request_and_provider_failure(self):
        # Exercise the installed SDK's own HTTP stack without network or credentials.
        import httpx2
        seen = []
        def handler(request):
            seen.append(request)
            return httpx2.Response(429, json={"error": {"message": "test rate limit"}})
        async with AsyncOpenAI(api_key="test", max_retries=0,
                               http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler))) as client:
            values = await DecisionsEvaluator(client, 1).evaluate(product(), FilterSpec(requirements=["SSD"]))
        self.assertEqual(values[0].outcome, "error")
        self.assertEqual(seen[0].url.path, "/v1/decisions")

    async def test_mcp_discovery_and_structured_response(self):
        request = SearchRequest(url=DEFAULT_URL, filter={"requirements": ["SSD"]})
        evaluator = SimpleNamespace(evaluate=AsyncMock(return_value=[outcome()]))
        expected = await evaluate_products(Extraction([product()], 0), request, Settings(), evaluator, "now", monotonic())
        with patch("shopping_assistant.server.search", AsyncMock(return_value=expected)):
            async with Client(mcp) as client:
                tools = await client.list_tools()
                self.assertEqual([tool.name for tool in tools], ["filter_products"])
                result = await client.call_tool("filter_products", request.model_dump(mode="json"))
                self.assertEqual(result.structured_content["counts"]["match"], 1)
                self.assertEqual(result.structured_content["matches"][0]["product"]["url"], product().url)

    async def test_mcp_rejects_unsupported_site_before_search(self):
        async with Client(mcp) as client:
            result = await client.call_tool("filter_products", {
                "url": "http://127.0.0.1", "filter": {"requirements": ["SSD"]}
            }, raise_on_error=False)
            self.assertTrue(result.is_error)


if __name__ == "__main__":
    unittest.main()
