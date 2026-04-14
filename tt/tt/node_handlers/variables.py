from tt.node_handlers import register

@register("lexical_declaration")
@register("variable_declaration")
def visit_variable_declaration(walker, node) -> str:
    # A declaration has children. We want to extract 'kind' (let/const) and variable_declarator
    decls = []
    for c in node.children:
        if c.type == "variable_declarator":
            decl_name = c.child_by_field_name("name")
            decl_val = c.child_by_field_name("value")
            name_str = walker.extract_text(decl_name) if decl_name else ""
            val_str = walker.visit(decl_val) if decl_val else "None"
            decls.append(f"{name_str} = {val_str}")
    return "\n".join(decls)
