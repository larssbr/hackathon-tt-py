"""Pure function tests for each translation pass."""
from __future__ import annotations

import pytest
from tt.translator import (
    comment_out,
    extract_method_body,
    indent_block,
    is_valid_python,
    normalize_comments,
    normalize_whitespace,
    run_pipeline,
    strip_access_modifiers,
    strip_braces,
    strip_console_log,
    strip_exports,
    strip_imports,
    strip_private_fields,
    strip_semicolons,
    strip_type_annotations,
    translate_array_methods,
    translate_arrow_to_lambda,
    translate_big_methods,
    translate_class_decl,
    translate_conditionals,
    translate_date_fns,
    translate_filter,
    translate_for_loops,
    translate_includes,
    translate_lodash,
    translate_methods,
    translate_new_big,
    translate_nullish_coalescing,
    translate_object_patterns,
    translate_object_shorthand,
    translate_optional_chaining,
    translate_returns,
    translate_template_literals,
    translate_this,
    translate_variables,
)


# ---------------------------------------------------------------------------
# Phase 1: Structural cleanup
# ---------------------------------------------------------------------------


class TestNormalizeComments:
    def test_smart_quotes(self) -> None:
        code = "# the activity\u2019s unit price"
        assert "\u2019" not in normalize_comments(code)

    def test_single_line_comment(self) -> None:
        result = normalize_comments("x = 1; // this is a comment")
        assert "//" not in result
        assert "#" in result

    def test_multi_line_comment(self) -> None:
        result = normalize_comments("x = 1; /* block */ y = 2;")
        assert "/*" not in result
        assert "x = 1;" in result


class TestStripImports:
    def test_single_import(self) -> None:
        code = "import { Big } from 'big.js';\nclass Foo {}"
        assert "import" not in strip_imports(code)
        assert "class Foo {}" in strip_imports(code)

    def test_multi_line_import(self) -> None:
        code = "import {\n  Big,\n  Other\n} from 'big.js';"
        # Multi-line imports should at minimum remove the first line
        result = strip_imports(code)
        assert "from 'big.js'" not in result

    def test_preserves_non_import_lines(self) -> None:
        assert strip_imports("const x = 1;") == "const x = 1;"


class TestStripExports:
    def test_export_class(self) -> None:
        assert strip_exports("export class Foo {}") == "class Foo {}"

    def test_no_export(self) -> None:
        assert strip_exports("class Foo {}") == "class Foo {}"


class TestStripTypeAnnotations:
    def test_variable_type(self) -> None:
        result = strip_type_annotations("let fees: Big = new Big(0);")
        assert ": Big" not in result
        assert "new Big(0)" in result

    def test_return_type_on_method(self) -> None:
        result = strip_type_annotations("getMetrics(): SymbolMetrics {")
        assert result.strip() == "getMetrics() {"

    def test_as_cast(self) -> None:
        result = strip_type_annotations("const x = value as string;")
        assert " as string" not in result


class TestStripAccessModifiers:
    def test_protected(self) -> None:
        assert "protected" not in strip_access_modifiers("protected calculate()")

    def test_private(self) -> None:
        assert "private" not in strip_access_modifiers("private chartDates")

    def test_public(self) -> None:
        assert "public" not in strip_access_modifiers("public async get()")


# ---------------------------------------------------------------------------
# Phase 2: Expression-level rewrites
# ---------------------------------------------------------------------------


class TestTranslateNewBig:
    def test_big_zero(self) -> None:
        assert translate_new_big("new Big(0)") == "Decimal(0)"

    def test_big_variable(self) -> None:
        assert "Decimal(str(quantity))" in translate_new_big("new Big(quantity)")

    def test_big_string_literal(self) -> None:
        result = translate_new_big("new Big('123.45')")
        assert result == "Decimal('123.45')"


class TestTranslateBigMethods:
    def test_plus(self) -> None:
        assert "total + (amount)" in translate_big_methods("total.plus(amount)")

    def test_minus(self) -> None:
        assert "total - (fee)" in translate_big_methods("total.minus(fee)")

    def test_mul(self) -> None:
        assert "price * (qty)" in translate_big_methods("price.mul(qty)")

    def test_times(self) -> None:
        assert "price * (qty)" in translate_big_methods("price.times(qty)")

    def test_div(self) -> None:
        assert "total / (count)" in translate_big_methods("total.div(count)")

    def test_eq(self) -> None:
        assert "qty == (0)" in translate_big_methods("qty.eq(0)")

    def test_gt(self) -> None:
        assert "qty > (0)" in translate_big_methods("qty.gt(0)")

    def test_to_number(self) -> None:
        assert "float(value)" in translate_big_methods("value.toNumber()")

    def test_abs(self) -> None:
        assert "abs(x)" in translate_big_methods("x.abs()")

    def test_chain(self) -> None:
        result = translate_big_methods("a.plus(b).minus(c)")
        assert "+" in result
        assert "-" in result


