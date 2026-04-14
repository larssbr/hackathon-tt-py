# SPEC.md — Translation Domain Specification

## Translation Target

Translate the Ghostfolio ROAI portfolio calculator from TypeScript to Python.

### Source Files (in order of importance)

| File | Role | Complexity |
|------|------|------------|
| `roai/portfolio-calculator.ts` | ROAI subclass — `getSymbolMetrics()`, `calculateOverallPerformance()` | ~500 lines, core algorithm |
| `portfolio-calculator.ts` | Abstract base — `computeSnapshot()`, `computeTransactionPoints()` | ~800 lines, orchestrator |
| `portfolio.helper.ts` | `getFactor()` utility | 19 lines, trivial |

### Output Target

`translations/ghostfolio_pytx/app/implementation/portfolio/calculator/roai/portfolio_calculator.py`

Must implement the abstract interface in `app/wrapper/portfolio/calculator/portfolio_calculator.py`.

---

## Dependency Matrix

Every `import` in the two calculator files, classified by translation strategy.

### External Libraries → Python Stdlib/Packages

| TypeScript Import | Source | Python Equivalent | Strategy |
|---|---|---|---|
| `Big` | `big.js` | `decimal.Decimal` | Method-chain → operator rewrite |
| `format` | `date-fns` | `datetime.strftime` | Function call mapping |
| `differenceInDays` | `date-fns` | `(a - b).days` | Inline expression |
| `isBefore` | `date-fns` | `a < b` | Inline operator |
| `isAfter` | `date-fns` | `a > b` | Inline operator |
| `addMilliseconds` | `date-fns` | `a + timedelta(milliseconds=n)` | Inline expression |
| `eachYearOfInterval` | `date-fns` | date range generator | Helper function |
| `eachDayOfInterval` | `date-fns` | date range generator | Helper function |
| `subDays` | `date-fns` | `d - timedelta(days=n)` | Inline expression |
| `startOfDay`, `endOfDay` | `date-fns` | `d.replace(hour=0,...)` | Method call |
| `isWithinInterval` | `date-fns` | `start <= d <= end` | Inline expression |
| `cloneDeep` | `lodash` | `copy.deepcopy` | Direct replacement |
| `sortBy` | `lodash` | `sorted(arr, key=fn)` | Direct replacement |
| `sum` | `lodash` | `sum(arr)` | Direct replacement |
| `uniqBy` | `lodash` | `{fn(x): x for x in arr}.values()` | Inline pattern |
| `isNumber` | `lodash` | `isinstance(x, (int, float, Decimal))` | Inline check |
| `Logger` | `@nestjs/common` | `logging.getLogger` | Direct replacement |

### Internal Ghostfolio Imports → Already in Scaffold or Translate

| TypeScript Import | Source | Disposition |
|---|---|---|
| `PortfolioCalculator` | base class | Provided by wrapper (`portfolio_calculator.py`) |
| `CurrentRateService` | service | Provided by wrapper (`current_rate_service.py`) |
| `getFactor` | `portfolio.helper` | Translate: 3-line function (BUY=1, SELL=-1, else 0) |
| `getIntervalFromDateRange` | `calculation-helper` | Translate: date range utility |
| `DATE_FORMAT` | `common/helper` | Constant: `'%Y-%m-%d'` |
| `parseDate` | `common/helper` | `date.fromisoformat(s)` or `datetime.strptime(s, fmt)` |
| `getSum` | `common/helper` | `sum()` |
| `resetHours` | `common/helper` | `d.replace(hour=0, minute=0, second=0, microsecond=0)` |

### Type Interfaces → Python Dicts or Dataclasses

| TypeScript Interface | Key Fields | Python Representation |
|---|---|---|
| `PortfolioOrder` | date, fee, feeInBaseCurrency, quantity, unitPrice, type, SymbolProfile | `dict` (already in wrapper) |
| `PortfolioOrderItem` | extends PortfolioOrder + itemType, unitPriceInBaseCurrency | `dict` with extra keys |
| `TransactionPoint` | date, fees, interest, items (list), liabilities | `dict` |
| `TransactionPointSymbol` | symbol, currency, quantity, investment, averagePrice, fee, assetSubClass | `dict` |
| `SymbolMetrics` | 25 fields — all `Big` → `Decimal`, date-keyed dicts | `dict[str, Any]` |
| `TimelinePosition` | 20 fields — all `Big` → `Decimal` | `dict` |
| `PortfolioSnapshot` | positions, totals, historicalData, errors | `dict` |
| `AssetProfileIdentifier` | dataSource, symbol | `dict` |

---

## Library API Translation Table

### Big.js → decimal.Decimal

