import pandas as pd
import sys

csv_path = r'C:\MyFiles\DOCUMENT-2026\2026\May2026\behavioriq_V2\data\amazon_com-product_reviews__20200101_20200331_sample.csv'

try:
    df = pd.read_csv(csv_path)
    print(f"Shape: {df.shape}")
    print(f"\nColumns: {df.columns.tolist()}")
    print(f"\nFirst 3 rows:")
    print(df.head(3).to_string())
    print(f"\nData types:")
    print(df.dtypes)
    print(f"\nMissing values:")
    print(df.isnull().sum())
    print(f"\nSample review:")
    print(f"  Review: {df.iloc[0]['review_body'][:100] if 'review_body' in df.columns else 'N/A'}")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
