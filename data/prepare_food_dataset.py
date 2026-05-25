#!/usr/bin/env python3
"""
BehaviorIQ — Amazon Fine Food Reviews Data Prep (LOCAL VERSION)
Converts raw Amazon Food Reviews → Task A + Task B datasets
Run this ONCE to prepare the data locally
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import sys
import os

warnings.filterwarnings("ignore")

print("=" * 70)
print("BehaviorIQ: Amazon Fine Food Reviews Data Prep")
print("=" * 70)

# ─────────────────────────────────────────────────────────────────
# STEP 1: Validate input file exists
# ─────────────────────────────────────────────────────────────────
print("\n[1/11] Checking for Reviews.csv...")

# Expected locations (user can place it in any of these)
POSSIBLE_PATHS = [
    "data/Reviews.csv",
    "Reviews.csv",
    os.path.expanduser("~/Downloads/Reviews.csv"),
    os.path.expanduser("~/Downloads/amazon-fine-food-reviews/Reviews.csv"),
]

input_file = None
for path in POSSIBLE_PATHS:
    if os.path.exists(path):
        input_file = path
        print(f"✅ Found: {path}")
        break

if not input_file:
    print("❌ Reviews.csv not found in expected locations:")
    for path in POSSIBLE_PATHS:
        print(f"   - {path}")
    print("\n📥 Please download from Kaggle:")
    print("   https://www.kaggle.com/snap/amazon-fine-food-reviews")
    print("   Place Reviews.csv in the current directory or data/ folder")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────
# STEP 2: Load raw data
# ─────────────────────────────────────────────────────────────────
print(f"\n[2/11] Loading {input_file}...")
try:
    df = pd.read_csv(input_file)
    print(f"✅ Loaded: {df.shape[0]:,} rows × {df.shape[1]} cols")
    print(f"   Columns: {df.columns.tolist()}")
    print(f"\n   Score distribution:")
    for score, count in df['Score'].value_counts().sort_index().items():
        print(f"     {score}★: {count:,} reviews")
except Exception as e:
    print(f"❌ Error loading CSV: {e}")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────
# STEP 3: Clean & deduplicate
# ─────────────────────────────────────────────────────────────────
print("\n[3/11] Cleaning data...")
df_orig_size = len(df)

# Drop duplicates (keep latest review per user-product pair)
df = df.sort_values("Time").drop_duplicates(
    subset=["UserId", "ProductId"], keep="last"
).copy()

# Drop rows with missing critical fields
df = df.dropna(subset=["Text", "Summary", "UserId", "ProductId", "Score"])

# Clean text
df["Text"] = df["Text"].str.strip()
df["Summary"] = df["Summary"].str.strip()

# Filter out reviews that are too short (likely spam)
df = df[df["Text"].str.len() >= 20].copy()

print(f"✅ Cleaned: {df_orig_size:,} → {len(df):,} rows")
print(f"   Removed: {df_orig_size - len(df):,} rows (duplicates, nulls, short text)")

# ─────────────────────────────────────────────────────────────────
# STEP 4: Add temporal & helpfulness features
# ─────────────────────────────────────────────────────────────────
print("\n[4/11] Adding temporal features...")

df["date"] = pd.to_datetime(df["Time"], unit="s")
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month
df["helpfulness_ratio"] = np.where(
    df["HelpfulnessDenominator"] > 0,
    df["HelpfulnessNumerator"] / df["HelpfulnessDenominator"],
    0.0
)

print(f"✅ Date range: {df['date'].min().date()} → {df['date'].max().date()}")
print(f"   Unique users: {df['UserId'].nunique():,}")
print(f"   Unique products: {df['ProductId'].nunique():,}")

# ─────────────────────────────────────────────────────────────────
# STEP 5: Select top 500 active users (for rich profiles)
# ─────────────────────────────────────────────────────────────────
print("\n[5/11] Selecting active users (5+ reviews)...")

user_counts = df.groupby("UserId").size()
top_500 = user_counts[user_counts >= 5].nlargest(500).index

df_active = df[df["UserId"].isin(top_500)].copy()

print(f"✅ Top 500 users with 5+ reviews:")
print(f"   Events: {len(df_active):,}")
print(f"   Avg reviews/user: {len(df_active)/500:.1f}")
print(f"   Unique products: {df_active['ProductId'].nunique():,}")

# ─────────────────────────────────────────────────────────────────
# STEP 6: Map user IDs to friendly format
# ─────────────────────────────────────────────────────────────────
print("\n[6/11] Creating user mappings...")

uid_map = {uid: f"user_{i+1:04d}" for i, uid in enumerate(top_500)}
df_active["user_id"] = df_active["UserId"].map(uid_map)

print(f"✅ Created {len(uid_map)} user IDs (user_0001 → user_0500)")

# ─────────────────────────────────────────────────────────────────
# STEP 7: Build product metadata (from ALL reviews for global context)
# ─────────────────────────────────────────────────────────────────
print("\n[7/11] Building product metadata...")

product_stats = df.groupby("ProductId").agg(
    avg_rating=("Score", "mean"),
    review_count=("Score", "count"),
    sample_summary=("Summary", lambda x: x.iloc[0]),
    sample_text=("Text", lambda x: x.iloc[0][:200]),  # First 200 chars
).reset_index()

product_stats["avg_rating"] = product_stats["avg_rating"].round(2)

# Get products from top 500 users
top_products = df_active["ProductId"].value_counts().head(200).index
product_meta = product_stats[product_stats["ProductId"].isin(top_products)].copy()

print(f"✅ Product metadata: {len(product_meta)} products")

# ─────────────────────────────────────────────────────────────────
# STEP 8: Build TASK A dataset (Review Generation)
# ─────────────────────────────────────────────────────────────────
print("\n[8/11] Building Task A dataset (Review Generation)...")

task_a = df_active[[
    "user_id", "ProductId", "Score", "Summary", "Text",
    "helpfulness_ratio", "date", "year", "month"
]].copy()

task_a.columns = [
    "user_id", "product_id", "rating", "review_summary",
    "review_text", "helpfulness_ratio", "date", "year", "month"
]

# Add user profile features
user_profiles = df_active.groupby("user_id").agg(
    avg_rating_given=("Score", "mean"),
    review_count=("Score", "count"),
    pct_5star=("Score", lambda x: (x == 5).mean()),
    pct_1star=("Score", lambda x: (x == 1).mean()),
    std_rating=("Score", "std"),
    preferred_rating=("Score", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.mean()),
).reset_index()

task_a = task_a.merge(user_profiles, on="user_id", how="left")

print(f"✅ Task A: {len(task_a):,} reviews")
print(f"   Columns: {task_a.columns.tolist()}")

# ─────────────────────────────────────────────────────────────────
# STEP 9: Build TASK B dataset (Recommendations)
# ─────────────────────────────────────────────────────────────────
print("\n[9/11] Building Task B dataset (Recommendations)...")

task_b = df_active[[
    "user_id", "ProductId", "Score", "date"
]].copy()

task_b.columns = ["user_id", "product_id", "rating", "date"]

# Add product popularity rank (for cold-start baseline)
product_pop = df["ProductId"].value_counts().reset_index()
product_pop.columns = ["product_id", "global_popularity"]
task_b = task_b.merge(product_pop, on="product_id", how="left")

print(f"✅ Task B: {len(task_b):,} interactions")
print(f"   Rating distribution:")
for score, count in task_b["rating"].value_counts().sort_index().items():
    print(f"     {score}★: {count:,}")

# ─────────────────────────────────────────────────────────────────
# STEP 10: Build Nigerian context mapping
# ─────────────────────────────────────────────────────────────────
print("\n[10/11] Mapping Nigerian product categories...")

NIGERIAN_CATEGORY_MAP = {
    "spice": "Spices & Seasonings",
    "seasoning": "Spices & Seasonings",
    "pepper": "Spices & Seasonings",
    "salt": "Spices & Seasonings",
    "tea": "Beverages & Drinks",
    "coffee": "Beverages & Drinks",
    "drink": "Beverages & Drinks",
    "juice": "Beverages & Drinks",
    "snack": "Snacks & Biscuits",
    "chip": "Snacks & Biscuits",
    "cookie": "Snacks & Biscuits",
    "candy": "Snacks & Confectionery",
    "chocolate": "Snacks & Confectionery",
    "rice": "Grains & Staples",
    "pasta": "Grains & Staples",
    "noodle": "Grains & Staples",
    "flour": "Grains & Staples",
    "oil": "Oils & Condiments",
    "sauce": "Oils & Condiments",
    "dog": "Pet Food & Supplies",
    "cat": "Pet Food & Supplies",
    "vitamin": "Health & Supplements",
    "protein": "Health & Supplements",
    "organic": "Organic & Natural",
}

def get_nigerian_category(summary_text: str) -> str:
    text_lower = str(summary_text).lower()
    for keyword, category in NIGERIAN_CATEGORY_MAP.items():
        if keyword in text_lower:
            return category
    return "General Food & Grocery"

product_meta["nigerian_category"] = product_meta["sample_summary"].apply(
    get_nigerian_category
)

print(f"✅ Nigerian categories:")
for cat, count in product_meta["nigerian_category"].value_counts().items():
    print(f"   {cat}: {count}")

# ─────────────────────────────────────────────────────────────────
# STEP 11: Validation checks
# ─────────────────────────────────────────────────────────────────
print("\n[11/11] Running validation checks...")

checks = {
    "No null user_ids (Task A)": task_a["user_id"].isna().sum() == 0,
    "No null product_ids (Task A)": task_a["product_id"].isna().sum() == 0,
    "No null ratings (Task A)": task_a["rating"].isna().sum() == 0,
    "No null review text (Task A)": task_a["review_text"].isna().sum() == 0,
    "Valid ratings 1-5 (Task A)": task_a["rating"].between(1, 5).all(),
    "No null user_ids (Task B)": task_b["user_id"].isna().sum() == 0,
    "500 users present": task_a["user_id"].nunique() == 500,
    "Products have metadata": len(product_meta) > 0,
}

all_passed = True
for check, result in checks.items():
    status = "✅" if result else "❌"
    if not result:
        all_passed = False
    print(f"  {status} {check}")

if not all_passed:
    print("\n❌ Some checks failed!")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────
# SAVE OUTPUTS
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SAVING OUTPUTS")
print("=" * 70)

output_dir = "data"
os.makedirs(output_dir, exist_ok=True)

task_a_path = os.path.join(output_dir, "food_reviews_task_a.csv")
task_b_path = os.path.join(output_dir, "food_reviews_task_b.csv")
products_path = os.path.join(output_dir, "food_products_meta.csv")

task_a.to_csv(task_a_path, index=False)
task_b.to_csv(task_b_path, index=False)
product_meta.to_csv(products_path, index=False)

print(f"\n✅ Saved to {output_dir}/")
print(f"   {task_a_path}")
print(f"   {task_b_path}")
print(f"   {products_path}")

# ─────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"✅ Task A (Reviews)     : {len(task_a):,} rows")
print(f"✅ Task B (Interactions): {len(task_b):,} rows")
print(f"✅ Products (Metadata)  : {len(product_meta):,} products")
print(f"\n🎉 Data prep complete! Ready for agents.")
