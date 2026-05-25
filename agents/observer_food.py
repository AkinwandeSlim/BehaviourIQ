# agents/observer_food.py
import os
import sys
import pandas as pd
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from memory.vector_store import build_user_profile_v2

# ── Paths ─────────────────────────────────────────────────────────────────────
_REVIEWS_PATH  = os.path.join(_ROOT, "data", "food_reviews.csv")
_PRODUCTS_PATH = os.path.join(_ROOT, "data", "products_metadata.csv")


class ObserverFoodAgent:
    """
    Loads user review history from food_reviews.csv and builds a rich
    taste profile for use by Task A (review generation) and Task B (recommendations).
    CSV is loaded ONCE at init — not on every observe() call.
    """

    def __init__(self):
        print("[Observer] Loading food reviews dataset...")
        self.reviews_df  = pd.read_csv(_REVIEWS_PATH)
        self.products_df = pd.read_csv(_PRODUCTS_PATH)

        # Precompute global popularity list for cold-start handler
        self.top_products = (
            self.reviews_df.groupby("product_id")
            .agg(review_count=("rating", "count"),
                 avg_rating=("rating", "mean"))
            .sort_values("review_count", ascending=False)
            .head(100)
            .reset_index()
        )

        # Build product_id → category/name lookup
        self._product_meta = self.products_df.set_index("product_id").to_dict("index")

        print(f"[Observer] Ready — {len(self.reviews_df):,} reviews, "
              f"{self.reviews_df['user_id'].nunique():,} users")

    # ── helpers ────────────────────────────────────────────────────────────────
    def _product_info(self, product_id: str) -> dict:
        meta = self._product_meta.get(product_id, {})
        return {
            "name":     meta.get("product_name",  f"Product {product_id}"),
            "category": meta.get("category",       "General Food"),
        }

    def _native(self, val):
        """Cast numpy scalars to Python native types (avoids JSON crash)."""
        if isinstance(val, (np.integer,)):  return int(val)
        if isinstance(val, (np.floating,)): return float(val)
        if isinstance(val, (np.bool_,)):    return bool(val)
        return val

    # ── main method ────────────────────────────────────────────────────────────
    def observe(self, user_id: str) -> dict:
        """
        Build a full taste profile for user_id.
        Raises ValueError if user not found.
        """
        user_df = self.reviews_df[self.reviews_df["user_id"] == user_id].copy()
        if user_df.empty:
            raise ValueError(f"User '{user_id}' not found in food_reviews.csv")

        # ── basic stats ────────────────────────────────────────────────────────
        review_count    = int(len(user_df))
        avg_rating      = float(round(user_df["rating"].mean(), 2))
        std_rating      = float(round(user_df["rating"].std(ddof=0), 2)) if review_count > 1 else 0.0
        pct_5star       = float(round((user_df["rating"] == 5).mean() * 100, 1))
        pct_1star       = float(round((user_df["rating"] == 1).mean() * 100, 1))
        pct_positive    = float(round((user_df["rating"] >= 4).mean() * 100, 1))
        preferred_rating = int(user_df["rating"].mode().iloc[0])

        # Helpfulness avg (use column if present)
        if "helpfulness_ratio" in user_df.columns:
            helpfulness_avg = float(round(user_df["helpfulness_ratio"].mean(), 2))
        else:
            helpfulness_avg = 0.0

        # ── segment ───────────────────────────────────────────────────────────
        if "segment" in user_df.columns:
            segment = str(user_df["segment"].iloc[0])
        elif review_count <= 2:
            segment = "cold"
        elif review_count <= 4:
            segment = "lukewarm"
        else:
            segment = "warm"

        # ── category preferences ───────────────────────────────────────────────
        enriched = user_df.copy()
        enriched["category"] = enriched["product_id"].apply(
            lambda pid: self._product_info(pid)["category"]
        )
        top_categories = (
            enriched["category"]
            .value_counts()
            .head(5)
            .index.tolist()
        )

        # ── recent reviews (last 5, sorted newest first) ───────────────────────
        if "date" in user_df.columns:
            sorted_df = user_df.sort_values("date", ascending=False)
        else:
            sorted_df = user_df

        recent_reviews = []
        for _, row in sorted_df.head(5).iterrows():
            pinfo = self._product_info(str(row["product_id"]))
            recent_reviews.append({
                "product_id":   str(row["product_id"]),
                "product_name": pinfo["name"],
                "category":     pinfo["category"],
                "rating":       int(row["rating"]),
                "summary":      str(row.get("review_summary", ""))[:80],
                "text":         str(row.get("review_text", ""))[:200],
            })

        # ── purchased products (all reviewed product_ids) ──────────────────────
        purchased_products = user_df["product_id"].unique().tolist()

        # ── taste profile text (rich text for Claude + ChromaDB) ───────────────
        category_str = ", ".join(top_categories) if top_categories else "General Food"
        recent_str   = "; ".join(
            f"{r['product_name']} ({r['category']}, rated {r['rating']}⭐)"
            for r in recent_reviews[:3]
        )

        taste_profile_text = f"""
Food Reviewer Profile — {user_id}
Segment: {segment.upper()} ({review_count} reviews)
Rating behaviour: avg={avg_rating}/5 | std={std_rating} | preferred={preferred_rating}⭐
Positivity: {pct_positive}% positive reviews | {pct_5star}% five-star | {pct_1star}% one-star
Top food categories: {category_str}
Review helpfulness score: {helpfulness_avg}
Recent activity: {recent_str}
""".strip()

        # ── store embedding in ChromaDB ────────────────────────────────────────
        metadata = {
            "segment":          segment,
            "review_count":     float(review_count),
            "avg_rating":       avg_rating,
            "pct_positive":     pct_positive,
            "pct_5star":        pct_5star,
            "top_category":     top_categories[0] if top_categories else "General Food",
        }
        build_user_profile_v2(user_id, taste_profile_text, metadata)

        return {
            "user_id":           user_id,
            "segment":           segment,
            "review_count":      review_count,
            "avg_rating_given":  avg_rating,
            "std_rating_given":  std_rating,
            "pct_5star":         pct_5star,
            "pct_1star":         pct_1star,
            "pct_positive":      pct_positive,
            "preferred_rating":  preferred_rating,
            "helpfulness_avg":   helpfulness_avg,
            "top_categories":    top_categories,
            "recent_reviews":    recent_reviews,
            "purchased_products": purchased_products,
            "taste_profile_text": taste_profile_text,
        }