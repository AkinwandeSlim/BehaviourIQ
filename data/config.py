# data/config.py
"""
Shared constants for BehaviorIQ.
Import this anywhere you need the category map or model name.
"""

import os
import pandas as pd

# ── model ─────────────────────────────────────────────────────────────────────
# IMPORTANT: claude-sonnet-4-5 is the model that works with the current API key
CLAUDE_MODEL = "claude-sonnet-4-5"
MAX_TOKENS   = 800

# ── paths ─────────────────────────────────────────────────────────────────────
DATA_DIR     = os.path.join(os.path.dirname(__file__))
CSV_PATH     = os.path.join(DATA_DIR, "user_events.csv")
PRODUCTS_PATH = os.path.join(DATA_DIR, "products.json")

# ── category mapping (modulo on sorted categoryids — balanced & deterministic) ─
CATEGORY_LABELS = ["tech", "fashion", "food", "fitness", "travel", "finance"]


def build_category_map(df: pd.DataFrame) -> dict:
    """Map each numeric categoryid → one of 6 named categories."""
    sorted_ids = sorted(df["categoryid"].unique())
    return {int(cid): CATEGORY_LABELS[i % 6] for i, cid in enumerate(sorted_ids)}


def apply_category_map(df: pd.DataFrame, cat_map: dict) -> pd.DataFrame:
    """Add 'category' and 'item' columns to a raw events DataFrame."""
    df = df.copy()
    df["category"] = df["categoryid"].map(cat_map).fillna("tech")
    df["item"]     = df.apply(
        lambda r: f"{r['category'].title()} Item #{r['itemid']}", axis=1
    )
    return df