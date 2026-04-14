"""Tests for domain models — all should pass immediately (pure Pydantic validation)."""
from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from src.models import (
    ImportClassification,
    ImportMapping,
    LibraryMethodMapping,
    NodeKind,
    PassResult,
    QuarantinedNode,
    TranslationPipelineConfig,
    TranslationResult,
    TranslationStatus,
    TypeFieldMapping,
    TypeSurfaceEntry,
)


# ---------------------------------------------------------------------------
# QuarantinedNode
# ---------------------------------------------------------------------------

class TestQuarantinedNode:
    def test_valid_node(self) -> None:
        node = QuarantinedNode(
            kind=NodeKind.METHOD,
            ts_source="public foo<T>(): T {",
            reason="Generic type parameter",
        )
        assert node.kind == NodeKind.METHOD

    def test_empty_reason_raises(self) -> None:
        with pytest.raises(ValidationError, match="reason must not be empty"):
            QuarantinedNode(kind=NodeKind.METHOD, ts_source="x", reason="   ")

    def test_optional_line_number(self) -> None:
        node = QuarantinedNode(kind=NodeKind.IMPORT, ts_source="import x", reason="TS import")
        assert node.line_number is None


# ---------------------------------------------------------------------------
# PassResult
# ---------------------------------------------------------------------------

class TestPassResult:
    def test_counts_must_match_list(self) -> None:
        with pytest.raises(ValidationError, match="does not match"):
            PassResult(
                pass_name="test",
                nodes_quarantined=2,  # says 2
                quarantined=[],       # but list is empty
                output="",
            )

    def test_valid_with_quarantine(self) -> None:
        node = QuarantinedNode(kind=NodeKind.METHOD, ts_source="x", reason="test")
        result = PassResult(
            pass_name="translate_methods",
            nodes_translated=3,
            nodes_quarantined=1,
            quarantined=[node],
            output="class Foo(Bar):",
        )
        assert result.nodes_quarantined == 1

    def test_empty_pass(self) -> None:
        result = PassResult(pass_name="strip_imports", output="clean code")
        assert result.nodes_translated == 0
        assert result.nodes_quarantined == 0


# ---------------------------------------------------------------------------
# TranslationResult
# ---------------------------------------------------------------------------

class TestTranslationResult:
    def _make(self, quarantined: list[QuarantinedNode] | None = None) -> TranslationResult:
        return TranslationResult(
            source_file=Path("portfolio-calculator.ts"),
            output_file=Path("portfolio_calculator.py"),
            status=TranslationStatus.OK,
            quarantined=quarantined or [],
        )

    def test_is_clean_when_no_quarantine(self) -> None:
        assert self._make().is_clean is True

    def test_not_clean_with_quarantine(self) -> None:
        node = QuarantinedNode(kind=NodeKind.METHOD, ts_source="x", reason="test")
        result = self._make(quarantined=[node])
        assert result.is_clean is False
        assert result.total_quarantined == 1

    def test_path_fields_accept_strings(self) -> None:
        # Pydantic coerces str → Path
        r = TranslationResult(
            source_file="foo.ts",  # type: ignore[arg-type]
            output_file="foo.py",  # type: ignore[arg-type]
            status=TranslationStatus.OK,
        )
        assert isinstance(r.source_file, Path)


# ---------------------------------------------------------------------------
# TranslationPipelineConfig
# ---------------------------------------------------------------------------

class TestTranslationPipelineConfig:
    def test_defaults(self) -> None:
        cfg = TranslationPipelineConfig()
        assert cfg.source_encoding == "utf-8"
        assert cfg.fail_on_quarantine is False
        assert cfg.indent == "    "

    def test_non_whitespace_indent_raises(self) -> None:
        with pytest.raises(ValidationError, match="only whitespace"):
            TranslationPipelineConfig(indent="xx")

    def test_custom_config(self) -> None:
        cfg = TranslationPipelineConfig(fail_on_quarantine=True, max_method_lines=50)
        assert cfg.fail_on_quarantine is True
        assert cfg.max_method_lines == 50


# ---------------------------------------------------------------------------
# ImportMapping
# ---------------------------------------------------------------------------

class TestImportMapping:
    def test_external_lib_mapping(self) -> None:
        m = ImportMapping(
            ts_module="big.js",
            ts_symbols=["Big"],
            classification=ImportClassification.EXTERNAL_LIB,
            py_module="decimal",
            py_symbols=["Decimal"],
        )
        assert m.classification == ImportClassification.EXTERNAL_LIB
        assert m.py_module == "decimal"

    def test_internal_provided(self) -> None:
        m = ImportMapping(
            ts_module="@ghostfolio/api/app/portfolio/calculator/portfolio-calculator",
            ts_symbols=["PortfolioCalculator"],
            classification=ImportClassification.INTERNAL_PROVIDED,
            notes="Already in wrapper layer",
        )
        assert m.classification == ImportClassification.INTERNAL_PROVIDED

    def test_framework_drop(self) -> None:
        m = ImportMapping(
            ts_module="@nestjs/common",
            ts_symbols=["Logger"],
            classification=ImportClassification.FRAMEWORK_DROP,
        )
        assert m.py_module is None


# ---------------------------------------------------------------------------
# LibraryMethodMapping
# ---------------------------------------------------------------------------

class TestLibraryMethodMapping:
    def test_operator_mapping(self) -> None:
        m = LibraryMethodMapping(
            ts_pattern=".plus(",
            py_replacement=" + (",
            is_operator=True,
        )
        assert m.is_operator is True

    def test_function_mapping(self) -> None:
        m = LibraryMethodMapping(
            ts_pattern="cloneDeep(",
            py_replacement="copy.deepcopy(",
            is_operator=False,
        )
        assert m.is_operator is False


# ---------------------------------------------------------------------------
# TypeSurfaceEntry
# ---------------------------------------------------------------------------

class TestTypeSurfaceEntry:
    def test_symbol_metrics_entry(self) -> None:
        entry = TypeSurfaceEntry(
            ts_interface="SymbolMetrics",
            ts_file="libs/common/src/lib/interfaces/symbol-metrics.interface.ts",
            fields=[
                TypeFieldMapping(ts_name="grossPerformance", ts_type="Big", py_type="Decimal"),
                TypeFieldMapping(ts_name="netPerformance", ts_type="Big", py_type="Decimal"),
                TypeFieldMapping(ts_name="hasErrors", ts_type="boolean", py_type="bool"),
            ],
        )
        assert len(entry.fields) == 3
        assert entry.fields[0].py_type == "Decimal"

    def test_default_representation_is_dict(self) -> None:
        entry = TypeSurfaceEntry(
            ts_interface="PortfolioOrder",
            ts_file="interfaces/portfolio-order.interface.ts",
        )
        assert entry.py_representation == "dict"
