"""Recursive AST visitor that translates TS nodes to Python source."""
from typing import Any
import sys
from pydantic import BaseModel
from tt.ast_parser import get_node_text

import sys

# To be compatible with models if we copy it, though for now let's use a dummy QuarantinedNode
# if it's not present in tt.
try:
    from models import QuarantinedNode, NodeKind
except ImportError:
    class NodeKind:
        UNKNOWN = "unknown"
    class QuarantinedNode(BaseModel):
        kind: str
        ts_source: str
        reason: str
        line_number: int | None = None

class ASTWalker:
    def __init__(self, source_bytes: bytes):
        self.source = source_bytes
        self.quarantined: list[QuarantinedNode] = []
        self.indent_level = 0
        from tt.node_handlers import get_handler
        self.get_handler = get_handler

    def visit(self, node) -> str:
        if not node:
            return ""
        
        handler = self.get_handler(node.type)
        if handler:
            return handler(self, node)

        # Fallback to generic visit or own method
        handler_name = f"visit_{node.type}"
        handler_method = getattr(self, handler_name, self.generic_visit)
        return handler_method(node)

    def generic_visit(self, node) -> str:
        """Default: visit children and concatenate results."""
        return "".join(self.visit(child) for child in node.children)

    def extract_text(self, node) -> str:
        if not node:
            return ""
        return get_node_text(node, self.source)
