# prompt-banana 🍌

Collaboration harness for team **Prompt Banana** — Enhanced Hackathon 2026.

This directory contains the structured human–AI collaboration layer for our
TypeScript→Python translation tool (`tt`). It is not the translator itself —
that lives in `tt/`. It is the evidence layer: domain models, pipeline
abstractions, tests, and the interaction log judges can audit.

## What lives here

| Path | Purpose |
|------|---------|
| `src/models.py` | Pydantic models for every pipeline concept (`TranslationResult`, `QuarantinedNode`, etc.) |
| `src/pipeline.py` | Ordered transformation passes + `TranslationPipeline` orchestrator |
| `tests/` | pytest suite — defines expected behaviour before implementation |
| `SPEC.md` | Problem spec, I/O formats, edge cases, data quality rules |
| `PROMPTS.md` | Human–AI interaction log (Treude & Gerosa 2025 taxonomy) |

## Running tests

```bash
uv run --python 3.11 pytest tests/ -v
```

## Design principles

- Every concept has a Pydantic model — no raw dicts crossing boundaries
- Every pass is a pure function `str → PassResult` — easy to test in isolation
- Untranslatable constructs are **quarantined**, not silently dropped
- Tests are written before implementation (TDD)
- All AI suggestions are logged in `PROMPTS.md` with human decisions recorded
