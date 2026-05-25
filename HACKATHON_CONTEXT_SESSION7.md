# DSN X BCT LLM Agent Challenge — Project Context Document
> Paste this at the start of any new Claude session to resume instantly.
> Last updated: 2026-05-24 (Session 7 — Data prep complete, predictor_food.py validated)

---

## COMPETITION OVERVIEW
- **Hackathon:** DSN X BCT LLM Agent Challenge (Hackathon 3.0)
- **Prize:** ₦1,500,000 first place
- **Deadline:** 24 May 2026 midnight
- **Submission:** Three deliverables — (1) containerised app link, (2) solution paper 4-8 pages, (3) GitHub repo

## TWO REQUIRED TASKS
### Task A — User Modeling
- Input: user persona + product details
- Output: predicted star rating (1-5) + written review text
- Evaluated on: ROUGE/BERTScore, RMSE, behavioural fidelity, solution paper, code reproducibility
- **Bonus marks** for Nigerian contextualisation

### Task B — Recommendation
- Input: user persona alone
- Output: ranked personalised recommendations
- Evaluated on: NDCG@10/Hit Rate (30pts), Cold-Start & Cross-Domain (25pts), Contextual Relevance human eval (20pts), Solution Paper (15pts), Code Reproducibility (10pts)
- Must handle: cold-start users, cross-domain, multiturn scenarios

---

## PROJECT: BehaviorIQ V2
**Path:** `C:\MyFiles\DOCUMENT-2026\2026\May2026\behavioriq_V2`
**Virtual env:** `venv\Scripts\activate`

### Developer Profile
- OS: Windows 11 Pro, HP EliteBook 1050 G1, Intel i7-8850H, 32GB RAM
- Python 3.14 at C:\Python314
- Experienced: Python, Streamlit, Kafka, Flink, real-time ML, concept drift detection

---

## DATASET — Amazon Fine Food Reviews ✅ COMPLETE

### Raw Dataset
- Source: Kaggle `amazon-fine-food-reviews/Reviews.csv`
- Shape: 568,454 rows × 10 columns
- Columns: Id, ProductId, UserId, ProfileName, HelpfulnessNumerator, HelpfulnessDenominator, Score, Time, Summary, Text

### Processed Dataset — `data/food_reviews.csv` ✅
- Shape: 560,777 rows × 16 columns
- All validation checks passed
- Columns:
  ```
  user_id, product_id, rating, review_text, review_summary, date,
  helpfulness_ratio, review_count, avg_rating_given, std_rating_given,
  pct_5star, pct_1star, pct_positive, preferred_rating,
  avg_helpfulness, segment
  ```

### Three User Segments (NO artificial cap — all users included)
| Segment | Reviews | Users | Purpose |
|---------|---------|-------|---------|
| cold | 1-2 reviews | 208,047 | Cold-start demonstration (25pts) |
| lukewarm | 3-4 reviews | 24,417 | Cross-domain demonstration |
| warm | 5+ reviews | 23,592 | Full personalisation |

### Product Metadata — `data/products_metadata.csv` ✅
- Shape: 74,258 rows × 7 columns
- Columns: product_id, product_type, category, review_count, avg_rating, pct_5star, product_name
- Sample: prod_71171 → "Cookie Pack" (Snacks & Confectionery)
- Sample: prod_46206 → "Pure White Rice" (Grains & Staples)

### PENDING VALIDATION
```powershell
# Run this to confirm product ID format matches between files
python -c "
import pandas as pd
reviews = pd.read_csv('data/food_reviews.csv', nrows=5)
meta = pd.read_csv('data/products_metadata.csv')
print('Review product_ids:', reviews['product_id'].tolist())
print('Metadata product_ids:', meta['product_id'].head(5).tolist())
print('Match test:', reviews['product_id'].iloc[0] in meta['product_id'].values)
"
```
Paste this output at start of next session to confirm ID alignment.

---

## ARCHITECTURE

```
Amazon Fine Food Reviews (560K reviews)
        │
        ▼
agents/observer_food.py          ← NEXT TO BUILD
  Reads user review history
  Builds taste profile + segments
  Stores embedding in ChromaDB
        │
        ├──────────────────────────────────────────┐
        ▼                                          ▼
agents/predictor_food.py         agents/recommender_food.py
  TASK A: Review Generator         TASK B: Personalised Recs
  Claude + Nigerian voice          Claude + RAG + collab filtering
        │                                          │
        │                          agents/cold_start_handler.py
        │                            cold/lukewarm users
        │                                          │
        └──────────────┬───────────────────────────┘
                       ▼
        agents/orchestrator_food.py   ← TO BUILD
          LangGraph pipeline
                       │
                       ▼
        app.py (Streamlit)
          Tab 1: Review Generator (Task A)
          Tab 2: Recommendations (Task B)
          Tab 3: User Profile Viewer
                       │
                       ▼
        Docker Compose (reused from BehaviorIQ V1)
```

