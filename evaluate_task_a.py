"""
Task A Evaluation: ROUGE & Behavioral Fidelity Metrics
Evaluates review generation quality against real user reviews
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.orchestrator_food import BehaviorIQOrchestrator
from dotenv import load_dotenv

load_dotenv()

try:
    from rouge_score import rouge_scorer
    ROUGE_AVAILABLE = True
except ImportError:
    print("⚠️  rouge-score not installed. Install with: pip install rouge-score")
    ROUGE_AVAILABLE = False

try:
    from bert_score import score as bert_score
    BERT_AVAILABLE = True
except ImportError:
    print("⚠️  bert-score not installed. Install with: pip install bert-score")
    BERT_AVAILABLE = False


def evaluate_task_a(n_samples=50, output_file="EVALUATION_RESULTS.json"):
    """
    Evaluate Task A by comparing generated reviews against real reviews
    
    Metrics:
    - ROUGE-1, ROUGE-L (n-gram overlap with real reviews)
    - Behavioral metrics (rating accuracy, Nigerian marker usage)
    - Confidence vs accuracy correlation
    """
    
    print("🔍 Starting Task A Evaluation...")
    print(f"   Sample size: {n_samples} user-product pairs")
    print(f"   ROUGE available: {ROUGE_AVAILABLE}")
    print(f"   BERTScore available: {BERT_AVAILABLE}\n")
    
    orch = BehaviorIQOrchestrator()
    
    # Get diverse test cases
    reviews_df = orch.reviews_data
    test_users = reviews_df['user_id'].unique()[:n_samples]
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'n_samples': n_samples,
        'model': 'claude-sonnet-4-5',
        'metrics': {
            'rouge1_f1': [],
            'rougeL_f1': [],
            'rating_accuracy': [],
            'confidence_scores': [],
            'nigerian_markers': [],
            'generation_success': 0,
            'generation_failure': 0
        },
        'samples': []
    }
    
    if ROUGE_AVAILABLE:
        scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
    
    print("Generating predictions and comparing to real reviews...\n")
    
    for i, user_id in enumerate(test_users):
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{n_samples}")
        
        # Get user's real reviews for context
        user_reviews = reviews_df[reviews_df['user_id'] == user_id]
        
        if len(user_reviews) == 0:
            continue
        
        # Pick a product this user reviewed (we'll use as "unseen" for evaluation)
        test_product_id = user_reviews.iloc[-1]['product_id']
        test_product_name = user_reviews.iloc[-1].get('product_name', 'Unknown')
        real_review_text = user_reviews.iloc[-1].get('review_text', '')
        real_rating = user_reviews.iloc[-1].get('rating', 0)
        
        try:
            # Generate prediction
            prediction = orch.task_a_generate_review(user_id, test_product_id)
            results['metrics']['generation_success'] += 1
            
            predicted_rating = prediction['rating']
            predicted_text = prediction['review_text']
            confidence = prediction['confidence']
            nigerian_markers = prediction.get('nigerian_markers', [])
            
            # Rating accuracy (0-1, where 1 = exact match)
            rating_diff = abs(predicted_rating - real_rating)
            rating_accuracy = max(0, 1 - (rating_diff / 5.0))
            results['metrics']['rating_accuracy'].append(rating_accuracy)
            results['metrics']['confidence_scores'].append(confidence)
            
            # Nigerian markers metric
            marker_count = len(nigerian_markers)
            results['metrics']['nigerian_markers'].append(marker_count)
            
            # ROUGE scores if available
            if ROUGE_AVAILABLE and len(real_review_text) > 0:
                rouge_scores = scorer.score(real_review_text, predicted_text)
                results['metrics']['rouge1_f1'].append(rouge_scores['rouge1'].fmeasure)
                results['metrics']['rougeL_f1'].append(rouge_scores['rougeL'].fmeasure)
            
            # Store sample
            results['samples'].append({
                'user_id': user_id,
                'product_id': test_product_id,
                'product_name': test_product_name,
                'real_rating': real_rating,
                'predicted_rating': predicted_rating,
                'rating_match': rating_accuracy,
                'confidence': confidence,
                'nigerian_markers_count': marker_count,
                'user_segment': prediction.get('user_segment', 'unknown'),
                'real_review_snippet': real_review_text[:100],
                'predicted_review_snippet': predicted_text[:100]
            })
            
        except Exception as e:
            results['metrics']['generation_failure'] += 1
            print(f"    ⚠️  Error for {user_id}-{test_product_id}: {str(e)}")
    
    # Compute aggregate metrics
    print("\n📊 Computing aggregate metrics...\n")
    
    aggregated = {
        'total_predictions': results['metrics']['generation_success'],
        'success_rate': results['metrics']['generation_success'] / (results['metrics']['generation_success'] + results['metrics']['generation_failure']),
        'avg_rating_accuracy': np.mean(results['metrics']['rating_accuracy']) if results['metrics']['rating_accuracy'] else 0,
        'avg_confidence': np.mean(results['metrics']['confidence_scores']) if results['metrics']['confidence_scores'] else 0,
        'avg_nigerian_markers': np.mean(results['metrics']['nigerian_markers']) if results['metrics']['nigerian_markers'] else 0
    }
    
    if ROUGE_AVAILABLE and results['metrics']['rouge1_f1']:
        aggregated['avg_rouge1_f1'] = np.mean(results['metrics']['rouge1_f1'])
        aggregated['avg_rougeL_f1'] = np.mean(results['metrics']['rougeL_f1'])
    
    results['aggregated_metrics'] = aggregated
    
    # Print results
    print("=" * 70)
    print("📈 TASK A EVALUATION RESULTS")
    print("=" * 70)
    print(f"\n✅ Model: {results['model']}")
    print(f"📅 Timestamp: {results['timestamp']}")
    print(f"🎯 Sample Size: {n_samples} user-product pairs")
    print(f"\n{'Metric':<35} {'Score':<15} {'Interpretation':<20}")
    print("-" * 70)
    
    print(f"{'Success Rate':<35} {aggregated['success_rate']:.1%}{'':>10} {'Predictions generated':<20}")
    print(f"{'Avg Rating Accuracy':<35} {aggregated['avg_rating_accuracy']:.1%}{'':>10} {'Ratings match real':<20}")
    print(f"{'Avg Confidence Score':<35} {aggregated['avg_confidence']:.2f}/1.0{'':>6} {'Model confidence':<20}")
    print(f"{'Avg Nigerian Markers':<35} {aggregated['avg_nigerian_markers']:.1f}{'':>13} {'Markers per review':<20}")
    
    if ROUGE_AVAILABLE and results['metrics']['rouge1_f1']:
        print(f"{'Avg ROUGE-1 F1':<35} {aggregated['avg_rouge1_f1']:.3f}{'':>10} {'Unigram overlap':<20}")
        print(f"{'Avg ROUGE-L F1':<35} {aggregated['avg_rougeL_f1']:.3f}{'':>10} {'Longest common subseq':<20}")
    
    print("\n" + "=" * 70)
    
    # Sample predictions
    print("\n📝 Sample Predictions (first 3):\n")
    for sample in results['samples'][:3]:
        print(f"User: {sample['user_id']} → Product: {sample['product_name']}")
        print(f"  Real Rating: {sample['real_rating']}/5, Predicted: {sample['predicted_rating']}/5")
        print(f"  Rating Accuracy: {sample['rating_match']:.1%} | Confidence: {sample['confidence']:.1%}")
        print(f"  Nigerian Markers: {sample['nigerian_markers_count']} | Segment: {sample['user_segment']}")
        print(f"  Real Review: \"{sample['real_review_snippet']}...\"")
        print(f"  Predicted:  \"{sample['predicted_review_snippet']}...\"")
        print()
    
    # Save results to file
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_file}")
    print("\n🎯 Key Findings:")
    print(f"   • Task A successfully generated {aggregated['success_rate']:.0%} of predictions")
    print(f"   • Rating predictions matched real ratings {aggregated['avg_rating_accuracy']:.0%} of the time")
    print(f"   • Average Nigerian cultural markers per review: {aggregated['avg_nigerian_markers']:.1f}")
    print(f"   • Model confidence averaged {aggregated['avg_confidence']:.1%}")
    
    if ROUGE_AVAILABLE and results['metrics']['rouge1_f1']:
        print(f"   • ROUGE-1 overlap with real reviews: {aggregated['avg_rouge1_f1']:.1%}")
        print(f"   • ROUGE-L overlap with real reviews: {aggregated['avg_rougeL_f1']:.1%}")
    
    return results


if __name__ == "__main__":
    # Run evaluation with 50 samples
    results = evaluate_task_a(n_samples=50, output_file="EVALUATION_RESULTS.json")
    
    print("\n" + "=" * 70)
    print("✨ Evaluation complete! Share EVALUATION_RESULTS.json with judges.")
    print("=" * 70)
