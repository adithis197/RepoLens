from rank_bm25 import BM25Okapi
import networkx as nx
import numpy as np


def select_top_k(snapshot, graph, context, token_budget=8000):
    # Only consider files that have content
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
        tokens = (f.path + " " + (f.content or "")[:200]).lower().split()
        corpus.append(tokens)

    bm25 = BM25Okapi(corpus)
    query_tokens = " ".join(context.keywords).lower().split()
    bm25_raw = bm25.get_scores(query_tokens)
    max_b = max(bm25_raw) if max(bm25_raw) > 0 else 1
    bm25_scores = {
        candidates[i].path: float(bm25_raw[i]) / max_b
        for i in range(len(candidates))
    }

    # --- Pre-rank top 50 for CodeBERT (saves time) ---
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

    # Files outside top 50 get 0
    codebert_scores = {f.path: 0.0 for f in candidates}
    codebert_scores.update(codebert_scores_partial)

    # --- Combine all three signals ---
    ranked = sorted(
        candidates,
        key=lambda f: (
            0.4 * pagerank_scores.get(f.path, 0) +
            0.4 * bm25_scores.get(f.path, 0) +
            0.2 * codebert_scores.get(f.path, 0)
        ),
        reverse=True
    )

    # --- Pick files until token budget is full ---
    selected = []
    used_tokens = 0
    for f in ranked:
        tokens = len(f.content) // 4
        if used_tokens + tokens > token_budget:
            break
        selected.append(f)
        used_tokens += tokens

    print(f"[retrieval] selected {len(selected)} files, ~{used_tokens} tokens")
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