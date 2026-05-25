# BehaviorIQ: Testing & Improvement Guide

> How to test, evaluate, and improve the system

---

## 📦 What Has Been Built

### Core Components ✅

1. **Task A: Review Generator** (`agents/predictor_food.py`)
   - Generates predicted reviews (rating + text) for user-product pairs
   - Uses Claude Sonnet 4.5 with Nigerian cultural context
   - Analyzes user behavior patterns to predict authentic reviews
   - Returns: rating, review_text, summary, confidence, nigerian_markers

2. **Task B: Recommendation Engine** (`agents/cold_start_handler.py`)
   - Recommends top 10 products for users
   - Smart cold-start handling (81% of users have ≤4 reviews)
   - Category preference inference from review history
   - Hybrid scoring: 50% popularity + 50% category match

3. **Orchestrator** (`agents/orchestrator_food.py`)
   - Unified API coordinating both tasks
   - Data loading and caching
   - Batch processing for evaluation
   - Pre-computed popularity scores

4. **Streamlit UI** (`app_food.py`)
   - Interactive two-tab interface
   - Task A: Generate reviews with user/product inputs
   - Task B: Get recommendations with strategy display
   - About tab with system documentation

5. **Data Pipeline**
   - 560,777 cleaned Amazon Food Reviews
   - 256,056 unique users with behavior profiles
   - 74,258 enriched products with realistic names
   - 7 Nigerian-centric product categories

---

## 🧪 Testing Strategies

### Level 1: Quick Verification (2 minutes)

```bash
# Activate venv
source venv/bin/activate

# Run verification script
python verify.py
```

**Checks:**
- ✅ All modules import correctly
- ✅ Data loads successfully
- ✅ Product metadata is accessible
- ✅ Component initialization works

**Expected output:**
```
✨ ALL VERIFICATION CHECKS PASSED
🚀 System is ready for deployment!
```

---

### Level 2: Individual Component Testing (5-10 minutes)

#### Test Task A Components

```python
from agents.predictor_food import build_user_profile, generate_review

# Test 1: User profile building
reviews = [
    {'rating': 5, 'review_text': 'Excellent!'},
    {'rating': 5, 'review_text': 'Great product'},
    {'rating': 4, 'review_text': 'Very good'},
]
profile = build_user_profile(reviews)

print(f"Profile segment: {profile['segment']}")        # Should be 'cold' (3 reviews)
print(f"Average rating: {profile['avg_rating']}")       # Should be ~4.67
print(f"% 5-star: {profile['pct_5star'] * 100:.0f}%")  # Should be 66.7%
assert profile['segment'] in ['cold', 'lukewarm', 'warm']
assert 4.0 <= profile['avg_rating'] <= 5.0
print("✅ Task A component test passed")
```

#### Test Task B Components

```python
from agents.cold_start_handler import ColdStartHandler
import pandas as pd

# Test 2: Cold start handler initialization
handler = ColdStartHandler()

# Create sample interaction data
interactions = pd.DataFrame({
    'user_id': ['u1', 'u1', 'u2', 'u2', 'u2'],
    'product_id': ['p1', 'p2', 'p1', 'p3', 'p4'],
    'rating': [5, 4, 5, 3, 2]
})

# Compute popularity
popularity = handler.compute_popularity(interactions)
print(f"Computed popularity for {len(popularity)} products")
assert len(popularity) > 0
assert 'popularity_score' in popularity.columns
print("✅ Task B component test passed")
```

---

### Level 3: End-to-End Integration Test (15-30 minutes)

#### Option A: Streamlit UI (Interactive)

```bash
# Activate venv
source venv/bin/activate

# Launch Streamlit
streamlit run app_food.py

# Then in browser (http://localhost:8501):
# Tab 1 - Task A:
#   - Enter user_id: user_00001
#   - Enter product_id: prod_00001
#   - Click "Generate Review"
#   - Observe: rating, confidence, Nigerian markers

# Tab 2 - Task B:
#   - Enter user_id: user_00001
#   - Click "Get Recommendations"
#   - Observe: strategy used, product names, reasons
```

