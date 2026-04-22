from rank_bm25 import BM25Okapi
import networkx as nx
import numpy as np

# Target: 8-10 files at full content, so LLM sees real functions/classes
MIN_FILES = 6
MAX_FILES = 10
# Budget is generous because Groq handles it easily
TOKEN_BUDGET_DEFAULT = 24000
# But cap per-file content so one massive file doesn't eat everything
MAX_CHARS_PER_FILE = 6000  # ~1500 tokens — enough to see all major functions


def _truncate_content(content: str) -> str:
    if not content:
        return ""
    if len(content) <= MAX_CHARS_PER_FILE:
        return content
    # keep the start (imports, classes, main logic) + trailing note
    return content[:MAX_CHARS_PER_FILE] + "\n\n# ... (file continues)"


def select_top_k(snapshot, graph, context, token_budget=TOKEN_BUDGET_DEFAULT):
    candidates = [f for f in snapshot.file_tree if f.content]

    if not candidates:
        print("[retrieval] no candidates found")
        return []

    # --- Signal 1: PageRank ---
    try:
        centrality = nx.pagerank(graph)
    except Exception:
        centrality = {}
    max_c = max(centrality.values()) if centrality else 1
    pagerank_scores = {
        f.path: centrality.get(f.path, 0) / max_c
        for f in candidates
    }

    # --- Signal 2: BM25 ---
    corpus = []
    for f in candidates:
        tokens = (f.path + " " + (f.content or "")[:300]).lower().split()
        corpus.append(tokens)

    bm25 = BM25Okapi(corpus)
    query_tokens = " ".join(context.keywords).lower().split()
    bm25_raw = bm25.get_scores(query_tokens)
    max_b = max(bm25_raw) if max(bm25_raw) > 0 else 1
    bm25_scores = {
        candidates[i].path: float(bm25_raw[i]) / max_b
        for i in range(len(candidates))
    }

    # --- Pre-rank top 50 for CodeBERT ---
    pre_ranked = sorted(
        candidates,
        key=lambda f: (
            0.5 * pagerank_scores.get(f.path, 0) +
            0.5 * bm25_scores.get(f.path, 0)
        ),
        reverse=True
    )
    top_50 = pre_ranked[:50]

    # --- Signal 3: CodeBERT ---
    codebert_scores_partial = compute_codebert_scores(top_50, context.summary)
    codebert_scores = {f.path: 0.0 for f in candidates}
    codebert_scores.update(codebert_scores_partial)

    # --- Penalty: de-rank tests/examples/docs ---
    def penalty(path: str) -> float:
        low = path.lower()
        if any(p in low for p in [
            "tests/", "test_", "/tests/", "examples/", "docs/", "doc/",
            "/example/", "/tutorial/", "/sample/", "__pycache__/"
        ]):
            return 0.2  # 80% penalty — push these way down
        if low.endswith((".md", ".rst", ".txt", ".yml", ".yaml", ".toml", ".cfg")):
            return 0.5
        return 1.0

    # --- Bonus: boost entry points (from Person 2 context) ---
    entry_set = set(getattr(context, "entry_points", []))

    def bonus(path: str) -> float:
        return 1.5 if path in entry_set else 1.0

    # --- Combine all signals ---
    ranked = sorted(
        candidates,
        key=lambda f: (
            0.4 * pagerank_scores.get(f.path, 0) +
            0.4 * bm25_scores.get(f.path, 0) +
            0.2 * codebert_scores.get(f.path, 0)
        ) * penalty(f.path) * bonus(f.path),
        reverse=True
    )

    # --- Pick up to MAX_FILES, using full content up to MAX_CHARS_PER_FILE ---
    selected = []
    used_tokens = 0

    for f in ranked:
        if len(selected) >= MAX_FILES:
            break

        truncated = _truncate_content(f.content)
        tokens = len(truncated) // 4

        # Always include MIN_FILES even if over budget
        if len(selected) < MIN_FILES:
            selected.append(f)
            used_tokens += tokens
            continue

        if used_tokens + tokens > token_budget:
            break

        selected.append(f)
        used_tokens += tokens

    # Mutate content to truncated version so the LLM gets the truncated one
    for f in selected:
        f.content = _truncate_content(f.content)

    print(f"[retrieval] selected {len(selected)} files, ~{used_tokens} tokens")
    print("[retrieval] selected paths:")
    for f in selected:
        print(f"  {f.path} ({len(f.content or '')} chars)")
    return selected


def compute_codebert_scores(candidates, repo_summary):
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("microsoft/codebert-base")
        query_embedding = model.encode(repo_summary)
        file_texts = [(f.content or "")[:512] for f in candidates]
        file_embeddings = model.encode(file_texts)

        scores = {}
        for i, f in enumerate(candidates):
            norm = (
                np.linalg.norm(query_embedding) *
                np.linalg.norm(file_embeddings[i])
            )
            similarity = (
                float(np.dot(query_embedding, file_embeddings[i]) / norm)
                if norm > 0 else 0.0
            )
            scores[f.path] = max(0.0, similarity)

        max_s = max(scores.values()) if scores and max(scores.values()) > 0 else 1
        return {k: v / max_s for k, v in scores.items()}

    except Exception as e:
        print(f"[retrieval] CodeBERT failed, skipping: {e}")
        return {f.path: 0.0 for f in candidates}


def compress_remaining(snapshot, selected_paths):
    selected_set = set(selected_paths)
    folder_files = {}

    for f in snapshot.file_tree:
        if f.path not in selected_set:
            folder = f.path.split("/")[0]
            folder_files.setdefault(folder, []).append(f.path)

    summaries = {}
    for folder, files in folder_files.items():
        summaries[folder] = f"{len(files)} files (not included in detail)"

    return summaries