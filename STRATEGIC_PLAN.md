# HACKATHON STRATEGIC PLAN - Professional Architecture Review

## 1. REQUIREMENTS VALIDATION

### Task A: User Modeling (Review Generator)
**Requirement:**
- Input: User persona + product details
- Output: Generated star rating (1-5) + written review text
- Evaluation: ROUGE/BERTScore + RMSE + behavioural fidelity

**Current Status:** ❌ MISSING ENTIRELY (Critical Gap)

**What This Means:**
- Must generate realistic reviews based on user purchase history
- Ratings must follow user's historical rating patterns
- Text must sound authentic to user's voice & behaviour
- Nigerian context bonus: Reviews should reflect Nigerian consumer perspective

---

### Task B: Personalized Recommendations
**Requirement:**
- Input: User persona alone (no product specified)
- Output: Ranked list of recommended products
- Handle: Cold-start users, cross-domain recommendations, multi-turn context
- Evaluation: NDCG@10 + Hit Rate + Contextual Relevance (human eval)

**Current Status:** ✅ PARTIAL (BehaviorIQ covers this but missing cold-start)

**What This Means:**
- Recommendations from user behaviour patterns ← BehaviorIQ does this
- Cold-start handling (NEW users with no history) ← **We must add this**
- Cross-domain (recommend products from different categories) ← Needs validation
- Multi-turn (remembers conversation context across requests) ← Needs validation

---

### Dataset Requirements
**Specified in Brief:**
- ✅ Yelp OR Amazon Reviews OR Goodreads
- ✅ Amazon Fine Food Reviews (SELECTED) - Perfect for Nigerian context

**Schema Fit:**
```
✅ UserId, ProductId, Rating (1-5), Review Text, Timestamp
✅ 568K reviews, 256K users, 74K products
✅ Food is high cultural resonance for Nigerian localisation
```

---

### Bonus Points: Nigerian Contextualisation
**What This Requires:**
- Reviews in Nigerian English voice
- Nigerian product references (Maggi, Indomie, palm oil, pepper soup, etc.)
- Nigerian mindset (value-for-money, NEPA power concerns, naira pricing)
- Natural Nigerian expressions ("this thing sweet well well", "na so", "e go do")

---

## 2. ARCHITECTURE BLUEPRINT

### System Components (High-Level)

```
┌─────────────────────────────────────────────────────┐
│         HACKATHON SUBMISSION SYSTEM                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  FRONTEND (Streamlit UI)                            │
│  ├─ Tab 1: Review Generator (Task A)                │
│  ├─ Tab 2: Recommendations (Task B)                 │
│  └─ Tab 3: User Profile Viewer                      │
│                                                     │
│  BACKEND (Agents)                                   │
│  ├─ observer_food.py          [Data Ingestion]     │
│  │  └─ Builds user food taste profiles from history│
│  ├─ predictor_food.py         [Task A]             │
│  │  └─ Claude generates Nigerian-voice reviews     │
│  ├─ recommender_food.py       [Task B]             │
│  │  └─ Personalised recommendations                │
│  ├─ cold_start_handler.py     [Task B - Cold-start]│
│  │  └─ Handles users with <5 reviews              │
│  └─ orchestrator_food.py      [LangGraph Pipeline] │
│     └─ Chains all agents together                   │
│                                                     │
│  DATA LAYER                                         │
│  ├─ data/food_reviews_processed.csv                 │
│  ├─ chroma_db/ (vector embeddings of reviews)      │
│  └─ data/products_food.json (product metadata)     │
│                                                     │
│  DEPLOYMENT                                         │
│  ├─ Docker containerised app                        │
│  ├─ Environment: Python 3.10, Claude API            │
│  └─ Startup: `docker-compose up`                   │
└─────────────────────────────────────────────────────┘
```

---

## 3. DETAILED TASK BREAKDOWN

### TASK A: Review Generator
**File:** `agents/predictor_food.py`

**Input:**
```python
user_profile = {
    "user_id": "A3SGXH7AUHU8GW",
    "avg_rating": 4.2,
    "rating_std": 0.8,
    "purchase_history": [
        {"product": "Dog Food", "rating": 5, "summary": "Good Quality"},
        {"product": "Peanut Spread", "rating": 1, "summary": "Not as Advertised"}
    ],
    "preferences": "Prefers premium pet foods"
}

product_details = {
    "product_id": "B00ABC123XYZ",
    "name": "Premium Spiced Rice Mix",
    "category": "Food & Pantry",
    "price": 12.99,
    "description": "Nigerian-inspired seasoned rice blend"
}
```

**Processing:**
1. Extract user's rating distribution (mean, std, min, max ratings)
2. Analyze user's review language patterns (word choice, sentiment intensity)
3. Prompt Claude with Nigerian context system prompt
4. Generate rating based on user's historical patterns + product category fit
5. Generate review text in user's voice + Nigerian English

**Output:**
```python
{
    "rating": 4,  # Within user's typical range
    "review_text": "This one is correct! The spices blend well well. Good value for money compared to Maggi. E go do the work for my family jollof rice. Only small thing - packaging could be better but product quality is sharp sharp.",
    "confidence": 0.87,
    "reasoning": "Rating 4 aligns with user's avg 4.2; text reflects Nigerian voice; product quality matches stated preferences"
}
```

**Evaluation Metrics:**
- ROUGE/BERTScore: How similar is generated review to typical reviews for same product?
- RMSE: Does predicted rating fall within user's historical rating distribution?
- Behavioural Fidelity: Does the review sound like THIS user would write it?

---

### TASK B: Recommendations
**File:** `agents/recommender_food.py` + `agents/cold_start_handler.py`

