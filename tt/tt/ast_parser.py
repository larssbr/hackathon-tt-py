"""Parse TypeScript source into a tree-sitter AST."""
import tree_sitter_typescript as ts_typescript
from tree_sitter import Language, Parser
import tree_sitter

TS_LANGUAGE = Language(ts_typescript.language_typescript())

def parse_typescript(source: str) -> tree_sitter.Tree:
    """Parse TypeScript source code and return the syntax tree."""
    parser = Parser()
    parser.language = TS_LANGUAGE
    return parser.parse(bytes(source, "utf-8"))

def walk_tree(node, source_bytes: bytes):
    """Yield all nodes in depth-first order."""
    yield node
    for child in node.children:
        yield from walk_tree(child, source_bytes)

def get_node_text(node, source_bytes: bytes) -> str:
    """Extract the source text for a given AST node."""
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8")
