# Reproduce the submission

## What to inspect first

Read the README's judging-criteria sections, watch the existing video, and follow
[the text walkthrough](walkthrough.md). The implementation maps directly to:

- Usefulness: confirmed requirements become clickable shortlists.
- Technical execution: `shopping_assistant/pipeline.py` enforces prices and aggregates outcomes;
  `decisions.py` evaluates semantic evidence; `server.py` exposes the MCP tool.
- Originality: one reusable shopping brief combines exact constraints, semantic
  preferences, and explicit uncertainty across repeated searches.
- Functionality: deterministic integration tests plus a separately measured live
  semantic evaluation.

## Five-minute local check (no API key)

From the repository root, with Python 3.11 or newer:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

The tests include an isolated localhost storefront, saved price editing, a real
in-process MCP client, repeated filtering, and price reset. They do not modify
an already-running presenter's catalog. Expected result: all tests pass.

For an interactive demonstration, start a storefront in one terminal:

```sh
.venv/bin/python -m shopping_assistant.demo_shop
```

In another terminal:

```sh
SHOPPING_DEMO_ENABLED=1 .venv/bin/python -m shopping_assistant.cli examples/demo-shop.json
```

Open http://127.0.0.1:8765/admin and reset prices before starting. The first search
returns three matches below $800. Change Atlas Air 14 from $950 to $750 and
repeat the command: four matches, including Atlas Air 14. Reset afterwards.

## Semantic evaluation (requires API access)

Set `OPENAI_API_KEY` in your local `.env`, then run:

```sh
.venv/bin/python scripts/evaluate_semantics.py
```

This makes 12 paid Decisions calls with no SDK retries. The versioned input is
`evaluations/semantic-cases.json`. Cases cover explicit support, contradiction,
missing information, ambiguous configurations, AND/OR criteria, optional
preferences, and an instruction embedded in product text. The runner uses the
same Decisions adapter as the plugin and records every outcome, API errors,
dataset hash, model, timestamp, and total elapsed time in `evaluations/latest.json`.
A nonzero exit means at least one mismatch or API error. These authored synthetic
cases are a regression sample, not a representative market benchmark.

## ChatGPT plugin and dot workflow

Follow [plugin setup](plugin-release.md), with the MCP server running and the
shop enabled. Ask for the criteria in `examples/demo-shop-laptops.json`, confirm
the interpretation, and inspect returned links and per-criterion outcomes.

To demonstrate a dot follow-up, ask the connected dot to save a recheck of those
same criteria. Record the saved schedule, change the price before the scheduled
run, and inspect its result for the newly matching product. The dot supplies
scheduling and previous-result context; the MCP server fetches fresh catalog
content on each call. Keep the backend, catalog, and connection running.
Only product URLs reachable by the reviewing user should be presented as links
that user can open; the local catalog requires access to the host computer.

## Evidence map

- `tests/test_shopping.py`: extraction, boundaries, uncertainty, failure handling,
  caps, deadlines, and MCP schema/output.
- `tests/test_demo_shop.py`: persistent price change through MCP and reset.
- `evaluations/latest.json`: dated live semantic results for the fixed cases.
- `docs/media/shopping-assistant.mp4`: original product walkthrough.
- `.github/workflows/tests.yml`: repeatable CI checks without API secrets.

Tests exercise the backend and MCP contract. Host scheduling is a separate
integration, demonstrated by its saved task and completed run rather than inferred
from a filtering test.

## Recorded outcome

The baseline matched 11/12 labels. After clarifying explicit negation in the
production prompt, the next run matched 12/12 with zero API errors in 5.84 seconds.
Both reports are retained. The cases guided this prompt change and are therefore
a development regression set, not a held-out evaluation.
