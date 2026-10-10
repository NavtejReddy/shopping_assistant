# Shopping Assistant

Describe what you need once, then turn a catalog into a shortlist you can inspect. Shopping Assistant converts confirmed shopping requirements into matching product links, combining exact budget checks with natural-language evaluation of product descriptions.

For example: **“Find laptops under $800 with at least 16GB RAM and SSD storage.”** ChatGPT constructs the filter, the MCP backend checks listed prices in code, and OpenAI Decisions (`gpt-6-luna`) evaluates semantic requirements. Missing facts remain explicit instead of becoming guessed specifications. A connected dot can reuse the same filter for follow-up searches; scheduling is provided by the host, not this backend.

## Why this project matters

### Usefulness: turn a shopping brief into an actionable shortlist

Shopping requirements combine hard constraints, such as budget, with preferences and details buried in descriptions. This project lets a user express those requirements together, confirm the interpretation, and receive product links with per-criterion outcomes. Separating mandatory requirements from preferences keeps an attractive optional feature from overriding a deal-breaker.

The price-change walkthrough makes the benefit concrete: Atlas Air 14 starts at $950 and becomes budget-eligible after a change to $750. Reusing the original filter lets the user check what now qualifies without restating the shopping brief. The current prototype supports specific test catalogs; usefulness on arbitrary retailers and time saved by real shoppers have not been measured.

### Technical execution: use code and AI where each fits

Prices use decimal comparisons, including the difference between “under” and “at most.” Decisions handles natural-language criteria against supplied product evidence. Exact rejections skip semantic API calls, and each remaining product groups its semantic questions into one request. Bounded concurrency, product caps, deadlines, and explicit error outcomes keep the execution inspectable.

The integration is a working MCP tool plus a packaged skill that guides confirmation and result presentation. Review the [filtering pipeline](shopping_assistant/pipeline.py), [Decisions adapter](shopping_assistant/decisions.py), [MCP server](shopping_assistant/server.py), and [shopping skill](plugins/shopping-assistant/skills/shopping-assistant/SKILL.md). This submission does not claim a custom sidebar extension, an Agents API integration, or MCP event triggers.

### Originality: preserve the shopping intent and uncertainty across checks

The distinctive design is the combination of a conversational shopping brief, deterministic budget enforcement, evidence-based semantic classification, and a reusable filter for later searches. A missing specification produces an uncertain result; a provider failure remains an error. Neither is silently presented as a product rejection.

This is a specific workflow contribution, not a claim that shopping assistants or price alerts are new. The opportunity is to carry the same user-confirmed requirements from an initial shortlist into ongoing checks through a connected dot.

### How well it works: provide reproducible evidence

The project has 22 locally passing tests covering extraction, filter validation, price boundaries, uncertainty, provider failures, deadlines, result caps, MCP output, and a local price-change integration. A clean installation passed the suite without API credentials. See [engine tests](tests/test_shopping.py), [storefront integration tests](tests/test_demo_shop.py), and the [CI workflow](.github/workflows/tests.yml).

