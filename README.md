# Mercor Search Challenge – Final Submission
**Author:** Disha Dwivedi

This repository contains my end-to-end solution for the Mercor Search Challenge.  
Pipeline overview: **ANN retrieval (Turbopuffer) → Hard Filters → Voyage Rerank → Feature Boosts → (optional) GPT Rerank → Submit to Evaluator**.

---

## Setup

### Python & dependencies
```bash
python -V               # Python 3.10+
pip install -r requirements.txt

## Required environment variables (no .env needed)
export TURBOPUFFER_API_KEY="..."
export VOYAGE_API_KEY="..."
export EVAL_AUTH_EMAIL="you@example.com"   # Authorization header for evaluator
export TPUF_NAMESPACE="search-test-v4"
export TPUF_REGION="aws-us-west-2"
```

## How To Run
### Single Run
```bash
python main.py --one configs/radiology.yml
```
### All Roles
```bash
python main.py --all
```
### Output artifacts

- submissions/evaluator_outputs.json – aggregated evaluator responses for each role (auto-saved).

- Console prints per-role chosen IDs and the evaluator JSON response.

### Manual cURL (debug)
```
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: $EVAL_AUTH_EMAIL" \
  -d '{"config_path":"radiology.yml","object_ids":["ID1","ID2","..."]}' \
  https://mercor-dev--search-eng-interview.modal.run/evaluate
```

## Role configs (YAML)

- natural_query – role description embedded for ANN.

- hard – strict must-haves (degrees_any_of, country_any_of, domain_years.min_years).
- Candidates failing a hard rule are not submitted.

- soft – preferences (prefer_titles_any_of, prefer_keywords, prefer_recent_update_months, degree bonuses).

- weights – blend weights for ann, rerank, features, optional gpt.

- limits – ann_top_k and final_k (size of submitted list, typically 10).

- Filenames must match what the evaluator expects (e.g., tax_lawyer.yml, bankers.yml, …).

## Scoring pipeline (brief)

- Embed & retrieve (ANN) using Voyage voyage-3 + TPUF ANN.

- Hard filters (strict) for degree/country/domain years (counted only on matching titles).

- Rerank (Voyage) with rerank-2 on (query_text, rerankSummary).

- Feature boosts: title exact/fuzzy matches, keyword hits, recency bonus, degree bonuses.

- Blend & submit
```bash
final = w_ann*ann + w_rerank*voyage + w_feat*features
# Sort, take top-10 _ids, submit to evaluator.
```
## Contact

- Name: Disha Dwivedi
- Email: dishadwivedi123g@gmail.com
- LinkedIn: https://www.linkedin.com/in/disha-dwivedi-b69025257/ 
- GitHub: https://github.com/Dis1309/
