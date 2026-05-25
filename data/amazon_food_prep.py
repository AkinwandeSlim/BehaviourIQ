# ============================================================
# BehaviorIQ — Amazon Fine Food Reviews Data Prep Notebook
# Run ONE cell at a time. Paste output before moving to next.
# ============================================================


# ─────────────────────────────────────────────────────────────
# CELL 1 — Imports
# ─────────────────────────────────────────────────────────────
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

print("✅ Imports done")
print(f"pandas  : {pd.__version__}")
print(f"numpy   : {np.__version__}")


# ─────────────────────────────────────────────────────────────
# CELL 2 — Load raw data
# ─────────────────────────────────────────────────────────────
df = pd.read_csv("/kaggle/input/amazon-fine-food-reviews/Reviews.csv")

print("=" * 55)
print("RAW DATASET OVERVIEW")
print("=" * 55)
print(f"Shape          : {df.shape}")
print(f"Columns        : {df.columns.tolist()}")
print()
print("Data types:")
print(df.dtypes)
print()
print("Null counts:")
print(df.isnull().sum())
print()
print("Sample rows:")
print(df.head(3).to_string())


# ─────────────────────────────────────────────────────────────
# CELL 3 — Score distribution (understand what we are working with)
# ─────────────────────────────────────────────────────────────
print("=" * 55)
print("SCORE DISTRIBUTION")
print("=" * 55)
score_dist = df["Score"].value_counts().sort_index()
total = len(df)
for score, count in score_dist.items():
    bar = "█" * int(count / total * 50)
    print(f"  {score}★  {count:>7,}  ({count/total*100:5.1f}%)  {bar}")

print()
print(f"Mean rating    : {df['Score'].mean():.3f}")
print(f"Median rating  : {df['Score'].median():.1f}")
print(f"Std deviation  : {df['Score'].std():.3f}")
print()

# Check for invalid scores
invalid = df[~df["Score"].between(1, 5)]
print(f"Invalid scores : {len(invalid)}")


# ─────────────────────────────────────────────────────────────
# CELL 4 — User activity distribution
# ─────────────────────────────────────────────────────────────
print("=" * 55)
print("USER ACTIVITY ANALYSIS")
print("=" * 55)

user_counts = df.groupby("UserId").size()

print(f"Total unique users     : {len(user_counts):,}")
print()
print("Reviews per user distribution:")
print(f"  Min    : {user_counts.min()}")
print(f"  Median : {user_counts.median():.0f}")
print(f"  Mean   : {user_counts.mean():.1f}")
print(f"  Max    : {user_counts.max():,}")
print()

# Segment breakdown
cold_mask     = user_counts <= 2
lukewarm_mask = (user_counts >= 3) & (user_counts <= 4)
warm_mask     = user_counts >= 5

cold_users     = user_counts[cold_mask]
lukewarm_users = user_counts[lukewarm_mask]
warm_users     = user_counts[warm_mask]

print("Segment breakdown:")
print(f"  Cold     (1-2 reviews)  : {len(cold_users):>7,} users  "
      f"({len(cold_users)/len(user_counts)*100:.1f}%)")
print(f"  Lukewarm (3-4 reviews)  : {len(lukewarm_users):>7,} users  "
      f"({len(lukewarm_users)/len(user_counts)*100:.1f}%)")
print(f"  Warm     (5+ reviews)   : {len(warm_users):>7,} users  "
      f"({len(warm_users)/len(user_counts)*100:.1f}%)")
print()

# Coverage check
total_reviews_by_segment = {
    "cold":     df[df["UserId"].isin(cold_users.index)].shape[0],
    "lukewarm": df[df["UserId"].isin(lukewarm_users.index)].shape[0],
    "warm":     df[df["UserId"].isin(warm_users.index)].shape[0],
}
print("Reviews per segment:")
for seg, count in total_reviews_by_segment.items():
    print(f"  {seg:<10}: {count:>7,} reviews ({count/total*100:.1f}% of dataset)")


# ─────────────────────────────────────────────────────────────
# CELL 5 — Product analysis
# ─────────────────────────────────────────────────────────────
print("=" * 55)
print("PRODUCT ANALYSIS")
print("=" * 55)

product_counts = df.groupby("ProductId").size()
product_ratings = df.groupby("ProductId")["Score"].mean()

print(f"Total unique products  : {product_counts.shape[0]:,}")
print()
print("Reviews per product:")
print(f"  Min    : {product_counts.min()}")
print(f"  Median : {product_counts.median():.0f}")
print(f"  Mean   : {product_counts.mean():.1f}")
print(f"  Max    : {product_counts.max():,}")
print()
print("Top 10 most reviewed products:")
top_products = product_counts.sort_values(ascending=False).head(10)
for pid, count in top_products.items():
    avg = product_ratings[pid]
    print(f"  {pid}  {count:>5,} reviews  avg={avg:.2f}★")
