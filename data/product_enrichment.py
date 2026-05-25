#!/usr/bin/env python
"""
Utility to load and enrich product metadata for agents.
"""

import pandas as pd
import os

_products_cache = None

def load_products_metadata():
    """Load enriched products metadata from CSV."""
    global _products_cache
    
    if _products_cache is not None:
        return _products_cache
    
    products_path = os.path.join("data", "products_metadata.csv")
    
    if not os.path.exists(products_path):
        return None
    
    _products_cache = pd.read_csv(products_path)
    return _products_cache

def get_product_info(product_id: str) -> dict:
    """Get product name and category by ID."""
    products = load_products_metadata()
    
    if products is None:
        return {
            "product_id": product_id,
            "product_name": product_id,
            "category": "General Food & Grocery",
            "avg_rating": 4.0,
            "review_count": 0,
        }
    
    prod = products[products["product_id"] == product_id]
    
    if prod.empty:
        return {
            "product_id": product_id,
            "product_name": product_id,
            "category": "General Food & Grocery",
            "avg_rating": 4.0,
            "review_count": 0,
        }
    
    row = prod.iloc[0]
    return {
        "product_id": product_id,
        "product_name": str(row.get("product_name", product_id))[:80],
        "category": str(row.get("category", "General Food & Grocery")),
        "avg_rating": float(row.get("avg_rating", 4.0)),
        "review_count": int(row.get("review_count", 0)),
    }
