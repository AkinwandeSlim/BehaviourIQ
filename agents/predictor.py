# agents/predictor.py
import anthropic
import json
import os
from dotenv import load_dotenv
from data.config import CLAUDE_MODEL, MAX_TOKENS

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are BehaviorIQ, a real-time personalisation engine for e-commerce.
Your job is to analyse raw shopping behaviour and identify exactly where a customer
is in their buying journey — using the language of conversion rate optimisation,
not AI jargon.

You now have access to:
- Department hierarchy (top-level categories like Fashion, Electronics, etc.)
- Shopping breadcrumbs (Department › Category › Subcategory) showing customer's
  exploration path across product hierarchies
- Buying stage signals that may differ PER DEPARTMENT (e.g., ready_to_buy in Fashion,
  awareness in Electronics)
- Cross-department patterns (e.g., Travel + Tech = packing for business trip)

Rules:
- Every signal you cite must come from the actual behaviour data provided
- Never use vague phrases like "user is exploring" or "product discovery"
- Always name the specific category, department, or item the signal relates to
- Buying stage must be exactly one of: awareness | consideration | ready_to_buy | repeat_buyer
  (Predict the OVERALL stage, but consider if department transitions suggest urgency)
- Use breadcrumb hierarchy to understand customer's journey depth (top-level dept
  vs specific subcategory = different intent levels)
- Detect cross-department patterns (Fashion + Electronics = complementary bundles?)
- Proactive message must feel written for THIS specific user, not a generic template
- You MUST respond in valid JSON only. No markdown, no explanation outside JSON."""


# ── Safe fallback if Claude returns malformed JSON ─────────────────────────
_FALLBACK = {
    "predicted_intent": "Customer is actively comparing products and moving toward a purchase decision",
    "buying_stage": "consideration",
    "confidence": 0.5,
    "conversion_triggers": [
        {
            "signal": "Multiple views across product categories detected",
            "interpretation": "Customer is in active comparison phase, not yet committed",
            "best_action": "Surface best-seller in their most-visited category with social proof"
        },
        {
            "signal": "Add-to-cart activity without completed transaction",
            "interpretation": "Price or trust barrier is preventing checkout",
            "best_action": "Show money-back guarantee or limited-time free shipping offer"
        },
        {
            "signal": "Return visits to same item detected",
            "interpretation": "Strong interest but hesitation — waiting for a trigger",
            "best_action": "Display low-stock alert or recent purchase count to create urgency"
        }
    ],
    "proactive_message": "You have great taste — here are the top picks based on what you have been browsing."
}


def predict_user_needs(observation: dict) -> dict:
    top_cats    = observation.get("top_product_categories", [])
    top_depts   = observation.get("top_departments", [])
    breadcrumbs = observation.get("breadcrumbs", [])
    conversion  = observation.get("conversion_rate", 0)
    abandoned   = observation.get("abandoned_items", [])
    purchased   = observation.get("purchased_items", [])

    # Format breadcrumbs for Claude
    breadcrumb_text = ""
    if breadcrumbs:
        breadcrumb_lines = []
        for bc in breadcrumbs:
            if bc and len(bc) > 0:
                breadcrumb_lines.append(f"  › {' › '.join(bc)}")
        breadcrumb_text = "\n".join(breadcrumb_lines)

    user_prompt = f"""
A customer has been active on our e-commerce platform.
Analyse their behaviour and identify where they are in their buying journey
and what will convert them right now.

── Behaviour Profile ──────────────────────────────────────────
{observation['profile_summary']}

── Shopping Journey (Department › Category › Subcategory) ────
{breadcrumb_text if breadcrumb_text else "  (N/A)"}

── Last 8 Actions (most recent last) ─────────────────────────
{json.dumps(observation['recent_actions'], indent=2)}

── Key Signals Summary ────────────────────────────────────────
Primary departments          : {', '.join(top_depts) if top_depts else "N/A"}
Primary interest categories  : {top_cats}
Overall conversion rate      : {conversion}%
Cart abandons (added but NOT purchased) : {abandoned}
Confirmed purchases          : {purchased}

── Department Analysis Tips ───────────────────────────────────
• If customer browses SINGLE department deeply → likely ready_to_buy in that dept
• If customer browses MULTIPLE departments → consider cross-dept bundling opportunity
• Cart abandons in one dept + views in another → friction in first dept?
• Weekend patterns + weekday patterns might differ by department

── Your Task ──────────────────────────────────────────────────
Based ONLY on the signals above, respond with this exact JSON.
Be specific — name actual categories and items from the data.
Think like a CRO specialist writing for an e-commerce dashboard:

{{
    "predicted_intent": "One clear sentence stating what this customer
                         is most likely about to buy and why — name the
                         specific category, department, or item, not vague intent",

    "buying_stage": "awareness | consideration | ready_to_buy | repeat_buyer",

    "confidence": 0.0,

    "conversion_triggers": [
        {{
            "signal": "Exact behaviour observed — e.g. viewed Electronics &
                       Gadgets #350689 four times across two days",
            "interpretation": "What this behaviour pattern reveals about
                               their purchase intent",
            "best_action": "The single most effective thing to show or say
                            to convert them right now"
        }},
        {{
            "signal": "...",
            "interpretation": "...",
            "best_action": "..."
        }},
        {{
            "signal": "...",
            "interpretation": "...",
            "best_action": "..."
        }}
    ],

    "proactive_message": "A natural, friendly message for this specific customer.
                          Reference their actual browsing behaviour. Max 20 words."
}}
"""

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}]
    )

    raw = response.content[0].text.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        result = json.loads(raw)

        # Validate buying_stage
        valid_stages = {"awareness", "consideration", "ready_to_buy", "repeat_buyer"}
        if result.get("buying_stage") not in valid_stages:
            result["buying_stage"] = "consideration"

        # Ensure confidence is a clean float
        try:
            result["confidence"] = round(float(result["confidence"]), 2)
        except (TypeError, ValueError):
            result["confidence"] = 0.5

        return result

    except json.JSONDecodeError:
        return _FALLBACK


# ── PredictorAgent class for app.py compatibility ──────────────
class PredictorAgent:
    """Wrapper class for prediction functionality"""
    
    def predict(self, observation: dict) -> dict:
        """Run prediction on observation"""
        return predict_user_needs(observation)