# utils.py
def get_attr(row, key, default=None):
    """
    Robustly fetch an attribute/field from a Turbopuffer Row.
    Works whether the row exposes attributes, a dict, or (rarely) .attributes.
    """
    # typical case: Row model with attributes on the object
    if hasattr(row, key):
        return getattr(row, key)

    # rare: dict-like
    if isinstance(row, dict):
        return row.get(key, default)

    # ultra-rare: nested attributes dict
    if hasattr(row, "attributes") and isinstance(row.attributes, dict):
        return row.attributes.get(key, default)

    return default
