"""Handlers for expression-level TypeScript AST nodes."""
from __future__ import annotations

import re
from tt.node_handlers import register


# ---------------------------------------------------------------------------
# Operator / method dispatch tables (data, not code)
# ---------------------------------------------------------------------------

# Big.js arithmetic and comparison methods → Python infix operators
_BIG_OPS: dict[str, str] = {
    "plus": "+", "add": "+", "minus": "-",
    "times": "*", "mul": "*", "div": "/",
    "eq": "==", "gt": ">", "gte": ">=", "lt": "<", "lte": "<=",
}

# Standalone TypeScript functions → Python equivalents
_STANDALONE_FN_MAP: dict[str, object] = {
    "format":           lambda a: f"{a[0]}.strftime({a[1]})",
    "differenceInDays": lambda a: f"({a[0]} - {a[1]}).days",
    "isBefore":         lambda a: f"{a[0]} < {a[1]}",
    "isAfter":          lambda a: f"{a[0]} > {a[1]}",
    "addMilliseconds":  lambda a: f"{a[0]} + timedelta(milliseconds={a[1]})",
    "isThisYear":       lambda a: f"{a[0]}.year == date.today().year",
    "cloneDeep":        lambda a: f"copy.deepcopy({a[0]})",
    "sortBy":           lambda a: f"sorted({a[0]}, key={a[1]})",
    "Object.keys":      lambda a: f"list({a[0]}.keys())",
}

# Member method → (obj, args) → Python string
_MEMBER_FN_MAP: dict[str, object] = {
    "abs":      lambda obj, args: f"abs({obj})",
    "toNumber": lambda obj, args: f"float({obj})",
    "toFixed":  lambda obj, args: f"round({obj}, {args[0] if args else 0})",
    "push":     lambda obj, args: f"{obj}.append({', '.join(args)})",
    "at":       lambda obj, args: f"{obj}[{args[0] if args else 0}]",
}


# ---------------------------------------------------------------------------
# new Big(...) / new Date(...)
# ---------------------------------------------------------------------------

def _translate_new_big(walker, args_node) -> str:
    """Translate `new Big(x)` → `Decimal(...)` form."""
    if not args_node or len(args_node.children) <= 2:
        return "Decimal(0)"
    arg = walker.visit(args_node.children[1])
    if arg in ("0", "0.0"):
        return "Decimal(0)"
    if arg.startswith(("'", '"')):
        return f"Decimal({arg})"
    return f"Decimal(str({arg}))"


def _translate_new_date(walker, args_node) -> str:
    """Translate `new Date(x)` / `new Date()` → Python datetime."""
    if not args_node or len(args_node.children) <= 2:
        return "date.today()"
    arg = walker.visit(args_node.children[1])
    return f"parse_date({arg})"


@register("new_expression")
def visit_new_expression(walker, node) -> str:
    ident = node.child_by_field_name("constructor")
    args = node.child_by_field_name("arguments")
    ident_str = walker.visit(ident)
    if ident_str == "Big":
        return _translate_new_big(walker, args)
    if ident_str == "Date":
        return _translate_new_date(walker, args)
    return walker.extract_text(node)


# ---------------------------------------------------------------------------
# Binary / unary / assignment operators
# ---------------------------------------------------------------------------

_TS_TO_PY_OPS: dict[str, str] = {"===": "==", "!==": "!=", "&&": "and", "||": "or"}


@register("binary_expression")
def visit_binary_expression(walker, node) -> str:
    left = walker.visit(node.child_by_field_name("left"))
    right = walker.visit(node.child_by_field_name("right"))
    op = walker.extract_text(node.child_by_field_name("operator"))
    return f"{left} {_TS_TO_PY_OPS.get(op, op)} {right}"


@register("unary_expression")
def visit_unary_expression(walker, node) -> str:
    op = walker.extract_text(node.child_by_field_name("operator"))
    arg = walker.visit(node.child_by_field_name("argument"))
    return f"not {arg}" if op == "!" else f"{op}{arg}"


@register("assignment_expression")
def visit_assignment_expression(walker, node) -> str:
    left = walker.visit(node.child_by_field_name("left"))
    right = walker.visit(node.child_by_field_name("right"))
    op = node.children[1].type
    return f"{left} {op} {right}"


@register("update_expression")
def visit_update_expression(walker, node) -> str:
    arg = node.child_by_field_name("argument")
    op = walker.extract_text(node).replace(walker.extract_text(arg), "").strip()
    arg_str = walker.visit(arg)
    if "++" in op:
        return f"{arg_str} += 1"
    if "--" in op:
        return f"{arg_str} -= 1"
    return arg_str


# ---------------------------------------------------------------------------
# Member / subscript access
# ---------------------------------------------------------------------------

@register("member_expression")
def visit_member_expression(walker, node) -> str:
    obj = walker.visit(node.child_by_field_name("object"))
    prop = walker.extract_text(node.child_by_field_name("property"))
    return f"{'self' if obj == 'this' else obj}.{prop}"


@register("subscript_expression")
def visit_subscript_expression(walker, node) -> str:
    obj = walker.visit(node.child_by_field_name("object"))
    idx = walker.visit(node.child_by_field_name("index"))
    return f"{obj}[{idx}]"


# ---------------------------------------------------------------------------
# Call expressions — member calls and standalone calls
# ---------------------------------------------------------------------------

