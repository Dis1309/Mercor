import os
import turbopuffer
import voyageai

VOYAGE_API_KEY = os.environ["VOYAGE_API_KEY"]
TURBOPUFFER_API_KEY = os.environ["TURBOPUFFER_API_KEY"]
TPUF_REGION = os.getenv("TPUF_REGION", "aws-us-west-2")
TPUF_NAMESPACE = os.getenv("TPUF_NAMESPACE", "search-test-v4")

_voy = voyageai.Client(api_key=VOYAGE_API_KEY)
_tpuf = turbopuffer.Turbopuffer(api_key=TURBOPUFFER_API_KEY, region=TPUF_REGION)
_ns = _tpuf.namespace(TPUF_NAMESPACE)

def embed_query(text: str):
    resp = _voy.embed(text, model="voyage-3")
    return resp.embeddings[0]  # 1024-d

def ann_query(embedding, top_k: int = 200):
    return _ns.query(
        rank_by=("vector", "ANN", embedding),
        top_k=top_k,
        include_attributes=True,
    )
