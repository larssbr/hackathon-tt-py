from tt.node_handlers import register

@register("new_expression")
def visit_new_expression(walker, node) -> str:
    # new Big(x) -> Decimal(str(x))
    ident = node.child_by_field_name("constructor")
    args = node.child_by_field_name("arguments")
    ident_str = walker.visit(ident)

    if ident_str == "Big":
        if args and len(args.children) > 2: # '(', arg, ')'
            arg_str = walker.visit(args.children[1])
            if arg_str in ["0", "0.0"]:
                return "Decimal(0)"
            elif arg_str.startswith("'") or arg_str.startswith('"'):
                return f"Decimal({arg_str})"
            return f"Decimal(str({arg_str}))"
        return "Decimal(0)"

    if ident_str == "Date":
        if args and len(args.children) > 2:
            arg_str = walker.visit(args.children[1])
            return f"parse_date({arg_str})"
        return "date.today()"

    return walker.extract_text(node)

@register("binary_expression")
def visit_binary_expression(walker, node) -> str:
    left = walker.visit(node.child_by_field_name("left"))
    right = walker.visit(node.child_by_field_name("right"))
    op = walker.extract_text(node.child_by_field_name("operator"))
    op_map = {"===": "==", "!==": "!=", "&&": "and", "||": "or"}
    op = op_map.get(op, op)
    return f"{left} {op} {right}"

@register("unary_expression")
def visit_unary_expression(walker, node) -> str:
    op = walker.extract_text(node.child_by_field_name("operator"))
    arg = walker.visit(node.child_by_field_name("argument"))
    if op == "!":
        return f"not {arg}"
    return f"{op}{arg}"

@register("assignment_expression")
def visit_assignment_expression(walker, node) -> str:
    left = walker.visit(node.child_by_field_name("left"))
    right = walker.visit(node.child_by_field_name("right"))
    op = node.children[1].type
    return f"{left} {op} {right}"

@register("update_expression")
def visit_update_expression(walker, node) -> str:
    # A unary expression: i++
    arg = node.child_by_field_name("argument")
    op = walker.extract_text(node).replace(walker.extract_text(arg), "").strip()
    arg_str = walker.visit(arg)
    if "++" in op:
        return f"{arg_str} += 1"
    if "--" in op:
        return f"{arg_str} -= 1"
    return f"{arg_str}"

@register("member_expression")
def visit_member_expression(walker, node) -> str:
    obj = walker.visit(node.child_by_field_name("object"))
    prop = node.child_by_field_name("property")
    prop_str = walker.extract_text(prop)

    # this.x -> self.x
    if obj == "this":
        obj = "self"

    return f"{obj}.{prop_str}"

@register("subscript_expression")
def visit_subscript_expression(walker, node) -> str:
    obj = walker.visit(node.child_by_field_name("object"))
    idx = walker.visit(node.child_by_field_name("index"))
    return f"{obj}[{idx}]"

_BIG_OPS = {
    "plus": "+", "add": "+", "minus": "-",
    "times": "*", "mul": "*", "div": "/",
    "eq": "==", "gt": ">", "gte": ">=", "lt": "<", "lte": "<="
}

_STANDALONE_FN_MAP = {
    "format": lambda a: f"{a[0]}.strftime({a[1]})",
    "differenceInDays": lambda a: f"({a[0]} - {a[1]}).days",
    "isBefore": lambda a: f"{a[0]} < {a[1]}",
    "isAfter": lambda a: f"{a[0]} > {a[1]}",
    "addMilliseconds": lambda a: f"{a[0]} + timedelta(milliseconds={a[1]})",
    "isThisYear": lambda a: f"{a[0]}.year == date.today().year",
    "cloneDeep": lambda a: f"copy.deepcopy({a[0]})",
    "sortBy": lambda a: f"sorted({a[0]}, key={a[1]})",
    "Object.keys": lambda a: f"list({a[0]}.keys())",
}

