#!/usr/bin/env python3
"""Test predictor Claude call with detailed logging"""

from dotenv import load_dotenv
load_dotenv()

import os
import anthropic
import json
from data.config import CLAUDE_MODEL, MAX_TOKENS

print(f"Model: {CLAUDE_MODEL}")
print(f"Max Tokens: {MAX_TOKENS}\n")

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Simple system + user prompt
SYSTEM_PROMPT = """You are a food product reviewer from Nigeria. Generate authentic reviews."""

USER_PROMPT = """Generate a review for a rice product. Return ONLY this JSON:
{
    "rating": 4,
    "review_summary": "Good rice",
    "review_text": "This is good rice",
    "nigerian_markers": ["e do well"],
    "confidence": 0.9,
    "reasoning": "User likes rice"
}"""

print("Calling Claude with exact predictor setup...\n")

try:
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": USER_PROMPT}]
    )
    
    raw = response.content[0].text.strip()
    print(f"Raw response:\n{raw}\n")
    
    # Try to parse
    result = json.loads(raw)
    print(f"✅ Parsed successfully!")
    print(f"Rating: {result['rating']}")
    print(f"Confidence: {result['confidence']}")
    
except json.JSONDecodeError as e:
    print(f"❌ JSON error: {e}")
    print(f"Raw was: {raw}")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