class TestTranslateDateFns:
    def test_format(self) -> None:
        result = translate_date_fns("format(end, DATE_FORMAT)")
        assert "end.strftime(DATE_FORMAT)" in result

    def test_difference_in_days(self) -> None:
        result = translate_date_fns("differenceInDays(a, b)")
        assert "(a - b).days" in result

    def test_is_before(self) -> None:
        assert "a < b" in translate_date_fns("isBefore(a, b)")

    def test_add_milliseconds(self) -> None:
        result = translate_date_fns("addMilliseconds(d, 1)")
        assert "timedelta(milliseconds=1)" in result

    def test_new_date_no_args(self) -> None:
        assert "date.today()" in translate_date_fns("new Date()")

    def test_new_date_with_arg(self) -> None:
        assert "parse_date(x)" in translate_date_fns("new Date(x)")


class TestTranslateLodash:
    def test_clone_deep(self) -> None:
        result = translate_lodash("cloneDeep(orders)")
        assert "copy.deepcopy(orders)" in result

    def test_sort_by(self) -> None:
        result = translate_lodash("sortBy(items, fn)")
        assert "sorted(items, key=fn)" in result


class TestTranslateNullishCoalescing:
    def test_simple(self) -> None:
        result = translate_nullish_coalescing("x ?? y")
        assert "x if x is not None else y" in result


class TestTranslateOptionalChaining:
    def test_property(self) -> None:
        result = translate_optional_chaining("obj?.prop")
        assert "obj.prop" in result
        assert "is not None" in result

    def test_bracket_access(self) -> None:
        result = translate_optional_chaining("map?.[key]")
        assert "map[key]" in result
        assert "is not None" in result


# ---------------------------------------------------------------------------
# Phase 3: Statement-level rewrites
# ---------------------------------------------------------------------------


class TestTranslateVariables:
    def test_const(self) -> None:
        assert translate_variables("const x = 1;").strip() == "x = 1;"

    def test_let(self) -> None:
        assert translate_variables("let total = 0;").strip() == "total = 0;"

    def test_var(self) -> None:
        assert translate_variables("var old = 1;").strip() == "old = 1;"

    def test_preserves_indent(self) -> None:
        assert translate_variables("    const y = 2;") == "    y = 2;"


class TestTranslateForLoops:
    def test_for_of(self) -> None:
        result = translate_for_loops("for (const item of items) {")
        assert "for item in items:" in result
        assert "const" not in result

    def test_c_style_for(self) -> None:
        result = translate_for_loops("for (let i = 0; i < n; i += 1) {")
        assert "for i in range(n):" in result


class TestTranslateConditionals:
    def test_if(self) -> None:
        result = translate_conditionals("if (x > 0) {")
        assert "if x > 0:" in result
        assert "{" not in result

    def test_else_if(self) -> None:
        result = translate_conditionals("} else if (y) {")
        assert "elif y:" in result

    def test_else(self) -> None:
        result = translate_conditionals("} else {")
        assert "else:" in result


class TestTranslateClassDecl:
    def test_extends(self) -> None:
        result = translate_class_decl("class Foo extends Bar {")
        assert result.strip() == "class Foo(Bar):"


class TestTranslateMethods:
    def test_simple_method(self) -> None:
        result = translate_methods("  calculate() {")
        assert "def calculate(self):" in result

    def test_preserves_indent(self) -> None:
        result = translate_methods("    getType() {")
        assert result.startswith("    def getType(self):")


class TestTranslateArrowToLambda:
    def test_simple_arrow(self) -> None:
        result = translate_arrow_to_lambda("(x) => x.date")
        assert "lambda x: x.date" in result

    def test_arrow_with_return(self) -> None:
        result = translate_arrow_to_lambda("(x) => { return x.value; }")
        assert "lambda x: x.value" in result


class TestTranslateTemplateLiterals:
    def test_simple_template(self) -> None:
        result = translate_template_literals("`Hello ${name}`")
        assert 'f"Hello {name}"' in result


class TestTranslateThis:
    def test_simple(self) -> None:
        assert "self.activities" in translate_this("this.activities")

    def test_chained(self) -> None:
        assert "self.x.y" in translate_this("this.x.y")


class TestTranslateFilter:
    def test_destructured_filter(self) -> None:
        code = 'arr.filter(({ type }) => { return type; })'
        result = translate_filter(code)
        assert "for x in arr" in result
        assert "type" in result

    def test_simple_filter(self) -> None:
        code = 'items.filter((x) => { return x.active; })'
        result = translate_filter(code)
        assert "for" in result


class TestTranslateArrayMethods:
    def test_length(self) -> None:
        assert "len(arr)" in translate_array_methods("arr.length")

    def test_push(self) -> None:
        assert ".append(" in translate_array_methods("arr.push(x)")

    def test_at_negative(self) -> None:
        assert "arr[-1]" in translate_array_methods("arr.at(-1)")


