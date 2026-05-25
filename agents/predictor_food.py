# agents/predictor_food.py
"""
TASK A: Food Review Rating & Text Generation Agent

Given a user's past review behavior + a product, generates:
- Predicted rating (1-5)
- Nigerian-voice review text
- Review summary
- Confidence score
- Reasoning

Uses Claude API (primary) + Groq (backup) + Fallback template
Multi-API strategy for reliability
"""

import anthropic
import json
import os
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import config
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from data.config import CLAUDE_MODEL, MAX_TOKENS

# Initialize Claude client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Try to import Groq client
try:
    from groq import Groq
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
    GROQ_AVAILABLE = os.getenv("GROQ_API_KEY", "") != ""
except (ImportError, Exception):
    groq_client = None
    GROQ_AVAILABLE = False

# ── Load enriched product metadata ────────────────────────────────────────
data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
try:
    PRODUCTS_META = pd.read_csv(os.path.join(data_dir, "products_metadata.csv"))
    PRODUCT_MAP = dict(zip(PRODUCTS_META["product_id"], 
                           zip(PRODUCTS_META["product_name"], 
                               PRODUCTS_META["category"])))
except FileNotFoundError:
    PRODUCTS_META = None
    PRODUCT_MAP = {}
    print("⚠️  Warning: products_metadata.csv not found. Using fallback product names.")


def get_product_info(product_id: str) -> tuple:
    """Get enriched product name and category."""
    if product_id in PRODUCT_MAP:
        return PRODUCT_MAP[product_id]
    return (f"Food Product {product_id}", "General Food & Grocery")


SYSTEM_PROMPT = """You are a Nigerian e-commerce reviewer for food products.
Your task is to generate authentic product reviews that reflect a real person's
purchase experience, with genuine Nigerian English voice and cultural references.

Key guidelines:
1. Use natural Nigerian English expressions (but don't overuse them)
2. Reference daily Nigerian life context where relevant
   (NEPA/power issues for refrigerated items, market price comparisons,
    value-for-money mindset, familiar brands like Maggi, Indomie, Dangote)
3. Be authentic and conversational — sound like a real person, not AI
4. Rating must follow the customer's historical rating patterns provided
5. Review text should be 200-400 characters of genuine experience
6. Include specific details that show you actually used the product

Natural Nigerian expressions to weave in:
- "this one is correct" (good quality)
- "e do well" / "e do am well well" (it works well)
- "sharp sharp" (quickly/immediately)
- "abeg" (please/emphatic)
- "chai" (expression of surprise or frustration)
- "na wa o" (expression of surprise)
- "well well" (very much)
- "value for money no be here" (great value)

You MUST respond in valid JSON only. No markdown, no explanation outside JSON."""


# ── Safe fallback if Claude returns malformed response ─────────────────────
_FALLBACK = {
    "rating": 4,
    "review_summary": "Good product, works as expected",
    "review_text": (
        "This product does the job well. Sharp sharp delivery, "
        "e do well overall. No complaints so far. "
        "Abeg, the price is fair for the quality. "
        "Will definitely buy again."
    ),
    "confidence": 0.5,
    "reasoning": "Fallback response — Claude API error or JSON parse failure",
    "nigerian_markers": ["e do well", "sharp sharp", "abeg"]
}


def build_user_profile(user_reviews: list) -> dict:
    """
    Extract user behaviour patterns from review history.
    Called by observer_food.py and passed to generate_review().
    """
    if not user_reviews:
        return {
            "avg_rating":      3.0,
            "std_rating":      0.0,
            "pct_5star":       0.0,
            "pct_1star":       0.0,
            "pct_positive":    0.0,
            "review_count":    0,
            "preferred_rating": 3,
            "sample_texts":    [],
            "segment":         "cold",
        }

    ratings = [r.get("rating", 3) for r in user_reviews if "rating" in r]

    if not ratings:
        return {
            "avg_rating":      3.0,
            "std_rating":      0.0,
            "pct_5star":       0.0,
            "pct_1star":       0.0,
            "pct_positive":    0.0,
            "review_count":    len(user_reviews),
            "preferred_rating": 3,
            "sample_texts":    [r.get("review_text", "")[:100] for r in user_reviews[:3]],
            "segment":         "cold" if len(user_reviews) <= 2 else "lukewarm",
        }

    n    = len(ratings)
    mean = sum(ratings) / n
    variance = sum((r - mean) ** 2 for r in ratings) / n
    std  = variance ** 0.5

    count = len(user_reviews)
    if count <= 2:
        segment = "cold"
    elif count <= 4:
        segment = "lukewarm"
    else:
        segment = "warm"

    return {
        "avg_rating":      round(mean, 2),
        "std_rating":      round(std, 2),
        "pct_5star":       round(sum(1 for r in ratings if r == 5) / n, 2),
        "pct_1star":       round(sum(1 for r in ratings if r == 1) / n, 2),
        "pct_positive":    round(sum(1 for r in ratings if r >= 4) / n, 2),
        "review_count":    count,
        "preferred_rating": max(set(ratings), key=ratings.count),
        "sample_texts":    [r.get("review_text", "")[:120] for r in user_reviews[:3]],
        "segment":         segment,
    }


