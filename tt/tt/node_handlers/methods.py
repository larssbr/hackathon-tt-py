from tt.node_handlers import register

@register("method_definition")
def visit_method_definition(walker, node) -> str:
    name_node = node.child_by_field_name("name")
    name = walker.extract_text(name_node) if name_node else "method"
    
    params_node = node.child_by_field_name("parameters")
    
    # We want to visit the parameters, but we definitely need `self` for Python class methods.
    params_str = "self"
    if params_node:
        extracted = walker.extract_text(params_node)
        # simplistic: (a: T, b: U) -> a, b
        # Let's extract identifiers from formal_parameters
        param_list = []
        body_prepend = []
        for child in params_node.children:
            if child.type == "required_parameter" or child.type == "optional_parameter":
                pat = child.child_by_field_name("pattern")
                if pat:
                    if pat.type == "object_pattern":
                        props = []
                        for sub_child in pat.children:
                            if sub_child.type in ["shorthand_property_identifier_pattern", "property_identifier_pattern"]:
                                props.append(walker.extract_text(sub_child))
                        param_list.append("options")
                        for p in props:
                            body_prepend.append(f"{p} = options.get('{p}')")
                    else:
                        param_list.append(walker.extract_text(pat))
            elif child.type == "identifier":
                param_list.append(walker.extract_text(child))
        if param_list:
            params_str += ", " + ", ".join(param_list)

    body_node = node.child_by_field_name("body")
    walker.indent_level += 1
    body_str = walker.visit(body_node) if body_node else ""
    walker.indent_level -= 1

    indent = "    " * walker.indent_level
    indented_body = "\n".join(f"{indent}    {line}" for line in body_str.split("\n") if line)
    
    if body_prepend:
        prepends = "\n".join(f"{indent}    {line}" for line in body_prepend)
        indented_body = prepends + "\n" + indented_body
        
    if not indented_body.strip():
        indented_body = f"{indent}    pass"

    return f"{indent}def {name}({params_str}):\n{indented_body}"

@register("statement_block")
def visit_statement_block(walker, node) -> str:
    # return the joined statements without outer braces
    stmts = []
    for c in node.children:
        if c.type not in ["{", "}"]:
            val = walker.visit(c)
            if val is not None:
                stmts.append(val)
    return "\n".join(s for s in stmts if s.strip())
