# BehaviorIQ — RetailRocket Data Prep & EDA
# Run this entire notebook on Kaggle with the RetailRocket dataset attached.
# Output: behavioriq_user_events.csv — drop-in replacement for your simulate.py data.

# ─────────────────────────────────────────────
# CELL 1 — Imports
# ─────────────────────────────────────────────
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

print("✅ Imports done")

# ─────────────────────────────────────────────
# CELL 2 — Load raw RetailRocket files
# ─────────────────────────────────────────────
# These paths work automatically on Kaggle when RetailRocket dataset is attached
events_df       = pd.read_csv("/kaggle/input/retailrocket/events.csv")
item_props_1    = pd.read_csv("/kaggle/input/retailrocket/item_properties_part1.csv")
item_props_2    = pd.read_csv("/kaggle/input/retailrocket/item_properties_part2.csv")
category_tree   = pd.read_csv("/kaggle/input/retailrocket/category_tree.csv")

print(f"Events shape:         {events_df.shape}")
print(f"Item props 1 shape:   {item_props_1.shape}")
print(f"Item props 2 shape:   {item_props_2.shape}")
print(f"Category tree shape:  {category_tree.shape}")
print()
print("Events columns:", events_df.columns.tolist())
print("Events sample:")
print(events_df.head())

# ─────────────────────────────────────────────
# CELL 3 — EDA: Understand the raw data
# ─────────────────────────────────────────────
print("=" * 50)
print("EVENT TYPE DISTRIBUTION")
print("=" * 50)
print(events_df["event"].value_counts())
print()

print("=" * 50)
print("BASIC STATS")
print("=" * 50)
print(f"Total events:        {len(events_df):,}")
print(f"Unique visitors:     {events_df['visitorid'].nunique():,}")
print(f"Unique items:        {events_df['itemid'].nunique():,}")
print(f"Date range:          {pd.to_datetime(events_df['timestamp'], unit='ms').min()} "
      f"→ {pd.to_datetime(events_df['timestamp'], unit='ms').max()}")

# ─────────────────────────────────────────────
# CELL 4 — EDA: Visualise event distribution
# ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 4))

# Plot 1: Event type counts
event_counts = events_df["event"].value_counts()
axes[0].bar(event_counts.index, event_counts.values, color=["#3B8BD4", "#1D9E75", "#D85A30"])
axes[0].set_title("Event Type Distribution")
axes[0].set_ylabel("Count")
for i, v in enumerate(event_counts.values):
    axes[0].text(i, v + 1000, f"{v:,}", ha="center", fontsize=9)

# Plot 2: Events per user (log scale)
user_event_counts = events_df.groupby("visitorid").size()
axes[1].hist(user_event_counts, bins=50, color="#AFA9EC", edgecolor="white")
axes[1].set_title("Events per User (log scale)")
axes[1].set_xlabel("Number of events")
axes[1].set_yscale("log")

# Plot 3: Events over time
events_df["date"] = pd.to_datetime(events_df["timestamp"], unit="ms").dt.date
daily = events_df.groupby("date").size()
axes[2].plot(daily.index, daily.values, color="#1D9E75", linewidth=1.5)
axes[2].set_title("Daily Event Volume")
axes[2].tick_params(axis="x", rotation=45)

plt.tight_layout()
plt.savefig("eda_overview.png", dpi=120, bbox_inches="tight")
plt.show()
print("✅ EDA overview saved")

# ─────────────────────────────────────────────
# CELL 5 — Build item → category mapping
# ─────────────────────────────────────────────
# Combine item properties
item_props = pd.concat([item_props_1, item_props_2], ignore_index=True)

# Extract category property for each item (most recent value)
cat_props = item_props[item_props["property"] == "categoryid"].copy()
cat_props = cat_props.sort_values("timestamp").drop_duplicates("itemid", keep="last")
item_to_cat = dict(zip(cat_props["itemid"], cat_props["value"].astype(str)))

