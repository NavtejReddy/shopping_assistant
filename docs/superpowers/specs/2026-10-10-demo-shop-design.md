# Local shopping demo

Approved in chat: one storefront, one price editor, ten fictional laptops, JSON persistence, and reset to starting prices. Use Python's standard-library HTTP server on 127.0.0.1:8765; no additional dependencies. Render HTML product cards compatible with the existing parser and individual product pages. Persist price edits with atomic file replacement. Accept writes only from same-origin forms with a per-process token. The MCP extractor permits only the exact demo listing when SHOPPING_DEMO_ENABLED=1. Keep existing production URL restrictions.

Verification: exercise actual HTTP price updates, reset, rejected writes, extraction and MCP filtering before/after a price drop without paid API calls. Run existing offline tests and inspect storefront/editor in a browser. Dots scheduling and remote deployment are outside this local build.
