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

<!-- Future entries follow the same format -->
