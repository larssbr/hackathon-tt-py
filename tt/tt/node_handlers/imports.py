from tt.node_handlers import register

@register("import_statement")
def visit_import_statement(walker, node) -> str:
    return ""  # Handled by wrapper
