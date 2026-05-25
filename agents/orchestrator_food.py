# agents/orchestrator_food.py
"""
ORCHESTRATOR: Unified Task A + Task B Coordinator

Chains together:
- observer_food.py → builds user profiles
- predictor_food.py → Task A: generates reviews
- cold_start_handler.py → Task B: generates recommendations

Provides unified API for Streamlit app and testing.
"""

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import sys
import os

# Add parent directory to path for imports FIRST
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))  # For agent imports

from predictor_food import PredictorAgent, build_user_profile
from cold_start_handler import ColdStartHandler

# Load data
data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
try:
    REVIEWS_DATA = pd.read_csv(os.path.join(data_dir, "food_reviews.csv"))
except FileNotFoundError:
    REVIEWS_DATA = None
    print("⚠️  Warning: food_reviews.csv not found")

try:
    PRODUCTS_META = pd.read_csv(os.path.join(data_dir, "products_metadata.csv"))
except FileNotFoundError:
    PRODUCTS_META = None
    print("⚠️  Warning: products_metadata.csv not found")


class BehaviorIQOrchestrator:
    """Main orchestrator for both Task A and Task B."""
    
    def __init__(self):
        """Initialize agents and load data."""
        self.predictor = PredictorAgent()
        self.recommender = ColdStartHandler()
        self.reviews_data = REVIEWS_DATA
        self.products_data = PRODUCTS_META
        
        # Pre-compute popularity for recommendations
        if self.reviews_data is not None:
            self.recommender.compute_popularity(
                self.reviews_data[["user_id", "product_id", "rating"]]
            )
    
    def get_user_reviews(self, user_id: str) -> List[Dict]:
        """Get historical reviews for a user."""
        if self.reviews_data is None:
            return []
        
        user_data = self.reviews_data[self.reviews_data["user_id"] == user_id]
        return [
            {
                "product_id": row["product_id"],
                "rating": row["rating"],
                "review_text": row["review_text"],
                "date": row["date"],
            }
            for _, row in user_data.iterrows()
        ]
    
    def task_a_generate_review(
        self,
        user_id: str,
        product_id: str,
    ) -> Dict:
        """
        Task A: Generate predicted review for user + product.
        
        Args:
            user_id: User identifier
            product_id: Product identifier
        
        Returns:
            {
                "rating": 1-5,
                "review_summary": "...",
                "review_text": "...",
                "nigerian_markers": [...],
                "confidence": 0.0-1.0,
                "reasoning": "...",
                "user_segment": "cold|lukewarm|warm",
                "product_info": {...}
            }
        """
        # Get user's review history
        user_reviews = self.get_user_reviews(user_id)
        
        # Generate review using predictor
        result = self.predictor.predict(user_id, product_id, user_reviews)
        
        # Add context
        profile = build_user_profile(user_reviews)
        
        # Look up product info
        if self.products_data is not None:
            prod = self.products_data[self.products_data["product_id"] == product_id]
            if not prod.empty:
                result["product_info"] = {
                    "product_id": product_id,
                    "product_name": prod.iloc[0]["product_name"],
                    "category": prod.iloc[0]["category"],
                    "avg_rating": float(prod.iloc[0]["avg_rating"]),
                    "review_count": int(prod.iloc[0]["review_count"]),
                }
        
        result["user_segment"] = profile.get("segment", "unknown")
        result["review_count"] = profile.get("review_count", 0)
        
        return result
    
    def task_b_get_recommendations(
        self,
        user_id: str,
        n_recommendations: int = 10,
    ) -> Dict:
        """
        Task B: Get personalized recommendations for user.
        
        Args:
            user_id: User identifier
            n_recommendations: Number of recommendations (default 10)
        
        Returns:
            {
                "user_id": "...",
                "user_segment": "new|cold|lukewarm|warm",
                "recommendations": [
                    {
                        "rank": 1,
                        "product_id": "...",
                        "product_name": "...",
                        "category": "...",
                        "score": 0.0-1.0,
                        "reason": "...",
                        "avg_rating": 0.0-5.0,
                        "review_count": N
                    },
                    ...
                ],
                "strategy": "popularity|category_inference|hybrid"
            }
        """
        # Get user's review history
        user_reviews = self.get_user_reviews(user_id)
        profile = build_user_profile(user_reviews)
        
        # Determine segment
        segment_map = {
            0: "new",
            "cold": "cold",
            "lukewarm": "lukewarm",
            "warm": "warm",
        }
        segment = segment_map.get(profile.get("segment"), "cold")
        
        if len(user_reviews) == 0:
            strategy = "popularity"
            recommendations = self.recommender.recommend_new_user(
                self.products_data if self.products_data is not None else pd.DataFrame(),
                n_recommendations
            )
        else:
            strategy = "category_inference"
            recommendations = self.recommender.recommend_cold_user(
                user_reviews,
                self.products_data if self.products_data is not None else pd.DataFrame(),
                n_recommendations
            )
        
        # Add product metadata enrichment
        for rec in recommendations:
            if self.products_data is not None:
                prod = self.products_data[
                    self.products_data["product_id"] == rec["product_id"]
                ]
                if not prod.empty:
                    rec["avg_rating"] = float(prod.iloc[0]["avg_rating"])
                    rec["review_count"] = int(prod.iloc[0]["review_count"])
        
        return {
            "user_id": user_id,
            "user_segment": segment,
            "review_count": len(user_reviews),
            "recommendations": recommendations,
            "strategy": strategy,
            "n_recommendations": len(recommendations),
        }
    
    def batch_task_a(
        self,
        user_product_pairs: List[Tuple[str, str]],
        verbose: bool = False,
    ) -> List[Dict]:
        """
        Batch generate reviews for multiple user-product pairs.
        
        Args:
            user_product_pairs: List of (user_id, product_id) tuples
            verbose: Print progress
        
        Returns:
            List of review predictions
        """
        results = []
        for i, (user_id, product_id) in enumerate(user_product_pairs):
            if verbose and (i + 1) % 10 == 0:
                print(f"  [{i+1}/{len(user_product_pairs)}] Processed pairs")
            
            result = self.task_a_generate_review(user_id, product_id)
            result["user_id"] = user_id
            result["product_id"] = product_id
            results.append(result)
        
        return results
    
    def batch_task_b(
        self,
        user_ids: List[str],
        n_recommendations: int = 10,
        verbose: bool = False,
    ) -> List[Dict]:
        """
        Batch get recommendations for multiple users.
        
        Args:
            user_ids: List of user IDs
            n_recommendations: Number of recommendations per user
            verbose: Print progress
        
        Returns:
            List of recommendation sets
        """
        results = []
        for i, user_id in enumerate(user_ids):
            if verbose and (i + 1) % 10 == 0:
                print(f"  [{i+1}/{len(user_ids)}] Generated recommendations")
            
            result = self.task_b_get_recommendations(user_id, n_recommendations)
            results.append(result)
        
        return results