print(f"Items with category mapping: {len(item_to_cat):,}")
print(f"Unique categories:           {len(set(item_to_cat.values())):,}")

# ─────────────────────────────────────────────
# CELL 6 — Map categories to human-readable names
# ─────────────────────────────────────────────
# RetailRocket categories are numeric IDs — we'll map them semantically
# using category_tree.csv hierarchy where available, otherwise by frequency

print("Category tree structure:")
print(category_tree.head(20))
print(f"\nTotal categories in tree: {len(category_tree)}")

# Find most common category IDs
events_df["categoryid"] = events_df["itemid"].map(item_to_cat)
top_cats = events_df["categoryid"].value_counts().head(30).index.tolist()

print("\nTop 20 category IDs by event volume:")
print(events_df["categoryid"].value_counts().head(20))

# Build semantic mapping using category tree where possible
# If category_tree has parent-child structure, use it for intelligent mapping
BEHAVIORIQ_CATEGORIES = ["tech", "fashion", "food", "fitness", "travel", "finance"]

# Check if category_tree has meaningful structure
if "categoryid" in category_tree.columns and "parentid" in category_tree.columns:
    # Use category tree for semantic mapping
    # Group categories by their parent to create clusters
    cat_to_parent = dict(zip(category_tree["categoryid"], category_tree["parentid"]))
    
    # Map parent clusters to BehaviorIQ categories based on frequency
    parent_counts = events_df["categoryid"].map(cat_to_parent).value_counts()
    top_parents = parent_counts.head(10).index.tolist()
    
    cat_name_map = {}
    for i, parent_id in enumerate(top_parents):
        # Map all children of this parent to the same BehaviorIQ category
        children = category_tree[category_tree["parentid"] == parent_id]["categoryid"].tolist()
        for child_id in children:
            cat_name_map[str(child_id)] = BEHAVIORIQ_CATEGORIES[i % len(BEHAVIORIQ_CATEGORIES)]
    
    print(f"\nSemantic mapping using {len(top_parents)} parent clusters")
else:
    # Fallback: use deterministic hash-based mapping (not round-robin)
    cat_name_map = {}
    for cat_id in top_cats:
        # Use hash for deterministic but distributed mapping
        cat_name_map[str(cat_id)] = BEHAVIORIQ_CATEGORIES[hash(str(cat_id)) % 6]
    print("\nUsing deterministic hash-based mapping")

# Fallback for unmapped categories
def map_category(cat_id):
    if pd.isna(cat_id):
        return "tech"  # default
    return cat_name_map.get(str(cat_id), BEHAVIORIQ_CATEGORIES[hash(str(cat_id)) % 6])

events_df["category"] = events_df["categoryid"].apply(map_category)

print("\nMapped category distribution:")
print(events_df["category"].value_counts())

# ─────────────────────────────────────────────
# CELL 7 — Map event types to BehaviorIQ actions
# ─────────────────────────────────────────────
# RetailRocket has: view, addtocart, transaction
# BehaviorIQ uses: view, click, search, purchase, skip, save

action_map = {
    "view":        "view",
    "addtocart":   "save",
    "transaction": "purchase"
}

events_df["action"] = events_df["event"].map(action_map).fillna("view")

print("Action distribution after mapping:")
print(events_df["action"].value_counts())

# ─────────────────────────────────────────────
# CELL 8 — Filter to active users (top 500)
# ─────────────────────────────────────────────
# Focus on users with meaningful history (at least 5 events)
user_counts = events_df.groupby("visitorid").size()
active_users = user_counts[user_counts >= 5].index

print(f"Users with 5+ events: {len(active_users):,}")

# Take top 500 most active users for demo richness
top_500_users = user_counts[user_counts >= 5].nlargest(500).index
filtered = events_df[events_df["visitorid"].isin(top_500_users)].copy()