print()

# Sample text from most reviewed product
top_pid = top_products.index[0]
sample = df[df["ProductId"] == top_pid].iloc[0]
print(f"Sample review from top product ({top_pid}):")
print(f"  Summary : {sample['Summary']}")
print(f"  Text    : {str(sample['Text'])[:200]}...")


# ─────────────────────────────────────────────────────────────
# CELL 6 — Helpfulness analysis
# ─────────────────────────────────────────────────────────────
print("=" * 55)
print("HELPFULNESS ANALYSIS")
print("=" * 55)

# Check denominator = 0 cases
zero_denom = (df["HelpfulnessDenominator"] == 0).sum()
print(f"Reviews with 0 votes   : {zero_denom:,} ({zero_denom/total*100:.1f}%)")

# Calculate ratio safely
df["helpfulness_ratio"] = np.where(
    df["HelpfulnessDenominator"] > 0,
    df["HelpfulnessNumerator"] / df["HelpfulnessDenominator"],
    np.nan
)

rated = df["helpfulness_ratio"].notna()
print(f"Reviews with votes     : {rated.sum():,} ({rated.sum()/total*100:.1f}%)")
print()
print("Helpfulness ratio (for reviewed items):")
print(f"  Mean   : {df['helpfulness_ratio'].mean():.3f}")
print(f"  Median : {df['helpfulness_ratio'].median():.3f}")
print(f"  % above 0.8 (highly helpful): "
      f"{(df['helpfulness_ratio'] >= 0.8).sum():,}")

# Fill NaN with 0 for users with no votes
df["helpfulness_ratio"] = df["helpfulness_ratio"].fillna(0.0)
print()
print("After filling NaN with 0:")
print(f"  Nulls remaining: {df['helpfulness_ratio'].isna().sum()}")


# ─────────────────────────────────────────────────────────────
# CELL 7 — Text quality check
# ─────────────────────────────────────────────────────────────
print("=" * 55)
print("TEXT QUALITY CHECK")
print("=" * 55)

# Check for null text
print(f"Null review text       : {df['Text'].isna().sum():,}")
print(f"Null summary           : {df['Summary'].isna().sum():,}")
print()

# Review text length distribution
df["text_length"] = df["Text"].fillna("").str.len()
df["summary_length"] = df["Summary"].fillna("").str.len()

print("Review text length (chars):")
print(f"  Min    : {df['text_length'].min()}")
print(f"  Median : {df['text_length'].median():.0f}")
print(f"  Mean   : {df['text_length'].mean():.0f}")
print(f"  Max    : {df['text_length'].max():,}")
print()

# Very short reviews (likely low quality)
short_reviews = (df["text_length"] < 20).sum()
print(f"Very short reviews (<20 chars) : {short_reviews:,} ({short_reviews/total*100:.1f}%)")
print()

# Sample of short reviews
print("Sample very short reviews:")
short_sample = df[df["text_length"] < 20][["Score","Summary","Text"]].head(5)
print(short_sample.to_string())


# ─────────────────────────────────────────────────────────────
# CELL 8 — Duplicate analysis
# ─────────────────────────────────────────────────────────────
print("=" * 55)
print("DUPLICATE ANALYSIS")
print("=" * 55)

# Same user reviewing same product multiple times
user_product_pairs = df.groupby(["UserId", "ProductId"]).size()
duplicate_pairs = user_product_pairs[user_product_pairs > 1]

print(f"Total user-product pairs       : {len(user_product_pairs):,}")
print(f"Duplicate pairs (same user, same product): {len(duplicate_pairs):,}")
print()

# Exact text duplicates
exact_dupes = df.duplicated(subset=["UserId", "ProductId", "Text"]).sum()
print(f"Exact text duplicates          : {exact_dupes:,}")
print()

# Show sample duplicate
if len(duplicate_pairs) > 0:
    sample_pair = duplicate_pairs.index[0]
    sample_dupes = df[
        (df["UserId"] == sample_pair[0]) &
        (df["ProductId"] == sample_pair[1])
    ][["Score", "Summary", "Time"]]
    print("Sample duplicate user-product pair:")
    print(sample_dupes.to_string())


# ─────────────────────────────────────────────────────────────
# CELL 9 — Build per-user features
# ─────────────────────────────────────────────────────────────
print("=" * 55)
print("BUILDING PER-USER FEATURES")
print("=" * 55)

