"""Run a small, paid Decisions evaluation against fixed synthetic labels."""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

from openai import AsyncOpenAI
from shopping_assistant.config import load_settings
from shopping_assistant.decisions import DecisionsEvaluator
from shopping_assistant.models import FilterSpec, Product

ROOT = Path(__file__).resolve().parents[1]


async def run(output):
    settings = load_settings()
    if not settings.api_key.get_secret_value():
        raise SystemExit('OPENAI_API_KEY is required for this paid evaluation.')
    data = (ROOT / 'evaluations/semantic-cases.json').read_bytes()
    cases = json.loads(data)
    rows = []
    started = time.monotonic()
    async with AsyncOpenAI(api_key=settings.api_key.get_secret_value(), timeout=30, max_retries=0) as client:
        evaluator = DecisionsEvaluator(client, concurrency=2)
        for case in cases:
            spec = FilterSpec(**{('preferences' if case.get('preference') else 'requirements'): [case['criterion']]})
            product = Product(id=case['id'], name='Synthetic evaluation laptop',
                              url='https://example.com/product', description=case['description'])
            result = (await evaluator.evaluate(product, spec))[0]
            rows.append(dict(case_id=case['id'], expected=case['expected'], actual=result.outcome,
                             correct=result.outcome == case['expected'], mandatory=result.mandatory))
    report = dict(timestamp=datetime.now(timezone.utc).isoformat(), model='gpt-6-luna',
                  dataset_sha256=hashlib.sha256(data).hexdigest(), cases=len(rows),
                  correct=sum(r['correct'] for r in rows), errors=sum(r['actual']=='error' for r in rows),
                  elapsed_seconds=round(time.monotonic()-started, 2), results=rows,
                  scope='Single run on 12 authored synthetic cases; not a general shopping accuracy estimate.')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='results'}, indent=2))
    return 0 if all(r['correct'] for r in rows) else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'evaluations/latest.json')
    raise SystemExit(asyncio.run(run(parser.parse_args().output)))
