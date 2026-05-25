#!/usr/bin/env python3
"""Test Task B for the problematic user"""

from dotenv import load_dotenv
load_dotenv()

from agents.orchestrator_food import BehaviorIQOrchestrator

print("Testing Task B (Recommendations)...")
print()

orch = BehaviorIQOrchestrator()

# Test with the problematic user
user_id = "user_00034"

try:
    print(f"Getting recommendations for {user_id}...")
    result = orch.task_b_get_recommendations(user_id, n_recommendations=5)
    
    print(f"✅ Success!")
    print(f"   Segment: {result['user_segment']}")
    print(f"   Strategy: {result['strategy']}")
    print(f"   Recommendations: {len(result['recommendations'])}")
    print()
    
    for i, rec in enumerate(result['recommendations'][:3], 1):
        print(f"   #{i}: {rec['product_name']}")
        print(f"       Score: {rec['score']:.2f} | Rating: {rec['avg_rating']:.1f}⭐")
        print(f"       Reason: {rec['reason']}")
        print()
        
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
