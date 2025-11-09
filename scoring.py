# scoring.py
import re
from datetime import datetime, timedelta
from dateutil import parser as dtparse
from rapidfuzz import fuzz
from datetime import datetime, timedelta, timezone 
from utils import get_attr

def _safe_parse(dt_str):
    if not dt_str:
        return None
    try:
        dt = dtparse.parse(dt_str)
        # normalize to naive UTC so we can compare with datetime.utcnow()
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        return None

def _norm_set(x):
    if not x: return set()
    return set(s.strip().lower() for s in x if isinstance(s, str))

def has_required_degree(row, allowed):
    degrees = _norm_set(get_attr(row, "deg_degrees", []))
    allowed = _norm_set(allowed)
    return bool(degrees & allowed)

def in_allowed_countries(row, allowed):
    country = (get_attr(row, "country", "") or "").strip().lower()
    return country in _norm_set(allowed)

def meets_total_years_bucket(row, min_bucket: str):
    buckets = get_attr(row, "exp_years", []) or []
    needed = int(min_bucket)
    return any(int((b or "0")) >= needed for b in buckets)

BUCKET_RE = re.compile(r"yrs_(\d+)::")

def _bucket_to_min_years(b: str):
    try: return int(b)
    except: return 0

def domain_years_from_experience(exp_lines, title_keywords):
    if not exp_lines: return 0.0
    total = 0.0
    kws = [k.lower() for k in title_keywords]
    for line in exp_lines:
        low = str(line).lower()
        if any(k in low for k in kws):
            m = BUCKET_RE.search(low)
            if m:
                total += _bucket_to_min_years(m.group(1))
    return total

def hard_filter(row, cfg):
    hard = cfg.get("hard", {})

    if "degrees_any_of" in hard and not has_required_degree(row, hard["degrees_any_of"]):
        return False
    if "country_any_of" in hard and not in_allowed_countries(row, hard["country_any_of"]):
        return False
    if "min_total_years_bucket" in hard and not meets_total_years_bucket(row, hard["min_total_years_bucket"]):
        return False

    dom = hard.get("domain_years")
    if dom:
        exp_lines = get_attr(row, "experience", []) or []
        want_titles = dom.get("title_keywords", [])
        min_years = float(dom.get("min_years", 0))
        yrs = domain_years_from_experience(exp_lines, want_titles)
        if yrs < min_years:
            return False

    if hard.get("require_us_mba", False):
        degrees = _norm_set(get_attr(row, "deg_degrees", []))
        if "mba" not in degrees:
            return False

    return True

def feature_score(row, cfg):
    soft = cfg.get("soft", {})
    score = 0.0

    want_titles = soft.get("prefer_titles_any_of", [])
    titles = get_attr(row, "exp_titles", []) or []
    if want_titles and titles:
        if _norm_set(titles) & _norm_set(want_titles):
            score += 0.9
        else:
            from rapidfuzz import fuzz
            best = max((fuzz.token_set_ratio(t, w) for t in titles for w in want_titles), default=0)
            score += 0.6 * (best / 100)

    want_kw = soft.get("prefer_keywords", [])
    if want_kw:
        txt = (get_attr(row, "rerankSummary", "") or "").lower()
        score += 0.15 * sum(1 for k in want_kw if k.lower() in txt)

    months = soft.get("prefer_recent_update_months")
    if months is not None:
        try:
            months = int(months)
        except Exception:
            months = 0
        upd = _safe_parse(get_attr(row, "updated_at", None))
        if upd:
            cutoff = datetime.utcnow() - timedelta(days=30 * months)
            if upd >= cutoff:
                score += 0.5

    for deg, bonus in (soft.get("degree_bonus", {}) or {}).items():
        if deg.lower() in _norm_set(get_attr(row, "deg_degrees", [])):
            score += float(bonus)

    dom = soft.get("domain_years_bonus")
    if dom:
        exp_lines = get_attr(row, "experience", []) or []
        yrs = domain_years_from_experience(exp_lines, dom.get("title_keywords", []))
        extra = max(0.0, yrs - float(dom.get("threshold", 0)))
        score += 0.1 * extra

    return score
