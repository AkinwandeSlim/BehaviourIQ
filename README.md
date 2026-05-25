# BehaviorIQ: AI-Powered Food Review & Recommendation System
## Hackathon 2026 Submission

> Personalized reviews and recommendations with authentic Nigerian cultural contextualisation

---

## 🎯 Overview

BehaviorIQ is an intelligent e-commerce system that:

1. **Task A:** Generates authentic product reviews (rating + text) reflecting individual customer behavior
   - **Evaluation:** ROUGE and BERTScore metrics
   - Uses customer purchase history to infer preferences and writing style
   - Nigerian-voice reviews with cultural references

2. **Task B:** Provides personalized recommendations for all user segments
   - **Evaluation:** NDCG@10 metric
   - Intelligent cold-start handling (81% of users have ≤4 reviews)
   - Category inference from limited review history

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Virtual environment (venv)
- ANTHROPIC_API_KEY environment variable

### Installation

```bash
# 1. Navigate to project
cd behavioriq_V2

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set API key
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Running the Streamlit App

```bash
# Activate venv first
source venv/bin/activate

# Launch UI
streamlit run app_food.py
```

Navigate to `http://localhost:8501`

---

## 📋 Tasks

### Task A: Review Generation (ROUGE/BERTScore)

Given user profile + product, generate:
- **Rating:** 1-5 stars reflecting user behavior
- **Review text:** 200-400 chars with Nigerian voice
- **Summary:** 10-20 word title
- **Confidence:** 0.5-1.0 score
- **Markers:** Nigerian expressions used

**Example:**
```
Input: user_00001 reviewing prod_00042 (Premium Dog Bites)
Output:
{
  "rating": 5,
  "review_summary": "Sharp Sharp Quality, This One Is Correct",
  "review_text": "Abeg, this dog bites is well well done! My dog just loves this. E do well sharp sharp. Value for money no be here, the quality is excellent. Sharp sharp delivery too. Will definitely buy again.",
  "nigerian_markers": ["abeg", "well well", "e do well", "sharp sharp"],
  "confidence": 0.87
}
```

### Task B: Recommendations (NDCG@10)

For any user, return top 10 products with:

**Strategies:**
- **New users (0 reviews):** Most popular products
- **Cold users (1-4 reviews):** Category inference + popularity
- **Warm users (5+ reviews):** Full personalization

**Example:**
```
Input: user_00001
Output:
{
  "user_segment": "cold",
  "strategy": "category_inference",
  "recommendations": [
    {
      "rank": 1,
      "product_name": "Premium Dog Bites #101",
      "category": "Pet Food",
      "score": 0.89,
      "reason": "Popular in Pet Food"
    },
    ...
  ]
}
```

---

## 🇳🇬 Nigerian Contextualisation

### Cultural Elements

**Language Markers:**
- "e do well" - it works well
- "sharp sharp" - quickly/immediately
- "abeg" - please/emphatic
- "chai" - surprise/frustration
- "value for money no be here" - great value
- "this one is correct" - good quality
- "na wa o" - expression of surprise
- "well well" - very much

**Product Categories:**
- Grains & Staples (28K products)
- General Food & Grocery (13K)
- Snacks & Confections (9.6K)
- Beverages (11K)
- Pet Food (4.8K)
- Spices & Seasonings (4.6K)
- Oils & Fats (2.4K)

**References:** NEPA power cuts, market prices, familiar brands (Maggi, Indomie, Dangote)

---

## 📊 Data

- **Source:** Amazon Fine Food Reviews (568K reviews)
- **Cleaned:** 560,777 reviews with user profiles
- **Users:** 256,056 unique customers
- **Products:** 74,258 enriched with realistic names
- **User Segments:**
  - Cold: 208K (81.2%) - 0-2 reviews
  - Lukewarm: 24K (9.5%) - 3-4 reviews
  - Warm: 24K (9.2%) - 5+ reviews

---

## 🏗️ Architecture

```
BehaviorIQ/
├── agents/
│   ├── predictor_food.py          # Task A: Review Generator
│   ├── cold_start_handler.py      # Task B: Recommender
│   ├── orchestrator_food.py       # Unified API
│   └── observer.py                # User profiler
├── data/
│   ├── food_reviews.csv           # 560K reviews
│   ├── products_metadata.csv      # 74K products
│   └── config.py                  # Constants
├── app_food.py                    # Streamlit UI
├── requirements.txt               # Dependencies
├── Dockerfile                     # Container config
└── docker-compose.yml             # Multi-container
```

### Core Flow

```
User Input (user_id + product_id)
           ↓
    [Orchestrator]
           ↓
    ├─→ [Task A: Predictor]
    │   - Build user profile
    │   - Get product info
    │   - Call Claude API
    │   - Return: rating + review_text
    │
    └─→ [Task B: Recommender]
        - Infer categories
        - Compute scores
        - Rank products
        - Return: top 10 with reasons
```

