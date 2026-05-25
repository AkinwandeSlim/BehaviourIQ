#!/usr/bin/env python3
"""Test integration of predictor_food.py and cold_start_handler.py"""

import sys
sys.path.insert(0, '.')

from agents.predictor_food import PredictorAgent, build_user_profile, get_product_info as pred_get_product_info
from agents.cold_start_handler import ColdStartHandler, get_product_info as csh_get_product_info

print("Testing integrations...")

# Test product info lookup
prod_name, prod_cat = pred_get_product_info('prod_00001')
print(f'✓ Product lookup works: {prod_name} ({prod_cat})')

# Test user profile building
sample_reviews = [
    {'rating': 5, 'review_text': 'Excellent product'},
    {'rating': 4, 'review_text': 'Very good'},
]
profile = build_user_profile(sample_reviews)
print(f'✓ Profile building works: avg_rating={profile["avg_rating"]}, segment={profile["segment"]}')

# Test PredictorAgent instantiation
agent = PredictorAgent()
print(f'✓ PredictorAgent initialized')

# Test ColdStartHandler instantiation
handler = ColdStartHandler()
print(f'✓ ColdStartHandler initialized')

# Verify both use same product lookup
name1, cat1 = pred_get_product_info('prod_00005')
name2, cat2 = csh_get_product_info('prod_00005')
assert name1 == name2 and cat1 == cat2, "Product info mismatch"
print(f'✓ Both modules return same product info: {name1}')

print('\n✅ All integration checks passed!')