user_features = df.groupby("UserId").agg(
    review_count      = ("Score", "count"),
    avg_rating_given  = ("Score", "mean"),
    std_rating_given  = ("Score", "std"),
    pct_5star         = ("Score", lambda x: (x == 5).mean()),
    pct_1star         = ("Score", lambda x: (x == 1).mean()),
    pct_positive      = ("Score", lambda x: (x >= 4).mean()),
    preferred_rating  = ("Score", lambda x: x.mode().iloc[0]),
    avg_text_length   = ("text_length", "mean"),
    avg_helpfulness   = ("helpfulness_ratio", "mean"),
    first_review_date = ("Time", "min"),
    last_review_date  = ("Time", "max"),
).reset_index()

# Fill std NaN (users with 1 review have no std)
user_features["std_rating_given"] = user_features["std_rating_given"].fillna(0.0)

# Round floats
for col in ["avg_rating_given", "std_rating_given", "pct_5star",
            "pct_1star", "pct_positive", "avg_text_length", "avg_helpfulness"]:
    user_features[col] = user_features[col].round(3)

# Add segment
def get_segment(count):
    if count <= 2:  return "cold"
    if count <= 4:  return "lukewarm"
    return "warm"

user_features["segment"] = user_features["review_count"].apply(get_segment)

print("User features shape:", user_features.shape)
print("Columns:", user_features.columns.tolist())
print()
print("Segment distribution:")
print(user_features["segment"].value_counts())
print()
print("Feature stats by segment:")
print(user_features.groupby("segment")[
    ["avg_rating_given","pct_5star","pct_1star","avg_helpfulness"]
].mean().round(3))
print()
print("Sample user features (warm):")
warm_sample = user_features[user_features["segment"] == "warm"].head(3)
print(warm_sample[[
    "UserId","review_count","avg_rating_given","pct_5star",
    "pct_positive","preferred_rating","segment"
]].to_string())


# ─────────────────────────────────────────────────────────────
# CELL 10 — Clean and merge
# ─────────────────────────────────────────────────────────────
print("=" * 55)
print("CLEANING AND MERGING")
print("=" * 55)

# Step 1 — Remove null text/summary
before = len(df)
df = df.dropna(subset=["Text", "Summary"])
print(f"Rows after dropping null text  : {len(df):,} (removed {before-len(df):,})")

# Step 2 — Remove very short reviews (< 10 chars — likely garbage)
before = len(df)
df = df[df["text_length"] >= 10]
print(f"Rows after removing short text : {len(df):,} (removed {before-len(df):,})")

# Step 3 — Remove duplicate user-product pairs (keep latest)
before = len(df)
df = df.sort_values("Time").drop_duplicates(
    subset=["UserId", "ProductId"], keep="last"
)
print(f"Rows after dedup               : {len(df):,} (removed {before-len(df):,})")

# Step 4 — Convert timestamp
df["date"] = pd.to_datetime(df["Time"], unit="s").dt.date.astype(str)

# Step 5 — Merge user features
df = df.merge(
    user_features[[
        "UserId", "review_count", "avg_rating_given",
        "std_rating_given", "pct_5star", "pct_1star",
        "pct_positive", "preferred_rating",
        "avg_text_length", "avg_helpfulness", "segment"
    ]],
    on="UserId", how="left"
)

print(f"After merge shape              : {df.shape}")
print()
print("Null check after merge:")
key_cols = ["UserId","ProductId","Score","Text","Summary",
            "review_count","avg_rating_given","segment"]
for col in key_cols:
    nulls = df[col].isna().sum()
    status = "✅" if nulls == 0 else f"⚠️  {nulls} nulls"
    print(f"  {col:<25} {status}")


# ─────────────────────────────────────────────────────────────
# CELL 11 — Build friendly user IDs
# ─────────────────────────────────────────────────────────────
print("=" * 55)
print("BUILDING FRIENDLY USER IDs")
print("=" * 55)

# Map all unique users to user_0001 format
all_user_ids = df["UserId"].unique()
uid_map = {uid: f"user_{i+1:05d}" for i, uid in enumerate(sorted(all_user_ids))}
df["user_id"] = df["UserId"].map(uid_map)

# Same for products
all_product_ids = df["ProductId"].unique()
pid_map = {pid: f"prod_{i+1:05d}" for i, pid in enumerate(sorted(all_product_ids))}
df["product_id"] = df["ProductId"].map(pid_map)

print(f"Total users mapped     : {len(uid_map):,}")
print(f"Total products mapped  : {len(pid_map):,}")
print()
print("Sample user ID mapping:")
for orig, friendly in list(uid_map.items())[:5]:
    print(f"  {orig}  →  {friendly}")
print()
print("Sample product ID mapping:")
for orig, friendly in list(pid_map.items())[:5]:
    print(f"  {orig}  →  {friendly}")