def _filter_to_comprehension(obj: str, args: list[str]) -> str:
    """Translate `.filter(lambda x: ...)` → `[x for x in obj if ...]`."""
    if not args:
        return f"list(filter({obj}))"
    m = re.match(r"lambda\s+(\w+)\s*:\s*(.+)", args[0].strip())
    if m:
        param, body = m.group(1), m.group(2).strip()
        return f"[{param} for {param} in {obj} if {body}]"
    return f"list(filter({', '.join(args)}, {obj}))"


def _visit_member_call(obj: str, prop: str, args: list[str]) -> str:
    """Translate a method call on an object to Python."""
    if prop in _BIG_OPS:
        return f"({obj} {_BIG_OPS[prop]} {args[0]})" if args else obj
    if prop == "filter":
        return _filter_to_comprehension(obj, args)
    handler = _MEMBER_FN_MAP.get(prop)
    if handler:
        return handler(obj, args)
    return f"{obj}.{prop}({', '.join(args)})"


def _visit_standalone_call(walker, fn_node, args: list[str]) -> str:
    """Translate a standalone function call to Python."""
    fn = walker.visit(fn_node)
    handler = _STANDALONE_FN_MAP.get(fn)
    if handler:
        return handler(args)
    return f"{fn}({', '.join(args)})"


def _collect_args(walker, args_node) -> list[str]:
    """Visit all argument nodes, skipping punctuation."""
    if not args_node:
        return []
    return [
        walker.visit(c)
        for c in args_node.children
        if c.type not in ("(", ")", ",")
    ]


@register("call_expression")
def visit_call_expression(walker, node) -> str:
    fn_node = node.child_by_field_name("function")
    args = _collect_args(walker, node.child_by_field_name("arguments"))
    if fn_node.type == "member_expression":
        obj = walker.visit(fn_node.child_by_field_name("object"))
        prop = walker.extract_text(fn_node.child_by_field_name("property"))
        return _visit_member_call(obj, prop, args)
    return _visit_standalone_call(walker, fn_node, args)


# ---------------------------------------------------------------------------
# Array and object literals
# ---------------------------------------------------------------------------

@register("array")
def visit_array(walker, node) -> str:
    elems = [walker.visit(c) for c in node.children if c.type not in ("[", "]", ",")]
    return f"[{', '.join(elems)}]"


def _visit_pair(walker, node) -> str:
    key_node = node.child_by_field_name("key")
    val_node = node.child_by_field_name("value")
    k = walker.visit(key_node)
    if key_node.type in ("property_identifier", "identifier"):
        k = f'"{k}"'
    return f"{k}: {walker.visit(val_node)}"


@register("object")
def visit_object(walker, node) -> str:
    elems = []
    for c in node.children:
        if c.type == "pair":
            elems.append(_visit_pair(walker, c))
        elif c.type == "shorthand_property_identifier":
            name = walker.extract_text(c)
            elems.append(f'"{name}": {walker.visit(c)}')
    return f"{{{', '.join(elems)}}}"


# ---------------------------------------------------------------------------
# Arrow functions → lambda
# ---------------------------------------------------------------------------

def _arrow_params(walker, params_node) -> tuple[str, str]:
    """Return (param_name, destructured_prefix) for an arrow function.

    For simple params like `(x)` returns `("x", "")`.
    For destructured params like `({ type, date })` returns `("x", "")` and
    the body will be rewritten by `_rewrite_destructured_body`.
    """
    raw = walker.extract_text(params_node).strip("()").strip()
    if "{" in raw:
        return "x", raw.translate(str.maketrans("", "", "{} "))
    return raw, ""


def _rewrite_destructured_body(body: str, props_csv: str) -> str:
    """Replace bare property names in body with `x.get('prop')` accesses."""
    for prop in props_csv.split(","):
        prop = prop.strip()
        if not prop:
            continue
        body = re.sub(rf"\b{re.escape(prop)}\b", f"x.get('{prop}')", body)
    return body


def _extract_single_return(walker, block_node) -> str | None:
    """If a statement_block contains exactly one return, return its value string."""
    for c in block_node.children:
        if c.type == "return_statement":
            return walker.visit(c).removeprefix("return").strip()
    return None


@register("arrow_function")
def visit_arrow_function(walker, node) -> str:
    params_node = node.child_by_field_name("parameters")
    body_node = node.child_by_field_name("body")

    param, destructured_props = _arrow_params(walker, params_node)
    body = walker.visit(body_node)

    if destructured_props:
        body = _rewrite_destructured_body(body, destructured_props)

    if body_node.type == "statement_block":
        single_return = _extract_single_return(walker, body_node)
        if single_return is not None:
            body = single_return

    return f"lambda {param}: {body}"


# ---------------------------------------------------------------------------
# Miscellaneous expressions
# ---------------------------------------------------------------------------

@register("expression_statement")
def visit_expression_statement(walker, node) -> str:
    return walker.visit(node.children[0])


@register("ternary_expression")
def visit_ternary_expression(walker, node) -> str:
    cond = walker.visit(node.child_by_field_name("condition"))
    cons = walker.visit(node.child_by_field_name("consequence"))
    alt = walker.visit(node.child_by_field_name("alternative"))
    return f"{cons} if {cond} else {alt}"


@register("optional_chain")
def visit_optional_chain(walker, node) -> str:
    base = walker.visit(node.children[0])
    if len(node.children) > 2 and node.children[1].type == "?.":
        prop = walker.extract_text(node.children[2])
        return f"({base}.{prop} if {base} is not None else None)"
    return walker.extract_text(node)