**Standard Scenario (User has history):**
```python
user_profile = {
    "user_id": "A3SGXH7AUHU8GW",
    "purchase_history": [...25 past reviews...],
    "taste_vector": [vector embedding],
    "preferred_categories": ["Spices", "Grains", "Sauces"],
    "budget_range": (8, 25),
}

# Output: Top 10 recommendations ranked by NDCG@10 score
recommendations = [
    {"rank": 1, "product_id": "B00XYZ789", "name": "...", "score": 0.92, "reason": "Similar to products you rated 5"},
    {"rank": 2, "product_id": "B00ABC456", "name": "...", "score": 0.88, "reason": "New Nigerian brand in your preferred category"},
    ...
]
```

**Cold-Start Scenario (NEW user, <5 reviews):**
```python
# Strategy: Use population-level statistics + minimal user signals
recommendations = [
    {"rank": 1, "product_id": "B00POPULAR01", "reason": "Most-reviewed food product overall", "score": 0.76},
    {"rank": 2, "product_id": "B00TRENDING01", "reason": "Trending in Food category this week", "score": 0.74},
    {"rank": 3, "product_id": "B00NIGERIAN01", "reason": "Popular Nigerian food product", "score": 0.72},
    ...
]
```

**Evaluation Metrics:**
- NDCG@10: Ranking quality (are relevant products ranked higher?)
- Hit Rate: % of recommendations that user interacts with (proxy metric)
- Contextual Relevance: Human judges assess "Does this rec make sense?"

---

## 4. CRITICAL SUCCESS FACTORS

### Gap Analysis

| Component | Status | Risk | Action |
|-----------|--------|------|--------|
| Task A: Review Generation | ❌ Missing | **CRITICAL** | Build predictor_food.py (45 mins) |
| Task B: Base Recommendations | ✅ Have it | None | Adapt from BehaviorIQ |
| Cold-Start Handler | ❌ Missing | **HIGH** (25pts!) | Build cold_start_handler.py (30 mins) |
| Nigerian Localisation | ⚠️ Partial | Medium | System prompts + examples (15 mins) |
| Solution Paper | ❌ Missing | **HIGH** (15pts!) | Write professionally (60 mins) |
| README + Reproducibility | ❌ Missing | Medium (10pts) | Document setup (20 mins) |

---

## 5. DATA PREP REQUIREMENTS

### Processing Pipeline

**Input:** `Amazon_Fine_Food_Reviews.csv` (568K rows)

**Processing Steps:**
1. Load raw CSV
2. Remove duplicates, null values, invalid ratings
3. Group by UserId → build user profiles
4. Sample 50K reviews for demo (avoid timeout in Streamlit)
5. Create product metadata JSON
6. Embed reviews in ChromaDB for similarity search
7. Save processed data to `data/food_reviews_processed.csv`

**Output:** Ready-to-use dataset for all three agents

---

## 6. TIMELINE & PRIORITY

### Hour 1: Data Prep ⏱️
- [ ] Load Amazon Food Reviews CSV
- [ ] Clean & validate (target: 50K reviews for demo)
- [ ] Create products_food.json
- [ ] Embed in ChromaDB

### Hour 2: Task A - Review Generator ⏱️
- [ ] Build `predictor_food.py` with Claude integration
- [ ] System prompt with Nigerian context
- [ ] Generate rating + review text
- [ ] Add to Streamlit UI (new tab)

### Hour 3: Task B - Cold-Start Handler ⏱️
- [ ] Build `cold_start_handler.py`
- [ ] Popularity-based fallback
- [ ] Category-based inference
- [ ] Integrate with recommender

### Hours 4-5: Solution Paper ⏱️
- [ ] Document architecture
- [ ] Explain Nigerian contextualisation strategy
- [ ] Results & evaluation approach
- [ ] Professional polish

### Hours 5-6: README + Testing ⏱️
- [ ] Docker setup validation
- [ ] README with reproduction steps
- [ ] Final submission package

---

## 7. VALIDATION QUESTIONS FOR YOU

### Before we proceed, please answer:

1. **Data Scope:** Should we use full 568K reviews or subsample to 50K for faster demo?
   - Option A: 50K (faster, but judges might request full dataset)
   - Option B: 568K (comprehensive, but Streamlit might be slow)

2. **Cold-Start Strategy:** For users with <5 reviews, which approach?
   - Option A: Pure popularity-based (highest-rated products)
   - Option B: Hybrid (popularity + category inference from tiny sample)

3. **Nigerian Localisation Scope:** How aggressive?
   - Option A: Light (Nigerian expressions in reviews only)
   - Option B: Full (Food references, pricing mindset, cultural context everywhere)

4. **Architecture:** Keep BehaviorIQ agents or rebuild from scratch?
   - Option A: Adapt existing orchestrator.py, predictor.py, recommender.py
   - Option B: Fresh build (cleaner but riskier in time)

---

## 8. SUCCESS CRITERIA

**Minimum Viable Submission (No Disqualification):**
- ✅ Task A working (reviews generate successfully)
- ✅ Task B working (recommendations output correctly)
- ✅ Both containerised in Docker
- ✅ One solution paper submitted

**Winning Submission (Competitive Points):**
- ✅ Task A: Nigerian-voice reviews that judges find authentic
- ✅ Task B: Cold-start handling explicitly documented & working
- ✅ NDCG@10 > 0.7 (estimated from similar systems)
- ✅ Solution paper with clear methodology
- ✅ README that judges can run in 2 commands

---

## SIGN-OFF

**This plan requires your validation before any code changes.**

Please confirm:
1. ✅ Approach is sound?
2. ✅ Architecture makes sense?
3. ✅ Priorities are correct?
4. ✅ Ready to proceed with implementation?

Once approved, I will execute this plan systematically, one task at a time.
