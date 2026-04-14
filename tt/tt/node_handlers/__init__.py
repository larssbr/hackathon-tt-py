"""Dispatch registration for node handlers."""
from typing import Callable, Any

_handlers = {}

def register(node_type: str):
    def decorator(fn: Callable):
        _handlers[node_type] = fn
        return fn
    return decorator

def get_handler(node_type: str) -> Callable | None:
    return _handlers.get(node_type)

import tt.node_handlers.imports
import tt.node_handlers.classes
import tt.node_handlers.methods
import tt.node_handlers.variables
import tt.node_handlers.control_flow
import tt.node_handlers.literals
import tt.node_handlers.expressions
