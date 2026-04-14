# AST Migration Prompt — From Regex Passes to Tree-sitter AST

## Context

We are building `tt`, a TypeScript-to-Python translator for a hackathon competition.
Our current translator uses 15 regex-based passes (see `prompt-banana/src/pipeline.py`).
Regex works for simple patterns but breaks on nested expressions, multi-line
constructs, and context-dependent translations (e.g. Big.js chains where parentheses
must balance correctly).

We want to migrate the core translation engine to use **tree-sitter** with the
**tree-sitter-typescript** grammar. This gives us a full, correct AST to walk
instead of fragile regex patterns.

## Constraints (from COMPETITION_RULES.md)

- Rule 5: "You may use AST libraries in python" — explicitly allowed
- Rule 6: "Your python code may not call node/js-tools" — tree-sitter is pure Python bindings, no node.js needed
- Rule 9: No project-specific mappings in `tt/` core — generic AST node handlers only

## Dependencies to add

```toml
# In tt/pyproject.toml
dependencies = [
    "tree-sitter>=0.23",
    "tree-sitter-typescript>=0.23",
]
```

## Architecture

```
tt/tt/
├── cli.py                  # existing — no change
├── translator.py           # replace regex with AST pipeline
├── ast_parser.py           # NEW: tree-sitter setup + TS parsing
├── ast_walker.py           # NEW: recursive AST-to-Python visitor
├── node_handlers/          # NEW: one handler per AST node type
│   ├── __init__.py
│   ├── imports.py          # import_statement → skip (Python imports added by scaffold)
│   ├── classes.py          # class_declaration → class X(Base):
│   ├── methods.py          # method_definition → def name(self, ...):
│   ├── variables.py        # variable_declaration → assignment
│   ├── expressions.py      # Big.js chains, date-fns calls → Decimal, datetime
│   ├── control_flow.py     # if_statement, for_in_statement → Python equivalents
│   └── literals.py         # string, number, boolean, null → Python literals
└── mappings/               # existing concept, now AST-aware
    ├── bigjs.py            # Big.js AST patterns → Decimal expressions
    ├── datefns.py          # date-fns AST patterns → datetime expressions
    └── lodash.py           # lodash AST patterns → Python builtins
```

## Step-by-step migration plan

### Step 1: Set up tree-sitter parser (ast_parser.py)

```python
"""Parse TypeScript source into a tree-sitter AST."""
import tree_sitter_typescript as ts_typescript
from tree_sitter import Language, Parser

TS_LANGUAGE = Language(ts_typescript.language())

def parse_typescript(source: str) -> tree_sitter.Tree:
    """Parse TypeScript source code and return the syntax tree."""
    parser = Parser(TS_LANGUAGE)
    return parser.parse(bytes(source, "utf-8"))

def walk_tree(node, source_bytes: bytes):
    """Yield all nodes in depth-first order."""
    yield node
    for child in node.children:
        yield from walk_tree(child, source_bytes)

def get_node_text(node, source_bytes: bytes) -> str:
    """Extract the source text for a given AST node."""
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8")
```

### Step 2: Write the AST walker (ast_walker.py)

The walker visits every node in the tree and dispatches to a handler based on
the node type. Unknown node types are passed through as-is (with a quarantine
warning).

```python
"""Recursive AST visitor that translates TS nodes to Python source."""
from .ast_parser import get_node_text
from .models import QuarantinedNode, NodeKind

class ASTWalker:
    def __init__(self, source_bytes: bytes):
        self.source = source_bytes
        self.quarantined: list[QuarantinedNode] = []
        self.indent_level = 0

    def visit(self, node) -> str:
        handler_name = f"visit_{node.type}"
        handler = getattr(self, handler_name, self.generic_visit)
        return handler(node)

    def generic_visit(self, node) -> str:
        """Default: visit children and concatenate results."""
        return "".join(self.visit(child) for child in node.children)

    def visit_import_statement(self, node) -> str:
        return ""  # imports handled by scaffold

    def visit_class_declaration(self, node) -> str:
        # Extract class name and superclass from AST children
        ...

    def visit_method_definition(self, node) -> str:
        # Extract method name, params; emit def name(self, ...):
        ...

    # ... one visit_* method per node type we care about
```

### Step 3: Handle the critical node types

These are the TypeScript AST node types that appear in `portfolio-calculator.ts`
and must be handled for correct translation:

