import os, json, yaml, requests, math
from tbuf_client import embed_query, ann_query
from rerank import rerank_pairs
from scoring import hard_filter, feature_score
from utils import get_attr

EVAL_URL = "https://mercor-dev--search-eng-interview.modal.run/evaluate"
AUTH_EMAIL = os.environ["EVAL_AUTH_EMAIL"]  # use the same email they asked for

def run_role(config_path: str):
    cfg = yaml.safe_load(open(config_path, "r"))
    name = cfg["name"]
    qtext = cfg["natural_query"]
    ann_k = cfg.get("limits", {}).get("ann_top_k", 300)
    final_k = cfg.get("limits", {}).get("final_k", 10)
    w_ann = cfg.get("weights", {}).get("ann", 0.4)
    w_rr  = cfg.get("weights", {}).get("rerank", 0.45)
    w_ft  = cfg.get("weights", {}).get("features", 0.15)

    print(f"[{name}] embedding query…")
    qvec = embed_query(qtext)

    print(f"[{name}] ANN retrieve top {ann_k}…")
    res = ann_query(qvec, top_k=ann_k)
    rows = res.rows  # contains .id and .attributes

    print(f"[{name}] hard filtering…")
    filtered = [r for r in rows if hard_filter(r, cfg)]
    if not filtered:
        print("No candidates survived hard filters; falling back to top-ANN.")
        filtered = rows[:final_k]

    print(f"[{name}] reranking {len(filtered)} with voyage rerank-2…")
    docs = [get_attr(r, "rerankSummary") or "" for r in filtered]    
    rr_scores = rerank_pairs(qtext, docs)

    print(f"[{name}] feature scoring…")
    ft_scores = [feature_score(r, cfg) for r in filtered]

    # TPUF ANN score is implicitly the ranking position; approximate ANN similarity
    # Since we don't get raw similarity back, derive a monotone score from index:
    ann_scores = [1.0 - (i / max(1, len(filtered)-1)) for i,_ in enumerate(filtered)]

    final = []
    for r, s_ann, s_rr, s_ft in zip(filtered, ann_scores, rr_scores, ft_scores):
        score = w_ann*s_ann + w_rr*s_rr + w_ft*s_ft
        final.append((score, r))

    final.sort(key=lambda x: x[0], reverse=True)
    top = final[:final_k]
    ids = [r.id for _, r in top]

    print(f"[{name}] picked {len(ids)} candidates.")
    return ids

def evaluate(config_path: str, object_ids: list[str]):
    body = {"config_path": os.path.basename(config_path), "object_ids": object_ids}
    headers = {"Content-Type": "application/json", "Authorization": AUTH_EMAIL}
    r = requests.post(EVAL_URL, headers=headers, data=json.dumps(body), timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"Eval failed {r.status_code}: {r.text}")
    print("Eval response:", r.text)

if __name__ == "__main__":
    import argparse, glob
    ap = argparse.ArgumentParser()
    ap.add_argument("--one", help="configs/<file>.yml to run once")
    ap.add_argument("--all", action="store_true", help="run all 10 configs")
    args = ap.parse_args()

    if args.one:
        ids = run_role(args.one)
        evaluate(args.one, ids)
    else:
        files = sorted(glob.glob("configs/*.yml"))
        if not args.all:
            print("Tip: pass --one configs/tax_lawyer.yml or --all")
        for f in files:
            ids = run_role(f)
            evaluate(f, ids)
