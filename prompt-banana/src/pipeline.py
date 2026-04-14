"""
Translation pipeline for TypeScript → Python.

The pipeline runs an ordered sequence of transformation passes over a
TypeScript source string. Each pass is a pure function: str → PassResult.
Order matters — later passes depend on earlier ones having already rewritten
the code (e.g. imports must be stripped before class-body passes run).

Pass order:
  Phase 1 — Structural cleanup:
    1. strip_imports         — remove TS import statements
    2. strip_type_annotations — remove TS-only type info (:Type, <Generic>, as X)
    3. translate_class       — rewrite class/extends declarations

  Phase 2 — Expression-level rewrites (order-sensitive):
    4. translate_big_js      — Big.js method chains → Decimal operators
    5. translate_date_fns    — date-fns calls → datetime equivalents
    6. translate_lodash      — lodash calls → Python builtins
    7. translate_nullish     — ??, ?. → Python guard expressions

  Phase 3 — Statement-level rewrites:
    8. translate_variables   — const/let/var → Python assignment
    9. translate_for_loops   — for (const x of y) → for x in y:
   10. translate_conditionals — if (x) { → if x:
   11. translate_methods     — method signatures (drop visibility/types)
   12. translate_returns     — enum return statements

  Phase 4 — Cleanup:
   13. strip_braces          — remove bare closing braces
   14. strip_semicolons      — remove trailing semicolons
   15. normalize_whitespace  — collapse blank lines

Anything the passes cannot handle is quarantined with a reason string so a
human (or a later, smarter pass) can finish the job.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from .models import (
    NodeKind,
    PassResult,
    QuarantinedNode,
    TranslationPipelineConfig,
    TranslationResult,
    TranslationStatus,
)

# A Pass is a callable: (code: str) -> PassResult
Pass = Callable[[str], PassResult]


# ---------------------------------------------------------------------------
# Individual passes
# ---------------------------------------------------------------------------

def strip_imports(code: str) -> PassResult:
    """Remove TypeScript import lines; Python imports are added by the scaffold."""
    pattern = re.compile(r"^import\s+.*?;?\s*$", re.MULTILINE)
    matches = pattern.findall(code)
    output = pattern.sub("", code)
    return PassResult(
        pass_name="strip_imports",
        nodes_translated=len(matches),
        nodes_quarantined=0,
        output=output,
    )


def translate_class(code: str) -> PassResult:
    """Rewrite `export class X extends Y {` → `class X(Y):`."""
    pattern = re.compile(r"export\s+class\s+(\w+)\s+extends\s+(\w+)\s*\{")
    matches = pattern.findall(code)
    output = pattern.sub(r"class \1(\2):", code)
    return PassResult(
        pass_name="translate_class",
        nodes_translated=len(matches),
        nodes_quarantined=0,
        output=output,
    )


def translate_methods(code: str) -> PassResult:
    """
    Rewrite TS method signatures to Python `def` equivalents.

    Handles: `public/protected/private async? name(params): ReturnType {`
    Quarantines methods with generic type parameters — those need manual review.
    """
    quarantined: list[QuarantinedNode] = []
    translated = 0

    def replace(m: re.Match[str]) -> str:
        nonlocal translated
        name = m.group("name")
        params = m.group("params")
        if "<" in params:
            quarantined.append(
                QuarantinedNode(
                    kind=NodeKind.METHOD,
                    ts_source=m.group(0),
                    reason="Generic type parameters in method signature require manual translation",
                )
            )
            return m.group(0)  # leave unchanged
        translated += 1
        return f"def {name}(self):"

    pattern = re.compile(
        r"(?:public|protected|private)?\s*(?:async\s+)?(?P<name>\w+)"
        r"\s*\((?P<params>[^)]*)\)\s*(?::\s*[\w<>\[\]|, ]+)?\s*\{",
    )
    output = pattern.sub(replace, code)
    return PassResult(
        pass_name="translate_methods",
        nodes_translated=translated,
        nodes_quarantined=len(quarantined),
        quarantined=quarantined,
        output=output,
    )


def translate_returns(code: str) -> PassResult:
    """Rewrite `return Enum.VALUE;` → `return "VALUE"`."""
    pattern = re.compile(r"return\s+(\w+)\.(\w+);")
    matches = pattern.findall(code)
    output = pattern.sub(r'return "\2"', code)
    return PassResult(
        pass_name="translate_returns",
        nodes_translated=len(matches),
        nodes_quarantined=0,
        output=output,
    )


def strip_type_annotations(code: str) -> PassResult:
    """Remove TypeScript type annotations that have no Python equivalent.

    Handles: `: Type`, `as Type`, generic type params in variable positions.
    Does NOT touch class-level or method-level generics (those are in other passes).
    """
    translated = 0

    # Remove `: TypeName` from variable declarations (but not dict keys)
    # e.g. `let fees: Big = new Big(0)` → `let fees = new Big(0)`
    type_ann = re.compile(r":\s*[\w<>\[\]|, ]+(?=\s*[=;,)\]}])")
    type_matches = type_ann.findall(code)
    output = type_ann.sub("", code)
    translated += len(type_matches)

    # Remove `as TypeName` casts
    as_cast = re.compile(r"\s+as\s+\w[\w<>\[\]|, ]*")
    as_matches = as_cast.findall(output)
    output = as_cast.sub("", output)
    translated += len(as_matches)

    return PassResult(
        pass_name="strip_type_annotations",
        nodes_translated=translated,
        nodes_quarantined=0,
        output=output,
    )


def translate_big_js(code: str) -> PassResult:
    """Rewrite Big.js expressions to Python Decimal equivalents.

    Mapping:
        new Big(x)     → Decimal(str(x))  /  Decimal(0) for literal zero
        .plus(expr)    → + (expr)
        .minus(expr)   → - (expr)
        .times(expr)   → * (expr)
        .div(expr)     → / (expr)
        .eq(expr)      → == (expr)
        .gt(expr)      → > (expr)
        .gte(expr)     → >= (expr)
        .lt(expr)      → < (expr)
        .lte(expr)     → <= (expr)
        .abs()         → abs(...)
        .toNumber()    → float(...)
        .round(n)      → round(..., n)
    """
    translated = 0
    quarantined: list[QuarantinedNode] = []
    output = code

    # new Big(0) → Decimal(0)
    pattern_big_zero = re.compile(r"new\s+Big\(\s*0\s*\)")
    matches = pattern_big_zero.findall(output)
    output = pattern_big_zero.sub("Decimal(0)", output)
    translated += len(matches)

    # new Big(expr) → Decimal(str(expr))
    pattern_big = re.compile(r"new\s+Big\(([^)]+)\)")
    matches = pattern_big.findall(output)
    output = pattern_big.sub(r"Decimal(str(\1))", output)
    translated += len(matches)

    # Method chains → operators
    chain_mappings = [
        (r"\.plus\(", " + (", True),
        (r"\.minus\(", " - (", True),
        (r"\.times\(", " * (", True),
        (r"\.div\(", " / (", True),
        (r"\.eq\(", " == (", True),
        (r"\.gt\(", " > (", True),
        (r"\.gte\(", " >= (", True),
        (r"\.lt\(", " < (", True),
        (r"\.lte\(", " <= (", True),
    ]

    for ts_pat, py_repl, _ in chain_mappings:
        pat = re.compile(re.escape(ts_pat) if not ts_pat.startswith(r"\.") else ts_pat)
        m = pat.findall(output)
        output = pat.sub(py_repl, output)
        translated += len(m)

    # .abs() → abs(...)  — complex, quarantine for now
    abs_pattern = re.compile(r"(\w+)\.abs\(\)")
    abs_matches = abs_pattern.findall(output)
    if abs_matches:
        output = abs_pattern.sub(r"abs(\1)", output)
        translated += len(abs_matches)

    # .toNumber() → float(...)
    to_num = re.compile(r"(\w+)\.toNumber\(\)")
    to_num_matches = to_num.findall(output)
    output = to_num.sub(r"float(\1)", output)
    translated += len(to_num_matches)

    return PassResult(
        pass_name="translate_big_js",
        nodes_translated=translated,
        nodes_quarantined=len(quarantined),
        quarantined=quarantined,
        output=output,
    )


def translate_date_fns(code: str) -> PassResult:
    """Rewrite date-fns function calls to Python datetime equivalents.

    Handles the subset used by the portfolio calculator.
    """
    translated = 0
    output = code

    # format(date, DATE_FORMAT) → date.strftime('%Y-%m-%d') or str
    # Simplified: format(x, DATE_FORMAT) → x.strftime(DATE_FORMAT)
    fmt_pat = re.compile(r"format\(([^,]+),\s*DATE_FORMAT\)")
    fmt_m = fmt_pat.findall(output)
    output = fmt_pat.sub(r"\1.strftime(DATE_FORMAT)", output)
    translated += len(fmt_m)

    # differenceInDays(a, b) → (a - b).days
    diff_pat = re.compile(r"differenceInDays\(([^,]+),\s*([^)]+)\)")
    diff_m = diff_pat.findall(output)
    output = diff_pat.sub(r"(\1 - \2).days", output)
    translated += len(diff_m)

    # isBefore(a, b) → a < b
    before_pat = re.compile(r"isBefore\(([^,]+),\s*([^)]+)\)")
    before_m = before_pat.findall(output)
    output = before_pat.sub(r"\1 < \2", output)
    translated += len(before_m)

    # isAfter(a, b) → a > b
    after_pat = re.compile(r"isAfter\(([^,]+),\s*([^)]+)\)")
    after_m = after_pat.findall(output)
    output = after_pat.sub(r"\1 > \2", output)
    translated += len(after_m)

    # subDays(d, n) → d - timedelta(days=n)
    sub_pat = re.compile(r"subDays\(([^,]+),\s*([^)]+)\)")
    sub_m = sub_pat.findall(output)
    output = sub_pat.sub(r"\1 - timedelta(days=\2)", output)
    translated += len(sub_m)

    return PassResult(
        pass_name="translate_date_fns",
        nodes_translated=translated,
        nodes_quarantined=0,
        output=output,
    )


def translate_lodash(code: str) -> PassResult:
    """Rewrite lodash calls to Python builtins."""
    translated = 0
    output = code

    # cloneDeep(x) → copy.deepcopy(x)
    clone_pat = re.compile(r"cloneDeep\(")
    clone_m = clone_pat.findall(output)
    output = clone_pat.sub("copy.deepcopy(", output)
    translated += len(clone_m)

    # sortBy(arr, fn) → sorted(arr, key=fn)
    sort_pat = re.compile(r"sortBy\(([^,]+),\s*([^)]+)\)")
    sort_m = sort_pat.findall(output)
    output = sort_pat.sub(r"sorted(\1, key=\2)", output)
    translated += len(sort_m)

    return PassResult(
        pass_name="translate_lodash",
        nodes_translated=translated,
        nodes_quarantined=0,
        output=output,
    )


def translate_nullish(code: str) -> PassResult:
    """Rewrite nullish coalescing (??) and optional chaining (?.) to Python."""
    translated = 0
    quarantined: list[QuarantinedNode] = []
    output = code

    # x ?? y → x if x is not None else y
    nullish_pat = re.compile(r"(\w+)\s*\?\?\s*(\w+)")
    nullish_m = nullish_pat.findall(output)
    output = nullish_pat.sub(r"\1 if \1 is not None else \2", output)
    translated += len(nullish_m)

    # x?.y → simple cases: x.get('y') for dict access patterns
    # Complex chains are quarantined
    optional_simple = re.compile(r"(\w+)\?\.\((\w+)\)")
    # For now, just record optional chaining for quarantine
    optional_pat = re.compile(r"\w+\?\.\w+")
    opt_matches = optional_pat.findall(output)
    for m in opt_matches:
        quarantined.append(
            QuarantinedNode(
                kind=NodeKind.OPTIONAL_CHAIN,
                ts_source=m,
                reason="Optional chaining requires context-aware translation (dict.get vs getattr)",
            )
        )

    return PassResult(
        pass_name="translate_nullish",
        nodes_translated=translated,
        nodes_quarantined=len(quarantined),
        quarantined=quarantined,
        output=output,
    )


def translate_variables(code: str) -> PassResult:
    """Rewrite const/let/var declarations to Python assignments."""
    translated = 0
    output = code

    # const x = ... → x = ...
    # let x = ...   → x = ...
    # var x = ...   → x = ...
    var_pat = re.compile(r"^(\s*)(?:const|let|var)\s+", re.MULTILINE)
    var_m = var_pat.findall(output)
    output = var_pat.sub(r"\1", output)
    translated += len(var_m)

    return PassResult(
        pass_name="translate_variables",
        nodes_translated=translated,
        nodes_quarantined=0,
        output=output,
    )


def translate_for_loops(code: str) -> PassResult:
    """Rewrite TypeScript for-of loops to Python for-in loops.

    `for (const x of arr) {` → `for x in arr:`
    """
    translated = 0
    quarantined: list[QuarantinedNode] = []

    # Simple for-of: for (const x of arr) {
    simple_pat = re.compile(
        r"for\s*\(\s*(?:const|let|var)\s+(\w+)\s+of\s+([^)]+)\)\s*\{"
    )

    # Destructuring for-of: for (const { a, b } of arr) { — quarantine
    destruct_pat = re.compile(
        r"for\s*\(\s*(?:const|let|var)\s+\{([^}]+)\}\s+of\s+([^)]+)\)\s*\{"
    )

    def replace_destruct(m: re.Match[str]) -> str:
        quarantined.append(
            QuarantinedNode(
                kind=NodeKind.FOR_LOOP,
                ts_source=m.group(0),
                reason="Destructuring in for-of requires manual translation",
            )
        )
        return m.group(0)

    output = destruct_pat.sub(replace_destruct, code)

    def replace_simple(m: re.Match[str]) -> str:
        nonlocal translated
        translated += 1
        return f"for {m.group(1)} in {m.group(2).strip()}:"

    output = simple_pat.sub(replace_simple, output)

    return PassResult(
        pass_name="translate_for_loops",
        nodes_translated=translated,
        nodes_quarantined=len(quarantined),
        quarantined=quarantined,
        output=output,
    )


def translate_conditionals(code: str) -> PassResult:
    """Rewrite `if (expr) {` → `if expr:` and `} else {` → `else:`."""
    translated = 0
    output = code

    # if (expr) { → if expr:
    if_pat = re.compile(r"if\s*\((.+?)\)\s*\{")
    if_m = if_pat.findall(output)
    output = if_pat.sub(r"if \1:", output)
    translated += len(if_m)

    # } else if (expr) { → elif expr:
    elif_pat = re.compile(r"\}\s*else\s+if\s*\((.+?)\)\s*\{")
    elif_m = elif_pat.findall(output)
    output = elif_pat.sub(r"elif \1:", output)
    translated += len(elif_m)

    # } else { → else:
    else_pat = re.compile(r"\}\s*else\s*\{")
    else_m = else_pat.findall(output)
    output = else_pat.sub("else:", output)
    translated += len(else_m)

    return PassResult(
        pass_name="translate_conditionals",
        nodes_translated=translated,
        nodes_quarantined=0,
        output=output,
    )


def strip_braces(code: str) -> PassResult:
    """Remove bare closing braces left over after method/class translation."""
    pattern = re.compile(r"^\s*\}\s*$", re.MULTILINE)
    matches = pattern.findall(code)
    output = pattern.sub("", code)
    return PassResult(
        pass_name="strip_braces",
        nodes_translated=len(matches),
        nodes_quarantined=0,
        output=output,
    )


def strip_semicolons(code: str) -> PassResult:
    """Remove trailing semicolons from statements."""
    pattern = re.compile(r";\s*$", re.MULTILINE)
    matches = pattern.findall(code)
    output = pattern.sub("", code)
    return PassResult(
        pass_name="strip_semicolons",
        nodes_translated=len(matches),
        nodes_quarantined=0,
        output=output,
    )


def normalize_whitespace(code: str) -> PassResult:
    """Collapse runs of 3+ blank lines down to 2."""
    pattern = re.compile(r"\n{3,}")
    matches = pattern.findall(code)
    output = pattern.sub("\n\n", code)
    return PassResult(
        pass_name="normalize_whitespace",
        nodes_translated=len(matches),
        nodes_quarantined=0,
        output=output,
    )


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

DEFAULT_PASSES: list[Pass] = [
    # Phase 1 — Structural cleanup
    strip_imports,
    strip_type_annotations,
    translate_class,
    # Phase 2 — Expression-level rewrites
    translate_big_js,
    translate_date_fns,
    translate_lodash,
    translate_nullish,
    # Phase 3 — Statement-level rewrites
    translate_variables,
    translate_for_loops,
    translate_conditionals,
    translate_methods,
    translate_returns,
    # Phase 4 — Cleanup
    strip_braces,
    strip_semicolons,
    normalize_whitespace,
]


class TranslationPipeline:
    """Runs an ordered sequence of passes over a TypeScript source string."""

    def __init__(
        self,
        config: TranslationPipelineConfig | None = None,
        passes: list[Pass] | None = None,
    ) -> None:
        self.config = config or TranslationPipelineConfig()
        self._passes: list[Pass] = passes if passes is not None else list(DEFAULT_PASSES)

    def add_pass(self, pass_: Pass) -> "TranslationPipeline":
        """Append a pass to the end of the pipeline (fluent API)."""
        self._passes.append(pass_)
        return self

    def translate(self, code: str, source_file: Path, output_file: Path) -> TranslationResult:
        """Run all passes and return a fully populated TranslationResult."""
        current = code
        pass_results: list[PassResult] = []
        all_quarantined: list[QuarantinedNode] = []

        for pass_fn in self._passes:
            result = pass_fn(current)
            pass_results.append(result)
            all_quarantined.extend(result.quarantined)
            current = result.output

        # Clean up excess blank lines
        current = re.sub(r"\n{3,}", "\n\n", current).strip()

        status = (
            TranslationStatus.QUARANTINED if all_quarantined else TranslationStatus.OK
        )

        return TranslationResult(
            source_file=source_file,
            output_file=output_file,
            status=status,
            passes_applied=[p.pass_name for p in pass_results],
            pass_results=pass_results,
            quarantined=all_quarantined,
            output=current,
        )

    def translate_file(self, source: Path, output: Path) -> TranslationResult:
        """Read source, translate, write output, return result."""
        code = source.read_text(encoding=self.config.source_encoding)
        result = self.translate(code, source_file=source, output_file=output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(result.output, encoding=self.config.source_encoding)
        return result