print(f"Filtered events (top 500 users): {len(filtered):,}")

# ─────────────────────────────────────────────
# CELL 9 — EDA: Category mix for top users
# ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Category distribution for filtered users
cat_dist = filtered["category"].value_counts()
colors = ["#3B8BD4", "#1D9E75", "#D85A30", "#AFA9EC", "#FAC775", "#F0997B"]
axes[0].pie(cat_dist.values, labels=cat_dist.index, colors=colors,
            autopct="%1.1f%%", startangle=90)
axes[0].set_title("Category Distribution (Top 500 Users)")

# Action distribution
action_dist = filtered["action"].value_counts()
axes[1].bar(action_dist.index, action_dist.values, color=colors[:len(action_dist)])
axes[1].set_title("Action Distribution (Top 500 Users)")
axes[1].set_ylabel("Count")

plt.tight_layout()
plt.savefig("eda_filtered.png", dpi=120, bbox_inches="tight")
plt.show()
print("✅ Filtered EDA saved")

# ─────────────────────────────────────────────
# CELL 10 — Build dwell_seconds (simulate from event weights)
# ─────────────────────────────────────────────
# RetailRocket has no dwell time — we simulate it deterministically
# This is realistic: purchases = longer engagement, views = shorter
# Use item_id hash for deterministic values

def deterministic_dwell(action, item_id):
    """Generate deterministic dwell time based on action and item_id."""
    # Seed with item_id for consistency
    np.random.seed(hash(str(item_id)) % 10000)
    
    dwell_ranges = {
        "view":     (5, 45),
        "save":     (30, 90),
        "purchase": (60, 180),
        "click":    (5, 30),
        "search":   (10, 40),
        "skip":     (2, 10),
    }
    
    min_sec, max_sec = dwell_ranges.get(action, (5, 30))
    return np.random.randint(min_sec, max_sec)

filtered["dwell_seconds"] = filtered.apply(
    lambda row: deterministic_dwell(row["action"], row["itemid"]), axis=1
)

print("Dwell seconds stats:")
print(filtered.groupby("action")["dwell_seconds"].describe())

# ─────────────────────────────────────────────
# CELL 11 — Build item names from item_id
# ─────────────────────────────────────────────
# RetailRocket item names are not provided — generate readable names
# from category + item_id for demo purposes
# Use deterministic selection based on item_id hash

def make_item_name(row):
    category_items = {
        "tech":    ["Laptop", "Phone", "Tablet", "Headphones", "Camera", "Speaker", "Monitor", "Keyboard", "Mouse", "Router"],
        "fashion": ["Jacket", "Sneakers", "Watch", "Bag", "Sunglasses", "Dress", "Boots", "Scarf", "Belt", "Hat"],
        "food":    ["Coffee", "Blender", "Cookbook", "Meal Kit", "Spice Set", "Tea", "Juicer", "Air Fryer", "Knife Set", "Storage Container"],
        "fitness": ["Dumbbells", "Yoga Mat", "Protein Powder", "Running Shoes", "Resistance Band", "Fitness Tracker", "Jump Rope", "Kettlebell", "Foam Roller", "Gloves"],
        "travel":  ["Luggage", "Backpack", "Travel Pillow", "Adapter", "Guidebook", "Tent", "Passport Holder", "Packing Cubes", "Travel Wallet", "Neck Pillow"],
        "finance": ["Course", "Book", "Planner", "Calculator", "Subscription", "Report", "Software", "Template", "Workbook", "Consultation"],
    }
    items = category_items.get(row["category"], ["Product"])
    # Deterministic selection based on item_id
    item_idx = hash(str(row['itemid'])) % len(items)
    return f"{items[item_idx]} #{row['itemid'] % 1000:03d}"

filtered["item"] = filtered.apply(make_item_name, axis=1)

print("Sample item names:")
print(filtered[["category", "item"]].drop_duplicates().head(12))

