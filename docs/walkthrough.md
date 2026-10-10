# Shopping Assistant: text walkthrough

This companion explains the reproducible scenario alongside the existing video.
It is not a transcript of a recorded scheduled run.

1. **Express the brief.** “Find laptops under $800 with at least 16GB RAM and SSD
   storage.” Confirm the catalog and distinguish requirements from preferences.
2. **Represent the request.** `examples/demo-shop-laptops.json` encodes the strict
   USD budget and two mandatory semantic criteria. The same arguments can be reused.
3. **Evaluate evidence.** Exact price checks run first. Only budget-eligible
   products require semantic evaluation. Missing specifications remain uncertain.
4. **Change a price.** In the local Fieldwork editor, change Atlas Air 14 from
   $950 to $750. It now passes the budget threshold. Its description supplies
   the RAM and storage facts for the semantic checks.
5. **Repeat the search.** The MCP tool fetches current catalog content again.
   Match results include product URLs, prices, and criterion outcomes.
6. **Use a dot for follow-up.** A saved dot task can repeat the confirmed tool
   request. Supply previous results as context when requesting notifications
   only for newly matching products.

For the deterministic price-only version, resetting and repeating
`examples/demo-shop.json` produces three matches before the price edit and four
afterwards. The semantic version additionally evaluates the two requirements.
See [reproduction commands and evidence](evaluation.md).