| tree-sitter node type | TS construct | Python output |
|---|---|---|
| `import_statement` | `import { Big } from 'big.js'` | Skip (scaffold handles) |
| `class_declaration` | `export class X extends Y { }` | `class X(Y):` |
| `method_definition` | `protected foo(x: T): R { }` | `def foo(self, x):` |
| `variable_declaration` | `const x: Type = expr` | `x = expr` |
| `lexical_declaration` | `let x = expr` | `x = expr` |
| `if_statement` | `if (expr) { ... }` | `if expr:` |
| `else_clause` | `} else { ... }` | `else:` |
| `for_in_statement` | `for (const x of arr) { }` | `for x in arr:` |
| `return_statement` | `return expr;` | `return expr` |
| `expression_statement` | `x = x.plus(y);` | `x = x + y` |
| `call_expression` | `format(d, DATE_FORMAT)` | `d.strftime(DATE_FORMAT)` |
| `new_expression` | `new Big(0)` | `Decimal(0)` |
| `member_expression` | `obj.property` | `obj["property"]` or `obj.property` |
| `binary_expression` | `a + b`, `a > b` | Same (usually) |
| `assignment_expression` | `x = y` | `x = y` |
| `arrow_function` | `(x) => { ... }` | `lambda x: ...` or `def` |
| `template_string` | `` `text ${expr}` `` | `f"text {expr}"` |
| `object` | `{ key: value }` | `{"key": value}` |
| `array` | `[a, b, c]` | `[a, b, c]` |
| `type_annotation` | `: Type` | Strip |
| `as_expression` | `x as Type` | Strip |
| `optional_chain` | `x?.y` | `x.get("y")` or guard |
| `ternary_expression` | `c ? a : b` | `a if c else b` |
| `property_signature` | `key: Type;` (interface) | Skip or TypedDict field |

### Step 4: Handle Big.js method chains (the hardest part)

Big.js chains like `total.plus(fee).minus(tax).times(rate)` are represented
in the AST as nested `call_expression` nodes. The AST walker must:

1. Detect that the callee is a `member_expression` with property name in
   `{plus, minus, times, div, eq, gt, gte, lt, lte, abs, toNumber, round}`
2. Recursively translate the object (left side of `.`)
3. Map the method to a Python operator or function
4. Recursively translate the argument(s)

```
AST for: total.plus(fee)
  call_expression
    member_expression
      identifier: "total"     → translate recursively
      property_identifier: "plus"  → map to " + "
    arguments
      identifier: "fee"       → translate recursively
Result: "total + fee"

AST for: new Big(amount)
  new_expression
    identifier: "Big"         → map to "Decimal"
    arguments
      identifier: "amount"    → wrap in str(): "str(amount)"
Result: "Decimal(str(amount))"
```

### Step 5: Integrate with existing pipeline

The AST walker replaces the regex passes but the Pydantic models
(`PassResult`, `TranslationResult`, `QuarantinedNode`) stay. The pipeline
becomes:

```python
def translate_with_ast(ts_source: str, source_file, output_file) -> TranslationResult:
    tree = parse_typescript(ts_source)
    source_bytes = ts_source.encode("utf-8")
    walker = ASTWalker(source_bytes)
    python_code = walker.visit(tree.root_node)
    # ... wrap in TranslationResult with quarantine info
```

### Step 6: Test against known TypeScript snippets

Write tests that parse real TypeScript from the ghostfolio calculator and
verify the AST walker produces correct Python. Start with the simplest methods:

1. `getPerformanceCalculationType()` — trivial enum return
2. `calculateOverallPerformance()` — accumulator loop with Big.js
3. `getSymbolMetrics()` — the full algorithm

### Validation approach

For each translated method:
1. Parse TS with tree-sitter → verify AST is correct
2. Walk AST → emit Python
3. Run Python through `compile()` → verify it's syntactically valid
4. Run through `make translate-and-test-ghostfolio_pytx` → verify functional correctness

## Why this is better than regex

| Regex | AST |
|---|---|
| Breaks on nested parens in Big.js chains | Tree structure handles nesting naturally |
| Can't distinguish `{` in object literal vs block | AST knows the node type |
| Can't detect that `x?.y` inside a `for` vs `if` needs different handling | Full context from parent nodes |
| Separate passes interfere with each other | Single tree walk, no interference |
| Pattern order matters, fragile | Visit dispatch by node type, order-independent |

## What to keep from the regex pipeline

- The **Pydantic models** — `PassResult`, `TranslationResult`, `QuarantinedNode`
- The **quarantine concept** — unknown node types get quarantined, not silently dropped
- The **library mapping tables** — Big.js → Decimal, date-fns → datetime; these become
  lookup dicts in the AST handlers instead of regex patterns
- The **test structure** — unit tests per handler, integration test against full pipeline

## Risk: What if tree-sitter can't parse our specific TS?

tree-sitter-typescript parses all valid TypeScript. It uses error recovery for
invalid syntax — we get a tree with `ERROR` nodes we can quarantine. This is
strictly better than regex which simply fails to match.

## Time estimate for migration

| Task | Effort |
|---|---|
| Set up tree-sitter parser + basic walker | 30 min |
| Handle structural nodes (class, method, variable, if, for) | 45 min |
| Handle Big.js chain translation | 45 min |
| Handle date-fns + lodash | 20 min |
| Integration with existing pipeline | 15 min |
| Test against real calculator TS | 30 min |
| **Total** | **~3 hours** |