def generate_review(
    user_profile: dict,
    product_name: str,
    product_category: str = "General Food",
    product_description: str = "",
    max_attempts: int = 3,
) -> dict:
    """
    Generate predicted review using Claude with Nigerian voice.

    Args:
        user_profile     : output of build_user_profile()
        product_name     : human-readable product name
        product_category : food category string
        product_description: optional extra product context
        max_attempts     : retry count on JSON parse failure

    Returns dict with: rating, review_summary, review_text,
                       nigerian_markers, confidence, reasoning
    """
    sample_text = (
        user_profile["sample_texts"][0]
        if user_profile.get("sample_texts")
        else "No previous reviews available"
    )

    prod_context = f"\nDescription: {product_description}" if product_description else ""

    user_prompt = f"""Generate a food product review for this Nigerian customer.

── Customer Profile ──────────────────────────────────────────
Segment          : {user_profile.get('segment', 'warm').upper()} user
Average rating   : {user_profile['avg_rating']}/5
Rating std dev   : {user_profile['std_rating']} (0=consistent, 2=variable)
Gives 5★         : {user_profile['pct_5star']*100:.0f}% of the time
Gives 1★         : {user_profile['pct_1star']*100:.0f}% of the time
Positive reviews : {user_profile['pct_positive']*100:.0f}%
Total reviews    : {user_profile['review_count']}
Preferred rating : {user_profile['preferred_rating']}★
Sample writing   : "{sample_text}"

── Product to Review ─────────────────────────────────────────
Name             : {product_name}
Category         : {product_category}{prod_context}

── Your Task ─────────────────────────────────────────────────
Generate an authentic Nigerian-voice review matching this customer's behaviour.

IMPORTANT:
- Rating MUST be close to their avg_rating ({user_profile['avg_rating']})
- If they are a harsh rater (avg < 3), generate a critical review
- If they are generous (avg > 4.5), generate an enthusiastic review
- Match their writing style from the sample text above

Respond with ONLY this exact JSON (no markdown, no extra text):
{{
    "rating": <1-5 integer matching customer's avg pattern>,
    "review_summary": "<10-20 word title for the review>",
    "review_text": "<200-400 character authentic Nigerian review>",
    "nigerian_markers": ["expression1", "expression2"],
    "confidence": <0.5-1.0 float>,
    "reasoning": "<one sentence: why this rating based on customer profile>"
}}"""

    for attempt in range(max_attempts):
        try:
            # TRY CLAUDE FIRST (PRIMARY)
            try:
                response = client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=MAX_TOKENS,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                raw = response.content[0].text.strip()
                source = "Claude"
                
            except Exception as claude_error:
                # CLAUDE FAILED - TRY GROQ (BACKUP)
                if GROQ_AVAILABLE:
                    try:
                        response = groq_client.chat.completions.create(
                            model="mixtral-8x7b-32768",
                            max_tokens=800,
                            messages=[
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": user_prompt}
                            ]
                        )
                        raw = response.choices[0].message.content.strip()
                        source = "Groq"
                    except Exception as groq_error:
                        # GROQ FAILED - USE FALLBACK
                        print(f"[PREDICTOR] Claude failed: {type(claude_error).__name__}")
                        print(f"[PREDICTOR] Groq failed: {type(groq_error).__name__}")
                        print(f"[PREDICTOR] Using fallback response")
                        return _FALLBACK
                else:
                    # GROQ NOT AVAILABLE - USE FALLBACK
                    print(f"[PREDICTOR] Claude failed: {type(claude_error).__name__}")
                    print(f"[PREDICTOR] Groq not configured - using fallback response")
                    return _FALLBACK

            # Strip markdown fence if present (proven pattern)
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:].lstrip()
                raw = raw.split("```")[0].strip()

            result = json.loads(raw)

            # Ensure all required keys exist with proper types
            result.setdefault("rating",          4)
            result.setdefault("review_summary",  "Good product")
            result.setdefault("review_text",     _FALLBACK["review_text"])
            result.setdefault("nigerian_markers", [])
            result.setdefault("confidence",      0.7)
            result.setdefault("reasoning",       "")

            # Validate rating is 1-5
            result["rating"] = max(1, min(5, int(result.get("rating", 4))))

            # Mark confidence higher if successfully called API
            if result.get("confidence", 0) < 0.7:
                result["confidence"] = 0.75 if source == "Claude" else 0.72

            return result

        except json.JSONDecodeError as e:
            if attempt == max_attempts - 1:
                print(f"[PREDICTOR] JSON decode error on attempt {attempt+1}: {str(e)[:100]}")
            continue
        except Exception as e:
            if attempt == max_attempts - 1:
                print(f"[PREDICTOR] Exception on attempt {attempt+1}: {type(e).__name__}: {str(e)[:100]}")
            continue

    return _FALLBACK


def predict(user_id: str, product_id: str, user_reviews: list) -> dict:
    """
    Task A API: Generate rating + review for a user-product pair.
    
    Args:
        user_id       : user identifier (for logging)
        product_id    : food product identifier
        user_reviews  : list of user's past reviews with 'rating' and 'review_text'
    
    Returns:
        dict with: rating, review_summary, review_text, nigerian_markers, confidence, reasoning
    """
    # Build user profile from review history
    profile = build_user_profile(user_reviews)
    
    # Get enriched product info (real name + category from metadata)
    product_name, product_category = get_product_info(product_id)
    
    # Generate review with enriched product context
    return generate_review(profile, product_name, product_category)


class PredictorAgent:
    """Wrapper class for app.py compatibility and orchestration."""
    
    def predict(self, user_id: str, product_id: str, user_reviews: list) -> dict:
        """Generate review for user + product."""
        return predict(user_id, product_id, user_reviews)
    
    def build_profile(self, user_reviews: list) -> dict:
        """Expose profile builder for orchestrators."""
        return build_user_profile(user_reviews)