# ─────────────────────────────────────────────────────────────
# CELL 12 — Build final clean dataset
# ─────────────────────────────────────────────────────────────
print("=" * 55)
print("BUILDING FINAL DATASET")
print("=" * 55)

final = df[[
    "user_id",
    "product_id",
    "Score",
    "Text",
    "Summary",
    "date",
    "helpfulness_ratio",
    "review_count",
    "avg_rating_given",
    "std_rating_given",
    "pct_5star",
    "pct_1star",
    "pct_positive",
    "preferred_rating",
    "avg_helpfulness",
    "segment",
]].rename(columns={
    "Score":   "rating",
    "Text":    "review_text",
    "Summary": "review_summary",
})

# Clean text fields
final["review_text"]    = final["review_text"].str.strip()
final["review_summary"] = final["review_summary"].str.strip()

# Ensure types
final["rating"]       = final["rating"].astype(int)
final["review_count"] = final["review_count"].astype(int)

print("Final dataset shape    :", final.shape)
print("Columns                :", final.columns.tolist())
print()
print("Segment distribution:")
seg_dist = final.drop_duplicates("user_id")["segment"].value_counts()
print(seg_dist)
print()
print("Sample rows (one per segment):")
for seg in ["cold","lukewarm","warm"]:
    row = final[final["segment"] == seg].iloc[0]
    print(f"\n  [{seg.upper()}]")
    print(f"  user_id        : {row['user_id']}")
    print(f"  product_id     : {row['product_id']}")
    print(f"  rating         : {row['rating']}★")
    print(f"  avg_given      : {row['avg_rating_given']}")
    print(f"  review_count   : {row['review_count']}")
    print(f"  review_summary : {row['review_summary']}")
    print(f"  review_text    : {str(row['review_text'])[:150]}...")


# ─────────────────────────────────────────────────────────────
# CELL 13 — Validation checks
# ─────────────────────────────────────────────────────────────
print("=" * 55)
print("VALIDATION CHECKS")
print("=" * 55)

checks = {
    "No null user_ids":            final["user_id"].isna().sum() == 0,
    "No null product_ids":         final["product_id"].isna().sum() == 0,
    "No null ratings":             final["rating"].isna().sum() == 0,
    "No null review_text":         final["review_text"].isna().sum() == 0,
    "No null review_summary":      final["review_summary"].isna().sum() == 0,
    "No null segment":             final["segment"].isna().sum() == 0,
    "Valid ratings 1-5":           final["rating"].between(1, 5).all(),
    "Valid segments only":         final["segment"].isin(["cold","lukewarm","warm"]).all(),
    "No null avg_rating_given":    final["avg_rating_given"].isna().sum() == 0,
    "Cold users have 1-2 reviews": final[final["segment"]=="cold"]["review_count"].max() <= 2,
    "Warm users have 5+ reviews":  final[final["segment"]=="warm"]["review_count"].min() >= 5,
    "No duplicate user-product":   final.duplicated(["user_id","product_id"]).sum() == 0,
}

all_passed = True
for check, result in checks.items():
    status = "✅" if result else "❌"
    if not result:
        all_passed = False
    print(f"  {status} {check}")

print()
if all_passed:
    print("🎉 ALL CHECKS PASSED — dataset is ready")
else:
    print("⚠️  Fix failing checks before saving")

print()
print("=" * 55)
print("FINAL SUMMARY")
print("=" * 55)
print(f"Total rows             : {len(final):,}")
print(f"Unique users           : {final['user_id'].nunique():,}")
print(f"Unique products        : {final['product_id'].nunique():,}")
print(f"Date range             : {final['date'].min()} → {final['date'].max()}")
print(f"Avg reviews per user   : {len(final)/final['user_id'].nunique():.1f}")
print()
print("Segment breakdown (users):")
u_seg = final.drop_duplicates("user_id")["segment"].value_counts()
for seg, count in u_seg.items():
    print(f"  {seg:<10}: {count:>6,} users")
print()
print("Rating distribution:")
for r, count in final["rating"].value_counts().sort_index().items():
    bar = "█" * int(count / len(final) * 40)
    print(f"  {r}★  {count:>7,}  {bar}")


# ─────────────────────────────────────────────────────────────
# CELL 14 — Save
# ─────────────────────────────────────────────────────────────
output_path = "/kaggle/working/behavioriq_food_reviews.csv"
final.to_csv(output_path, index=False)

import os
size_mb = os.path.getsize(output_path) / (1024 * 1024)

print("=" * 55)
print("SAVED")
print("=" * 55)
print(f"File     : {output_path}")
print(f"Size     : {size_mb:.1f} MB")
print(f"Rows     : {len(final):,}")
print(f"Columns  : {final.columns.tolist()}")
print()
print("Download from Kaggle Output panel")
print("Place in: data/behavioriq_food_reviews.csv")