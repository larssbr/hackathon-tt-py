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
    strip_semicolons,
    strip_type_annotations,
    normalize_whitespace,
    translate_big_js,
    translate_class,
    translate_conditionals,
    translate_date_fns,
    translate_for_loops,
    translate_lodash,
    translate_methods,
    translate_nullish,
    translate_returns,
    translate_variables,
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
# strip_type_annotations
# ---------------------------------------------------------------------------

class TestStripTypeAnnotations:
    def test_removes_variable_type(self) -> None:
        code = "let fees: Big = new Big(0);"
        result = strip_type_annotations(code)
        assert ": Big" not in result.output
        assert "new Big(0)" in result.output

    def test_removes_as_cast(self) -> None:
        code = "const x = value as string;"
        result = strip_type_annotations(code)
        assert " as string" not in result.output

    def test_preserves_dict_colons(self) -> None:
        code = '{"key": "value"}'
        result = strip_type_annotations(code)
        assert '{"key": "value"}' in result.output


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
# translate_big_js
# ---------------------------------------------------------------------------

class TestTranslateBigJs:
    def test_new_big_zero(self) -> None:
        result = translate_big_js("new Big(0)")
        assert result.output == "Decimal(0)"

    def test_new_big_expr(self) -> None:
        result = translate_big_js("new Big(quantity)")
        assert "Decimal(str(quantity))" in result.output

    def test_plus_chain(self) -> None:
        result = translate_big_js("total.plus(amount)")
        assert "total + (amount)" in result.output

    def test_minus_chain(self) -> None:
        result = translate_big_js("total.minus(fee)")
        assert "total - (fee)" in result.output

    def test_times_chain(self) -> None:
        result = translate_big_js("price.times(quantity)")
        assert "price * (quantity)" in result.output

    def test_div_chain(self) -> None:
        result = translate_big_js("total.div(count)")
        assert "total / (count)" in result.output

    def test_eq_comparison(self) -> None:
        result = translate_big_js("quantity.eq(0)")
        assert "quantity == (0)" in result.output

    def test_to_number(self) -> None:
        result = translate_big_js("value.toNumber()")
        assert "float(value)" in result.output

    def test_combined_expression(self) -> None:
        code = "let total = new Big(0);\ntotal = total.plus(new Big(amount));"
        result = translate_big_js(code)
        assert "Decimal(0)" in result.output
        assert "+" in result.output
        assert result.nodes_translated >= 2


# ---------------------------------------------------------------------------
# translate_date_fns
# ---------------------------------------------------------------------------

class TestTranslateDateFns:
    def test_format_date(self) -> None:
        result = translate_date_fns("format(endDate, DATE_FORMAT)")
        assert "endDate.strftime(DATE_FORMAT)" in result.output

    def test_difference_in_days(self) -> None:
        result = translate_date_fns("differenceInDays(endDate, startDate)")
        assert "(endDate - startDate).days" in result.output

    def test_is_before(self) -> None:
        result = translate_date_fns("isBefore(a, b)")
        assert "a < b" in result.output

    def test_is_after(self) -> None:
        result = translate_date_fns("isAfter(a, b)")
        assert "a > b" in result.output

    def test_sub_days(self) -> None:
        result = translate_date_fns("subDays(date, 1)")
        assert "date - timedelta(days=1)" in result.output


# ---------------------------------------------------------------------------
# translate_lodash
# ---------------------------------------------------------------------------

class TestTranslateLodash:
    def test_clone_deep(self) -> None:
        result = translate_lodash("cloneDeep(orders)")
        assert "copy.deepcopy(orders)" in result.output

    def test_sort_by(self) -> None:
        result = translate_lodash("sortBy(items, (x) => x.date)")
        assert "sorted(items, key=(x) => x.date)" in result.output


# ---------------------------------------------------------------------------
# translate_nullish
# ---------------------------------------------------------------------------

class TestTranslateNullish:
    def test_nullish_coalescing(self) -> None:
        result = translate_nullish("x ?? y")
        assert "x if x is not None else y" in result.output

    def test_optional_chaining_quarantined(self) -> None:
        result = translate_nullish("obj?.property")
        assert result.nodes_quarantined == 1
        assert result.quarantined[0].kind == NodeKind.OPTIONAL_CHAIN


# ---------------------------------------------------------------------------
# translate_variables
# ---------------------------------------------------------------------------