**What to check:**
- ✅ Reviews generate with realistic ratings
- ✅ Nigerian expressions appear naturally
- ✅ Confidence scores vary by user segment
- ✅ Recommendations match user's preference history
- ✅ Cold-start users get popular products

#### Option B: Python Script (Batch Testing)

```python
from agents.orchestrator_food import BehaviorIQOrchestrator
import pandas as pd

orch = BehaviorIQOrchestrator()

# Get diverse test cases
test_users = orch.reviews_data['user_id'].unique()[:5]
test_products = orch.reviews_data['product_id'].unique()[:5]

print("Testing Task A (Review Generation)...")
for user in test_users:
    for product in test_products:
        result = orch.task_a_generate_review(user, product)
        assert 1 <= result['rating'] <= 5
        assert len(result['review_text']) > 50
        assert 0 <= result['confidence'] <= 1
        print(f"  ✓ {user} → {product}: {result['rating']}/5")

print("\nTesting Task B (Recommendations)...")
for user in test_users:
    result = orch.task_b_get_recommendations(user, n_recommendations=10)
    assert result['user_segment'] in ['new', 'cold', 'lukewarm', 'warm']
    assert len(result['recommendations']) <= 10
    print(f"  ✓ {user}: {result['user_segment']} ({result['strategy']})")
```

---

### Level 4: Evaluation Metrics

#### Task A: Review Generation (ROUGE/BERTScore)

```python
from agents.orchestrator_food import BehaviorIQOrchestrator
from rouge_score import rouge_scorer
import pandas as pd

orch = BehaviorIQOrchestrator()

# Setup
scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
results = []

# Get test cases where we have actual reviews
test_df = orch.reviews_data.head(100)

print("Computing ROUGE scores...")
for idx, row in test_df.iterrows():
    user_id = row['user_id']
    product_id = row['product_id']
    actual_review = row['review_text']
    
    # Get user history (excluding this review)
    user_history = orch.reviews_data[
        (orch.reviews_data['user_id'] == user_id) & 
        (orch.reviews_data['product_id'] != product_id)
    ].head(10).to_dict('records')
    
    if len(user_history) == 0:
        continue
    
    # Generate prediction
    pred = orch.task_a_generate_review(user_id, product_id)
    predicted_review = pred['review_text']
    
    # Compute ROUGE
    scores = scorer.score(actual_review, predicted_review)
    
    results.append({
        'user_id': user_id,
        'product_id': product_id,
        'rouge1': scores['rouge1'].fmeasure,
        'rougeL': scores['rougeL'].fmeasure,
        'rating_match': 1 if row['rating'] == pred['rating'] else 0,
    })

# Summary
df_results = pd.DataFrame(results)
print(f"\nTask A Evaluation Results ({len(df_results)} samples):")
print(f"  ROUGE-1: {df_results['rouge1'].mean():.3f}")
print(f"  ROUGE-L: {df_results['rougeL'].mean():.3f}")
print(f"  Rating accuracy: {df_results['rating_match'].mean():.1%}")

# Save for later analysis
df_results.to_csv('task_a_evaluation.csv', index=False)
```

#### Task B: Recommendations (NDCG@10)