---

## FILES STATUS

### ✅ Complete & Validated
| File | Status | Notes |
|------|--------|-------|
| `data/food_reviews.csv` | ✅ | 560,777 rows, all checks passed |
| `data/products_metadata.csv` | ✅ | 74,258 products, 7 columns |
| `agents/predictor_food.py` | ✅ | Task A review generator, Nigerian voice |
| `docker-compose.yml` | ✅ | Reused from V1 — Kafka KRaft + app + producer |
| `Dockerfile` | ✅ | Reused from V1 |
| `data/kafka_producer.py` | ✅ | Reused from V1 |
| `data/config.py` | ✅ | CLAUDE_MODEL, MAX_TOKENS, paths |

### ❌ Still To Build (in priority order)
| File | Priority | Est. Time | Purpose |
|------|----------|-----------|---------|
| `agents/observer_food.py` | 🔴 NEXT | 45 mins | Reads CSV, builds user profile |
| `agents/cold_start_handler.py` | 🔴 HIGH | 30 mins | 25pts cold-start criterion |
| `agents/recommender_food.py` | 🔴 HIGH | 45 mins | Task B recommendations |
| `agents/orchestrator_food.py` | 🟡 MED | 20 mins | LangGraph pipeline |
| `app.py` (new version) | 🟡 MED | 60 mins | Two-tab UI for both tasks |
| `solution_paper.pdf` | 🔴 HIGH | 90 mins | Judges read this FIRST |
| `README.md` | 🟡 MED | 30 mins | 10pts code reproducibility |

---

## predictor_food.py — VALIDATED ✅

### Key functions
```python
build_user_profile(user_reviews: list) -> dict
# Extracts: avg_rating, std_rating, pct_5star, pct_1star,
#           pct_positive, review_count, preferred_rating,
#           sample_texts, segment

generate_review(user_profile, product_name, product_category,
                product_description, max_attempts=3) -> dict
# Returns: rating, review_summary, review_text,
#          nigerian_markers, confidence, reasoning

class PredictorAgent:
    def predict(user_reviews, product_name, product_category, product_description) -> dict
```

### Nigerian system prompt — key expressions
```
"this one is correct" / "e do well" / "sharp sharp" /
"abeg" / "chai" / "na wa o" / "well well" /
"value for money no be here"
```

### IMPORTANT — Add PredictorAgent class at bottom if missing
```python
class PredictorAgent:
    def predict(self, user_reviews, product_name,
                product_category="General Food",
                product_description="") -> dict:
        profile = build_user_profile(user_reviews)
        return generate_review(profile, product_name,
                               product_category, product_description)
```

---

## NEXT IMMEDIATE STEP — observer_food.py

### What it must do
1. Load `data/food_reviews.csv`
2. For a given `user_id`, fetch all their reviews
3. Build a structured observation dict:
```python
{
    "user_id": str,
    "segment": "cold" | "lukewarm" | "warm",
    "review_count": int,
    "avg_rating_given": float,
    "std_rating_given": float,
    "pct_5star": float,
    "pct_1star": float,
    "pct_positive": float,
    "preferred_rating": int,
    "top_categories": list,          # most reviewed categories
    "recent_reviews": list,          # last 5 reviews with product+rating+text
    "purchased_products": list,      # product_ids already reviewed
    "taste_profile_text": str,       # rich text for Claude + ChromaDB embedding
    "helpfulness_avg": float,        # quality of their reviews
}
```
4. Store embedding in ChromaDB (`user_profiles` collection)
5. Return observation dict to orchestrator

### Key design decisions
- Load CSV once at class init (not on every observe() call)
- Cast numeric columns to Python native types (avoid numpy int64 → json crash)
- Handle missing users gracefully with ValueError
- `taste_profile_text` is the text sent to Claude — make it rich and specific

---

## COLD-START HANDLER — cold_start_handler.py

### What it must do
When `segment == "cold"` or `segment == "lukewarm"`:

**Cold (1-2 reviews):**
- Return top-10 most reviewed products globally (popularity baseline)
- Label explicitly as "Cold-start mode" in UI
- Include one category inference if possible from their 1-2 reviews

