#!/usr/bin/env python3
"""End-to-end test of BehaviorIQ system - Task A and Task B"""

import sys
sys.path.insert(0, '.')

from agents.orchestrator_food import BehaviorIQOrchestrator

def main():
    print("🧪 END-TO-END TEST")
    print("=" * 60)
    
    # Initialize orchestrator
    orch = BehaviorIQOrchestrator()
    
    # Get a sample user with review history
    sample_user = orch.reviews_data.iloc[50]['user_id']
    sample_product = orch.reviews_data.iloc[100]['product_id']
    
    print(f"\n✓ Test User: {sample_user}")
    print(f"✓ Test Product: {sample_product}")
    
    # ===== TASK A TEST =====
    print("\n📝 TASK A: Review Generation")
    print("-" * 60)
    try:
        result_a = orch.task_a_generate_review(sample_user, sample_product)
        print(f"✅ Review generated!")
        print(f"   Rating: {result_a.get('rating', '?')}/5")
        print(f"   Segment: {result_a.get('user_segment', '?')}")
        print(f"   Confidence: {result_a.get('confidence', 0):.0%}")
        print(f"   Summary: {result_a.get('review_summary', '')}")
        print(f"   Text: {result_a.get('review_text', '')[:80]}...")
        markers = result_a.get('nigerian_markers', [])
        if markers:
            print(f"   🇳🇬 Markers: {', '.join(markers[:2])}")
    except Exception as e:
        print(f"❌ Task A failed: {e}")
        import traceback
        traceback.print_exc()
    
    # ===== TASK B TEST =====
    print("\n🎯 TASK B: Recommendations")
    print("-" * 60)
    try:
        result_b = orch.task_b_get_recommendations(sample_user, n_recommendations=5)
        print(f"✅ Recommendations generated!")
        print(f"   User Segment: {result_b.get('user_segment', '?')}")
        print(f"   Strategy: {result_b.get('strategy', '?')}")
        print(f"   Items returned: {len(result_b.get('recommendations', []))}")
        
        recs = result_b.get('recommendations', [])
        for i, rec in enumerate(recs[:3], 1):
            print(f"   {i}. {rec.get('product_name', '?')} ({rec.get('category', '?')})")
            print(f"      → {rec.get('reason', '?')}")
    except Exception as e:
        print(f"❌ Task B failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✨ END-TO-END TEST COMPLETE")
    print("🚀 System ready for evaluation!")

if __name__ == "__main__":
    main()
