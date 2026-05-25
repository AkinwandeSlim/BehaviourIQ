# diagnostics.py
import pandas as pd
import os
from data.category_map import CATEGORY_NAMES, enrich_dataframe

from data.category_map import print_mapping_coverage, enrich_dataframe

df = pd.read_csv("C:\\MyFiles\\DOCUMENT-2026\\2026\\May2026\\behavioriq_V2\\data\\food_reviews.csv")

print(df.head(4))
# df = enrich_dataframe(df)
# print_mapping_coverage(df)

# unmapped = df[~df["categoryid"].isin(CATEGORY_NAMES.keys())]
# print("\nRemaining top unmapped:")
# print(unmapped["categoryid"].value_counts().head(15))






# import pandas as pd
# import os
# try:
#     tree_path = os.path.join(os.path.dirname(__file__), 'data', 'category_tree.csv')
#     print(tree_path)
#     if not os.path.exists(tree_path):
#         tree_path = os.path.join(os.path.dirname(__file__), 'category_tree.csv')
#     df_tree = pd.read_csv(tree_path)
#     df_tree['categoryid'] = pd.to_numeric(df_tree['categoryid'], errors='coerce').astype('Int64')
#     df_tree['parentid'] = pd.to_numeric(df_tree['parentid'], errors='coerce').astype('Int64')
#     print( df_tree.set_index('categoryid')['parentid'].head(to_dict())
# except Exception as e:
#     print(f"Warning: Could not load category_tree.csv: {e}")