---

## 🔧 API Usage

### Direct Python

```python
from agents.orchestrator_food import BehaviorIQOrchestrator

orch = BehaviorIQOrchestrator()

# Task A
review = orch.task_a_generate_review("user_00001", "prod_00001")
print(f"Rating: {review['rating']}/5")
print(f"Text: {review['review_text']}")

# Task B
recs = orch.task_b_get_recommendations("user_00001", n_recommendations=10)
for rec in recs['recommendations']:
    print(f"{rec['rank']}. {rec['product_name']} ({rec['category']})")
```

### Batch Processing

```python
# Task A: Multiple pairs
pairs = [("user_00001", "prod_00001"), ("user_00002", "prod_00002")]
results_a = orch.batch_task_a(pairs, verbose=True)

# Task B: Multiple users
users = ["user_00001", "user_00002", ...]
results_b = orch.batch_task_b(users, n_recommendations=10, verbose=True)
```

---

## 🎨 Streamlit UI

### Tab 1: Task A - Generate Review
- Input user_id and product_id
- View predicted rating (1-5 stars)
- See full review text with Nigerian expressions
- Check confidence score
- View detailed reasoning

### Tab 2: Task B - Get Recommendations
- Input user_id
- Select number of recommendations (5-20)
- View ranked product table
- Check scores and reasons
- Explore individual recommendation details

### Tab 3: About
- Project overview
- Task descriptions
- Dataset statistics
- Technical stack

---

## 🐳 Docker

```bash
# Build
docker-compose build

# Run
docker-compose up

# Access
open http://localhost:8501
```

---

## 📈 Key Innovations

### 1. Cold-Start Strategy
- **Problem:** 81% users have ≤4 reviews
- **Solution:** Category preference inference + hybrid scoring
- **Result:** Maintains NDCG@10 quality with sparse data

### 2. Nigerian Cultural Voice
- **Problem:** Generic AI reviews lack authenticity
- **Solution:** System prompt + expression injection + keywords
- **Result:** Culturally relevant, locally authentic reviews

### 3. Product Enrichment
- **Problem:** Amazon dataset lacks product names
- **Solution:** Type inference from review content → realistic names
- **Result:** 74K products with names like "Premium Dog Bites"

### 4. Hybrid Recommendations
- **Problem:** New users need balanced exploration/personalization
- **Solution:** 50% popularity + 50% category match scoring
- **Result:** Effective cold-start while maintaining relevance

---

## 📝 Configuration

### Environment Variables
```bash
ANTHROPIC_API_KEY=sk-ant-...     # Required
```

### data/config.py
```python
CLAUDE_MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 800
```

---

## 🔍 Module Reference

### predictor_food.py
- `build_user_profile(reviews)` - Extract behavior patterns
- `generate_review(profile, product, category)` - Claude generation
- `predict(user_id, product_id, reviews)` - Main API
- `PredictorAgent` - Wrapper class

### cold_start_handler.py
- `compute_popularity(interactions_df)` - Global scoring
- `recommend_new_user(products_df, n)` - Strategy for 0 reviews
- `recommend_cold_user(reviews, products_df, n)` - Strategy for 1-4 reviews
- `ColdStartHandler` - Main class

### orchestrator_food.py
- `task_a_generate_review(user_id, product_id)` - Task A API
- `task_b_get_recommendations(user_id, n)` - Task B API
- `batch_task_a(pairs, verbose)` - Batch Task A
- `batch_task_b(users, n, verbose)` - Batch Task B
- `BehaviorIQOrchestrator` - Main coordinator

---

## 📚 Evaluation

### Task A: ROUGE/BERTScore
1. Generate predictions for test set
2. Compare review_text with actual reviews
3. Compute ROUGE-L and BERTScore
4. Higher overlap = better score

### Task B: NDCG@10
1. Generate top 10 recommendations
2. Check ranking against actual reviews
3. Compute NDCG@10 metric
4. Higher ranking of true positives = better score

---

## ✅ Submission Status

- [x] Task A: Review generation working
- [x] Task B: Recommendations working
- [x] Nigerian contextualisation integrated
- [x] Cold-start handling implemented
- [x] Streamlit UI complete
- [x] Docker setup ready
- [x] Documentation complete
- [x] Batch processing for evaluation
- [x] All dependencies in requirements.txt

---

## 🐛 Troubleshooting

**"ModuleNotFoundError: No module named 'data'"**
→ Run from project root, activate venv

**"ANTHROPIC_API_KEY not found"**
→ `export ANTHROPIC_API_KEY="sk-ant-..."`

**"products_metadata.csv not found"**
→ Verify data/enrich_products.py ran successfully

**Port 8501 already in use**
→ `streamlit run app_food.py --server.port 8502`

---

**Last Updated:** May 24, 2026  
**Status:** Ready for Submission ✅