```python
from agents.orchestrator_food import BehaviorIQOrchestrator
import numpy as np
import pandas as pd

orch = BehaviorIQOrchestrator()

def compute_ndcg(recommendations, relevant_products, k=10):
    """Compute NDCG@k"""
    dcg = 0.0
    for rank, rec in enumerate(recommendations[:k], 1):
        if rec['product_id'] in relevant_products:
            dcg += 1.0 / np.log2(rank + 1)
    
    # Ideal DCG: all relevant products ranked first
    idcg = sum(1.0 / np.log2(i + 1) for i in range(1, min(len(relevant_products), k) + 1))
    
    return dcg / idcg if idcg > 0 else 0.0

# Setup
results = []
test_users = orch.reviews_data['user_id'].unique()[:50]

print("Computing NDCG@10 scores...")
for user_id in test_users:
    # Get user's review history (split into train/test)
    user_reviews = orch.reviews_data[orch.reviews_data['user_id'] == user_id]
    
    if len(user_reviews) < 2:
        continue
    
    # Use first 80% for training, last 20% for evaluation
    split = int(len(user_reviews) * 0.8)
    train_reviews = user_reviews.iloc[:split].to_dict('records')
    test_reviews = user_reviews.iloc[split:].to_dict('records')
    test_products = set(r['product_id'] for r in test_reviews)
    
    # Get recommendations
    recs = orch.task_b_get_recommendations(user_id, n_recommendations=10)
    recommendations = recs['recommendations']
    
    # Compute NDCG
    ndcg = compute_ndcg(recommendations, test_products, k=10)
    
    results.append({
        'user_id': user_id,
        'segment': recs['user_segment'],
        'strategy': recs['strategy'],
        'ndcg@10': ndcg,
        'test_items': len(test_products),
    })

# Summary
df_results = pd.DataFrame(results)
print(f"\nTask B Evaluation Results ({len(df_results)} users):")
print(f"  NDCG@10 (overall): {df_results['ndcg@10'].mean():.3f}")
print(f"  NDCG@10 (cold-start): {df_results[df_results['segment']=='cold']['ndcg@10'].mean():.3f}")
print(f"  NDCG@10 (warm): {df_results[df_results['segment']=='warm']['ndcg@10'].mean():.3f}")

df_results.to_csv('task_b_evaluation.csv', index=False)
```

---

## 🚀 How to Run for Evaluation

### Quick Demo

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Launch interactive UI
streamlit run app_food.py

# 3. Test both tasks manually in browser
```

### Batch Evaluation

```bash
# 1. Run verification
python verify.py

# 2. Batch Task A (1000 random pairs)
python -c "
from agents.orchestrator_food import BehaviorIQOrchestrator
import random

orch = BehaviorIQOrchestrator()
users = list(orch.reviews_data['user_id'].unique())
products = list(orch.reviews_data['product_id'].unique())

pairs = [(random.choice(users), random.choice(products)) for _ in range(100)]
results_a = orch.batch_task_a(pairs, verbose=True)
print(f'Generated {len(results_a)} reviews')
"

# 3. Batch Task B (100 users)
python -c "
from agents.orchestrator_food import BehaviorIQOrchestrator
import random

orch = BehaviorIQOrchestrator()
users = list(orch.reviews_data['user_id'].unique())[:100]

results_b = orch.batch_task_b(users, n_recommendations=10, verbose=True)
print(f'Generated {len(results_b)} recommendation sets')
"
```

---

## 📈 Improvement Roadmap

### Phase 1: Quality Improvements (Quick Wins)

#### Task A: Review Generation

**Current:** Uses Claude with fallback for errors

**Improvements:**
1. **Fine-tune system prompt with examples**
   - Add 5-10 good examples of Nigerian-voice reviews
   - Include counter-examples to avoid
   ```python
   # In predictor_food.py SYSTEM_PROMPT
   SYSTEM_PROMPT = """...\n
   Examples of good reviews:
   - "E do well sharp sharp. This one is correct!" (5 stars, enthusiastic)
   - "Chai, the quality disappeared o. Not like before." (2 stars, disappointed)
   ...
   """
   ```

2. **Add style matching from user's existing reviews**
   - Extract writing patterns (sentence length, word frequency)
   - Match tone (positive, critical, balanced)
   ```python
   def analyze_writing_style(sample_texts):
       return {
           'avg_sentence_length': ...,
           'tone': 'positive' | 'critical' | 'balanced',
           'uses_comparisons': bool,
       }
   ```

3. **Constraint on review length**
   - Ensure generated text is 200-400 chars (not fallback defaults)
   - Add validation before returning

#### Task B: Recommendations

**Current:** Category inference + 50/50 popularity blend

**Improvements:**
1. **Add temporal factors**
   - Weight recent purchases higher
   - Detect trend changes (was buying pet food, now buying coffee)
   ```python
   def compute_recency_weight(user_reviews):
       # More recent = higher weight
       return weighted_avg(reviews_by_time)
   ```

2. **Add collaborative filtering**
   - Find similar users → recommend their liked products
   - Currently using only user profile
   ```python
   def find_similar_users(user_id, user_profiles, similarity='cosine'):
       similar = [u for u in users if similarity(u.profile, target.profile) > 0.7]
       return recommend_by_similar_users(similar)
   ```

3. **Cold-start: Diversify by category**
   - Don't recommend 10 from same category
   - Ensure breadth
   ```python
   recommendations = []
   for category in priority_categories:
       recommendations.extend(top_3_in_category)
   ```

---

### Phase 2: Content Improvements (1-2 hours)

#### 1. Product Name Enrichment

**Current:** Inferred from review content (generic but realistic)

**Future:**
- Extract actual brand names from reviews
- Add price/size info when available
- Create product description from reviews

```python
def enrich_product_description(product_id, reviews_df):
    """Extract rich product info from reviews"""
    product_reviews = reviews_df[reviews_df['product_id'] == product_id]
    
    # Extract mentioned brands
    brands = extract_entities(product_reviews['review_text'])
    
    # Infer price range from review mentions
    price_mentions = extract_price_refs(product_reviews['review_text'])
    
    # Common product features
    features = extract_features(product_reviews['review_text'])
    
    return {
        'brands': brands,
        'price_range': price_mentions,
        'features': features,
    }
