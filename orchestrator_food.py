"""
Orchestrator: Chains Task A (Review Generator) and Task B (Recommender)

Loads food_reviews.csv data and coordinates between agents.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from agents.predictor_food import ReviewPredictor
from agents.cold_start_handler import ColdStartHandler


class BehaviorIQFoodOrchestrator:
    """Orchestrates Task A and Task B agents for food reviews."""
    
    def __init__(self, data_path: str = "data/food_reviews.csv"):
        """
        Initialize orchestrator with data.
        
        Args:
            data_path: Path to food_reviews.csv
        """
        self.data_path = data_path
        self.data = None
        self.predictor = ReviewPredictor()
        self.recommender = ColdStartHandler()
        
        # Statistics caches
        self.products_cache = None
        self.user_segments = None
        
        self._load_data()
    
    def _load_data(self):
        """Load and validate data."""
        if not Path(self.data_path).exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        self.data = pd.read_csv(self.data_path)
        print(f"✅ Loaded {len(self.data):,} reviews from {self.data_path}")
        
        # Build product cache
        self._build_product_cache()
        
        # Build user segments
        user_data = self.data.groupby("user_id").agg({
            "segment": "first",
            "review_count": "first",
            "avg_rating_given": "first",
        }).reset_index()
        
        self.user_segments = user_data.set_index("user_id").to_dict("index")
        print(f"✅ Indexed {len(self.user_segments):,} users")
    
    def _build_product_cache(self):
        """Build product metadata cache."""
        self.products_cache = self.data.groupby("product_id").agg({
            "rating": ["mean", "count"],
            "review_summary": "first",
        }).reset_index()
        
        self.products_cache.columns = ["product_id", "avg_rating", "review_count", "sample_summary"]
        
        # Infer category from summary (simple heuristic)
        categories = {
            "spice": "Spices & Seasonings",
            "seasoning": "Spices & Seasonings",
            "pepper": "Spices & Seasonings",
            "tea": "Beverages & Drinks",
            "coffee": "Beverages & Drinks",
            "drink": "Beverages & Drinks",
            "snack": "Snacks & Biscuits",
            "chip": "Snacks & Biscuits",
            "rice": "Grains & Staples",
            "pasta": "Grains & Staples",
            "noodle": "Grains & Staples",
            "oil": "Oils & Condiments",
            "sauce": "Oils & Condiments",
            "pet": "Pet Food & Supplies",
            "dog": "Pet Food & Supplies",
            "cat": "Pet Food & Supplies",
            "vitamin": "Health & Supplements",
            "protein": "Health & Supplements",
            "organic": "Organic & Natural",
        }
        
        def infer_category(summary: str) -> str:
            if pd.isna(summary):
                return "General Food & Grocery"
            text = str(summary).lower()
            for keyword, category in categories.items():
                if keyword in text:
                    return category
            return "General Food & Grocery"
        
        self.products_cache["category"] = self.products_cache["sample_summary"].apply(infer_category)
        self.products_cache["product_name"] = self.products_cache["sample_summary"].str[:50]
        
        print(f"✅ Indexed {len(self.products_cache):,} products")
    
    def get_user_reviews(self, user_id: str) -> List[Dict]:
        """Get review history for a user."""
        user_data = self.data[self.data["user_id"] == user_id]
        
        reviews = []
        for _, row in user_data.iterrows():
            reviews.append({
                "product_id": row["product_id"],
                "rating": int(row["rating"]),
                "review_text": row["review_text"],
                "review_summary": row["review_summary"],
                "date": row["date"],
            })
        
        return reviews
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile summary."""
        if user_id not in self.user_segments:
            return None
        
        profile = self.user_segments[user_id].copy()
        profile["user_id"] = user_id
        profile["review_count"] = int(profile["review_count"])
        profile["avg_rating_given"] = float(profile["avg_rating_given"])
        
        return profile
    
    def task_a_generate_review(
        self,
        user_id: str,
        product_id: str,
    ) -> Dict:
        """
        TASK A: Generate predicted review for user-product pair.
        
        Args:
            user_id: User identifier
            product_id: Product identifier
        
        Returns:
            {
                "status": "success|error",
                "rating": int 1-5,
                "review_text": str,
                "review_summary": str,
                "confidence": float,
                "user_profile": Dict,
                "product_info": Dict,
                "error": str (if failed),
            }
        """
        try:
            # Get user reviews
            user_reviews = self.get_user_reviews(user_id)
            
            if not user_reviews:
                return {
                    "status": "error",
                    "error": f"User {user_id} not found in dataset",
                }
            
            # Get product info
            product = self.products_cache[self.products_cache["product_id"] == product_id]
            if product.empty:
                return {
                    "status": "error",
                    "error": f"Product {product_id} not found in dataset",
                }
            
            product_info = {
                "product_id": product_id,
                "product_name": product.iloc[0]["product_name"],
                "category": product.iloc[0]["category"],
                "avg_rating": float(product.iloc[0]["avg_rating"]),
                "review_count": int(product.iloc[0]["review_count"]),
            }
            
            # Build user profile
            user_profile = self.predictor.build_user_profile(user_reviews)
            
            # Generate review
            generated = self.predictor.generate_review(
                user_profile=user_profile,
                product_name=product_info["product_name"],
                product_category=product_info["category"],
            )
            
            return {
                "status": "success",
                "rating": generated["rating"],
                "review_text": generated["review_text"],
                "review_summary": generated.get("review_summary", ""),
                "confidence": generated["confidence"],
                "reasoning": generated.get("reasoning", ""),
                "nigerian_markers": generated.get("nigerian_markers", []),
                "user_profile": user_profile,
                "product_info": product_info,
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }
    
    def task_b_get_recommendations(
        self,
        user_id: str,
        n_recommendations: int = 10,
    ) -> Dict:
        """
        TASK B: Get personalized recommendations for user.
        
        Handles cold-start users automatically.
        
        Args:
            user_id: User identifier
            n_recommendations: Number of recommendations to return
        
        Returns:
            {
                "status": "success|error",
                "strategy": "new_user|cold_user|warm_user",
                "user_profile": Dict,
                "recommendations": List[Dict],
                "error": str (if failed),
            }
        """
        try:
            # Compute global popularity (one-time)
            if self.recommender.global_popularity is None:
                interactions = self.data[["user_id", "product_id", "rating"]]
                self.recommender.compute_popularity(interactions)
                print("✅ Computed global popularity scores")
            
            # Get user reviews
            user_reviews = self.get_user_reviews(user_id)
            
            # Get user profile
            user_profile = self.get_user_profile(user_id)
            
            if user_profile is None:
                return {
                    "status": "error",
                    "error": f"User {user_id} not found in dataset",
                }
            
            # Get recommendations
            result = self.recommender.recommend(
                user_reviews=user_reviews,
                products_df=self.products_cache,
                n_recommendations=n_recommendations,
            )
            
            return {
                "status": "success",
                "strategy": result["strategy"],
                "review_count": result["review_count"],
                "user_profile": user_profile,
                "recommendations": result["recommendations"],
                "explanation": result["explanation"],
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }
    
    def get_sample_users(self, segment: Optional[str] = None, limit: int = 5) -> List[str]:
        """Get sample user IDs for testing."""
        data = self.data
        
        if segment:
            data = data[data["segment"] == segment]
        
        return data["user_id"].unique()[:limit].tolist()
    
    def get_sample_products(self, limit: int = 5) -> List[str]:
        """Get sample product IDs for testing."""
        return self.products_cache["product_id"].head(limit).tolist()


