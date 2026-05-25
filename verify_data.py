#!/usr/bin/env python
# Quick data verification script
# Run with: python verify_data.py

import pandas as pd
import os
import sys

print("=" * 70)
print("FOOD REVIEWS DATA VERIFICATION")
print("=" * 70)

# Check which files exist
data_dir = "data"
print(f"\nChecking files in {data_dir}/ directory:")
print("-" * 70)

csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
for f in sorted(csv_files):
    path = os.path.join(data_dir, f)
    size_mb = os.path.getsize(path) / (1024 ** 2)
    print(f"  ✅ {f:<50} {size_mb:>8.1f} MB")

# Try to load food_reviews.csv
print("\n" + "=" * 70)
print("ATTEMPTING TO LOAD food_reviews.csv")
print("=" * 70)

food_file = os.path.join(data_dir, "food_reviews.csv")

if os.path.exists(food_file):
    print(f"✅ File found: {food_file}")
    try:
        df = pd.read_csv(food_file, nrows=5)  # Load first 5 rows to check
        print(f"\n✅ FILE LOADED SUCCESSFULLY")
        print(f"\n   Shape (first check): {df.shape}")
        print(f"   Columns: {df.columns.tolist()}")
        print(f"\n   Data types:")
        for col, dtype in df.dtypes.items():
            print(f"     {col:<30} {dtype}")
        print(f"\n   First row:")
        print(df.iloc[0].to_string())
        print(f"\n🎉 DATA IS READY TO USE")
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        sys.exit(1)
else:
    print(f"❌ File NOT found: {food_file}")
    print(f"\n   Searched in: {os.path.abspath(data_dir)}")
    print(f"\n   Available CSV files:")
    for f in csv_files:
        print(f"     - {f}")
    print(f"\n   Action needed: Download food_reviews.csv from Kaggle and save to data/")
    sys.exit(1)