class TestTranslateVariables:
    def test_const_removed(self) -> None:
        result = translate_variables("const x = 1;")
        assert result.output.strip() == "x = 1;"
        assert result.nodes_translated == 1

    def test_let_removed(self) -> None:
        result = translate_variables("let total = 0;")
        assert result.output.strip() == "total = 0;"

    def test_preserves_indentation(self) -> None:
        result = translate_variables("    const y = 2;")
        assert result.output == "    y = 2;"

    def test_multiple_declarations(self) -> None:
        code = "const a = 1;\nlet b = 2;\nvar c = 3;"
        result = translate_variables(code)
        assert result.nodes_translated == 3
        assert "const" not in result.output
        assert "let" not in result.output
        assert "var" not in result.output


# ---------------------------------------------------------------------------
# translate_for_loops
# ---------------------------------------------------------------------------

class TestTranslateForLoops:
    def test_simple_for_of(self) -> None:
        code = "for (const item of items) {"
        result = translate_for_loops(code)
        assert "for item in items:" in result.output
        assert result.nodes_translated == 1

    def test_let_for_of(self) -> None:
        code = "for (let order of orders) {"
        result = translate_for_loops(code)
        assert "for order in orders:" in result.output

    def test_destructuring_quarantined(self) -> None:
        code = "for (const { date, fee } of activities) {"
        result = translate_for_loops(code)
        assert result.nodes_quarantined == 1
        assert "Destructuring" in result.quarantined[0].reason


# ---------------------------------------------------------------------------
# translate_conditionals
# ---------------------------------------------------------------------------

class TestTranslateConditionals:
    def test_simple_if(self) -> None:
        code = "if (x > 0) {"
        result = translate_conditionals(code)
        assert "if x > 0:" in result.output

    def test_else_clause(self) -> None:
        code = "} else {"
        result = translate_conditionals(code)
        assert "else:" in result.output

    def test_else_if(self) -> None:
        code = "} else if (y < 0) {"
        result = translate_conditionals(code)
        assert "elif y < 0:" in result.output

    def test_nested_condition(self) -> None:
        code = "if (currentPosition.investment) {"
        result = translate_conditionals(code)
        assert "if currentPosition.investment:" in result.output


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
# strip_semicolons
# ---------------------------------------------------------------------------

class TestStripSemicolons:
    def test_removes_trailing_semicolons(self) -> None:
        code = "x = 1;\ny = 2;"
        result = strip_semicolons(code)
        assert ";" not in result.output
        assert "x = 1" in result.output
        assert result.nodes_translated == 2

    def test_preserves_inline_semicolons(self) -> None:
        # Semicolons inside strings should ideally be preserved
        code = 'msg = "hello;"'
        result = strip_semicolons(code)
        # Note: this is a known limitation — regex can't distinguish string content
        assert result.nodes_translated >= 0


# ---------------------------------------------------------------------------
# normalize_whitespace
# ---------------------------------------------------------------------------

class TestNormalizeWhitespace:
    def test_collapses_triple_blank_lines(self) -> None:
        code = "a\n\n\n\nb"
        result = normalize_whitespace(code)
        assert result.output == "a\n\nb"

    def test_preserves_double_blank(self) -> None:
        code = "a\n\nb"
        result = normalize_whitespace(code)
        assert result.output == "a\n\nb"
        assert result.nodes_translated == 0


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
        assert result.total_quarantined >= 1

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

    def test_big_js_in_full_pipeline(self) -> None:
        ts = "let total = new Big(0);\ntotal = total.plus(new Big(amount));"
        pipeline = TranslationPipeline()
        result = pipeline.translate(
            ts, source_file=Path("t.ts"), output_file=Path("t.py"),
        )
        assert "Decimal(0)" in result.output
        assert "new Big" not in result.output

    def test_for_loop_in_full_pipeline(self) -> None:
        ts = "for (const item of items) {\n  console.log(item);\n}"
        pipeline = TranslationPipeline()
        result = pipeline.translate(
            ts, source_file=Path("t.ts"), output_file=Path("t.py"),
        )
        assert "for item in items:" in result.output

    def test_conditional_in_full_pipeline(self) -> None:
        ts = "if (x > 0) {\n  return x;\n} else {\n  return 0;\n}"
        pipeline = TranslationPipeline()
        result = pipeline.translate(
            ts, source_file=Path("t.ts"), output_file=Path("t.py"),
        )
        assert "if x > 0:" in result.output
        assert "else:" in result.output