**Lukewarm (3-4 reviews):**
- Hybrid: 50% popularity + 50% category-based from their small history
- Label as "Limited history mode" in UI
- Cross-domain: if they reviewed "Snacks", also recommend from "Beverages"

**Warm (5+ reviews):**
- Full personalisation via recommender_food.py + ChromaDB collab filtering

### Precomputed popularity list needed
```python
# In observer_food.py or config — precompute at startup
top_products = df.groupby("product_id").agg(
    review_count=("rating","count"),
    avg_rating=("rating","mean")
).sort_values("review_count", ascending=False).head(100)
```

---

## SCORING STRATEGY

### Task B points breakdown
| Criterion | Points | How we address it |
|-----------|--------|-------------------|
| Ranking quality NDCG@10 | 30 | ChromaDB similarity + Claude ranking |
| Cold-start & cross-domain | 25 | cold_start_handler.py — explicit 3-mode system |
| Contextual relevance human eval | 20 | Nigerian voice + behaviour-grounded reasons |
| Solution paper | 15 | Write last, professionally |
| Code reproducibility | 10 | README + docker compose up = one command |

### Nigerian contextualisation bonus
- Food products map naturally to Nigerian daily life
- Every review references: market prices, power (NEPA), familiar brands
- Cross-category recommendations use Nigerian meal context
  (spices → rice → palm oil → pepper soup seasoning)

---

## REUSED FROM BehaviorIQ V1 (do not rebuild)
- `docker-compose.yml` — Kafka KRaft + app service + producer profile
- `Dockerfile` — multi-stage Python build with model pre-caching
- `data/kafka_producer.py` — event replay with configurable delay
- `data/live_stream.py` — background thread for simulated streaming
- `memory/vector_store.py` — ChromaDB wrapper with `build_user_profile_v2()`
- `data/config.py` — CLAUDE_MODEL = "claude-sonnet-4-5", MAX_TOKENS = 800

---

## CRITICAL FACTS (do not change)
- **Model:** `claude-sonnet-4-5` — from `data/config.py` as `CLAUDE_MODEL`
- **MAX_TOKENS:** 800 — from `data/config.py`
- **ChromaDB:** absolute paths only, collection = `user_profiles`
- **`.env`:** UTF-8 via PowerShell `Out-File -Encoding utf8`
- **JSON parsing:** always strip ```json fences before json.loads()
- **numpy types:** always cast to Python native before json.dumps()
- **food_reviews.csv:** 560,777 rows — never modify this file

---

## HOW TO RUN
```powershell
cd C:\MyFiles\DOCUMENT-2026\2026\May2026\behavioriq_V2
venv\Scripts\activate
streamlit run app.py          # local dev

# OR with Docker (full stack)
docker compose up --build
# Open: http://localhost:8501
```

---

## SOLUTION PAPER OUTLINE (write after code is done)
1. **Abstract** (100 words) — two-task agent, Amazon food reviews, Nigerian context
2. **Architecture** (1 page) — diagram + component description
3. **Task A — User Modeling** (1 page) — profile extraction, Nigerian prompt design, rating prediction approach
4. **Task B — Recommendation** (1 page) — three-mode system (cold/lukewarm/warm), NDCG approach, collab filtering
5. **Nigerian Contextualisation** (half page) — cultural signal design, expressions used, food category mapping
6. **Ablation Studies** (half page) — with vs without Nigerian context, with vs without collab filtering
7. **Results & Evaluation** (half page) — sample outputs, RMSE estimate, qualitative examples
8. **Future Work** (quarter page) — Kafka real-time, concept drift, multiturn conversation

---

## USEFUL COMMANDS
```powershell
# Activate venv
venv\Scripts\activate

# Check data files
dir data\

# Verify product ID alignment (PENDING)
python -c "
import pandas as pd
reviews = pd.read_csv('data/food_reviews.csv', nrows=5)
meta = pd.read_csv('data/products_metadata.csv')
print('Review IDs:', reviews['product_id'].tolist())
print('Meta IDs:', meta['product_id'].head(5).tolist())
print('Match:', reviews['product_id'].iloc[0] in meta['product_id'].values)
"

# Clear ChromaDB (after major changes)
rmdir /s /q chroma_db

# Install dependencies
pip install langchain langchain-anthropic langgraph chromadb sentence-transformers streamlit anthropic pandas plotly python-dotenv kafka-python streamlit-autorefresh
```