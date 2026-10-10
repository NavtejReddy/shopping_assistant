import asyncio
from decimal import Decimal
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup
from fastmcp import Client
import httpx

from shopping_assistant.demo_shop import ShopServer
from shopping_assistant.extraction import DEMO_URL, ExtractionError, parse_products, validate_url
from shopping_assistant.server import mcp


class DemoShopTests(unittest.TestCase):
    def test_demo_url_is_opt_in_and_narrow(self):
        with patch.dict(os.environ, {"SHOPPING_DEMO_ENABLED": "0"}):
            with self.assertRaises(ExtractionError):
                validate_url(DEMO_URL)
        with patch.dict(os.environ, {"SHOPPING_DEMO_ENABLED": "1"}):
            self.assertEqual(validate_url(DEMO_URL + "/"), DEMO_URL)
            for url in [DEMO_URL + "?x=1", DEMO_URL.replace("127.0.0.1", "localhost"),
                        DEMO_URL.replace("8765", "8000"), DEMO_URL.replace("/laptops", "/admin")]:
                with self.subTest(url=url), self.assertRaises(ExtractionError):
                    validate_url(url)

    def test_persisted_price_edit_through_real_mcp_and_reset(self):
        # Ephemeral server port isolates test data from the presenter's running shop.
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"SHOPPING_DEMO_ENABLED": "1"}):
            state = Path(directory) / "prices.json"
            server = ShopServer(("127.0.0.1", 0), state)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            origin = f"http://127.0.0.1:{server.server_port}"
            try:
                with httpx.Client(base_url=origin, trust_env=False) as http:
                    editor = http.get("/admin")
                    self.assertEqual(editor.status_code, 200)
                    token = BeautifulSoup(editor.text, "html.parser").select_one('[name="token"]')["value"]
                    def extracted():
                        response = http.get("/laptops")
                        self.assertEqual(response.headers["cache-control"], "no-store")
                        return parse_products(response.text, DEMO_URL)
                    async def result():
                        # Route only the HTTP connection to the isolated test server;
                        # retain the production URL validator, parser, pipeline and MCP.
                        async def test_fetch(url, client):
                            async with httpx.AsyncClient(base_url=origin, trust_env=False) as local:
                                response = await local.get("/laptops")
                            return parse_products(response.text, url)
                        with patch("shopping_assistant.pipeline.fetch_products", test_fetch):
                            async with Client(mcp) as client:
                                response = await client.call_tool("filter_products", {
                                    "url": DEMO_URL,
                                    "filter": {"price": [{"operator": "lt", "amount": "800"}]}
                                })
                                return response.structured_content
                    before = asyncio.run(result())
                    self.assertEqual(before["counts"]["match"], 3)
                    self.assertNotIn("1", [r["product"]["id"] for r in before["matches"]])
                    self.assertEqual(http.post("/admin/price", data={"id": "1", "price": "750"}).status_code, 403)
                    for price in ["NaN", "-1", "1.234", "1000000"]:
                        self.assertEqual(http.post("/admin/price", data={"token": token, "id": "1", "price": price}).status_code, 400)
                    payload = {"token": token, "id": "1", "price": "750"}
                    self.assertEqual(http.post("/admin/price", data=payload, headers={"Origin": "https://evil.example"}).status_code, 403)
                    self.assertEqual(http.post("/admin/price", data=payload).status_code, 303)
                    self.assertEqual(extracted().products[0].price, Decimal("750.00"))
                    after = asyncio.run(result())
                    self.assertEqual(after["counts"]["match"], 4)
                    self.assertIn("1", [r["product"]["id"] for r in after["matches"]])
                    self.assertEqual(http.get("/product/1").status_code, 200)
                    self.assertEqual(http.get("/missing").status_code, 404)
                    # A second server instance reads the persisted price without reseeding.
                    with ShopServer(("127.0.0.1", 0), state) as reopened:
                        self.assertEqual(reopened.products()[0]["price"], "750.00")
                    self.assertEqual(http.post("/admin/reset", data={"token": token}).status_code, 303)
                    self.assertEqual(extracted().products[0].price, Decimal("950.00"))
                    self.assertEqual(asyncio.run(result())["counts"]["match"], 3)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


if __name__ == "__main__":
    unittest.main()
