#!/usr/bin/env python
"""
Product Enrichment Script - IMPROVED VERSION

Instead of using review summaries as product names (which are user comments),
infer actual product TYPES from review text and create realistic product names.

Reads: data/food_reviews.csv + data/food_reviews.csv
Outputs: data/products_metadata.csv with realistic product names & Nigerian categories
"""

import pandas as pd
import re


def infer_product_type(review_text: str, review_summary: str) -> str:
    """
    Infer actual product type from review content.
    Extract keywords that indicate what the product actually is.
    """
    combined = (str(review_text) + " " + str(review_summary)).lower()
    
    # Product type patterns (more specific keywords first)
    product_types = {
        "Dog Food": ["dog food", "dog treats", "kibble", "canine", "puppy food", "labrador", "german shepherd"],
        "Cat Food": ["cat food", "feline", "kitty", "cat treat", "kitten"],
        "Pet Treats": ["dog treat", "cat treat", "pet chew", "dental chew", "rawhide"],
        
        "Noodles": ["noodle", "ramen", "indomie", "pasta", "spaghetti"],
        "Rice": ["rice", "basmati", "jasmine", "grain"],
        "Beans": ["bean", "lentil", "chickpea", "legume"],
        "Flour": ["flour", "wheat flour", "cornmeal", "grain flour"],
        
        "Seasoning": ["seasoning", "maggi", "bouillon", "spice mix", "flavoring", "curry"],
        "Salt": ["salt", "sea salt", "himalayan"],
        "Oil": ["oil", "coconut oil", "olive oil", "vegetable oil"],
        
        "Tea": ["tea", "black tea", "green tea", "herbal tea"],
        "Coffee": ["coffee", "espresso", "ground coffee"],
        "Milk Powder": ["milk powder", "nido", "milo", "cocoa mix"],
        "Juice": ["juice", "drink", "beverage"],
        
        "Chocolate": ["chocolate", "cocoa", "candy bar"],
        "Cookies": ["cookie", "biscuit", "wafer", "cracker"],
        "Snacks": ["chip", "crisp", "snack", "popcorn"],
        "Candy": ["candy", "lollipop", "sweet"],
        
        "Peanuts": ["peanut", "groundnut", "nut butter"],
        "Cereal": ["cereal", "grain", "oatmeal"],
    }
    
    for product_type, keywords in product_types.items():
        for keyword in keywords:
            if keyword in combined:
                return product_type
    
    return "General Food Item"


def categorize_product_nigerian(product_type: str) -> str:
    """
    Map product type to Nigerian-relevant food categories.
    """
    nigerian_categories = {
        "Beverages & Drinks": ["Tea", "Coffee", "Milk Powder", "Juice"],
        "Pet Food & Supplies": ["Dog Food", "Cat Food", "Pet Treats"],
        "Grains & Staples": ["Noodles", "Rice", "Beans", "Flour", "Cereal"],
        "Spices & Seasonings": ["Seasoning", "Salt"],
        "Oils & Condiments": ["Oil"],
        "Snacks & Confectionery": ["Chocolate", "Cookies", "Snacks", "Candy", "Peanuts"],
    }
    
    for category, product_types in nigerian_categories.items():
        if product_type in product_types:
            return category
    
    return "General Food & Grocery"


