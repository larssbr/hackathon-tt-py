# Explanation of the submission

## Team: Prompt Banana

## Solution

### Architecture

`tt` is a **multi-pass, regex-based TypeScript-to-Python translator** built entirely in Python. It reads TypeScript source files, runs them through an ordered pipeline of transformation passes, and emits Python code into the `app/implementation/` directory.

```
TypeScript source (.ts)
        │
        ▼
┌─────────────────────────────────┐
│  Phase 1 — Structural Cleanup   │
│  strip_imports                   │  Remove TS import statements
│  strip_type_annotations          │  Remove : Type, as X, generics
│  translate_class                 │  export class X extends Y { → class X(Y):
└─────────────┬───────────────────┘
              ▼
┌─────────────────────────────────┐
│  Phase 2 — Expression Rewrites   │
│  translate_big_js                │  Big.js → decimal.Decimal
│  translate_date_fns              │  date-fns → datetime/timedelta
│  translate_lodash                │  cloneDeep/sortBy → builtins
│  translate_nullish               │  ??, ?. → Python guards
└─────────────┬───────────────────┘
              ▼
┌─────────────────────────────────┐
│  Phase 3 — Statement Rewrites    │
│  translate_variables             │  const/let/var → assignment
│  translate_for_loops             │  for (const x of y) → for x in y:
│  translate_conditionals          │  if/else if/else → if/elif/else
│  translate_methods               │  method signatures → def ...(self):
│  translate_returns               │  Enum.VALUE → "VALUE"
└─────────────┬───────────────────┘
              ▼
┌─────────────────────────────────┐
│  Phase 4 — Cleanup               │
│  strip_braces                    │  Remove bare closing }
│  strip_semicolons                │  Remove trailing ;
│  normalize_whitespace            │  Collapse blank lines
└─────────────┬───────────────────┘
              ▼
        Python source (.py)
```

### How it works

1. **Scaffold setup** — `tt translate` first copies the immutable wrapper layer (`app/main.py`, `app/wrapper/`) from the example skeleton. This provides the FastAPI server, endpoints, auth, and abstract calculator interface.

2. **Translation** — The translator reads the TypeScript source for `RoaiPortfolioCalculator` and runs it through 15 ordered passes. Each pass is a pure function `str → PassResult` that transforms the code and reports what it translated or quarantined.

3. **Quarantine** — Constructs the translator cannot handle cleanly (generic type parameters, complex destructuring, optional chaining) are flagged as quarantined with a reason string, rather than being silently dropped or incorrectly translated. This makes gaps visible and auditable.

4. **Output** — The translated Python code is written to `app/implementation/portfolio/calculator/roai/portfolio_calculator.py`, implementing the abstract interface from the wrapper.

### Key design decisions

| Decision | Rationale |
|---|---|
| **Regex-based, no AST parser** | Faster to build under hackathon time constraints. Each pass is small and testable. Trade-off: less robust than a full AST, but sufficient for the focused translation target. |
| **15 passes in fixed order** | Order matters — imports must be stripped before class body passes run; Big.js must be rewritten before variable declarations are translated. Explicit ordering prevents pass interference. |
| **Quarantine over silent failure** | When a pass encounters something it can't translate (e.g. `<T>` generics, `?.` chaining), it leaves the code unchanged and logs a `QuarantinedNode`. This is auditable and honest — no hidden bugs. |
| **Pydantic models for everything** | Every pipeline concept (`PassResult`, `TranslationResult`, `QuarantinedNode`) is a validated Pydantic model. No raw dicts cross boundaries. Validators catch inconsistencies (e.g. quarantine count must match list length). |
| **Generic library mappings, not domain-specific** | Big.js → Decimal and date-fns → datetime are language-level mappings in the translator core. Project-specific import paths go in `tt_import_map.json` per Rule 9. |
| **Decimal, not float** | Financial calculations require exact arithmetic. `decimal.Decimal` is the direct Python equivalent of Big.js — both avoid IEEE 754 floating-point surprises. |

### Domain analysis (SPEC.md)

Before writing translation passes, we built a full domain specification:

- **Dependency matrix** — classified every TypeScript import (external lib / internal provided / needs translation / framework drop)
- **Library API mapping** — Big.js (12 methods), date-fns (14 functions), lodash (5 functions) → Python equivalents
- **Type surface** — 7 TypeScript interfaces mapped to Python dict representations
- **Call graph** — traced `getSymbolMetrics()` and `calculateOverallPerformance()` execution flow
- **Edge case inventory** — truthiness traps (`[]` truthy in TS, falsy in Python), nullish coalescing, optional chaining
- **Test oracle** — 21 TypeScript spec files prioritized from simplest to most complex

This analysis lives in [`prompt-banana/SPEC.md`](prompt-banana/SPEC.md).

### Translation target

The core algorithm is `getSymbolMetrics()` in the ROAI portfolio calculator (~300 lines of TypeScript). It:

1. Filters activities by symbol
2. Adds synthetic boundary orders (start/end date)
3. Loops through orders by date, accumulating: `totalInvestment`, `totalUnits`, `lastAveragePrice`, `grossPerformanceFromSells`, fees, dividends
4. For each chart date, computes: `currentValues`, `investmentValuesAccumulated`, `netPerformanceValues`, `timeWeightedInvestmentValues`
5. Returns a 25-field `SymbolMetrics` dict

The `calculateOverallPerformance()` method then aggregates per-symbol metrics into a portfolio-level `PortfolioSnapshot`.

## Coding approach

### Methodology: TDD + domain-first analysis

1. **Understand the domain before coding** — Read all TypeScript source, interfaces, spec files, and competition rules. Build the dependency matrix and type surface map before writing any translation logic.

2. **Tests before passes** — Every translation pass has unit tests that define expected behavior. Tests were written first (TDD). Two were intentionally left failing to mark next implementation tasks.

3. **Iterate via `make translate-and-test-ghostfolio_pytx`** — Each change to the translator was validated against the full API test suite. Green tests were committed immediately.

4. **Human-AI collaboration** — Claude Code was used to build the translator (`tt`), analyze the TypeScript domain, and write tests. The translator itself uses zero LLMs at runtime — it is fully deterministic regex passes. All AI interactions are logged in [`prompt-banana/PROMPTS.md`](prompt-banana/PROMPTS.md).

### Evidence layer: prompt-banana/

The `prompt-banana/` directory is the collaboration harness — not the translator itself, but the design documentation and domain models that demonstrate understanding:

| File | Purpose |
|---|---|
| `SPEC.md` | Full domain specification (dependency matrix, type surface, call graph, edge cases) |
| `PROMPTS.md` | Human-AI interaction log with decisions recorded |
| `src/models.py` | Pydantic models for every pipeline concept |
| `src/pipeline.py` | 15 ordered transformation passes |
| `tests/` | 79 tests — all passing |

### Literature review

A condensed reference of TypeScript-to-Python translation methods (AST-based, ML classification, LLM-assisted) is in [`tt-literature-review/TRANSLATION_METHODS.md`](tt-literature-review/TRANSLATION_METHODS.md). Key insight: for this constrained problem (one calculator file, known types, fixed test suite), a focused regex pipeline outperforms a general-purpose transpiler.
