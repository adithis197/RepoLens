"""
Step 1: Tree-sitter AST Parsing → File-Level Dependency Graph

Nodes  = files
Edges  = import/require relationships between files

Output is a NetworkX DiGraph used for centrality scoring in Step 2B.
"""
import networkx as nx
from ..step0_ingestion.ingestion import RepoSnapshot


def build_dependency_graph(snapshot: RepoSnapshot) -> nx.DiGraph:
    """
    Parse import/require statements across supported languages
    and return a directed dependency graph.
    """
    graph = nx.DiGraph()

    for file_node in snapshot.file_tree:
        graph.add_node(file_node.path)

    # TODO:
    # 1. For each file with content, run Tree-sitter parse_imports()
    # 2. Resolve relative imports to absolute paths
    # 3. Add edges: graph.add_edge(importer, importee)

    return graph


def parse_imports(file_path: str, content: str, language: str) -> list[str]:
    """
    Use Tree-sitter to extract import targets from a source file.
    Returns a list of raw import strings (not yet resolved to paths).
    """
    # TODO: instantiate Tree-sitter parser for `language`
    # and run a query to capture import nodes
    raise NotImplementedError


def get_high_centrality_files(graph: nx.DiGraph, top_n: int = 20) -> list[str]:
    """
    Return the top-N files by PageRank / in-degree centrality.
    These are fed to Step 2A for semantic inference.
    """
    scores = nx.pagerank(graph)
    return sorted(scores, key=scores.get, reverse=True)[:top_n]