```

#### 2. Nigerian Context Expansion

**Current:** 8 expressions, 7 categories

**Future:**
- Add regional references (Lagos, Kano, Abuja specific foods)
- Include cost comparisons ("cheaper than Market price")
- Add slang variations

```python
NIGERIAN_CONTEXT = {
    'regions': {
        'Lagos': ['mainland traffic', 'Victoria Island', 'LEKKI toll'],
        'Kano': ['groundnut oil', 'northern spices'],
        'Abuja': ['city traders', 'ultra-modern'],
    },
    'brands': ['Maggi', 'Indomie', 'Dangote', 'Golden Morn'],
    'slang': [
        'e choke well',      # it's very good
        'fine fine',         # excellent
        'my brother',        # friendly address
    ],
}
```

#### 3. User Segmentation Enhancement

**Current:** Simple cold/lukewarm/warm by review count

**Future:**
- Segment by behavior patterns
- Product preference stability
- Review sentiment evolution

```python
def advanced_segmentation(user_reviews):
    """More nuanced user segmentation"""
    return {
        'base_segment': 'cold' | 'lukewarm' | 'warm',
        'behavior': 'consistent' | 'exploratory' | 'trending',
        'sentiment': 'positive_biased' | 'balanced' | 'critical',
        'loyalty': 'high' | 'medium' | 'low',
    }
```

---

### Phase 3: Performance Optimization (2-3 hours)

#### 1. Caching Improvements

```python
# Current: Simple CSV caching
# Future: Add incremental updates

@cache
def get_user_profile(user_id):
    # Cache with TTL
    # Invalidate on new review
    pass

def update_cache_on_new_review(user_id, product_id):
    # Incrementally update profile
    # Don't recompute full history
    pass
```

#### 2. API Call Optimization

```python
# Current: One Claude call per review

# Future: Batch multiple reviews
def generate_reviews_batch(user_product_pairs, batch_size=5):
    # Generate 5 reviews per Claude call
    # Improves throughput 5x
    pass

# Future: Cache common profiles
@cache
def get_system_prompt_cached(user_segment):
    # Reuse system prompt variations
    pass
```

#### 3. Vector Embeddings (ChromaDB)

```python
# Current: Not using
# Future: Store embeddings for similarity

def init_embeddings():
    # Embed all product reviews
    # Embed all user profiles
    client = chromadb.Client()
    client.create_collection("reviews")
    client.create_collection("profiles")

def find_similar_reviews(review_text):
    # Find conceptually similar reviews
    # Improve generation quality
    pass
