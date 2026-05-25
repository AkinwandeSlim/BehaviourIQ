import pandas as pd
from category_map import CATEGORY_NAMES, print_mapping_coverage

df = pd.read_csv('behavioriq_user_events_v2.csv')

print("=== CATEGORY MAPPING COVERAGE TEST ===")
coverage = print_mapping_coverage(df)

print(f"\nTop 10 categories in dataset:")
print(df['categoryid'].value_counts().head(10))

print(f"\nMapped vs Unmapped:")
mapped = df['categoryid'].isin(CATEGORY_NAMES.keys())
print(f"Mapped events: {mapped.sum()} ({coverage:.1f}%)")
print(f"Unmapped events: {(~mapped).sum()} ({100-coverage:.1f}%)")

print(f"\nTop unmapped categories:")
unmapped_cats = df[~mapped]['categoryid'].value_counts().head(5)
print(unmapped_cats)
