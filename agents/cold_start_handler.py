"""
TASK B: Cold-Start Handler for New Users

Handles recommendation scenarios:
1. New users (0 reviews) → Return most popular products
2. Cold users (1-4 reviews) → Category-based inference
3. Warm users (5+ reviews) → Standard recommender

Implements hybrid strategy to maximize NDCG@10 score.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Load enriched product metadata
data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
try:
    PRODUCTS_META = pd.read_csv(os.path.join(data_dir, "products_metadata.csv"))
    PRODUCT_MAP = dict(zip(PRODUCTS_META["product_id"], 
                           zip(PRODUCTS_META["product_name"], 
                               PRODUCTS_META["category"])))
except FileNotFoundError:
    PRODUCTS_META = None
    PRODUCT_MAP = {}
    print("⚠️  Warning: products_metadata.csv not found. Using fallback product names.")


def get_product_info(product_id: str) -> tuple:
    """Get enriched product name and category from metadata."""
    if product_id in PRODUCT_MAP:
        return PRODUCT_MAP[product_id]
    return (f"Food Product {product_id}", "General Food & Grocery")


class ColdStartHandler:
    """Recommend products for users with limited history."""
    
    def __init__(self, products_df: Optional[pd.DataFrame] = None):
        """
        Initialize with product metadata.
        
        Args:
            products_df: DataFrame with columns:
                - product_id, product_name, category, avg_rating, review_count
        """
        self.products_df = products_df
        self.global_popularity = None
        self.category_stats = None
    
    def compute_popularity(self, interactions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute global popularity for each product.
        
        Args:
            interactions_df: Columns: user_id, product_id, rating
        
        Returns:
            DataFrame with product_id and popularity score
        """
        popularity = interactions_df.groupby("product_id").agg(
            review_count=("product_id", "count"),
            avg_rating=("rating", "mean"),
        ).reset_index()
        
        # Normalize to 0-1 score
        max_reviews = popularity["review_count"].max()
        popularity["popularity_score"] = (
            0.7 * (popularity["review_count"] / max_reviews) +  # 70% volume
            0.3 * (popularity["avg_rating"] / 5.0)  # 30% quality
        )
        
        self.global_popularity = popularity
        return popularity
    
    def recommend_new_user(
        self,
        products_df: pd.DataFrame,
        n_recommendations: int = 10,
    ) -> List[Dict]:
        """
        Recommend for brand-new user (0 reviews).
        
        Strategy: Most popular products overall.
        
        Returns:
            List of {product_id, product_name, reason, rank_score}
        """
        if self.global_popularity is None:
            raise ValueError("Call compute_popularity() first")
        
        top_products = self.global_popularity.nlargest(n_recommendations, "popularity_score")
        
        recommendations = []
        for idx, (_, row) in enumerate(top_products.iterrows(), 1):
            product_id = row["product_id"]
            product_name, category = get_product_info(product_id)
            
            recommendations.append({
                "product_id": product_id,
                "product_name": product_name,
                "category": category,
                "rank": idx,
                "score": float(row["popularity_score"]),
                "reason": "Most popular among all users",
                "avg_rating": float(row["avg_rating"]),
                "review_count": int(row["review_count"]),
            })
        
        return recommendations
    
    def infer_categories_from_history(
        self,
        user_reviews: List[Dict],
        products_df: pd.DataFrame,
    ) -> Dict[str, float]:
        """
        Infer user's category preferences from limited review history.
        
        Args:
            user_reviews: List of {product_id, rating}
            products_df: Product metadata
        
        Returns:
            Dict mapping category → preference_score (0-1)
        """
        if not user_reviews:
            return {}
        
        category_scores = {}
        
        for review in user_reviews:
            prod_id = review.get("product_id")
            rating = review.get("rating", 3)
            
            # Get product's category from enriched metadata
            _, category = get_product_info(prod_id)
            
            # Weight by rating (5-stars = 1.0, 1-star = 0.2)
            weight = (rating - 1) / 4.0  # Normalize to 0-1
            
            category_scores[category] = category_scores.get(category, 0) + weight
        
        # Normalize to 0-1
        if category_scores:
            max_score = max(category_scores.values())
            if max_score > 0:
                category_scores = {k: v / max_score for k, v in category_scores.items()}
        
        return category_scores
    
    def recommend_cold_user(
        self,
        user_reviews: List[Dict],
        products_df: pd.DataFrame,
        n_recommendations: int = 10,
        exclude_seen: bool = True,
    ) -> List[Dict]:
        """
        Recommend for cold-start user (1-4 reviews).
        
        Strategy:
        1. Infer preferred categories from review history
        2. Recommend top products in those categories
        3. Mix with global popular products for exploration
        
        Returns:
            List of {product_id, product_name, reason, rank_score}
        """
        if self.global_popularity is None:
            raise ValueError("Call compute_popularity() first")
        
        # Infer category preferences
        category_prefs = self.infer_categories_from_history(user_reviews, products_df)
        
        # Get products already seen
        seen_products = {r.get("product_id") for r in user_reviews}
        
        # Score all products
        product_scores = []
        
        # Use enriched product metadata
        products_to_score = PRODUCTS_META if PRODUCTS_META is not None else products_df
        
        for _, prod in products_to_score.iterrows():
            prod_id = prod["product_id"]
            
            # Skip if already reviewed
            if exclude_seen and prod_id in seen_products:
                continue
            
            # Get global popularity
            pop = self.global_popularity[self.global_popularity["product_id"] == prod_id]
            if pop.empty:
                continue
            
            pop_score = pop.iloc[0]["popularity_score"]
            
            # Get enriched product info
            product_name, category = get_product_info(prod_id)
            
            # Add category preference boost
            category_boost = category_prefs.get(category, 0.3)  # Default 0.3 if unknown
            
            # Composite score: 50% popularity + 50% category match
            final_score = 0.5 * pop_score + 0.5 * category_boost
            
            product_scores.append({
                "product_id": prod_id,
                "product_name": product_name,
                "category": category,
                "score": final_score,
                "popularity": pop_score,
                "category_match": category_boost,
            })
        
        # Sort by score and take top N
        product_scores.sort(key=lambda x: x["score"], reverse=True)
        top_products = product_scores[:n_recommendations]
        
        # Determine reason based on category match
        recommendations = []
        for idx, prod in enumerate(top_products, 1):
            if prod["category_match"] > 0.6:
                reason = f"Popular in {prod['category']}"
            elif prod["popularity"] > 0.7:
                reason = "Trending among all users"
            else:
                reason = "Recommended based on your taste"
            
            recommendations.append({
                "product_id": prod["product_id"],
                "product_name": prod["product_name"],
                "category": prod["category"],
                "rank": idx,
                "score": float(prod["score"]),
                "reason": reason,
                "category_match_score": float(prod["category_match"]),
            })
        
        return recommendations
    
    def recommend(
        self,
        user_reviews: List[Dict],
        products_df: pd.DataFrame,
        n_recommendations: int = 10,
    ) -> Dict:
        """
        Unified recommendation endpoint.
        
        Automatically selects strategy based on review count.
        
        Returns:
            {
                "strategy": "new_user" | "cold_user" | "warm_user",
                "recommendations": List[Dict],
                "explanation": str,
            }
        """
        if self.global_popularity is None:
            raise ValueError("Call compute_popularity() first")
        
        review_count = len(user_reviews)
        
        if review_count == 0:
            return {
                "strategy": "new_user",
                "review_count": 0,
                "recommendations": self.recommend_new_user(products_df, n_recommendations),
                "explanation": "New user: recommending most popular products",
            }
        
        elif review_count <= 4:
            return {
                "strategy": "cold_user",
                "review_count": review_count,
                "recommendations": self.recommend_cold_user(
                    user_reviews, products_df, n_recommendations
                ),
                "explanation": f"Cold-start user ({review_count} reviews): using category inference",
            }
        
        else:
            return {
                "strategy": "warm_user",
                "review_count": review_count,
                "recommendations": [],  # Will be handled by main recommender
                "explanation": "Warm user: use standard collaborative filtering",
            }


