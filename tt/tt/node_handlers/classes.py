from tt.node_handlers import register

@register("class_declaration")
def visit_class_declaration(walker, node) -> str:
    name_node = node.child_by_field_name("name")
    name = walker.extract_text(name_node) if name_node else "UnknownClass"
    
    # We might have an 'extends' or 'implements'. Let's parse base classes if any.
    # In tree-sitter, the superclass is part of a `class_heritage` node.
    base_class = ""
    for child in node.children:
        if child.type == "class_heritage":
            extends = child.child_by_field_name("class") # no, might not exist this way. We can extract it by walking.
            # Usually tree-sitter typescript: class_heritage -> extends_clause -> identifier
            pass
            
    # For now, we only need to pass through the class name.
    # Actually, translator does f"class {name}({base}):", but the ast_walker is primarily for methods based on the extraction logic.
    # If we are parsing a whole class body, we iterate over class_body.
    body_node = node.child_by_field_name("body")
    body_str = walker.visit(body_node) if body_node else ""
    return f"class {name}:\n{body_str}"

@register("class_body")
def visit_class_body(walker, node) -> str:
    # Just render all methods and fields inside it.
    children_res = []
    for c in node.children:
        if c.type in ["{", "}"]:
            continue
        children_res.append(walker.visit(c))
    return "\n".join(r for r in children_res if r.strip())