def _visit_member_call(obj_str, prop_str, args_list):
    if prop_str in _BIG_OPS:
        if args_list:
            return f"({obj_str} {_BIG_OPS[prop_str]} {args_list[0]})"
        return f"{obj_str}"
    if prop_str == "abs":
        return f"abs({obj_str})"
    if prop_str == "toNumber":
        return f"float({obj_str})"
    if prop_str == "toFixed":
        return f"round({obj_str}, {args_list[0] if args_list else 0})"
    if prop_str == "push":
        return f"{obj_str}.append({', '.join(args_list)})"
    if prop_str == "at":
        return f"{obj_str}[{args_list[0] if args_list else 0}]"
    if prop_str == "filter":
        # Emit a list comprehension: [x for x in obj if <predicate>]
        # args_list[0] is the already-visited lambda/arrow string, e.g.
        # "lambda x: x.get('type')" or "lambda x: x > 0"
        if args_list:
            pred = args_list[0]
            # Extract the parameter name and body from a lambda string
            import re as _re
            m = _re.match(r"lambda\s+(\w+)\s*:\s*(.+)", pred.strip())
            if m:
                param, body = m.group(1), m.group(2).strip()
                return f"[{param} for {param} in {obj_str} if {body}]"
        # Fallback: can't parse the predicate, emit a filter() call
        return f"list(filter({', '.join(args_list)}, {obj_str}))"
    return f"{obj_str}.{prop_str}({', '.join(args_list)})"

def _visit_standalone_call(walker, fn_node, args_list):
    fn_str = walker.visit(fn_node)
    mapper = _STANDALONE_FN_MAP.get(fn_str)
    if mapper:
        return mapper(args_list)
    return f"{fn_str}({', '.join(args_list)})"

@register("call_expression")
def visit_call_expression(walker, node) -> str:
    fn_node = node.child_by_field_name("function")
    args_node = node.child_by_field_name("arguments")

    args_list = []
    if args_node:
        for c in args_node.children:
            if c.type not in ["(", ")", ","]:
                args_list.append(walker.visit(c))

    if fn_node.type == "member_expression":
        obj_str = walker.visit(fn_node.child_by_field_name("object"))
        prop_str = walker.extract_text(fn_node.child_by_field_name("property"))
        return _visit_member_call(obj_str, prop_str, args_list)

    return _visit_standalone_call(walker, fn_node, args_list)

@register("array")
def visit_array(walker, node) -> str:
    elems = []
    for c in node.children:
        if c.type not in ["[", "]", ","]:
            elems.append(walker.visit(c))
    return f"[{', '.join(elems)}]"

@register("object")
def visit_object(walker, node) -> str:
    elems = []
    for c in node.children:
        if c.type == "pair":
            key_node = c.child_by_field_name("key")
            val_node = c.child_by_field_name("value")
            k = walker.visit(key_node)
            # if key is unquoted identifier, quote it
            if key_node.type == "property_identifier" or key_node.type == "identifier":
                k = f'"{k}"'
            v = walker.visit(val_node)
            elems.append(f"{k}: {v}")
        elif c.type == "shorthand_property_identifier":
            id = walker.extract_text(c)
            elems.append(f'"{id}": {walker.visit(c)}')

    return f"{{{', '.join(elems)}}}"

@register("arrow_function")
def visit_arrow_function(walker, node) -> str:
    # simple lambda equivalent
    params_node = node.child_by_field_name("parameters")
    body_node = node.child_by_field_name("body")
    
    # If parameters contains object_pattern, we should just use `x` and rewrite body to `x.get(prop)` 
    # but that's very hard without rewriting the body string. 
    # Let's extract the property names, use a generic parameter `x`.
    params_str = walker.extract_text(params_node).strip("()")
    body = walker.visit(body_node)
    
    if "{" in params_str:
        props = params_str.translate(str.maketrans("", "", "{} ")).split(",")
        params = "x"
        for p in props:
            if p:
                body = body.replace(f" {p} ", f" x.get('{p}') ").replace(f" {p}", f" x.get('{p}')").replace(f"{p} ", f"x.get('{p}') ").replace(p, f"x.get('{p}')")
    else:
        params = params_str
        
    # If body is a block, this breaks Python lambdas if it has statements
    # Simple workaround for object returns or expression returns
    if body_node.type == "statement_block":
        # Check if it has a single return statement
        # This is a very rough heuristic
        return_found = False
        ret_val = ""
        for c in body_node.children:
            if c.type == "return_statement":
                return_found = True
                ret_val = walker.visit(c).replace("return", "").strip()
        if return_found:
            body = ret_val
    return f"lambda {params}: {body}"

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
    # Simplistic x?.y -> (x.y if x is not None else None)
    base = walker.visit(node.children[0])
    # The member accessor
    if len(node.children) > 2 and node.children[1].type == "?.":
        prop = walker.extract_text(node.children[2])
        return f"({base}.{prop} if {base} is not None else None)"
    return walker.extract_text(node)

