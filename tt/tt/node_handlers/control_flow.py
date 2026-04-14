from tt.node_handlers import register

@register("if_statement")
def visit_if_statement(walker, node) -> str:
    cond = node.child_by_field_name("condition")
    cond_str = walker.visit(cond) if cond else "True"
    
    cons_node = node.child_by_field_name("consequence")
    cons_str = walker.visit(cons_node) if cons_node else "pass"
    
    # Python expects indentation
    lines = cons_str.split("\n")
    indented_cons = "\n".join("    " + l for l in lines if l) or "    pass"
    
    res = f"if {cond_str}:\n{indented_cons}"
    
    alt_node = node.child_by_field_name("alternative")
    if alt_node:
        alt_str = walker.visit(alt_node)
        res += f"\n{alt_str}"
        
    return res

@register("else_clause")
def visit_else_clause(walker, node) -> str:
    # children [else, statement] etc
    # If the statement is an if_statement, we can turn it into elif. To be simple, we can just do:
    # else:
    #    ...
    # The grammar has `alternative` as `else_clause`. Its children: "else", then a statement.
    stmt = node.children[-1]
    if stmt.type == "if_statement":
        # we can format it as elif
        ifs = walker.visit(stmt)
        # ifs is "if cond:\n    block"
        return "el" + ifs
    else:
        alt_str = walker.visit(stmt)
        lines = alt_str.split("\n")
        indented = "\n".join("    " + l for l in lines if l) or "    pass"
        return f"else:\n{indented}"
        
@register("for_in_statement")
def visit_for_in_statement(walker, node) -> str:
    left = node.child_by_field_name("left")
    left_str = walker.extract_text(left)
    # usually `const x` or `let x` or `x`. We can extract just the identifier:
    if left_str.startswith("const ") or left_str.startswith("let "):
        left_str = left_str.split()[1]
        
    right = node.child_by_field_name("right")
    right_str = walker.visit(right)
    
    body = node.child_by_field_name("body")
    body_str = walker.visit(body)
    
    lines = body_str.split("\n")
    indented = "\n".join("    " + l for l in lines if l) or "    pass"
    return f"for {left_str} in {right_str}:\n{indented}"

@register("for_statement")
def visit_for_statement(walker, node) -> str:
    # A traditional for-loop: for (let i = 0; i < x.length; i++) { ... }
    # Often translated to a while loop in python if it's complex, or range if simple.
    
    # Just render as while loop for safety
    init = node.child_by_field_name("initializer")
    cond = node.child_by_field_name("condition")
    inc = node.child_by_field_name("increment")
    body = node.child_by_field_name("body")
    
    init_str = walker.visit(init) if init else ""
    cond_str = walker.visit(cond) if cond else "True"
    inc_str = walker.visit(inc) if inc else ""
    
    body_str = walker.visit(body) if body else ""
    
    lines = []
    if init_str:
        lines.append(init_str)
    
    lines.append(f"while {cond_str}:")
    
    body_lines = body_str.split("\n")
    for l in body_lines:
        lines.append("    " + l if l else "    ")
        
    if inc_str:
        lines.append("    " + inc_str)
        
    return "\n".join(lines)

@register("return_statement")
def visit_return_statement(walker, node) -> str:
    exprs = []
    for c in node.children:
        if c.type != "return" and c.type != ";":
            exprs.append(walker.visit(c))
    if exprs:
        return f"return {''.join(exprs)}"
    return "return"
