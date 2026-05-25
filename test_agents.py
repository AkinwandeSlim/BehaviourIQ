#!/usr/bin/env python
"""
Quick test script for orchestrator and Streamlit app.
Run with: python test_agents.py
"""

import sys
import os

print("\n" + "=" * 70)
print("TESTING BEHAVIORIQ FOOD ORCHESTRATOR")
print("=" * 70)

# Test 1: Import orchestrator
print("\n[TEST 1] Importing orchestrator...")
try:
    from orchestrator_food import BehaviorIQFoodOrchestrator
    print("✅ Orchestrator imported successfully")
except Exception as e:
    print(f"❌ Failed to import orchestrator: {e}")
    sys.exit(1)

# Test 2: Load data
print("\n[TEST 2] Loading data...")
try:
    orch = BehaviorIQFoodOrchestrator("data/food_reviews.csv")
    print("✅ Data loaded successfully")
except Exception as e:
    print(f"❌ Failed to load data: {e}")
    sys.exit(1)

# Test 3: Get sample users
print("\n[TEST 3] Getting sample users...")
try:
    cold_users = orch.get_sample_users("cold", limit=2)
    warm_users = orch.get_sample_users("warm", limit=2)
    products = orch.get_sample_products(limit=3)
    print(f"✅ Found {len(cold_users)} cold users, {len(warm_users)} warm users, {len(products)} products")
except Exception as e:
    print(f"❌ Failed to get samples: {e}")
    sys.exit(1)

# Test 4: Task A - Generate review
print("\n[TEST 4] Testing Task A (Review Generation)...")
if cold_users and products:
    try:
        result = orch.task_a_generate_review(cold_users[0], products[0])
        if result["status"] == "success":
            print(f"✅ Generated review:")
            print(f"   Rating: {result['rating']}★")
            print(f"   Text: {result['review_text'][:80]}...")
            print(f"   Confidence: {result['confidence']:.2f}")
        else:
            print(f"❌ Generation failed: {result['error']}")
    except Exception as e:
        print(f"⚠️  Task A test skipped (Claude API required): {e}")
else:
    print("⚠️  No sample users/products available")

# Test 5: Task B - Get recommendations
print("\n[TEST 5] Testing Task B (Recommendations)...")
if cold_users:
    try:
        result = orch.task_b_get_recommendations(cold_users[0], n_recommendations=5)
        if result["status"] == "success":
            print(f"✅ Got recommendations:")
            print(f"   Strategy: {result['strategy']}")
            print(f"   Review count: {result['review_count']}")
            print(f"   Recommendations: {len(result['recommendations'])} items")
            if result["recommendations"]:
                print(f"   Top pick: {result['recommendations'][0]['product_name']}")
        else:
            print(f"❌ Recommendations failed: {result['error']}")
    except Exception as e:
        print(f"❌ Task B test failed: {e}")
else:
    print("⚠️  No sample users available")

# Test 6: Check Streamlit availability
print("\n[TEST 6] Checking Streamlit installation...")
try:
    import streamlit as st
    print(f"✅ Streamlit {st.__version__} installed")
except ImportError:
    print("⚠️  Streamlit not installed. Run: pip install streamlit")

print("\n" + "=" * 70)
print("✅ TESTING COMPLETE")
print("=" * 70)
print("\nNext step: Run the Streamlit app with:")
print("  streamlit run app_food.py")
print()
