"""
Translation pipeline for TypeScript → Python.

The pipeline runs an ordered sequence of transformation passes over a
TypeScript source string. Each pass is a pure function: str → PassResult.
Order matters — later passes depend on earlier ones having already rewritten
the code (e.g. imports must be stripped before class-body passes run).

Pass order (current):
  1. strip_imports     — remove TS import statements
  2. translate_class   — rewrite class/extends declarations
  3. translate_methods — rewrite method signatures (drop TS visibility/types)
  4. translate_returns — rewrite simple enum return statements
  5. strip_braces      — remove bare closing braces

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


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

DEFAULT_PASSES: list[Pass] = [
    strip_imports,
    translate_class,
    translate_methods,
    translate_returns,
    strip_braces,
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
