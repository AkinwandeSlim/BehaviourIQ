#!/usr/bin/env python3
"""Test available Claude models"""

from dotenv import load_dotenv
load_dotenv()

import os
import anthropic

print("Testing different Claude model names...\n")

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Test various model names
models_to_test = [
    "claude-3-5-sonnet-20241022",
    "claude-sonnet-4-5",
    "claude-3-5-sonnet",
    "claude-3-sonnet-20240229",
    "claude-3-opus-20240229",
]

for model_name in models_to_test:
    try:
        print(f"Testing: {model_name}...", end=" ")
        response = client.messages.create(
            model=model_name,
            max_tokens=50,
            messages=[{"role": "user", "content": "Say OK"}]
        )
        print("✅ Works!")
        print(f"  Response: {response.content[0].text}\n")
        break
    except anthropic.NotFoundError:
        print("❌ Model not found")
    except anthropic.APIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}")
