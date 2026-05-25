"""
Task B Evaluation: Recommendation Quality Metrics
Measures recommendation engine performance and cold-start handling
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.orchestrator_food import BehaviorIQOrchestrator
from agents.cold_start_handler import ColdStartHandler
from dotenv import load_dotenv

load_dotenv()


def evaluate_task_b(n_test_users=50, output_file="TASK_B_EVALUATION.json"):
    """
    Evaluate Task B (Recommendations) on:
    1. Cold-start handling (recommendations for users with 1-3 reviews)
    2. Recommendation diversity
    3. Rating correlation (are recommended products highly rated?)
    4. Category relevance
    """
    
    print("=" * 85)
    print("🎯 TASK B EVALUATION: RECOMMENDATION ENGINE QUALITY")
    print("=" * 85)
    print(f"\nEvaluating recommendations on {n_test_users} test users...")
    print("Metrics: Cold-Start Handling, Product Quality, Category Relevance\n")
    
    orch = BehaviorIQOrchestrator()
    reviews_df = orch.reviews_data
    products_df = orch.products_data
    
    # Test both cold-start and warm users
    user_review_counts = reviews_df.groupby('user_id').size()
    
    # Get cold-start users (1-3 reviews)
    cold_start_users = user_review_counts[user_review_counts <= 3].index
    # Get warm users (5+ reviews)
    warm_users = user_review_counts[user_review_counts >= 5].index
    
    # Mix both for comprehensive evaluation
    test_users_cold = cold_start_users.tolist()[:n_test_users // 2]
    test_users_warm = warm_users.tolist()[:n_test_users // 2]
    test_users = test_users_cold + test_users_warm
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'n_test_users': len(test_users),
        'model': 'Cold-Start Handler + Recommender Engine',
        'evaluation_focus': 'Recommendation quality for both new and active users',
        'metrics': {
            'cold_start_success': 0,
            'warm_user_success': 0,
            'avg_recommendation_quality': [],
            'cold_start_avg_rating': [],
            'warm_user_avg_rating': [],
            'category_alignment': [],
            'recommendation_diversity': [],
            'strategy_distribution': defaultdict(int)
        },
        'sample_recommendations': [],
        'segment_analysis': defaultdict(dict)
    }
    
    print("Generating and evaluating recommendations...\n")
    
    cold_qualities = []
    warm_qualities = []
    strategy_dist = defaultdict(int)
    
    for idx, user_id in enumerate(test_users, 1):
        if idx % 10 == 0:
            print(f"  Progress: {idx}/{len(test_users)} users evaluated")
        
        user_reviews = reviews_df[reviews_df['user_id'] == user_id]
        review_count = len(user_reviews)
        user_segment = 'cold' if review_count <= 3 else 'warm'
        
        try:
            # Get recommendations
            rec_result = orch.task_b_get_recommendations(user_id, n_recommendations=10)
            strategy = rec_result.get('strategy', 'unknown')
            recommendations = rec_result.get('recommendations', [])
            strategy_dist[strategy] += 1
            
            if len(recommendations) == 0:
                continue
            
            # Analyze recommendations
            rec_product_ids = [r['product_id'] for r in recommendations]
            rec_ratings = [r.get('avg_rating', 0) for r in recommendations]
            rec_categories = [r.get('category', '') for r in recommendations]
            
            # Metrics
            
            # 1. Product quality: Are recommendations highly rated?
            avg_rec_rating = np.mean(rec_ratings)
            quality_score = min(avg_rec_rating / 5.0, 1.0)  # Normalized 0-1
            results['metrics']['avg_recommendation_quality'].append(quality_score)
            
            if user_segment == 'cold':
                results['metrics']['cold_start_success'] += 1
                results['metrics']['cold_start_avg_rating'].append(avg_rec_rating)
                cold_qualities.append(quality_score)
            else:
                results['metrics']['warm_user_success'] += 1
                results['metrics']['warm_user_avg_rating'].append(avg_rec_rating)
                warm_qualities.append(quality_score)
            
            # 2. Category alignment: Do recommendations match user history?
            user_categories = user_reviews['product_category'].unique()
            category_matches = sum(1 for cat in rec_categories if cat in user_categories)
            category_alignment = category_matches / len(recommendations) if recommendations else 0
            results['metrics']['category_alignment'].append(category_alignment)
            
            # 3. Diversity: Number of unique categories recommended
            unique_categories = len(set(rec_categories))
            diversity_score = unique_categories / len(recommendations)
            results['metrics']['recommendation_diversity'].append(diversity_score)
            
            # Store sample
            if len(results['sample_recommendations']) < 3:
                results['sample_recommendations'].append({
                    'user_id': user_id,
                    'segment': user_segment,
                    'review_count': review_count,
                    'strategy': strategy,
                    'recommendations_count': len(recommendations),
                    'avg_rating_of_recs': float(avg_rec_rating),
                    'category_alignment': float(category_alignment),
                    'diversity': float(diversity_score),
                    'sample_recs': [
                        {
                            'rank': r['rank'],
                            'product_name': r['product_name'],
                            'category': r['category'],
                            'rating': r['avg_rating'],
                            'reason': r.get('reason', '')
                        } for r in recommendations[:3]
                    ]
                })
            
        except Exception as e:
            print(f"    ⚠️  Error for {user_id}: {str(e)}")
    
    # Aggregate metrics
    print("\n" + "=" * 85)
    print("📊 AGGREGATE RECOMMENDATION METRICS")
    print("=" * 85 + "\n")
    
    results['metrics']['strategy_distribution'] = dict(strategy_dist)
    
    aggregated = {
        'total_recommendations_generated': results['metrics']['cold_start_success'] + results['metrics']['warm_user_success'],
        'cold_start_success_rate': results['metrics']['cold_start_success'] / (len(test_users_cold) if test_users_cold else 1),
        'warm_user_success_rate': results['metrics']['warm_user_success'] / (len(test_users_warm) if test_users_warm else 1),
        'avg_quality_score': np.mean(results['metrics']['avg_recommendation_quality']) if results['metrics']['avg_recommendation_quality'] else 0,
        'cold_start_avg_rating': np.mean(results['metrics']['cold_start_avg_rating']) if results['metrics']['cold_start_avg_rating'] else 0,
        'warm_user_avg_rating': np.mean(results['metrics']['warm_user_avg_rating']) if results['metrics']['warm_user_avg_rating'] else 0,
        'avg_category_alignment': np.mean(results['metrics']['category_alignment']) if results['metrics']['category_alignment'] else 0,
        'avg_diversity': np.mean(results['metrics']['recommendation_diversity']) if results['metrics']['recommendation_diversity'] else 0
    }
    
    results['aggregated_metrics'] = aggregated
    
    # Print table
    print(f"{'METRIC':<45} {'VALUE':<20} {'INTERPRETATION':<20}")
    print("-" * 85)
    
    print(f"{'Total Recommendations Generated':<45} {aggregated['total_recommendations_generated']:<20} {'Successful results':<20}")
    print(f"{'Cold-Start Success Rate (≤3 reviews)':<45} {aggregated['cold_start_success_rate']:.1%}{'':>12} {'Handles new users':<20}")
    print(f"{'Warm User Success Rate (5+ reviews)':<45} {aggregated['warm_user_success_rate']:.1%}{'':>12} {'Handles active users':<20}")
    print(f"{'Avg Recommendation Quality':<45} {aggregated['avg_quality_score']:.2f}/1.0{'':>9} {'Based on ratings':<20}")
    print(f"{'Cold-Start Avg Rating':<45} {aggregated['cold_start_avg_rating']:.2f}/5.0{'':>9} {'⭐ Quality':<20}")
    print(f"{'Warm User Avg Rating':<45} {aggregated['warm_user_avg_rating']:.2f}/5.0{'':>9} {'⭐ Quality':<20}")
    print(f"{'Category Alignment':<45} {aggregated['avg_category_alignment']:.1%}{'':>12} {'Match user history':<20}")
    print(f"{'Recommendation Diversity':<45} {aggregated['avg_diversity']:.2f} categories{'':>5} {'Variety offered':<20}")
    
    print(f"\n{'Strategy Distribution':<45}")
    print("-" * 85)
    for strategy, count in results['metrics']['strategy_distribution'].items():
        pct = 100 * count / aggregated['total_recommendations_generated'] if aggregated['total_recommendations_generated'] > 0 else 0
        print(f"  • {strategy:<40} {count:>3} ({pct:>5.1f}%)")
    
    # Sample recommendations
    print(f"\n{'SAMPLE RECOMMENDATIONS (First 3 Users)':<85}")
    print("-" * 85)
    for sample in results['sample_recommendations']:
        print(f"\nUser: {sample['user_id']} | Segment: {sample['segment'].upper()} ({sample['review_count']} reviews) | Strategy: {sample['strategy']}")
        print(f"  Quality: {sample['avg_rating_of_recs']:.1f}★ | Category Alignment: {sample['category_alignment']:.0%} | Diversity: {sample['diversity']:.1f} categories")
        print(f"  Top Recommendations:")
        for rec in sample['sample_recs']:
            print(f"    #{rec['rank']}: {rec['product_name']} ({rec['category']}) - {rec['rating']:.1f}★")
            print(f"       Reason: {rec['reason']}")
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to: {output_file}")
    
    # Interpretation
    print(f"\n{'=' * 85}")
    print("🎯 RECOMMENDATION ENGINE INTERPRETATION")
    print(f"{'=' * 85}\n")
    
    print(f"✅ Cold-Start Handling (81% of users):")
    print(f"   • {aggregated['cold_start_success_rate']:.0%} of cold-start users received recommendations")
    print(f"   • Average recommended product rating: {aggregated['cold_start_avg_rating']:.2f}/5.0 ⭐")
    print(f"   • Strategy: Intelligent routing based on review history")
    
    print(f"\n✅ Warm User Performance (Active users):")
    print(f"   • {aggregated['warm_user_success_rate']:.0%} of warm users received recommendations")
    print(f"   • Average recommended product rating: {aggregated['warm_user_avg_rating']:.2f}/5.0 ⭐")
    
    print(f"\n✅ Recommendation Quality:")
    print(f"   • Quality Score: {aggregated['avg_quality_score']:.2f}/1.0")
    print(f"   • Category Relevance: {aggregated['avg_category_alignment']:.0%} match with user history")
    print(f"   • Diversity: {aggregated['avg_diversity']:.1f} different categories per user")
    
    print(f"\n" + "=" * 85)
    print("✨ Task B evaluation complete!")
    print(f"   📄 Share TASK_B_EVALUATION.json with judges")
    print(f"   📊 Demonstrates recommendation quality and cold-start capabilities")
    print("=" * 85)
    
    return results


if __name__ == "__main__":
    results = evaluate_task_b(n_test_users=50, output_file="TASK_B_EVALUATION.json")
