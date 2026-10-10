import argparse
import asyncio
from pathlib import Path
import sys

from pydantic import ValidationError

from .models import SearchRequest
from .pipeline import search


def main():
    parser = argparse.ArgumentParser(description="Run a product filter from a JSON request file")
    parser.add_argument("request", type=Path)
    args = parser.parse_args()
    try:
        request = SearchRequest.model_validate_json(args.request.read_text())
        result = asyncio.run(search(request))
    except ValidationError:
        print("Invalid request or configuration. Check the documented schema and environment settings.", file=sys.stderr)
        raise SystemExit(2) from None
    except (OSError, ValueError):
        print("Search failed. Check the request file, supported URL, network, and OPENAI_API_KEY configuration.", file=sys.stderr)
        raise SystemExit(2) from None
    print(result.model_dump_json(indent=2))
    if result.counts["error"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