# ─────────────────────────────────────────────
# CELL 12 — Build final clean dataset
# ─────────────────────────────────────────────
# Convert timestamp to readable datetime
filtered["timestamp"] = pd.to_datetime(filtered["timestamp"], unit="ms")

# Rename visitorid → user_id with friendly format
# Map visitor IDs to user_001, user_002, etc.
visitor_id_map = {vid: f"user_{i+1:03d}" for i, vid in enumerate(top_500_users)}
filtered["user_id"] = filtered["visitorid"].map(visitor_id_map)

# Select and order final columns (matches BehaviorIQ schema exactly)
final_df = filtered[[
    "user_id",
    "action",
    "category",
    "item",
    "timestamp",
    "dwell_seconds"
]].copy()

# Sort by user and time
final_df = final_df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)

print("=" * 50)
print("FINAL DATASET SUMMARY")
print("=" * 50)
print(f"Total events:    {len(final_df):,}")
print(f"Unique users:    {final_df['user_id'].nunique():,}")
print(f"Date range:      {final_df['timestamp'].min()} → {final_df['timestamp'].max()}")
print()
print("Events per user stats:")
print(final_df.groupby("user_id").size().describe())
print()
print("Sample rows:")
print(final_df.head(10))

# ─────────────────────────────────────────────
# CELL 13 — EDA: User behaviour heatmap
# ─────────────────────────────────────────────
# Show category × action matrix for top 20 users
top20 = final_df["user_id"].value_counts().head(20).index
sample = final_df[final_df["user_id"].isin(top20)]

pivot = sample.pivot_table(
    index="user_id", columns="category",
    values="dwell_seconds", aggfunc="mean"
).fillna(0)

plt.figure(figsize=(12, 7))
sns.heatmap(pivot, cmap="Blues", annot=True, fmt=".0f",
            linewidths=0.5, cbar_kws={"label": "Avg dwell (sec)"})
plt.title("User × Category Avg Dwell Time (Top 20 Users)")
plt.tight_layout()
plt.savefig("eda_heatmap.png", dpi=120, bbox_inches="tight")
plt.show()
print("✅ Heatmap saved")

# ─────────────────────────────────────────────
# CELL 14 — Save output CSV
# ─────────────────────────────────────────────
output_path = "/kaggle/working/behavioriq_user_events.csv"
final_df.to_csv(output_path, index=False)

print(f"✅ Saved: {output_path}")
print(f"   Rows:    {len(final_df):,}")
print(f"   Columns: {final_df.columns.tolist()}")
print()
print("Next steps:")
print("1. Download behavioriq_user_events.csv from Kaggle output panel")
print("2. Replace data/user_events.csv in your BehaviorIQ project")
print("3. Run: streamlit run app.py")
print("4. All 500 real users are now available in the sidebar!")

# ─────────────────────────────────────────────
# CELL 15 — Quick validation check
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("VALIDATION CHECKS")
print("=" * 50)

checks = {
    "No null user_ids":       final_df["user_id"].isna().sum() == 0,
    "No null actions":        final_df["action"].isna().sum() == 0,
    "No null categories":     final_df["category"].isna().sum() == 0,
    "Valid actions only":     final_df["action"].isin(
                                  ["view","click","search","purchase","skip","save"]
                              ).all(),
    "Valid categories only":  final_df["category"].isin(
                                  ["tech","fashion","food","fitness","travel","finance"]
                              ).all(),
    "Dwell > 0":              (final_df["dwell_seconds"] > 0).all(),
    "500 users":              final_df["user_id"].nunique() == 500,
}

all_passed = True
for check, result in checks.items():
    status = "✅" if result else "❌"
    print(f"  {status} {check}")
    if not result:
        all_passed = False

print()
if all_passed:
    print("🎉 All checks passed — CSV is ready for BehaviorIQ!")
else:
    print("⚠️  Some checks failed — review the output above.")
