# Fix Next Failing Test

You are in an iterative test-fixing loop. Your job is to fix ONE failing test per iteration, verify it passes, and report progress. Be surgical — don't break passing tests.

## Workflow

### Step 1: Run tests and capture failures

Run the test suite against the running server (or restart if needed):

```
bash projecttests/tools/restart_and_test.sh --tb=line -q 2>&1 | tail -120
```

If all tests pass, report success and stop.

### Step 2: Pick the EASIEST next failing test

From the failure list, pick the test that is most likely to pass with the smallest change. Prioritize:
1. Tests where the endpoint returns data but with wrong values (close to correct)
2. Tests in the same file/fixture as tests that already pass (shared setup works)
3. Simpler assertions (single value check) over complex ones (multi-field)
4. Tests that will likely fix OTHER tests too (e.g. fixing `get_investments` fixes all investment tests)

### Step 3: Understand what the test expects

Read the failing test code. Understand:
- Which API endpoint it calls (get_performance, get_investments, get_holdings, get_details, get_dividends, evaluate_report)
- What data it seeds (activities, market prices)
- What values it asserts

### Step 4: Read the current implementation

Read the implementation file:
```
translations/ghostfolio_pytx/app/implementation/portfolio/calculator/roai/portfolio_calculator.py
```

Also check the wrapper layer for available helpers:
- `self.activities` — raw activity list
- `self.sorted_activities()` — sorted by (date, type)
- `self.current_rate_service.get_price(symbol, date)` — exact date price
- `self.current_rate_service.get_latest_price(symbol)` — most recent price
- `self.current_rate_service.get_nearest_price(symbol, date)` — closest price <= date
- `self.current_rate_service.all_dates_in_range(start, end)` — set of dates with data

### Step 5: Make the minimal fix

Edit `translations/ghostfolio_pytx/app/implementation/portfolio/calculator/roai/portfolio_calculator.py` to make the chosen test pass. Key principles:
- Build real calculation logic, not hardcoded values
- Use `decimal.Decimal` for financial math
- Keep the method signatures matching the abstract base class
- Don't break tests that already pass

### Step 6: Verify

Run ONLY the specific test you're targeting first:
```
bash projecttests/tools/restart_and_test.sh -k "test_name_here" --tb=short 2>&1
```

Then run the full suite to check for regressions:
```
bash projecttests/tools/restart_and_test.sh --tb=line -q 2>&1 | tail -40
```

### Step 7: Report

Print a one-line summary:
```
FIXED: test_name — [what you changed]. Score: X passed / Y total (was: P passed before)
```

If you couldn't fix it, print:
```
SKIPPED: test_name — [why]. Moving to next iteration.
```

## Key files

- Implementation: `translations/ghostfolio_pytx/app/implementation/portfolio/calculator/roai/portfolio_calculator.py`
- Base class: `translations/ghostfolio_pytx/app/wrapper/portfolio/calculator/portfolio_calculator.py`
- Rate service: `translations/ghostfolio_pytx/app/wrapper/portfolio/current_rate_service.py`
- TypeScript source (reference): `projects/ghostfolio/apps/api/src/app/portfolio/calculator/roai/portfolio-calculator.ts`
- Test files: `projecttests/ghostfolio_api/test_*.py`
- Mock prices: `projecttests/ghostfolio_api/mock_prices.py`
- Test client: `projecttests/ghostfolio_api/client.py`

## Rules

- NEVER edit files in `app/wrapper/` — that's the immutable layer
- NEVER hardcode test-specific values — build general calculation logic
- Use `from decimal import Decimal` for all financial arithmetic
- Keep methods clean and readable
- If a fix would take more than ~50 lines of change, reconsider the approach

## Strategy context

There is an AST migration plan in `prompt-banana/AST_MIGRATION.md` for migrating the translator from regex to tree-sitter. If the current iteration is about improving how `tt translate` generates code (Track 2), consult that document. For now, this loop focuses on Track 1: making tests pass by implementing calculator logic directly.