| Big.js | Python Decimal | Notes |
|---|---|---|
| `new Big(x)` | `Decimal(str(x))` | Always stringify to avoid float precision |
| `new Big(0)` | `Decimal(0)` | Integer zero is safe |
| `a.plus(b)` | `a + b` | Operator overloaded |
| `a.minus(b)` | `a - b` | |
| `a.times(b)` | `a * b` | |
| `a.div(b)` | `a / b` | |
| `a.eq(0)` | `a == Decimal(0)` or `a == 0` | |
| `a.eq(b)` | `a == b` | |
| `a.gt(b)` | `a > b` | |
| `a.gte(b)` | `a >= b` | |
| `a.lt(b)` | `a < b` | |
| `a.lte(b)` | `a <= b` | |
| `a.abs()` | `abs(a)` | |
| `a.toNumber()` | `float(a)` | |
| `a.round(n)` | `round(a, n)` | |

### date-fns → datetime

| date-fns | Python | Notes |
|---|---|---|
| `format(d, 'yyyy-MM-dd')` | `d.strftime('%Y-%m-%d')` | Format tokens differ |
| `differenceInDays(a, b)` | `(a - b).days` | Returns int |
| `isBefore(a, b)` | `a < b` | |
| `isAfter(a, b)` | `a > b` | |
| `subDays(d, n)` | `d - timedelta(days=n)` | |
| `addMilliseconds(d, n)` | `d + timedelta(milliseconds=n)` | |
| `startOfDay(d)` | `datetime.combine(d.date(), time.min)` | |
| `endOfDay(d)` | `datetime.combine(d.date(), time.max)` | |
| `startOfYear(d)` | `d.replace(month=1, day=1)` | |
| `endOfYear(d)` | `d.replace(month=12, day=31)` | |
| `isThisYear(d)` | `d.year == date.today().year` | |
| `isWithinInterval(d, {start, end})` | `start <= d <= end` | |
| `parseDate(s)` / `new Date(s)` | `date.fromisoformat(s)` | |
| `eachDayOfInterval({start, end})` | Generator with timedelta | |

### lodash → Python builtins

| lodash | Python | Notes |
|---|---|---|
| `cloneDeep(x)` | `copy.deepcopy(x)` | |
| `sortBy(arr, key)` | `sorted(arr, key=lambda x: x[key])` | |
| `sum(arr)` | `sum(arr)` | |
| `uniqBy(arr, fn)` | `list({fn(x): x for x in arr}.values())` | |
| `isNumber(x)` | `isinstance(x, (int, float, Decimal))` | |

---

## Call Graph

### `RoaiPortfolioCalculator` (the ROAI subclass)

```
getSymbolMetrics({chartDateMap, dataSource, end, exchangeRates, marketSymbolMap, start, symbol})
  ├─ filters orders by symbol
  ├─ early return if no orders or no market price
  ├─ adds synthetic 'start' and 'end' boundary orders
  ├─ groups orders by date
  ├─ MAIN LOOP: for each date in sorted(ordersByDate):
  │   ├─ for each order on that date:
  │   │   ├─ getFactor(type) → +1 (BUY), -1 (SELL), 0 (other)
  │   │   ├─ updates: totalUnits, totalInvestment, totalInvestmentWithCurrencyEffect
  │   │   ├─ tracks: fees, dividends, interest, liabilities
  │   │   ├─ computes: lastAveragePrice (for sell cost-basis)
  │   │   └─ computes: grossPerformanceFromSells (sell price - avg cost)
  │   └─ for chartDate coverage:
  │       ├─ currentValues[date] = totalUnits * marketPrice
  │       ├─ investmentValuesAccumulated[date] = running investment
  │       ├─ netPerformanceValues[date] = currentValue - investment + sellGains - fees
  │       └─ timeWeightedInvestmentValues[date] = TWI accumulation
  └─ returns: SymbolMetrics (25-field dict)

calculateOverallPerformance(positions: TimelinePosition[])
  ├─ for each position where includeInTotalAssetValue:
  │   ├─ accumulate: currentValueInBaseCurrency
  │   ├─ accumulate: totalInvestment
  │   ├─ accumulate: grossPerformance, netPerformance
  │   ├─ accumulate: totalFeesWithCurrencyEffect
  │   └─ accumulate: totalTimeWeightedInvestment
  └─ returns: PortfolioSnapshot

getPerformanceCalculationType()
  └─ returns: "ROAI"
```

### Base class `PortfolioCalculator.computeSnapshot()` (orchestrator)

```
computeSnapshot()
  ├─ build transactionPoints from activities
  ├─ get exchange rates for all currencies
  ├─ get market prices for all symbols (via currentRateService)
  ├─ build marketSymbolMap: { date → { symbol → price } }
  ├─ build chartDateMap (sampling for chart display)
  ├─ for each symbol in last transactionPoint:
  │   ├─ call getSymbolMetrics({symbol, ...}) ← THE CORE
  │   ├─ build TimelinePosition from SymbolMetrics
  │   └─ accumulate per-date values
  ├─ call calculateOverallPerformance(positions)
  ├─ build historicalData (chart points)
  └─ returns: PortfolioSnapshot
```