def main():
    """Demo: Test orchestrator with sample data."""
    
    print("\n" + "=" * 70)
    print("BEHAVIORIQ FOOD ORCHESTRATOR DEMO")
    print("=" * 70)
    
    orchestrator = BehaviorIQFoodOrchestrator()
    
    # Get sample users
    cold_users = orchestrator.get_sample_users("cold", limit=2)
    warm_users = orchestrator.get_sample_users("warm", limit=2)
    products = orchestrator.get_sample_products(limit=3)
    
    print(f"\n📊 Sample users (cold): {cold_users[:1]}")
    print(f"📊 Sample users (warm): {warm_users[:1]}")
    print(f"📊 Sample products: {products[:2]}")
    
    # TASK A: Generate reviews
    print("\n" + "-" * 70)
    print("TASK A: Review Generation")
    print("-" * 70)
    
    if cold_users and products:
        result = orchestrator.task_a_generate_review(cold_users[0], products[0])
        if result["status"] == "success":
            print(f"\n✅ Generated review for user={cold_users[0]}, product={products[0]}")
            print(f"   Rating: {result['rating']}★")
            print(f"   Text: {result['review_text'][:150]}...")
            print(f"   Confidence: {result['confidence']:.2f}")
        else:
            print(f"❌ Error: {result['error']}")
    
    # TASK B: Get recommendations
    print("\n" + "-" * 70)
    print("TASK B: Personalized Recommendations")
    print("-" * 70)
    
    for user_id in cold_users[:1] + warm_users[:1]:
        result = orchestrator.task_b_get_recommendations(user_id, n_recommendations=5)
        if result["status"] == "success":
            print(f"\n✅ Recommendations for {user_id} ({result['strategy']})")
            print(f"   Review count: {result['review_count']}")
            print(f"   Strategy: {result['explanation']}")
            print(f"   Top 3 recommendations:")
            for rec in result["recommendations"][:3]:
                print(f"     - {rec['product_name']} ({rec['category']}): {rec['reason']}")
        else:
            print(f"❌ Error: {result['error']}")
    
    print("\n" + "=" * 70)
    print("✅ ORCHESTRATOR READY FOR STREAMLIT APP")
    print("=" * 70)


if __name__ == "__main__":
    main()
