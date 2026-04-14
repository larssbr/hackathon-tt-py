"""
Tests for the translation pipeline passes.

These tests define the EXPECTED behaviour. Some will fail until the
corresponding pass is implemented correctly — that's by design (TDD).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src.pipeline import (
    DEFAULT_PASSES,
    TranslationPipeline,
    strip_braces,
    strip_imports,
    translate_class,
    translate_methods,
    translate_returns,
)
from src.models import NodeKind, TranslationStatus


# ---------------------------------------------------------------------------
# strip_imports
# ---------------------------------------------------------------------------

class TestStripImports:
    def test_removes_single_import(self) -> None:
        code = "import { Big } from 'big.js';\nclass Foo {}"
        result = strip_imports(code)
        assert "import" not in result.output
        assert result.nodes_translated == 1

    def test_removes_multiple_imports(self) -> None:
        code = "import A from 'a';\nimport B from 'b';\nconst x = 1;"
        result = strip_imports(code)
        assert result.nodes_translated == 2
        assert "const x = 1;" in result.output

    def test_no_imports_zero_translated(self) -> None:
        result = strip_imports("class Foo {}")
        assert result.nodes_translated == 0
        assert result.nodes_quarantined == 0


# ---------------------------------------------------------------------------
# translate_class
# ---------------------------------------------------------------------------

class TestTranslateClass:
    def test_simple_class(self) -> None:
        code = "export class RoaiPortfolioCalculator extends PortfolioCalculator {"
        result = translate_class(code)
        assert result.output.strip() == "class RoaiPortfolioCalculator(PortfolioCalculator):"
        assert result.nodes_translated == 1

    def test_no_class_zero_translated(self) -> None:
        result = translate_class("const x = 1;")
        assert result.nodes_translated == 0

    def test_export_keyword_removed(self) -> None:
        result = translate_class("export class Foo extends Bar {")
        assert "export" not in result.output


# ---------------------------------------------------------------------------
# translate_methods
# ---------------------------------------------------------------------------

class TestTranslateMethods:
    def test_protected_method(self) -> None:
        code = "  protected calculateOverallPerformance(positions: TimelinePosition[]) {"
        result = translate_methods(code)
        assert "def calculateOverallPerformance(self):" in result.output
        assert result.nodes_translated == 1

    def test_public_async_method(self) -> None:
        code = "  public async getPerformance(): Promise<PortfolioSnapshot> {"
        result = translate_methods(code)
        assert "def getPerformance(self):" in result.output

    def test_generic_params_quarantined(self) -> None:
        code = "  protected getSymbolMetrics<T>({ symbol }: { symbol: string }) {"
        result = translate_methods(code)
        assert result.nodes_quarantined == 1
        assert result.quarantined[0].kind == NodeKind.METHOD
        assert "Generic" in result.quarantined[0].reason

    def test_private_method(self) -> None:
        code = "  private chartDates: string[];"
        # property, not a method call — should not match
        result = translate_methods(code)
        assert result.nodes_translated == 0


# ---------------------------------------------------------------------------
# translate_returns
# ---------------------------------------------------------------------------

class TestTranslateReturns:
    def test_enum_return(self) -> None:
        code = "    return PerformanceCalculationType.ROAI;"
        result = translate_returns(code)
        assert result.output.strip() == 'return "ROAI"'
        assert result.nodes_translated == 1

    def test_no_enum_return_zero_translated(self) -> None:
        result = translate_returns("return someVariable;")
        assert result.nodes_translated == 0

    def test_multiple_returns(self) -> None:
        code = "return A.B;\nreturn C.D;"
        result = translate_returns(code)
        assert result.nodes_translated == 2


# ---------------------------------------------------------------------------
# strip_braces
# ---------------------------------------------------------------------------

class TestStripBraces:
    def test_removes_bare_closing_brace(self) -> None:
        code = "def foo(self):\n    pass\n}\n"
        result = strip_braces(code)
        assert "}" not in result.output
        assert result.nodes_translated == 1

    def test_does_not_remove_inline_brace(self) -> None:
        code = 'data = {"key": "value"}'
        result = strip_braces(code)
        assert result.nodes_translated == 0  # inline dict brace — not bare


# ---------------------------------------------------------------------------
# TranslationPipeline (integration)
# ---------------------------------------------------------------------------

class TestTranslationPipeline:
    SIMPLE_TS = """\
import { Big } from 'big.js';

export class RoaiPortfolioCalculator extends PortfolioCalculator {
  protected getPerformanceCalculationType() {
    return PerformanceCalculationType.ROAI;
  }
}
"""

    def test_full_pipeline_produces_python(self) -> None:
        pipeline = TranslationPipeline()
        result = pipeline.translate(
            self.SIMPLE_TS,
            source_file=Path("test.ts"),
            output_file=Path("test.py"),
        )
        assert "class RoaiPortfolioCalculator(PortfolioCalculator):" in result.output
        assert "def getPerformanceCalculationType(self):" in result.output
        assert 'return "ROAI"' in result.output
        assert "import" not in result.output

    def test_clean_result_has_ok_status(self) -> None:
        pipeline = TranslationPipeline()
        result = pipeline.translate(
            self.SIMPLE_TS,
            source_file=Path("test.ts"),
            output_file=Path("test.py"),
        )
        assert result.status == TranslationStatus.OK
        assert result.is_clean

    def test_passes_applied_in_order(self) -> None:
        pipeline = TranslationPipeline()
        result = pipeline.translate(
            self.SIMPLE_TS,
            source_file=Path("test.ts"),
            output_file=Path("test.py"),
        )
        assert result.passes_applied == [p.__name__ for p in DEFAULT_PASSES]

    def test_quarantined_status_on_generic_method(self) -> None:
        ts = "export class Foo extends Bar {\n  protected getMetrics<T>({ s }: { s: string }) {\n    return s;\n  }\n}"
        pipeline = TranslationPipeline()
        result = pipeline.translate(ts, source_file=Path("f.ts"), output_file=Path("f.py"))
        assert result.status == TranslationStatus.QUARANTINED
        assert result.total_quarantined == 1

    def test_add_pass_extends_pipeline(self) -> None:
        from src.models import PassResult

        def noop_pass(code: str) -> PassResult:
            return PassResult(pass_name="noop", output=code)

        pipeline = TranslationPipeline()
        pipeline.add_pass(noop_pass)
        result = pipeline.translate(
            "class Foo {}",
            source_file=Path("x.ts"),
            output_file=Path("x.py"),
        )
        assert "noop" in result.passes_applied

    def test_translate_file_writes_output(self, tmp_path: Path) -> None:
        src = tmp_path / "calc.ts"
        out = tmp_path / "calc.py"
        src.write_text("export class Foo extends Bar {\n}\n")
        pipeline = TranslationPipeline()
        result = pipeline.translate_file(src, out)
        assert out.exists()
        assert "class Foo(Bar):" in out.read_text()
        assert result.output_file == out