---

## Edge Cases & Truthiness Traps

| TypeScript | Python | Risk |
|---|---|---|
| `[]` is truthy | `[]` is falsy | Guard conditions flip |
| `null` / `undefined` | `None` | Two nulls → one |
| `0` is falsy | `0` is falsy | Same (safe) |
| `''` is falsy | `''` is falsy | Same (safe) |
| `if (x)` for Big | `if x:` — Decimal(0) is falsy | Must check `x is not None` instead |
| `?.` optional chaining | No equivalent | Must use `x.get('y')` or explicit guard |
| `x ?? y` nullish coalesce | `x if x is not None else y` | Python `or` is wrong (catches 0, '') |

---

## Test Oracle

The 21 TypeScript spec files under `roai/` define the exact scenarios the API tests check.
Each contains: activities (input), mock prices per date, and expected metric values.

Priority order for implementation:

| # | Spec File | Scenario | Key Assertion |
|---|---|---|---|
| 1 | `portfolio-calculator-no-orders.spec.ts` | Empty portfolio | All zeros |
| 2 | `portfolio-calculator-googl-buy.spec.ts` | Single BUY | totalInvestment, currentValue |
| 3 | `portfolio-calculator-baln-buy.spec.ts` | Single BUY, different symbol | Same pattern |
| 4 | `portfolio-calculator-baln-buy-and-sell.spec.ts` | BUY then full SELL | Zero position, realized gain |
| 5 | `portfolio-calculator-btcusd.spec.ts` | BTC single BUY | Crypto-specific |
| 6 | `portfolio-calculator-btcusd-buy-and-sell-partially.spec.ts` | Partial sell | Partial cost basis |
| 7 | `portfolio-calculator-msft-buy-with-dividend.spec.ts` | BUY + DIVIDEND | Dividend tracking |
| 8 | `portfolio-calculator-fee.spec.ts` | FEE transactions | Fee accumulation |
| 9 | `portfolio-calculator-novn-buy-and-sell-partially.spec.ts` | Partial sell CHF | Currency handling |
| 10 | `portfolio-calculator-novn-buy-and-sell.spec.ts` | Full sell CHF | Full realized |

---

## Data Quality Rules (Birgitta-inspired)

### DQ-1: Completeness

Every `SymbolMetrics` return must include all 30+ fields from the TypeScript
interface. Missing fields cause silent `KeyError` in the wrapper or assertion
failures in tests. The translator must emit **all** fields, even when zero.

**Check:** Validate that the Python return dict keys match the TypeScript return
object keys exactly. `set(py_keys) == set(ts_keys)`.

### DQ-2: Consistency (Arithmetic Precision)

`Big.js` arithmetic must translate to `Decimal` with consistent precision.
Values like `grossPerformance` depend on chains of `plus()`, `minus()`,
`mul()`, `div()` — one wrong operator or missing parenthesis cascades through
all downstream metrics.

**Check:** Each `Big` → `Decimal` translation must preserve operator precedence
and chain order. Test: translate known arithmetic chains and compare results.

### DQ-3: Referential Integrity

The `marketSymbolMap[dateString]?.[symbol]` lookups must map to the mock
prices seeded by `mock_prices.py`. If the translator misnames a field or
changes dictionary access patterns, lookups silently return `None` instead of
raising.

**Check:** All dictionary key accesses in the translated code match the keys
used by the wrapper's `current_rate_service.py`.

### DQ-4: Temporal Validity

Date formatting must use `yyyy-MM-dd` (`DATE_FORMAT`). The TypeScript uses
`format(date, DATE_FORMAT)` from date-fns. Python must use
`date.strftime("%Y-%m-%d")` or equivalent. Any format mismatch causes
silent lookup failures in `marketSymbolMap`.

**Check:** All date strings in translated code produce `YYYY-MM-DD` format.

### DQ-5: Quarantine Pattern

When the translator encounters a TypeScript construct it cannot translate
(generic type parameters, complex destructuring, nested ternaries), it must
**quarantine** the node with a reason string rather than silently dropping it
or emitting broken Python. Quarantined nodes are logged in `TranslationResult`
for human review.

**Check:** `TranslationResult.quarantined` list is non-empty for known-hard
constructs; none are silently swallowed.

---

## Constraints (from COMPETITION_RULES.md)

1. **No LLMs** in the translation runtime — `tt` must be deterministic
2. **No project-specific mappings** in `tt/` core — use `tt_import_map.json`
3. **No domain logic** in `tt/` — no hardcoded `grossPerformance` etc.
4. **Wrapper is immutable** — only `app/implementation/` is generated
5. **Translation must be actual translation** — not pre-written Python
6. **Python only** — no calling node/js-tools
