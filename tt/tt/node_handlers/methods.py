from tt.node_handlers import register


def _extract_params(walker, params_node):
    """Extract Python parameter list and any body-prepend lines from TS formal parameters."""
    param_list = []
    body_prepend = []
    if not params_node:
        return param_list, body_prepend
    for child in params_node.children:
        if child.type in ("required_parameter", "optional_parameter"):
            pat = child.child_by_field_name("pattern")
            if pat:
                if pat.type == "object_pattern":
                    props = []
                    for sub_child in pat.children:
                        if sub_child.type in ("shorthand_property_identifier_pattern", "property_identifier_pattern"):
                            props.append(walker.extract_text(sub_child))
                    param_list.append("options")
                    for p in props:
                        body_prepend.append(f"{p} = options.get('{p}')")
                else:
                    param_list.append(walker.extract_text(pat))
        elif child.type == "identifier":
            param_list.append(walker.extract_text(child))
    return param_list, body_prepend


@register("method_definition")
def visit_method_definition(walker, node) -> str:
    name_node = node.child_by_field_name("name")
    name = walker.extract_text(name_node) if name_node else "method"

    params_node = node.child_by_field_name("parameters")
    param_list, body_prepend = _extract_params(walker, params_node)
    params_str = "self"
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
