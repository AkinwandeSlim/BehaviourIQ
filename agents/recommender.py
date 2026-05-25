# agents/recommender.py
import anthropic
import json
import os
from dotenv import load_dotenv
from data.config import CLAUDE_MODEL, MAX_TOKENS, PRODUCTS_PATH
from memory.vector_store import (
    get_similar_users,
    collection,
    index_products,
    is_products_indexed,
    retrieve_relevant_products,
)

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Load catalogue
with open(PRODUCTS_PATH, "r", encoding="utf-8") as f:
    _ALL_PRODUCTS = json.load(f)

_BY_CATEGORY = {}
for p in _ALL_PRODUCTS:
    _BY_CATEGORY.setdefault(p.get("category", "other"), []).append(p)

if not is_products_indexed():
    index_products(_ALL_PRODUCTS)


# ── Strong System Prompt ─────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are BehaviorIQ's expert personalized recommendation engine.

You receive:
- Rich real user behavior profile from e-commerce events
- Department hierarchy & breadcrumbs showing customer's category exploration path
- Predicted intent and buying stage (may vary by department)
- Collaborative filtering signals (what similar users bought)
- Semantically relevant products from RAG

Task: Select exactly **4 best products** for this user right now.

Department-Aware Strategy:
- Prioritize primary department first (high urgency signals there)
- If customer shops 2+ departments → include 1 cross-department complementary item
  (e.g., Tech case for traveler's laptop, matching accessories for outfit)
- Match product breadcrumb depth to user's exploration depth
  (e.g., if user deeply explored Electronics › Laptops › Accessories,
   recommend from same breadcrumb level, not generic Electronics)
- Use collaborative signals to surface category pairs similar users bundle together

Strict Rules:
- ONLY use products from the provided list. Never invent items.
- Personalized reason MUST cite **specific** user signals (viewed items, abandoned carts,
  repeat views, categories, temporal patterns, departments).
- Use collaborative filtering when relevant ("Users like you also bought...").
- Vary categories — do not recommend 4 items from the same category unless urgency demands it.
- Prioritize urgency: abandoned carts > recent repeat views > general interest.
- match_score: 0.88–1.00 = excellent | 0.75–0.87 = strong | 0.60–0.74 = complementary.
- If cross-department recommendation, explicitly mention the bridge (e.g., "complements your
  Travel Accessories with practical tech").

Return ONLY valid JSON:
{
  "recommendations": [
    {
      "item_id": str,
      "item_name": str,
      "category": str,
      "price": number,
      "match_score": number,
      "personalized_reason": "2-3 sentences citing real user behavior + breadcrumb if relevant",
      "call_to_action": "Shop Now | Add to Cart | Learn More"
    }
  ]
}"""


def _get_collab_signal(user_id: str) -> str:
    similar_ids = get_similar_users(user_id, n=4)
    if not similar_ids:
        return "No strong collaborative signals available yet."

    signals = []
    for uid in similar_ids[:3]:
        try:
            result = collection.get(ids=[str(uid)], include=["documents"])
            if result and result.get("documents"):
                doc = result["documents"][0][:380]
                signals.append(f"Similar user {uid}: {doc}")
        except:
            continue
    return "\n".join(signals) if signals else "Limited collaborative data."


def _rag_retrieve(observation: dict, prediction: dict) -> list:
    intent = prediction.get("predicted_intent", "")
    top_cats = list(observation.get("top_cat_names", {}).keys())[:4]
    
    query = f"{intent} {' '.join(top_cats)}".strip()
    
    retrieved = retrieve_relevant_products(query, top_k=12, category_hint=" ".join(top_cats))

    if len(retrieved) >= 6:
        return retrieved

    # Smart fallback
    fallback = []
    for cat in top_cats:
        fallback.extend(_BY_CATEGORY.get(cat, [])[:4])
    
    return (retrieved + fallback)[:12]


def generate_recommendations(observation: dict, prediction: dict) -> list:
    user_id = observation.get("user_id")
    collab_signal = _get_collab_signal(user_id)
    rag_products = _rag_retrieve(observation, prediction)

    catalogue_for_claude = []
    for p in rag_products:
        catalogue_for_claude.append({
            "item_id": p.get("item_id") or p.get("id", ""),
            "name": p.get("name") or p.get("item_name", "Unknown"),
            "category": p.get("category", ""),
            "price": float(p.get("price", 49.99)),
            "description": p.get("description", "")[:220],
        })

    prompt = f"""User Profile:
{observation.get('profile_summary', 'No detailed profile')}

Predicted Intent: {prediction.get('predicted_intent', 'Not available')}
Buying Stage: {prediction.get('buying_stage', 'consideration')}

Shopping Breadcrumbs (Department › Category › Subcategory):
{json.dumps(observation.get('breadcrumbs', []), indent=2)}

Collaborative Filtering Signals:
{collab_signal}

Available Products (choose only from these):
{json.dumps(catalogue_for_claude, indent=2)}

Recommendation Strategy:
- Prioritize user's primary shopping departments/categories
- Include 1 cross-department complementary item if available (e.g., case for device, matching shoes)
- Match product specificity to user's breadcrumb depth
- Cite the breadcrumb or category path in the personalized_reason"""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            temperature=0.32,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.content[0].text.strip()

        if "```" in raw:
            raw = raw.split("```")[1].replace("json", "").strip()

        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1:
            raw = raw[start:end]

        data = json.loads(raw)
        recs = data.get("recommendations", [])[:4]

        cleaned = []
        for r in recs:
            cleaned.append({
                "item_id": str(r.get("item_id", "")),
                "item_name": str(r.get("item_name", r.get("name", "Product"))),
                "category": str(r.get("category", "")),
                "price": float(r.get("price", 49.99)),
                "match_score": round(float(r.get("match_score", 0.78)), 2),
                "personalized_reason": str(r.get("personalized_reason", "Strong match with your interests")),
                "call_to_action": str(r.get("call_to_action", "Shop Now")),
            })
        return cleaned

    except Exception as e:
        print(f"Recommender error: {e}")
        return _fallback_recommendations()


def _fallback_recommendations():
    """Diverse fallback"""
    recs = []
    cats = list(_BY_CATEGORY.keys())[:5]
    for cat in cats:
        if _BY_CATEGORY[cat]:
            p = _BY_CATEGORY[cat][0]
            recs.append({
                "item_id": p.get("item_id", ""),
                "item_name": p.get("name", "Product"),
                "category": cat,
                "price": p.get("price", 49.99),
                "match_score": 0.68,
                "personalized_reason": f"Popular choice in {cat}",
                "call_to_action": "Shop Now",
            })
    return recs[:4]





















# # agents/recommender.py
# import anthropic
# import json
# import os
# from dotenv import load_dotenv
# from data.config import CLAUDE_MODEL, MAX_TOKENS, PRODUCTS_PATH
# from memory.vector_store import (
#     get_similar_users,
#     collection,
#     index_products,
#     is_products_indexed,
#     retrieve_relevant_products,
# )

# load_dotenv()

# client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# # ── Load catalogue once ────────────────────────────────────────────────────────
# with open(PRODUCTS_PATH, "r", encoding="utf-8") as f:
#     _ALL_PRODUCTS = json.load(f)

# _BY_CATEGORY: dict = {}
# for p in _ALL_PRODUCTS:
#     _BY_CATEGORY.setdefault(p["category"], []).append(p)

# # ── Index products into RAG on startup (once per session) ──────────────────────
# if not is_products_indexed():
#     index_products(_ALL_PRODUCTS)


# # ── System prompt ──────────────────────────────────────────────────────────────
# SYSTEM_PROMPT = """You are BehaviorIQ's expert recommendation engine.

# You receive:
# 1. A detailed customer behaviour profile from real e-commerce data
# 2. Their predicted purchase intent and buying stage
# 3. Collaborative filtering signals (what similar users bought)
# 4. A shortlist of semantically relevant products (retrieved by RAG from your catalogue)

# Your job: select the 4 BEST matching products for this user RIGHT NOW.

# Rules:
# - Choose only from the provided product list — never invent items
# - Personalized reason MUST cite specific behaviour signals (named items they viewed, purchased, or abandoned)
# - Reference collaborative filtering when relevant: "Customers with your pattern also bought..."
# - Vary categories — avoid returning 4 items from the same category
# - match_score 0.85–1.0 = perfect signal match | 0.70–0.84 = strong | 0.50–0.69 = complementary
# - Prioritise urgency: cart abandons > repeat views > general interest

# Return ONLY valid JSON — no markdown, no explanation:
# {
#   "recommendations": [
#     {
#       "item_id": "string",
#       "item_name": "string",
#       "category": "string",
#       "price": number,
#       "match_score": number_between_0_and_1,
#       "personalized_reason": "2-3 sentences citing real behaviour signals",
#       "call_to_action": "Shop Now"
#     }
#   ]
# }"""


# # ── Collaborative filtering signal ─────────────────────────────────────────────
# def _get_collab_signal(user_id: str) -> str:
#     """Fetch similar users' profiles — robust truth check."""
#     similar_ids = get_similar_users(user_id, n=3)

#     if not similar_ids or len(similar_ids) == 0:
#         return "No similar user data available yet."

#     signals = []
#     for uid in similar_ids:
#         try:
#             result = collection.get(ids=[str(uid)], include=["documents"])
#             if result and result.get("documents") and len(result["documents"]) > 0:
#                 snippet = result["documents"][0][:300]
#                 signals.append(f"Similar user {uid}: {snippet}")
#         except Exception:
#             continue

#     return "\n".join(signals) if signals else "No similar user profiles found."


# # ── RAG retrieval ──────────────────────────────────────────────────────────────
# def _rag_retrieve(observation: dict, prediction: dict) -> list:
#     """
#     Build a rich query from the user profile + predicted intent,
#     then retrieve the most semantically relevant products from ChromaDB.
#     Falls back to category filtering if RAG returns nothing.
#     """
#     # Build query: intent + top category names (richer = better retrieval)
#     intent       = prediction.get("predicted_intent", "")
#     top_cats     = observation.get("top_product_categories", [])
#     profile_text = observation.get("profile_summary", "")

#     # Combine intent + top categories as the semantic query
#     cat_hint = " ".join(top_cats[:3]) if top_cats else ""
#     query    = f"{intent} {cat_hint}".strip() or profile_text[:300]

#     retrieved = retrieve_relevant_products(query, top_k=10, category_hint=cat_hint)

#     if retrieved:
#         print(f"✅ RAG: retrieved {len(retrieved)} products for Claude")
#         return retrieved

#     # Fallback: category-based filter
#     print("⚠️  RAG returned nothing — falling back to category filter")
#     return _category_fallback(top_cats)


# def _category_fallback(top_product_categories: list) -> list:
#     """Original category-based filter — kept as safety fallback."""
#     selected  = []
#     cats_used = set()

#     for cat in top_product_categories[:3]:
#         products = _BY_CATEGORY.get(cat, [])
#         if products:
#             selected.extend(products[:5])
#             cats_used.add(cat)

#     if len(cats_used) < 2:
#         for cat, products in _BY_CATEGORY.items():
#             if cat not in cats_used and products:
#                 selected.extend(products[:3])
#                 break

#     return selected if selected else _ALL_PRODUCTS


# # ── Fallback recommendations (no Claude) ───────────────────────────────────────
# def _fallback_recommendations() -> list:
#     recs = []
#     for cat, products in list(_BY_CATEGORY.items())[:4]:
#         if products:
#             p = products[0]
#             recs.append({
#                 "item_id":             p["item_id"],
#                 "item_name":           p["name"],
#                 "category":            p["category"],
#                 "price":               p["price"],
#                 "match_score":         0.5,
#                 "personalized_reason": "Popular item in this category",
#                 "call_to_action":      p.get("call_to_action", "Shop Now"),
#             })
#     return recs


# # ── Main entry point ───────────────────────────────────────────────────────────
# def generate_recommendations(observation: dict, prediction: dict) -> list:
#     user_id      = observation["user_id"]
#     buying_stage = prediction.get("buying_stage", "consideration")
#     intent       = prediction.get("predicted_intent", "")
#     triggers     = prediction.get("conversion_triggers", [])

#     # ── RAG retrieval (replaces _filter_catalogue) ─────────────────────────────
#     rag_products  = _rag_retrieve(observation, prediction)
#     collab_signal = _get_collab_signal(user_id)

#     # Serialise retrieved products for Claude
#     # RAG products may be dicts with rag_score — Claude doesn't need that field
#     catalogue_for_claude = []
#     for p in rag_products[:12]:   # cap at 12 to control token usage
#         catalogue_for_claude.append({
#             "item_id":        p.get("item_id",  p.get("item_id",  "")),
#             "name":           p.get("name",     p.get("item_name", "Unknown")),
#             "category":       p.get("category", ""),
#             "price":          p.get("price",    0.0),
#             "call_to_action": p.get("call_to_action", "Shop Now"),
#             # Include description if present (from original catalogue)
#             **({"description": p["description"]} if "description" in p else {}),
#         })

#     prompt = f"""Customer Profile:
# {observation.get('profile_summary', 'No profile available')}

# Predicted Intent: {intent}
# Buying Stage: {buying_stage}

# Collaborative Filtering Signal:
# {collab_signal}

# RAG-Retrieved Products (semantically matched to this user — choose only from these):
# {json.dumps(catalogue_for_claude, indent=2)}

# Select the 4 best products for this customer right now."""

#     try:
#         response = client.messages.create(
#             model=CLAUDE_MODEL,
#             max_tokens=MAX_TOKENS,
#             temperature=0.3,
#             system=SYSTEM_PROMPT,
#             messages=[{"role": "user", "content": prompt}]
#         )

#         raw_text = response.content[0].text.strip()

#         # Clean markdown fences
#         if "```" in raw_text:
#             raw_text = raw_text.split("```")[1]
#             if raw_text.startswith("json"):
#                 raw_text = raw_text[4:]
#             raw_text = raw_text.strip()

#         # Extract JSON block
#         if "{" in raw_text and "}" in raw_text:
#             start    = raw_text.find("{")
#             end      = raw_text.rfind("}") + 1
#             raw_text = raw_text[start:end]

#         data = json.loads(raw_text)
#         recs = data.get("recommendations", [])

#         cleaned = []
#         for r in recs[:4]:
#             cleaned.append({
#                 "item_id":             str(r.get("item_id", "")),
#                 "item_name":           str(r.get("item_name", "Unknown Product")),
#                 "category":            str(r.get("category", "")),
#                 "price":               float(r.get("price", 49.99)),
#                 "match_score":         round(float(r.get("match_score", 0.65)), 2),
#                 "personalized_reason": str(r.get("personalized_reason",
#                                                "Matches your recent browsing behaviour")),
#                 "call_to_action":      str(r.get("call_to_action", "Shop Now")),
#             })
#         return cleaned

#     except Exception as e:
#         print(f"Recommender error: {e}")
#         return _fallback_recommendations()