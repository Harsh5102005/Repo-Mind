"""AST-based chunker for Python files (RepoMind, Phase 1).

Reads a Python file, parses it with tree-sitter, and cuts it into
one Chunk per function and class, each labelled with its file,
name, type and line numbers.
"""

from dataclasses import dataclass
import sys
from pathlib import Path

import tree_sitter
import tree_sitter_python


# ------------------------------------------------------------------
# 1. The Chunk container: one labelled piece of code
# ------------------------------------------------------------------
@dataclass
class Chunk:
    text: str          # the full code of the function/class
    file_path: str     # which file it came from
    symbol_type: str   # "function" or "class"
    symbol_name: str   # e.g. "login_user"
    start_line: int    # 1-based, matches your editor
    end_line: int


# ------------------------------------------------------------------
# 2. Parser setup (done once, reused for every file)
# ------------------------------------------------------------------
PY_LANGUAGE = tree_sitter.Language(tree_sitter_python.language())
try:
    _parser = tree_sitter.Parser(PY_LANGUAGE)
except TypeError:  # older tree-sitter versions
    _parser = tree_sitter.Parser()
    _parser.language = PY_LANGUAGE


# ------------------------------------------------------------------
# 3. Tree-walking helper: finds functions/classes and cuts them out
# ------------------------------------------------------------------
def _walk(node, lines, source_bytes, file_path, chunks):
    # A decorated function/class is wrapped in a "decorated_definition"
    # node: look inside it instead of treating the wrapper itself as code.
    if node.type == "decorated_definition":
        for child in node.children:
            _walk(child, lines, source_bytes, file_path, chunks)
        return

    if node.type in ("function_definition", "class_definition"):
        name_node = node.child_by_field_name("name")
        if name_node is not None:
            name = source_bytes[name_node.start_byte:name_node.end_byte].decode(
                "utf-8", errors="replace"
            )
        else:
            name = "<anonymous>"

        # start_point/end_point are 0-based rows, so +1 = editor line numbers
        chunks.append(
            Chunk(
                text="\n".join(
                    lines[node.start_point[0] : node.end_point[0] + 1]
                ),
                file_path=file_path,
                symbol_type=(
                    "function"
                    if node.type == "function_definition"
                    else "class"
                ),
                symbol_name=name,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
            )
        )

    # Keep walking into children, so methods inside classes and
    # nested functions are found too.
    for child in node.children:
        _walk(child, lines, source_bytes, file_path, chunks)


# ------------------------------------------------------------------
# 4. Main function: file path in -> list of Chunks out
# ------------------------------------------------------------------
def chunk_file(path):
    path = Path(path)
    source_bytes = path.read_bytes()
    tree = _parser.parse(source_bytes)
    lines = source_bytes.decode("utf-8", errors="replace").splitlines()

    chunks = []
    _walk(tree.root_node, lines, source_bytes, str(path), chunks)
    return chunks


# ------------------------------------------------------------------
# 5. Test block: run this file directly to see the cutting work
# ------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ast_chunker.py <path-to-python-file>")
        raise SystemExit(1)

    for chunk in chunk_file(sys.argv[1]):
        print(
            f"--- {chunk.symbol_type}: {chunk.symbol_name} "
            f"({chunk.file_path}:{chunk.start_line}-{chunk.end_line}) ---"
        )
        print(chunk.text)
        print()
