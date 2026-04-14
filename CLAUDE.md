# Project: Enhanced Hackathon 2026 — TypeScript to Python Translator

## Team: Prompt Banana

## Quick Reference

### Fast iteration loop (edit implementation directly)
```bash
# Edit the calculator, then test without re-translating:
bash projecttests/tools/restart_and_test.sh --tb=short -q

# Run a single test:
bash projecttests/tools/restart_and_test.sh -k "test_btcusd_holding_values" --tb=short

# Full translate + test cycle (slower, regenerates from tt):
make translate-and-test-ghostfolio_pytx
```

### Auto-fix loop
```
/loop /fix-next-test
```
This runs the fix-next-test command repeatedly, fixing one failing test per iteration.

### Key files to edit
- **Implementation** (where the calculator logic lives):
  `translations/ghostfolio_pytx/app/implementation/portfolio/calculator/roai/portfolio_calculator.py`
- **Translator** (regex pipeline that generates the implementation):
  `tt/tt/translator.py`

### Directories and files you MUST NOT edit or commit changes to
These are judge-provided, read-only. Editing them risks disqualification.

- `projects/` — original TypeScript source (read-only reference)
- `projecttests/` — judge API test suite (never add/modify/delete)
- `evaluate/` — scoring scripts and rule checks
- `make/` — Makefile includes (e.g. `evalsolution.mk`)
- `helptools/` — scaffold setup scripts
- `dashboards/` — competition dashboard
- `Makefile` — top-level build file
- `COMPETITION_RULES.md` — judge document
- `tt_example/` — provided example translator (reference only)
- `translations/ghostfolio_pytx_example/` — reference skeleton (Rule 8)
- `translations/ghostfolio_pytx/app/wrapper/` — immutable scaffold layer (Rule 9, byte-identical)
- `translations/ghostfolio_pytx/app/main.py` — immutable (Rule 9, byte-identical)

### Files we CAN edit
- `tt/tt/` — our translator code (the core deliverable)
- `tt/tests/` — our translator tests
- `tt/pyproject.toml` — our dependencies
- `translations/ghostfolio_pytx/app/implementation/` — only via `tt translate`, not by hand
- `SOLUTION.md` — required submission document
- `prompt-banana/` — our collaboration harness
- `CLAUDE.md` — this file

### Architecture
- `RoaiPortfolioCalculator` extends `PortfolioCalculator` (abstract base)
- Methods to implement: `get_performance`, `get_investments`, `get_holdings`, `get_details`, `get_dividends`, `evaluate_report`
- `self.activities` — list of activity dicts with keys: symbol, date, type, quantity, unitPrice, fee, currency, dataSource
- `self.current_rate_service` — provides market prices: `.get_price(symbol, date)`, `.get_latest_price(symbol)`, `.get_nearest_price(symbol, date)`, `.all_dates_in_range(start, end)`
- Use `decimal.Decimal` for all financial math (not float)

### TypeScript source reference
The original algorithm is in:
`projects/ghostfolio/apps/api/src/app/portfolio/calculator/roai/portfolio-calculator.ts`

Key methods: `getSymbolMetrics()` (~600 lines) and `calculateOverallPerformance()` (~100 lines)

### Competition rules
- No LLMs in `tt/` runtime — translator must be deterministic
- Wrapper layer is byte-identical to example — never modify
- Score = 85% test pass rate + 15% code quality

### Two-track strategy

There are two parallel approaches to increasing the test pass rate:

**Track 1: Direct implementation** (fast, tactical)
Edit `portfolio_calculator.py` directly to implement calculator logic. Use `/fix-next-test` or `/loop /fix-next-test`. This gets tests passing immediately but the `tt translate` step won't reproduce the changes.

**Track 2: AST-based translator** (proper, strategic)
Migrate `tt/tt/translator.py` from regex passes to a tree-sitter AST walker. This produces correct, reproducible Python from the TypeScript source. Full plan in `prompt-banana/AST_MIGRATION.md`.

Key details from the AST migration plan:
- Dependencies: `tree-sitter>=0.23`, `tree-sitter-typescript>=0.23` (Rule 5 allows AST libs)
- Architecture: `ast_parser.py` (parse), `ast_walker.py` (visitor), `node_handlers/` (per-node-type)
- Hardest part: Big.js method chains (`total.plus(fee).minus(tax)`) — nested `call_expression` nodes in the AST
- Node type table: 25+ TS AST node types mapped to Python equivalents (see `prompt-banana/AST_MIGRATION.md` Step 3)
- Keeps existing Pydantic models, quarantine concept, and test structure
- ~3 hours estimated effort
