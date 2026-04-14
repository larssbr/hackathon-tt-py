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
    VARIABLE_DECL = "variable_decl"
    FOR_LOOP = "for_loop"
    CONDITIONAL = "conditional"
    BIG_JS_EXPR = "big_js_expr"
    DATE_FNS_CALL = "date_fns_call"
    LODASH_CALL = "lodash_call"
    OPTIONAL_CHAIN = "optional_chain"
    NULLISH_COALESCE = "nullish_coalesce"
    TYPE_ANNOTATION = "type_annotation"
    OBJECT_DESTRUCTURE = "object_destructure"
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
    import_map_path: Path | None = None  # project-specific tt_import_map.json

    @model_validator(mode="after")
    def indent_must_be_whitespace(self) -> "TranslationPipelineConfig":
        if self.indent.strip():
            raise ValueError("indent must contain only whitespace characters")
        return self


# ---------------------------------------------------------------------------
# Dependency analysis models
# ---------------------------------------------------------------------------


class ImportClassification(str, Enum):
    """How an import should be handled during translation."""

    EXTERNAL_LIB = "external_lib"         # Big.js, date-fns, lodash → Python equiv
    INTERNAL_PROVIDED = "internal_provided"  # already in wrapper/scaffold
    INTERNAL_TRANSLATE = "internal_translate"  # must be translated
    FRAMEWORK_DROP = "framework_drop"       # NestJS decorators, Prisma → drop


class ImportMapping(BaseModel):
    """Maps one TypeScript import to its Python translation strategy."""

    ts_module: str           # e.g. 'big.js', 'date-fns', '@ghostfolio/common/helper'
    ts_symbols: list[str]    # e.g. ['Big'], ['format', 'isBefore']
    classification: ImportClassification
    py_module: str | None = None   # e.g. 'decimal', 'datetime'
    py_symbols: list[str] = Field(default_factory=list)  # e.g. ['Decimal']
    notes: str = ""


class LibraryMethodMapping(BaseModel):
    """Maps a single library method call from TypeScript to Python."""

    ts_pattern: str      # e.g. '.plus(', 'new Big('
    py_replacement: str  # e.g. ' + ', 'Decimal('
    is_operator: bool = False   # True if TS method becomes Python operator
    notes: str = ""


class TypeFieldMapping(BaseModel):
    """Maps a TypeScript interface field to its Python equivalent."""

    ts_name: str         # e.g. 'grossPerformance'
    ts_type: str         # e.g. 'Big'
    py_type: str         # e.g. 'Decimal'
    py_name: str | None = None  # if different from ts_name (snake_case conversion)


class TypeSurfaceEntry(BaseModel):
    """Describes one TypeScript interface and its Python representation."""

    ts_interface: str     # e.g. 'SymbolMetrics'
    ts_file: str          # source file path
    fields: list[TypeFieldMapping] = Field(default_factory=list)
    py_representation: str = "dict"  # 'dict', 'TypedDict', 'dataclass'
