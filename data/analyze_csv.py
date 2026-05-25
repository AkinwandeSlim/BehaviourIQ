import pandas as pd

df = pd.read_csv('behavioriq_user_events_v2.csv')

print('=== DATASET OVERVIEW ===')
print(f'Shape: {df.shape}')
print(f'\n=== COLUMN DETAILS ===')
for col in df.columns:
    print(f'{col}: {df[col].dtype}, unique: {df[col].nunique()}, nulls: {df[col].isnull().sum()}')

print(f'\n=== ACTION DISTRIBUTION ===')
print(df['action'].value_counts())

print(f'\n=== USER STATS ===')
print(f'Unique users: {df["user_id"].nunique()}')
print(f'Events per user: min={df.groupby("user_id").size().min()}, max={df.groupby("user_id").size().max()}, median={df.groupby("user_id").size().median()}')

print(f'\n=== CATEGORY STATS ===')
print(f'Unique categories: {df["categoryid"].nunique()}')
print(f'Top 10 categories:')
print(df['categoryid'].value_counts().head(10))

print(f'\n=== ITEM STATS ===')
print(f'Unique items: {df["itemid"].nunique()}')

print(f'\n=== TEMPORAL STATS ===')
df['timestamp'] = pd.to_datetime(df['timestamp'])
print(f'Date range: {df["timestamp"].min()} to {df["timestamp"].max()}')
print(f'Days spanned: {(df["timestamp"].max() - df["timestamp"].min()).days}')

print(f'\n=== SAMPLE ROWS ===')
print(df.head(5))