def main():
    """Test orchestrator."""
    print("Initializing BehaviorIQ Orchestrator...")
    
    try:
        orchestrator = BehaviorIQOrchestrator()
        print("✓ Orchestrator initialized")
        
        # Sample Task A test
        if orchestrator.reviews_data is not None and len(orchestrator.reviews_data) > 0:
            sample_user = orchestrator.reviews_data.iloc[0]["user_id"]
            sample_product = orchestrator.reviews_data.iloc[0]["product_id"]
            
            print(f"\nTask A Test (user={sample_user}, product={sample_product}):")
            result_a = orchestrator.task_a_generate_review(sample_user, sample_product)
            print(f"  Rating: {result_a.get('rating')}/5")
            print(f"  Summary: {result_a.get('review_summary')}")
            print(f"  Segment: {result_a.get('user_segment')}")
            
            print(f"\nTask B Test (user={sample_user}):")
            result_b = orchestrator.task_b_get_recommendations(sample_user, n_recommendations=5)
            print(f"  Segment: {result_b.get('user_segment')}")
            print(f"  Strategy: {result_b.get('strategy')}")
            print(f"  Recommendations: {len(result_b.get('recommendations', []))} items")
            
            print("\n✅ Orchestrator tests passed!")
        else:
            print("⚠️  No review data loaded for testing")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
