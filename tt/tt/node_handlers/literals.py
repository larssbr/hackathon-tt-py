from tt.node_handlers import register

@register("identifier")
@register("property_identifier")
@register("shorthand_property_identifier")
@register("number")
@register("string")
def visit_literal(walker, node) -> str:
    return walker.extract_text(node)

@register("parenthesized_expression")
def visit_parenthesized_expression(walker, node) -> str:
    inner = node.children[1] # (, expr, )
    return f"({walker.visit(inner)})"

@register("true")
def visit_true(walker, node) -> str:
    return "True"

@register("false")
def visit_false(walker, node) -> str:
    return "False"

@register("null")
def visit_null(walker, node) -> str:
    return "None"

@register("undefined")
def visit_undefined(walker, node) -> str:
    return "None"

@register("this")
def visit_this(walker, node) -> str:
    return "self"

@register("type_annotation")
@register("as_expression")
def visit_type_annotation(walker, node) -> str:
    return ""  # stripped

@register("template_string")
def visit_template_string(walker, node) -> str:
    # Need to change `${var}` to `{var}` and add `f` prefix.
    # We can visit children.
    # template_string nodes hold template_substitution nodes, etc.
    res = []
    for c in node.children:
        if c.type == "template_substitution":
            inner = c.children[1] # skip ${ and }
            res.append(f"{{{walker.visit(inner)}}}")
        elif c.type in ["`", "'", '"']:
            pass
        else:
            res.append(walker.extract_text(c))
    s = "".join(res)
    # determine quote character
    if "\n" in s:
        return f'f"""{s}"""'
    return f'f"{s}"'
