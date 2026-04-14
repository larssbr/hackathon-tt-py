# Parallel Fix — Implement all calculator methods at once

You are orchestrating parallel agents to implement the ROAI portfolio calculator.
Each agent works on ONE method in an isolated git worktree, then you merge results.

## Step 1: Read the shared context

Before spawning agents, read these files yourself to understand the full picture:
- `translations/ghostfolio_pytx/app/implementation/portfolio/calculator/roai/portfolio_calculator.py` (current stub)
- `translations/ghostfolio_pytx/app/wrapper/portfolio/calculator/portfolio_calculator.py` (base class)
- `translations/ghostfolio_pytx/app/wrapper/portfolio/current_rate_service.py` (rate service API)
- `projects/ghostfolio/apps/api/src/app/portfolio/calculator/roai/portfolio-calculator.ts` (TS source reference)
- `projecttests/ghostfolio_api/mock_prices.py` (test price data)

## Step 2: Spawn parallel agents

Launch 6 agents in parallel using `isolation: "worktree"`. Each agent implements ONE method.
Give each agent the FULL context it needs (file paths, base class API, rate service API, test expectations).

**Agent 1: get_investments**
- Tests: test_btcusd_investments_*, test_remaining_specs::*_investments_*, test_novn_buy_and_sell::test_investments_*
- Must return `{"investments": [{"date": "YYYY-MM-DD", "investment": float}]}`
- Support `group_by` parameter: None (daily), "month", "year"
- Investment = cumulative sum of (quantity * unitPrice) for BUY, minus for SELL

**Agent 2: get_holdings**
- Tests: test_btcusd_holding_values, test_remaining_specs::*_holdings_*, test_details::*_holding_*
- Must return `{"holdings": {"SYMBOL": {"quantity": float, "investment": float, "marketPrice": float, "averagePrice": float, ...}}}`
- Use `current_rate_service.get_latest_price(symbol)` for current market price

**Agent 3: get_performance (chart + performance summary)**
- Tests: test_btcusd_chart_*, test_deeper::*, test_same_day_*, test_short_cover_*, test_msft_fractional_*
- Must return `{"chart": [...], "firstOrderDate": str, "performance": {...}}`
- Chart entries: one per date with `netWorth`, `totalInvestment`, `value`, `netPerformanceInPercentage`
- Performance: `netPerformance`, `totalInvestment`, `totalFees`, `currentNetWorth`, etc.
- This is the hardest method — reference `getSymbolMetrics()` in the TS source

**Agent 4: get_details**
- Tests: test_details::*
- Must return `{"accounts": {...}, "holdings": {...}, "summary": {...}, "hasError": bool}`
- Can reuse logic from get_holdings for the holdings dict
- Summary: `totalInvestment`, `netPerformance`, `currentValueInBaseCurrency`, `totalFees`

**Agent 5: get_dividends**
- Tests: test_dividends::*
- Must return `{"dividends": [{"date": "YYYY-MM-DD", "investment": float}]}`
- Filter activities where type == "DIVIDEND"
- Support `group_by`: None (daily), "month", "year"

**Agent 6: evaluate_report**
- Tests: test_report::*
- Must return x-ray report with rule categories and statistics
- Rules: "accountClusterRisk" (accounts), "currencyClusterRisk" (currencies), "feeRatioInitialInvestment" (fees)

## Step 3: Merge results

After all agents complete:
1. Read each worktree's version of `portfolio_calculator.py`
2. Manually merge the method implementations into the main file
3. Run `bash projecttests/tools/restart_and_test.sh --tb=short -q` to verify
4. Fix any integration issues between methods

## Key context to include in every agent prompt

```
Available APIs:
- self.activities: list[dict] with keys: symbol, date, type, quantity, unitPrice, fee, currency, dataSource
- self.sorted_activities(): same but sorted by (date, type_order)
- self.current_rate_service.get_price(symbol, date_str) -> float | None
- self.current_rate_service.get_latest_price(symbol) -> float
- self.current_rate_service.get_nearest_price(symbol, date_str) -> float
- self.current_rate_service.all_dates_in_range(start_str, end_str) -> set[str]

Rules:
- Use decimal.Decimal for all financial math
- Never edit files in app/wrapper/
- Activity types: BUY, SELL, DIVIDEND, FEE, LIABILITY
- Date format is always "YYYY-MM-DD" strings
```

## Step 4: Iterate

After the initial parallel pass, run `/loop /fix-next-test` to clean up any remaining failures sequentially.
