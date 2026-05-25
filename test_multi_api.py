"""
Test Multi-API Setup
Tests Claude + Groq + Fallback in order
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

print("\n" + "=" * 80)
print("🔄 MULTI-API TEST SUITE")
print("=" * 80 + "\n")

# Test 1: Check API keys loaded
print("Step 1: Checking API Keys in Environment...")
print("-" * 80)

claude_key = os.getenv("ANTHROPIC_API_KEY", "")
groq_key = os.getenv("GROQ_API_KEY", "")

print(f"  Claude API Key:  {('✓ Found (' + claude_key[:20] + '...)' if claude_key else '✗ NOT FOUND')}")
print(f"  Groq API Key:    {('✓ Found (' + groq_key[:20] + '...)' if groq_key else '✗ NOT FOUND')}")

# Test 2: Import clients
print("\nStep 2: Testing API Client Imports...")
print("-" * 80)

try:
    import anthropic
    claude_client = anthropic.Anthropic(api_key=claude_key) if claude_key else None
    print(f"  Claude Client:   {'✓ Available' if claude_key else '✗ Requires API key'}")
except Exception as e:
    print(f"  Claude Client:   ✗ Error: {str(e)[:50]}")
    claude_client = None

try:
    from groq import Groq
    groq_client = Groq(api_key=groq_key) if groq_key else None
    print(f"  Groq Client:     {'✓ Available' if groq_key else '✗ Requires API key'}")
except Exception as e:
    print(f"  Groq Client:     ✗ Error: {str(e)[:50]}")
    groq_client = None

# Test 3: Test predictor with multi-API
print("\nStep 3: Testing Predictor with Multi-API Fallback...")
print("-" * 80)

from agents.predictor_food import build_user_profile, generate_review

profile = {
    'avg_rating': 4.5,
    'std_rating': 0.5,
    'pct_5star': 0.8,
    'pct_1star': 0.0,
    'pct_positive': 1.0,
    'review_count': 3,
    'preferred_rating': 5,
    'sample_texts': ['Great product!', 'Very satisfied', 'Highly recommend'],
    'segment': 'warm'
}

try:
    result = generate_review(
        profile,
        product_name="Premium Rice",
        product_category="Grains",
        product_description="High-quality basmati rice",
        max_attempts=3
    )
    
    print(f"  ✓ Review generated successfully!")
    print(f"    - Rating: {result['rating']}/5")
    print(f"    - Confidence: {result['confidence']:.0%}")
    print(f"    - Review snippet: \"{result['review_text'][:60]}...\"")
    print(f"    - Nigerian markers: {result.get('nigerian_markers', [])[:2]}")
    
except Exception as e:
    print(f"  ✗ Error: {str(e)[:100]}")

# Test 4: Test orchestrator
print("\nStep 4: Testing Full Orchestrator (Both Tasks)...")
print("-" * 80)

try:
    from agents.orchestrator_food import BehaviorIQOrchestrator
    
    orch = BehaviorIQOrchestrator()
    print(f"  ✓ Orchestrator initialized")
    print(f"    - Reviews loaded: {len(orch.reviews_data):,}")
    print(f"    - Products loaded: {len(orch.products_data):,}")
    
    # Task A
    try:
        task_a = orch.task_a_generate_review("user_00001", "prod_00001")
        print(f"  ✓ Task A (Review Generation) succeeded")
        print(f"    - Rating: {task_a['rating']}/5, Confidence: {task_a.get('confidence', 0):.0%}")
    except Exception as e:
        print(f"  ✗ Task A failed: {str(e)[:50]}")
    
    # Task B
    try:
        task_b = orch.task_b_get_recommendations("user_00001", n_recommendations=5)
        print(f"  ✓ Task B (Recommendations) succeeded")
        print(f"    - Recommendations: {len(task_b.get('recommendations', []))} products")
        print(f"    - Strategy: {task_b.get('strategy', 'unknown')}")
    except Exception as e:
        print(f"  ✗ Task B failed: {str(e)[:50]}")
        
except Exception as e:
    print(f"  ✗ Orchestrator error: {str(e)[:100]}")

# Test 5: Summary
print("\n" + "=" * 80)
print("📊 API AVAILABILITY SUMMARY")
print("=" * 80)

print(f"""
Primary API (Claude):  {('✅ READY' if claude_client else '❌ NOT CONFIGURED')}
Backup API (Groq):     {('✅ READY' if groq_client else '❌ NOT CONFIGURED')}
Fallback Template:     ✅ ALWAYS AVAILABLE

System Status: {('✅ FULLY REDUNDANT' if (claude_client or groq_client) else '⚠️  USING FALLBACK ONLY')}

Priority Order:
  1. Claude (if API key present)
  2. Groq (if API key present)
  3. Fallback template (always works)

Evaluation Command:
  python evaluate_model_quick.py (doesn't need any API)

Interactive Demo:
  streamlit run app_food.py (will use available APIs)
""")

print("=" * 80)
print("✨ Test complete!\n")
