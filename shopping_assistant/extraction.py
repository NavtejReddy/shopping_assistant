from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
import os
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
import httpx

BASE_URL = "https://webscraper.io"
DEFAULT_URL = BASE_URL + "/test-sites/e-commerce/allinone/computers/laptops"
DEMO_ORIGIN = "http://127.0.0.1:8765"
DEMO_URL = DEMO_ORIGIN + "/laptops"
ALLOWED_PATHS = {
    "/test-sites/e-commerce/allinone/computers/laptops",
    "/test-sites/e-commerce/allinone/computers/tablets",
    "/test-sites/e-commerce/allinone/phones/touch",
}

from .models import Product


class ExtractionError(ValueError):
    pass


def validate_url(url: str) -> str:
    if os.getenv("SHOPPING_DEMO_ENABLED") == "1" and url in (DEMO_URL, DEMO_URL + "/"):
        return DEMO_URL
    try:
        parts = urlsplit(url)
        valid = (
            parts.scheme == "https" and parts.hostname == "webscraper.io"
            and parts.port in (None, 443) and parts.username is None
            and parts.password is None and not parts.query and not parts.fragment
            and parts.path.rstrip("/") in ALLOWED_PATHS
        )
    except ValueError:
        valid = False
    if not valid:
        raise ExtractionError("Unsupported URL. Use an HTTPS Web Scraper allinone laptops, tablets, or phones/touch listing, or http://127.0.0.1:8765/laptops with SHOPPING_DEMO_ENABLED=1. No query parameters.")
    return urlunsplit(("https", "webscraper.io", parts.path.rstrip("/"), "", ""))


@dataclass
class Extraction:
    products: list[Product]
    skipped: int


def parse_products(html: str, source_url: str) -> Extraction:
    source_url = validate_url(source_url)
    soup = BeautifulSoup(html, "html.parser")
    products, seen, skipped = [], set(), 0
    for card in soup.select(".thumbnail"):
        link = card.select_one("a.title[href]")
        if not link:
            skipped += 1
            continue
        url = urljoin(source_url, str(link.get("href")))
        parts = urlsplit(url)
        source = urlsplit(source_url)
        product_path = r"/product/\d+" if source_url == DEMO_URL else r"/test-sites/e-commerce/allinone/product/\d+"
        if (parts.scheme != source.scheme or parts.netloc != source.netloc
                or not re.fullmatch(product_path, parts.path)
                or parts.query or parts.fragment):
            skipped += 1
            continue
        if url in seen:
            continue
        name = str(link.get("title") or link.get_text(" ", strip=True)).strip()
        if not name:
            skipped += 1
            continue
        price_node = card.select_one('[itemprop="price"]') or card.select_one(".price")
        price = None
        if price_node:
            raw = price_node.get_text(strip=True)
            if re.fullmatch(r"\$?\s*\d[\d,]*(?:\.\d{1,2})?", raw):
                try:
                    price = Decimal(raw.replace("$", "").replace(",", "").strip())
                except InvalidOperation:
                    pass
        currency_node = card.select_one('[itemprop="priceCurrency"]')
        currency = str(currency_node.get("content")) if currency_node and currency_node.get("content") else None
        # USD is explicit in this site's product metadata; don't guess from '$'.
        description = card.select_one(".description")
        products.append(Product(
            id=parts.path.rsplit("/", 1)[-1], name=name[:500], url=url,
            description=description.get_text(" ", strip=True)[:8000] if description else "",
            price=price, currency=currency,
        ))
        seen.add(url)
    if not products:
        raise ExtractionError("No valid product cards found. The page may be unavailable or its layout may have changed.")
    return Extraction(products, skipped)


async def fetch_products(url: str, client: httpx.AsyncClient) -> Extraction:
    url = validate_url(url)
    try:
        # Never follow redirects to a different origin or an unapproved path.
        async with client.stream("GET", url, follow_redirects=False) as response:
            response.raise_for_status()
            if "text/html" not in response.headers.get("content-type", ""):
                raise ExtractionError("The listing did not return an HTML page.")
            body = bytearray()
            async for chunk in response.aiter_bytes():
                body.extend(chunk)
                if len(body) > 3_000_000:
                    raise ExtractionError("The listing exceeds the 3 MB extraction limit.")
    except httpx.HTTPError as exc:
        raise ExtractionError("Could not fetch the supported listing. Please retry later.") from exc
    return parse_products(body.decode("utf-8", errors="replace"), url)