def generate_product_name(product_type: str, popularity_rank: int) -> str:
    """
    Generate realistic product name based on type and popularity.
    """
    examples = {
        "Dog Food": ["Premium Dog Bites", "Canine Care Mix", "Pup Nutrition Plus", "Pet Joy Kibble"],
        "Cat Food": ["Feline Feast", "Kitty Delights", "Cat Care Nutrition", "Meow Mix"],
        "Pet Treats": ["Pet Snacks Plus", "Treat Time Bites", "Happy Pet Chews", "Pet Smile Treats"],
        
        "Noodles": ["Quick Noodle Pack", "Flavor Noodles", "Instant Pasta Mix", "Speed Noodles"],
        "Rice": ["Quality Rice Pack", "Pure White Rice", "Long Grain Premium", "Rice Staple"],
        "Beans": ["Dried Bean Mix", "Legume Pack", "Bean Variety", "Protein Beans"],
        "Flour": ["All Purpose Flour", "Premium Wheat Flour", "Baking Flour Mix", "Flour Blend"],
        
        "Seasoning": ["Magic Seasoning", "Flavor Cubes", "Taste Enhancer", "Seasoning Mix"],
        "Salt": ["Pure Sea Salt", "Table Salt Plus", "Iodized Salt", "Fine Salt"],
        "Oil": ["Cooking Oil Premium", "Pure Vegetable Oil", "Cooking Blend", "Oil Choice"],
        
        "Tea": ["Black Tea Leaves", "Tea Blend Mix", "Premium Tea", "Tea Variety"],
        "Coffee": ["Ground Coffee", "Coffee Beans", "Instant Coffee", "Premium Coffee"],
        "Milk Powder": ["Milk Nutrition", "Powder Milk Plus", "Creamer Mix", "Milk Blend"],
        "Juice": ["Juice Concentrate", "Fruit Juice Mix", "Juice Drink", "Juice Blend"],
        
        "Chocolate": ["Chocolate Bar", "Cocoa Treat", "Chocolate Blend", "Sweet Chocolate"],
        "Cookies": ["Cookie Pack", "Biscuit Mix", "Wafer Cookie", "Crispy Cookies"],
        "Snacks": ["Snack Pack", "Crispy Snacks", "Snack Mix", "Savory Snacks"],
        "Candy": ["Sweet Candy", "Candy Mix", "Lollipop Pack", "Treat Sweet"],
        "Peanuts": ["Roasted Peanuts", "Peanut Butter", "Nut Snack", "Peanut Mix"],
        "Cereal": ["Cereal Mix", "Grain Cereal", "Morning Cereal", "Oat Cereal"],
    }
    
    if product_type in examples:
        base_names = examples[product_type]
        # Cycle through names based on rank
        name = base_names[popularity_rank % len(base_names)]
        # Add rank for uniqueness
        return f"{name} #{(popularity_rank // len(base_names)) + 1}" if popularity_rank >= len(base_names) else name
    
    return f"Food Product #{popularity_rank + 1}"


print("=" * 70)
print("PRODUCT ENRICHMENT - IMPROVED VERSION")
print("=" * 70)

# Load food reviews
csv_path = "data/food_reviews.csv"
print(f"\nLoading {csv_path}...")

df = pd.read_csv(csv_path)
print(f"Loaded {len(df):,} reviews")

# Extract product metadata with better product type inference
print(f"\nAnalyzing review content to infer product types...")

products_list = []

for product_id in df["product_id"].unique():
    product_reviews = df[df["product_id"] == product_id]
    
    # Infer product type from all reviews for this product
    product_type = infer_product_type(
        " ".join(product_reviews["review_text"].head(5).astype(str)),
        " ".join(product_reviews["review_summary"].head(5).astype(str))
    )
    
    category = categorize_product_nigerian(product_type)
    
    products_list.append({
        "product_id": product_id,
        "product_type": product_type,
        "category": category,
        "review_count": len(product_reviews),
        "avg_rating": product_reviews["rating"].mean(),
        "pct_5star": (product_reviews["rating"] == 5).mean(),
    })

products = pd.DataFrame(products_list)

# Sort by review count to assign popularity rank
products = products.sort_values("review_count", ascending=False).reset_index(drop=True)

# Generate realistic product names
products["product_name"] = products.apply(
    lambda row: generate_product_name(row["product_type"], row.name),
    axis=1
)

# Round ratings
products["avg_rating"] = products["avg_rating"].round(2)
products["pct_5star"] = products["pct_5star"].round(2)

print(f"✅ Extracted metadata for {len(products):,} products")

# Save metadata
output_path = "data/products_metadata.csv"
products.to_csv(output_path, index=False)
print(f"✅ Saved to {output_path}")

print("\n" + "=" * 70)
print("SAMPLE PRODUCTS (Top 15 by review count)")
print("=" * 70)

for idx, row in products.head(15).iterrows():
    print(f"\n  #{idx+1}: {row['product_id']}")
    print(f"     Name: {row['product_name']}")
    print(f"     Type: {row['product_type']}")
    print(f"     Category: {row['category']}")
    print(f"     Reviews: {row['review_count']:,}, Avg: {row['avg_rating']}★")

print("\n" + "=" * 70)
print("CATEGORY DISTRIBUTION")
print("=" * 70)

category_stats = products.groupby("category").agg({
    "product_id": "count",
    "review_count": "sum",
    "avg_rating": "mean"
}).round(2)

category_stats.columns = ["Product Count", "Total Reviews", "Avg Rating"]
print(category_stats)

print("\n🎉 ENRICHMENT COMPLETE")
print("\nProducts now have REALISTIC product names based on content analysis!")

