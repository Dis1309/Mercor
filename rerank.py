# rerank.py
import os
import voyageai

VOYAGE_API_KEY = os.environ["VOYAGE_API_KEY"]
_voy = voyageai.Client(api_key=VOYAGE_API_KEY)

def _get_score(item):
    # Newer SDKs expose `relevance_score`; some examples use `score`.
    for attr in ("relevance_score", "score", "relevance"):
        if hasattr(item, attr):
            val = getattr(item, attr)
            try:
                return float(val)
            except Exception:
                return 0.0
    return 0.0

def rerank_pairs(query_text: str, docs: list[str]) -> list[float]:
    """
    Returns scores aligned with `docs` order using Voyage reranker.
    """
    if not docs:
        return []

    # Call voyage reranker
    rr = _voy.rerank(query=query_text, documents=docs, model="rerank-2")

    # Voyage may return results out of order; align back to our indices
    score_by_idx = {res.index: _get_score(res) for res in rr.results}

    # Build list in original docs order (missing indices -> 0.0)
    scores = [score_by_idx.get(i, 0.0) for i in range(len(docs))]

    # Optionally normalize to [0,1] if you want
    # (Voyage already returns a 0..1-ish score; keep as-is)
    return scores