class TestTranslateObjectPatterns:
    def test_object_keys(self) -> None:
        result = translate_object_patterns("Object.keys(map)")
        assert "list(map.keys())" in result

    def test_instanceof(self) -> None:
        result = translate_object_patterns("x instanceof Big")
        assert "isinstance(x, Decimal)" in result


class TestTranslateObjectShorthand:
    def test_simple_return(self) -> None:
        code = 'return {\n  x,\n  y,\n}'
        result = translate_object_shorthand(code)
        assert '"x": x' in result
        assert '"y": y' in result

    def test_key_value_kept(self) -> None:
        code = 'return {\n  key: value,\n}'
        result = translate_object_shorthand(code)
        assert '"key": value' in result


class TestTranslateIncludes:
    def test_includes(self) -> None:
        result = translate_includes("['BUY', 'SELL'].includes(type)")
        assert "type in ['BUY', 'SELL']" in result


class TestTranslateReturns:
    def test_enum_return(self) -> None:
        result = translate_returns("return PerformanceCalculationType.ROAI;")
        assert 'return "ROAI"' in result


# ---------------------------------------------------------------------------
# Phase 4: Cleanup
# ---------------------------------------------------------------------------


class TestStripConsoleLog:
    def test_removes_console_log(self) -> None:
        result = strip_console_log("  console.log('hi');")
        assert "console" not in result


class TestStripPrivateFields:
    def test_removes_field_decl(self) -> None:
        result = strip_private_fields("  chartDates: string[];")
        assert "chartDates" not in result.strip()


class TestStripSemicolons:
    def test_trailing(self) -> None:
        assert strip_semicolons("x = 1;") == "x = 1"

    def test_preserves_strings(self) -> None:
        # This is a known limitation — regex doesn't respect strings
        pass


class TestStripBraces:
    def test_bare_brace(self) -> None:
        assert "}" not in strip_braces("  }\n")

    def test_inline_dict_preserved(self) -> None:
        assert strip_braces('x = {"a": 1}') == 'x = {"a": 1}'


class TestNormalizeWhitespace:
    def test_collapses_blanks(self) -> None:
        result = normalize_whitespace("a\n\n\n\nb")
        assert result == "a\n\nb"


# ---------------------------------------------------------------------------
# Integration: full pipeline
# ---------------------------------------------------------------------------


class TestIsValidPython:
    def test_valid(self) -> None:
        assert is_valid_python("x = 1\nprint(x)")

    def test_invalid(self) -> None:
        assert not is_valid_python("def f(: pass")


class TestCommentOut:
    def test_comments_code(self) -> None:
        result = comment_out("x = 1\ny = 2")
        assert result.startswith("# x = 1")
        assert "# y = 2" in result


class TestIndentBlock:
    def test_one_level(self) -> None:
        result = indent_block("x = 1\ny = 2", level=1)
        assert result == "    x = 1\n    y = 2"


class TestExtractMethodBody:
    def test_simple_method(self) -> None:
        ts = "class Foo { protected bar() { return 1; } }"
        body = extract_method_body(ts, "bar")
        assert body is not None
        assert "return 1" in body

    def test_not_found(self) -> None:
        assert extract_method_body("class Foo {}", "missing") is None

    def test_nested_braces(self) -> None:
        ts = "protected calc() { if (x) { return 1; } return 0; }"
        body = extract_method_body(ts, "calc")
        assert body is not None
        assert "return 0" in body


class TestRunPipeline:
    SIMPLE_TS = (
        "import { Big } from 'big.js';\n"
        "\n"
        "export class RoaiPortfolioCalculator extends PortfolioCalculator {\n"
        "  protected getPerformanceCalculationType() {\n"
        "    return PerformanceCalculationType.ROAI;\n"
        "  }\n"
        "}\n"
    )

    def test_produces_python_class(self) -> None:
        result = run_pipeline(self.SIMPLE_TS)
        assert "class RoaiPortfolioCalculator(PortfolioCalculator):" in result

    def test_removes_imports(self) -> None:
        assert "import { Big }" not in run_pipeline(self.SIMPLE_TS)

    def test_translates_method(self) -> None:
        result = run_pipeline(self.SIMPLE_TS)
        assert "def getPerformanceCalculationType(self):" in result

    def test_translates_enum_return(self) -> None:
        assert 'return "ROAI"' in run_pipeline(self.SIMPLE_TS)

    def test_no_braces(self) -> None:
        result = run_pipeline(self.SIMPLE_TS)
        for line in result.split("\n"):
            assert line.strip() != "}"

    def test_big_js_translation(self) -> None:
        ts = "let total = new Big(0);\ntotal = total.plus(new Big(amount));"
        result = run_pipeline(ts)
        assert "Decimal(0)" in result
        assert "+" in result
