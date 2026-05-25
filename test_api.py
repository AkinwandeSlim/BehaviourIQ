#!/usr/bin/env python3
"""Quick test to verify Claude API is working"""

print("Testing Claude API connection...")
print()

from agents.orchestrator_food import BehaviorIQOrchestrator

try:
    print("Initializing orchestrator...")
    orch = BehaviorIQOrchestrator()
    print("✅ Orchestrator initialized successfully")
    print(f"   Reviews loaded: {len(orch.reviews_data):,}")
    print(f"   Products loaded: {len(orch.products_data):,}")
    print()
    
    # Test Task A with a known user
    print("Testing Task A (Review Generation)...")
    result = orch.task_a_generate_review("user_00001", "prod_00001")
    
    if result["confidence"] > 0.5:
        print("✅ Real Claude API working!")
        print(f"   Rating: {result['rating']}/5")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Review: {result['review_text'][:80]}...")
    else:
        print("⚠️  Using fallback (Claude API may have failed)")
        print(f"   Confidence: {result['confidence']}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
