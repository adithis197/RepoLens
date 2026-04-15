import networkx as nx
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
from tree_sitter import Language, Parser

from ..step0_ingestion.ingestion import RepoSnapshot

PY_LANGUAGE = Language(tspython.language())
JS_LANGUAGE = Language(tsjavascript.language())

LANGUAGE_MAP = {
    ".py": PY_LANGUAGE,
    ".js": JS_LANGUAGE,
    ".jsx": JS_LANGUAGE,
}


def _walk_imports_py(node, imports):
    """Recursively walk AST and extract Python import module names."""
    if node.type == "import_from_statement":
        for child in node.children:
            if child.type == "dotted_name":
                imports.append(child.text.decode("utf-8"))
                break
    elif node.type == "import_statement":
        for child in node.children:
            if child.type == "dotted_name":
                imports.append(child.text.decode("utf-8"))
    for child in node.children:
        _walk_imports_py(child, imports)


def _walk_imports_js(node, imports):
    """Recursively walk AST and extract JS import/require strings."""
    if node.type == "import_statement":
        for child in node.children:
            if child.type == "string":
                raw = child.text.decode("utf-8").strip().strip("\"'")
                imports.append(raw)
    elif node.type == "call_expression":
        fn = node.child_by_field_name("function")
        args = node.child_by_field_name("arguments")
        if fn and fn.text == b"require" and args:
            for child in args.children:
                if child.type == "string":
                    raw = child.text.decode("utf-8").strip().strip("\"'")
                    imports.append(raw)
    for child in node.children:
        _walk_imports_js(child, imports)


def parse_imports(file_path: str, content: str, ext: str) -> list:
    """Walk the AST directly to extract imports — no query API needed."""
    lang = LANGUAGE_MAP.get(ext)
    if not lang:
        return []
    try:
        parser = Parser(lang)
        tree = parser.parse(bytes(content, "utf-8"))
        imports = []
        if ext == ".py":
            _walk_imports_py(tree.root_node, imports)
        else:
            _walk_imports_js(tree.root_node, imports)
        return imports
    except Exception as e:
        print(f"[parser] failed to parse {file_path}: {e}")
        return []


def resolve_import(imp: str, current_file: str, all_paths: set) -> str | None:
    """Try to resolve an import string to an actual file path in the repo."""
    current_dir = "/".join(current_file.split("/")[:-1])

    if imp.startswith("."):
        clean = imp.lstrip("./")
        candidates = [
            f"{current_dir}/{clean}.py",
            f"{current_dir}/{clean}.js",
            f"{current_dir}/{clean}/index.js",
            f"{current_dir}/{clean}.ts",
            f"{current_dir}/{clean}.tsx",
        ]
        for c in candidates:
            if c in all_paths:
                return c
    else:
        as_path_py = imp.replace(".", "/") + ".py"
        as_path_js = imp.replace(".", "/") + ".js"
        for p in [as_path_py, as_path_js]:
            if p in all_paths:
                return p
        last = imp.split(".")[-1]
        for path in all_paths:
            if path.endswith(f"/{last}.py") or path.endswith(f"/{last}.js"):
                return path

    return None


def build_dependency_graph(snapshot: RepoSnapshot) -> nx.DiGraph:
    graph = nx.DiGraph()

    for node in snapshot.file_tree:
        graph.add_node(node.path)

    all_paths = {n.path for n in snapshot.file_tree}

    files_parsed = 0
    for file_node in snapshot.file_tree:
        if not file_node.content:
            continue
        ext = file_node.extension
        if ext not in LANGUAGE_MAP:
            continue

        imports = parse_imports(file_node.path, file_node.content, ext)
        files_parsed += 1
        for imp in imports:
            resolved = resolve_import(imp, file_node.path, all_paths)
            if resolved and resolved != file_node.path:
                graph.add_edge(file_node.path, resolved)

    print(f"[parser] parsed {files_parsed} files → "
          f"{graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    return graph


def get_high_centrality_files(graph: nx.DiGraph, top_n: int = 20) -> list:
    """Return top-N files by PageRank — most imported = most central."""
    if graph.number_of_nodes() == 0:
        return []
    if graph.number_of_edges() == 0:
        return list(graph.nodes)[:top_n]
    scores = nx.pagerank(graph)
    return sorted(scores, key=scores.get, reverse=True)[:top_n]