```

---

### Phase 4: Evaluation Metrics (1 hour)

#### Track Over Time

```python
def log_evaluation_metrics():
    """Track system performance"""
    metrics = {
        'task_a': {
            'rouge_l': 0.42,
            'rating_accuracy': 0.73,
            'confidence_avg': 0.82,
        },
        'task_b': {
            'ndcg@10': 0.65,
            'ndcg@10_cold': 0.58,
            'ndcg@10_warm': 0.71,
        },
        'timestamp': datetime.now(),
    }
    
    # Log to CSV for tracking
    pd.DataFrame([metrics]).to_csv('metrics.csv', mode='a')
```

#### A/B Testing Framework

```python
def evaluate_variant(variant_name, config):
    """Compare different configurations"""
    orch_old = BehaviorIQOrchestrator(config='baseline')
    orch_new = BehaviorIQOrchestrator(config=config)
    
    results = {
        'baseline': evaluate_all(orch_old),
        'variant': evaluate_all(orch_new),
    }
    
    return compare_results(results)
```

---

## 🔄 Iteration Workflow

### Weekly Improvement Cycle

**Monday:** Review metrics → Identify bottleneck
```bash
python evaluate.py --report weekly
# Output: Which task is underperforming?
# Which user segment needs help?
```

**Tuesday-Wednesday:** Implement improvements
```bash
# Edit predictor_food.py or cold_start_handler.py
# Add new feature/heuristic
# Test locally
```

**Thursday:** Evaluate changes
```bash
python test_e2e.py
python evaluate.py --compare baseline variant
```

**Friday:** Decide: ship or iterate
```bash
# If improvement > 5%: merge to main
# Else: debug or try different approach
```

---

## 📝 Common Issues & Solutions

### Issue: Low ROUGE Score for Task A

**Diagnosis:**
```python
# Check if reviews are too generic
for result in results:
    if result['review_text'] == FALLBACK_TEXT:
        print("Using fallback - Claude failed")
    if len(result['review_text']) < 100:
        print("Too short - consider length penalty")
```

**Solution:**
- Add stricter validation
- Increase MAX_TOKENS in config
- Improve system prompt with examples
- Add retry logic for failures

### Issue: Low NDCG for Cold Users

**Diagnosis:**
```python
# Segment analysis
cold_results = df[df['segment'] == 'cold']
print(f"Cold user NDCG: {cold_results['ndcg'].mean()}")
print(f"Category match rate: {(cold_results['found_category'] == True).mean()}")
```

**Solution:**
- Add more exploration in cold-start
- Reduce category match weight
- Add popularity boost
- Try different category inference

---

## 🎯 Testing Checklist

Before final submission:

- [ ] `verify.py` passes all checks
- [ ] Streamlit UI launches without errors
- [ ] Task A generates reviews with ratings 1-5
- [ ] Task A includes Nigerian markers
- [ ] Task B recommends products
- [ ] Task B handles cold users (0 reviews)
- [ ] Cold user recommendations include popular items
- [ ] Product names are realistic (not "prod_XXXXX")
- [ ] No console errors when switching tabs
- [ ] Batch processing works (100+ items)
- [ ] Docker build succeeds
- [ ] README is up to date

---

## 🚀 Running Full Evaluation

```bash
#!/bin/bash
# Full evaluation script

echo "🧪 FULL EVALUATION SUITE"
echo "========================"

# Activate venv
source venv/bin/activate

# Step 1: Verification
echo "Step 1: Verification"
python verify.py || exit 1

# Step 2: Unit tests
echo "Step 2: Component tests"
python test_components.py || exit 1

# Step 3: Task A evaluation
echo "Step 3: Task A (Review Generation)"
python evaluate_task_a.py

# Step 4: Task B evaluation
echo "Step 4: Task B (Recommendations)"
python evaluate_task_b.py

# Step 5: Performance
echo "Step 5: Performance Analysis"
python analyze_performance.py

echo "✨ EVALUATION COMPLETE"
```

---

**Last Updated:** May 24, 2026  
**Status:** Ready for Testing & Improvement ✅
