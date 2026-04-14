"""
Domain models for the tt translation pipeline.

Every external input and pipeline result is validated here via Pydantic.
These models reflect the actual structure of the TypeScript→Python translation
problem: a source file passes through ordered transformation passes, each node
is either translated cleanly or quarantined with a reason.
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, model_validator


class NodeKind(str, Enum):
    """TypeScript AST node categories the pipeline recognises."""

    CLASS = "class"
    METHOD = "method"
    PROPERTY = "property"
    IMPORT = "import"
    ENUM_REF = "enum_ref"
    GENERIC_TYPE = "generic_type"
    ARROW_FUNCTION = "arrow_function"
    UNKNOWN = "unknown"


class TranslationStatus(str, Enum):
    OK = "ok"
    QUARANTINED = "quarantined"  # translated with losses — needs human review
    SKIPPED = "skipped"          # intentionally not translated (e.g. type-only)


class QuarantinedNode(BaseModel):
    """A TypeScript construct the pipeline could not translate cleanly."""

    kind: NodeKind
    ts_source: str
    reason: str
    line_number: int | None = None

    @model_validator(mode="after")
    def reason_must_be_non_empty(self) -> "QuarantinedNode":
        if not self.reason.strip():
            raise ValueError("QuarantinedNode.reason must not be empty")
        return self


class PassResult(BaseModel):
    """Outcome of a single transformation pass over a code string."""

    pass_name: str
    nodes_translated: int = 0
    nodes_quarantined: int = 0
    quarantined: list[QuarantinedNode] = Field(default_factory=list)
    output: str  # code after this pass

    @model_validator(mode="after")
    def counts_match_list(self) -> "PassResult":
        if self.nodes_quarantined != len(self.quarantined):
            raise ValueError(
                f"nodes_quarantined={self.nodes_quarantined} "
                f"does not match len(quarantined)={len(self.quarantined)}"
            )
        return self


class TranslationResult(BaseModel):
    """Full result of translating one TypeScript source file."""

    source_file: Path
    output_file: Path
    status: TranslationStatus
    passes_applied: list[str] = Field(default_factory=list)
    pass_results: list[PassResult] = Field(default_factory=list)
    quarantined: list[QuarantinedNode] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    output: str = ""

    @property
    def is_clean(self) -> bool:
        """True when no nodes were quarantined."""
        return len(self.quarantined) == 0

    @property
    def total_quarantined(self) -> int:
        return len(self.quarantined)


class TranslationPipelineConfig(BaseModel):
    """Runtime configuration for the translation pipeline."""

    source_encoding: str = "utf-8"
    fail_on_quarantine: bool = False
    max_method_lines: int = 200
    indent: str = "    "  # 4 spaces — PEP 8
    passes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def indent_must_be_whitespace(self) -> "TranslationPipelineConfig":
        if self.indent.strip():
            raise ValueError("indent must contain only whitespace characters")
        return self