def demo():
    """Demo: Show cold-start recommendations."""
    
    # Sample product data
    products_data = {
        "product_id": [f"prod_{i:05d}" for i in range(1, 11)],
        "product_name": [
            "Indomie Noodles",
            "Maggi Cubes",
            "Milo Drink Mix",
            "Nido Milk",
            "Bournvita",
            "Colgate Toothpaste",
            "Lipton Tea Bags",
            "Rice (10kg)",
            "Beans (1kg)",
            "Vegetable Oil",
        ],
        "category": [
            "Grains & Staples",
            "Spices & Seasonings",
            "Beverages & Drinks",
            "Beverages & Drinks",
            "Beverages & Drinks",
            "Personal Care",
            "Beverages & Drinks",
            "Grains & Staples",
            "Grains & Staples",
            "Oils & Condiments",
        ],
    }
    
    products_df = pd.DataFrame(products_data)
    
    # Sample interactions
    interactions = pd.DataFrame({
        "user_id": ["user_001"] * 5 + ["user_002"] * 3 + ["user_003"] * 8,
        "product_id": [
            "prod_00001", "prod_00002", "prod_00003", "prod_00004", "prod_00005",
            "prod_00001", "prod_00002", "prod_00007",
            "prod_00003", "prod_00004", "prod_00005", "prod_00006", "prod_00007",
            "prod_00008", "prod_00009", "prod_00010"
        ],
        "rating": [5, 4, 5, 3, 4, 5, 5, 4, 5, 4, 5, 3, 4, 4, 5, 5],
    })
    
    handler = ColdStartHandler()
    handler.compute_popularity(interactions)
    
    print("\n" + "="*70)
    print("COLD-START HANDLER DEMO")
    print("="*70)
    
    # Test scenarios
    scenarios = [
        {
            "name": "New User (0 reviews)",
            "reviews": [],
        },
        {
            "name": "Cold User (2 reviews)",
            "reviews": [
                {"product_id": "prod_00001", "rating": 5},
                {"product_id": "prod_00002", "rating": 4},
            ],
        },
        {
            "name": "Warm User (6 reviews)",
            "reviews": [
                {"product_id": "prod_00001", "rating": 5},
                {"product_id": "prod_00002", "rating": 5},
                {"product_id": "prod_00003", "rating": 4},
                {"product_id": "prod_00004", "rating": 5},
                {"product_id": "prod_00007", "rating": 4},
                {"product_id": "prod_00008", "rating": 5},
            ],
        },
    ]
    
    for scenario in scenarios:
        print(f"\n{'-'*70}")
        print(f"Scenario: {scenario['name']}")
        print(f"{'-'*70}")
        
        result = handler.recommend(scenario["reviews"], products_df, n_recommendations=5)
        print(f"Strategy: {result['strategy']}")
        print(f"Explanation: {result['explanation']}")
        
        if result["recommendations"]:
            print(f"\nTop {len(result['recommendations'])} recommendations:")
            for rec in result["recommendations"]:
                print(f"  {rec['rank']}. {rec['product_name']} ({rec['category']})")
                print(f"     Score: {rec['score']:.3f}, Reason: {rec['reason']}")


if __name__ == "__main__":
    demo()