Live checks also exercised HTTP and stdio MCP discovery, public-catalog extraction, and a three-product Decisions smoke test. These checks establish working paths, not a broad semantic-accuracy benchmark. The [repeatable walkthrough](#repeatable-price-change-walkthrough) explains the expected price-only transition from three matches to four. Daily dot notifications and skill behavior inside ChatGPT are not established by the automated tests and require separate host-level verification.

## Potential market impact: shopping through ChatGPT and personal dots

Shopping Assistant points toward a shift in the shopping interface: from browsing
storefronts and repeatedly adjusting filters to expressing intent through ChatGPT
and delegating follow-up to a personal dot. The ambition is for a shopper's own
dot to become the primary interface for discovery, comparison, and monitoring,
bringing relevant choices back into the conversation when they fit the brief.

In that experience, the shopper describes their needs, budget, and preferences
once. Their dot carries those requirements across subsequent checks and presents
actionable options. Retailer websites become underlying sources of product
information rather than the place where every shopping journey must begin.
The shopper stays in control of decisions and purchases.

This could disrupt how products are discovered and how retailers earn attention.
Shoppers could spend less time repeating searches, while retailers with clear,
accurate product information could compete on how well their products satisfy a
specific need. The opportunity is a personal shopping relationship built around
the buyer's intent, rather than each store's navigation and filter interface.

The current catalog-filtering plugin is the first building block of that vision.
Expanding it into a broad shopping service would require retailer integrations,
reliable inventory and price updates, persistent shopping preferences, and
user-authorized transaction workflows. Market adoption and commercial impact
are hypotheses to test as that coverage grows.

### Dollar-scale opportunity

**A $1.23 trillion U.S. online retail market provides the backdrop for this
opportunity.** The U.S. Census Bureau's March 2026 release estimated 2025 retail
e-commerce sales at **$1,233.7 billion**. This measures retail transaction value,
not the revenue available to a shopping assistant.
[Source: U.S. Census Bureau, Q4 2025 release](https://www2.census.gov/retail/releases/historical/ecomm/25q4.pdf).

To illustrate the scale, if a future service influenced **0.01%** of that annual
spending, it would help direct approximately **$123 million in purchases**.
At **0.1%**, that becomes approximately **$1.23 billion**. Assuming all those
purchases were eligible for an illustrative **2% referral fee**, the respective
annual gross revenues would be approximately **$2.47 million** and **$24.67 million**,
before operating costs, refunds, and acquisition costs.

A separate subscription scenario—**10,000 paying users at $10 per month**—would
produce **$1.2 million in annual recurring revenue**, before costs and churn.
These are transparent scenario calculations, not forecasts, current traction,
company valuations, or estimates of this prototype's addressable market.
They show why moving even a small share of shopping discovery into ChatGPT and
personal dots could support a meaningful business as retailer coverage expands.

### Startup opportunity and business value

The startup opportunity is a personal shopping agent that maintains the customer
relationship across retailers. If discovery moves into ChatGPT and personal dots,
the agent could become the starting point for comparison and repeat purchases.
Retailers would compete to satisfy the shopper's stated requirements through
accurate, accessible product information.

Potential business models include:

- **Consumer subscriptions:** ongoing monitoring of complex shopping needs,
  price changes, and newly matching products.
- **Retailer integrations:** connections to structured product and inventory
  feeds that help personal dots discover and evaluate relevant offers.
- **Referral revenue:** disclosed commissions on resulting purchases, while
  keeping ranking aligned with the shopper's requirements rather than commission size.
- **Shopping infrastructure:** an API that provides evidence-based product
  filtering to other agents and applications.

Long-term business value would come from reliable retailer coverage,
user-controlled preference history, and measured recommendation quality.
Together, these could make the service more useful with repeated use and harder
to replace than a standalone model API wrapper. These are potential commercial
directions for the product, not current revenue streams.

## Measured semantic results

On October 10, 2026, the production Decisions adapter matched all **12 of 12**
expected labels in the authored semantic regression set, with **zero API errors**.
The run took **5.84 seconds** for the 12 sequential calls. Cases cover explicit
matches, contradictions, missing facts, ambiguous configurations, preferences,
AND/OR requirements, and an instruction embedded in product text.

The initial run scored 11/12 and exposed a negation error. Clarifying the prompt's
handling of explicitly absent features corrected that case in the subsequent run.
Both [baseline](evaluations/baseline.json) and [updated results](evaluations/latest.json)
are included. This is a small development regression set used to improve the
prompt, not held-out accuracy or a general shopping benchmark.
[Run it yourself](docs/evaluation.md#semantic-evaluation-requires-api-access).

## Product walkthrough

https://github.com/user-attachments/assets/950b7fef-8d07-4d82-97dd-15e2661a9fb5

[Watch or download the 60-second video (MP4)](docs/media/shopping-assistant.mp4).

[Read the text walkthrough](docs/walkthrough.md) · [Reproduce the results](docs/evaluation.md) · [Inspect semantic evaluation cases](evaluations/semantic-cases.json)

## Recommended workflow

**The intended end-to-end workflow is ChatGPT + the Shopping Assistant plugin + Decisions, with optional daily dot checks.** Filtering is implemented in this repository; recurring follow-up depends on a connected dot and a saved schedule. The steps below describe how to combine them, not evidence that a daily notification has already completed.

1. **Tell ChatGPT what you need.** Provide a supported catalog URL, budget, mandatory requirements, and optional preferences.
2. **Confirm the criteria.** ChatGPT turns your request into a structured filter before invoking the plugin.
3. **Let the plugin evaluate the catalog.** Code checks exact prices; OpenAI Decisions evaluates product descriptions against your requirements. Missing facts and failed checks stay explicit.
4. **Ask your dot to check every day.** Reuse the same confirmed criteria and notify you only when a new product matches, including its price and link.
5. **Review the match and open the product link.** You remain in control of the purchase decision.

Example request after connecting the plugin:

> Search http://127.0.0.1:8765/laptops for laptops under $800 with at least 16GB RAM and SSD storage. Check every day with the same criteria using filter_products. Notify me only about newly matching products, with their prices and links.

Confirm that your dot saved the recurring task. The dot manages scheduling; the plugin performs each fresh search. The catalog and MCP server must remain reachable from the dot's execution environment.

## Architecture

`ChatGPT + skill → filter_products MCP → allowed catalog → exact price checks → Decisions semantic checks → ranked product links`

The API key stays on the backend. Price-only requests skip OpenAI entirely.

## Setup

Requires Python 3.11 or newer. From this project directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

Copy `.env.example` to `.env` if you do not already have one (`cp .env.example .env`). Keep existing credentials when upgrading. The required variable for semantic filtering is `OPENAI_API_KEY`; `.env.example` documents optional limits. `.env` is ignored by Git and is never bundled into the plugin. Shell environment values take precedence. Price-only filtering needs no API key.

To recreate the exact tested dependency environment, use `requirements.lock.txt` before installing the project with `--no-deps -e .`. The lock was generated with Python 3.14 on macOS; other platforms may need to resolve their own dependencies from `pyproject.toml`.

## Run a search without ChatGPT

```sh
.venv/bin/python -m shopping_assistant.cli examples/price-only.json
.venv/bin/python -m shopping_assistant.cli examples/laptops.json
```

The second command sends paid API requests to OpenAI for up to the configured product cap. A small live check:

```sh
SHOPPING_MAX_PRODUCTS=3 .venv/bin/python -m shopping_assistant.cli examples/live-smoke.json
```

JSON goes to stdout. Exit code 2 means invalid setup/request or extraction failure; code 1 means at least one product ended in the error group. Results containing errors in optional preferences can remain matches, with `complete: false` and a warning.

## Run the MCP server

For an MCP client that launches a subprocess:

```sh
.venv/bin/python -m shopping_assistant.server
```

For a local Streamable HTTP client:

```sh
.venv/bin/python -m shopping_assistant.server --transport http --port 8000
```

The endpoint is `http://127.0.0.1:8000/mcp`. It is deliberately loopback-only and unauthenticated for local development. The server does not start automatically on installation. For a temporary personal setup, an HTTPS tunnel can expose this server without authentication. Anyone who knows that URL can trigger requests billed to the server owner. Per-search caps do not impose a total spending quota; stop the tunnel when finished.

For a stdio client, use the absolute path to this checkout's `.venv/bin/python`, arguments `-m shopping_assistant.server`, and this project directory as `cwd`. The `.env` is resolved relative to the source checkout, not the client's working directory.

## Tool contract

`filter_products(url, filter, result_limit=10)` accepts the shape illustrated in `examples/laptops.json`:

- `url`: HTTPS listing URL from the allowlist below, or the exact local Fieldwork listing when local catalog access is enabled; no query or fragment.
- `filter.price`: up to two `{operator, amount, currency}` conditions. Operators: `lt`, `lte`, `gt`, `gte`; currency: `USD`. Amounts support two decimal places. Comparisons use decimal arithmetic. Under $800 excludes exactly $800.
- `filter.requirements`: up to eight mandatory natural-language criteria (all must match).
- `filter.preferences`: up to four optional criteria, equally weighted for ranking.
- `result_limit`: 1–50, applied separately to each returned group. It does not change the evaluation cap.

Returns `matches`, `uncertain`, `errors`, and a sample of `excluded`, including original product descriptions, URLs, listed prices, and each criterion's classification/source. The model does not produce free-form rationales or verified evidence excerpts. Describe its judgments honestly using the accompanying source text.

`counts` covers all checked products, even when the returned groups are truncated. `products_found` counts unique valid products extracted; `products_checked` counts products processed (including failed evaluations), `products_not_checked` reports the cap, and `extraction_skipped` reports malformed cards. `complete` means no cap, extraction skips, or criterion errors; missing product information can still remain. `results_truncated` separately indicates omitted results. `fetched_at` is UTC.

Definite mandatory failures exclude a product. Unknown mandatory facts produce `uncertain`; mandatory API failures produce `errors`. Preferences cannot override a mandatory failure. With only preferences, at least one supported preference is required for the matches group; other products remain uncertain. Any preference API error is disclosed even when mandatory criteria pass.

## Supported pages and limits

- https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops
- https://webscraper.io/test-sites/e-commerce/allinone/computers/tablets
- https://webscraper.io/test-sites/e-commerce/allinone/phones/touch
- http://127.0.0.1:8765/laptops (local Fieldwork shop; requires `SHOPPING_DEMO_ENABLED=1`, see below)

These catalogs contain test listings, not current purchasable offers. Only the supplied listing is fetched. No product-detail browsing, pagination, images, other stores, currency conversion, taxes/shipping calculation, persistent cache, watchlists, or purchases. Unsupported URLs and redirects are rejected. The fetched body is capped at 3 MB.

Defaults: first 30 products, 5 simultaneous evaluations, 30-second request timeout, 180-second evaluation deadline measured from search start. A semantic search sends one Decisions request per product that passes exact checks, with all semantic questions grouped together. One SDK retry is allowed; cancelled or failed evaluations stay explicit. Repeating a search repeats the API calls. These are per-search limits, not production account quotas.

## Plugin and skill

`plugins/shopping-assistant/` contains the portable `plugin.json`, local `mcp.json`, and `skills/shopping-assistant/SKILL.md`. The skill guides confirmation, tool arguments, evidence-aware presentation, and refinements. MCP server instructions provide a short version to clients that only connect the tool.

The package points at the local HTTP endpoint; run it before connecting a supported local client. It is not installed, published, or registered in ChatGPT automatically. ChatGPT cloud cannot reach your machine's loopback URL. For a personal cloud setup, supply a reachable HTTPS endpoint and select No authentication during registration. Follow [plugin release instructions](docs/plugin-release.md). A skill file alone does not create a server connection. No custom visual extension or Chrome extension is needed for this MVP.

## Tests

```sh
.venv/bin/python -m unittest discover -s tests -v
```

The offline suite uses a saved public listing and mocked provider responses. It covers extraction, unsafe URLs, redirects, missing data, exact price boundaries, invalid filters, mandatory/preference behavior, provider failures/refusals, search deadlines, result caps, and MCP discovery/structured output. It does not require `.env` or contact external services. Storefront integration tests bind an ephemeral loopback port.

Try the skill's sample requests after connecting ChatGPT. Live tool selection and presentation are not validated by local tests.

Verified locally on October 10, 2026: all 22 tests passed; editable installation and dependency checks passed; both stdio and HTTP MCP tool discovery passed. Live extraction found 117 laptop products. A price-only run checked 30 products (14 below $400), and a three-product Decisions smoke test returned three RAM matches with preference ranking and no API errors. Both capped runs correctly reported partial coverage. These checks used small samples, not an accuracy benchmark for arbitrary prompts.

## Reference documentation

- [Decisions API](https://developers.openai.com/api/docs/guides/decisions)
- [Plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [FastMCP tools](https://gofastmcp.com/servers/tools)

The fixture `tests/fixtures/laptops.html` was retrieved from the public Web Scraper test catalog on October 10, 2026 and is retained solely for reproducible extraction tests.

## Local Fieldwork shop (editable prices)

The checkout includes **Fieldwork**, a ten-laptop sample shop with local SVG illustrations,
product pages, a price editor, and reset. It uses Python's standard library; no extra install.

Start the shop in one terminal:

```sh
.venv/bin/python -m shopping_assistant.demo_shop
```

Open http://127.0.0.1:8765/laptops and http://127.0.0.1:8765/admin.
Use the exact `127.0.0.1` address (not `localhost`). Prices persist in
`demo_shop/prices.local.json`; the reset button restores `demo_shop/products.json`.
This is a local-only catalog with no checkout or payments.

Start the MCP server in another terminal with local catalog access enabled:

```sh
SHOPPING_DEMO_ENABLED=1 .venv/bin/python -m shopping_assistant.server --transport http --port 8000
```

Alternatively add `SHOPPING_DEMO_ENABLED=1` to the checkout's `.env` and restart the MCP
server. Only the exact listing `http://127.0.0.1:8765/laptops` is additionally permitted;
other local addresses remain rejected. All catalog requests fetch fresh HTML.

### Repeatable price-change walkthrough

1. Reset prices in the editor.
2. Run `SHOPPING_DEMO_ENABLED=1 .venv/bin/python -m shopping_assistant.cli examples/demo-shop.json`.
   Three products are under $800; Atlas Air 14 is excluded at $950.
3. Change Atlas Air 14 to $750 and save. Refresh the storefront to see the change.
4. Repeat the same command. Four products now match, including Atlas Air 14 at $750.
5. Reset to repeat the walkthrough. No API requests are made by this price-only example.

For semantic filtering, use `examples/demo-shop-laptops.json` instead
(requires the existing OpenAI key and sends paid semantic requests). At starting prices,
none satisfy both the budget and 16GB RAM; after the edit Atlas Air 14 should qualify.
AI judgments still use the engine's existing uncertainty/error handling.

Once the plugin is connected to a local task accessible to your dot, request:
“Search http://127.0.0.1:8765/laptops for laptops under $800 with at least 16GB RAM and
SSD storage. Check every day with the same criteria using filter_products;
notify me about newly matching products with their prices and links.”
Confirm the dot saved the follow-up. Keep the shop, MCP server, and connected computer
running. Scheduling is managed by the dot, not by this website. Cloud-only access to
this loopback endpoint requires a reachable server connection.

## Contributing and publishing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local checks and
[personal GitHub instructions](docs/personal-github.md) for publishing without
using a work SSH identity. GitHub Actions runs tests without API credentials.
The Python dependency lock records the tested environment; the application is
intended to run from an editable source checkout (including `demo_shop/` assets).

The finished product video and preview are included in `docs/media/`.
The optional `demo-video/` authoring workspace is excluded from Git.
Generated plugin archives belong in `dist/` and are also excluded. No live tunnel
URL or account-specific plugin ID is required in committed configuration.

## License

Original project code is MIT licensed; see [LICENSE](LICENSE) and
[third-party notices](THIRD_PARTY_NOTICES.md) for the test fixture.
