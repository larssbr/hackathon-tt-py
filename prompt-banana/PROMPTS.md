# PROMPTS.md — Human–AI Collaboration Log

This file documents every significant human↔AI interaction during the hackathon.
Format follows the Treude & Gerosa 2025 taxonomy of interaction types.

---

## Entry 001 — Harness Setup

**Timestamp:** 2026-04-14T13:xx  
**Interaction type:** Conversational assistance + Code generation  
**Prompt used:**
> "Create with domain-aware content" — create the prompt-banana harness with
> Pydantic models and pipeline structure that reflect the actual translation domain,
> not generic placeholders.

**AI suggestion:**
- `src/models.py`: `NodeKind`, `TranslationStatus`, `QuarantinedNode`, `PassResult`,
  `TranslationResult`, `TranslationPipelineConfig` — all as Pydantic BaseModels
- `src/pipeline.py`: 5 ordered passes (`strip_imports`, `translate_class`,
  `translate_methods`, `translate_returns`, `strip_braces`) + `TranslationPipeline`
  orchestrator class
- `tests/test_models.py`: 12 tests covering Pydantic validators (all pass)
- `tests/test_pipeline.py`: 21 tests covering pass behaviour (2 intentionally failing —
  generic-method quarantine not yet implemented in regex)

**Human review:**
- Accepted structure as proposed — domain model accurately reflects the TypeScript AST
  constructs we need to handle
- 2 failing tests left failing intentionally: they define the next implementation task
  (generic type param detection in `translate_methods`)

**Test result:** 31 passed, 2 failed (expected)

---

## Entry 002 — Domain Analysis & Spec

**Timestamp:** 2026-04-14T14:xx
**Interaction type:** Conversational assistance + Research + Code generation
**Prompt used:**
> "What if we use tools like dependency matrix and other ideas to have a better
> overview of the project so that translation becomes correct" — after reading all
> TypeScript source files, interfaces, and competition rules.

**AI suggestion:**
- Created `SPEC.md`: full domain specification with dependency matrix, type surface
  map, library API translation table (Big.js → Decimal, date-fns → datetime,
  lodash → builtins), call graph for ROAI calculator, edge cases, and test oracle
  priority ordering
- Updated `src/models.py`: added 10 new `NodeKind` values for real TS constructs
  (BIG_JS_EXPR, DATE_FNS_CALL, OPTIONAL_CHAIN, etc.), plus new Pydantic models:
  `ImportClassification`, `ImportMapping`, `LibraryMethodMapping`,
  `TypeFieldMapping`, `TypeSurfaceEntry`
- Updated `src/pipeline.py`: expanded from 5 passes to 15 passes in 4 phases:
  structural cleanup → expression rewrites (Big.js, date-fns, lodash, nullish) →
  statement rewrites (variables, for-loops, conditionals) → cleanup (braces,
  semicolons, whitespace)
- Updated `tests/`: 50+ tests covering all new passes and models

**Human review:**
- Validated that dependency matrix approach is rule-compliant (Rule 5 explicitly
  allows AST libraries; Rule 9 provides tt_import_map.json for project-specific config)
- Confirmed Big.js → Decimal is a generic language-level mapping, not domain logic
- SPEC.md added data quality rules (DQ-1 through DQ-5) inspired by birgitta framework

**Test result:** (run after entry)

---

<!-- Future entries follow the same format -->
