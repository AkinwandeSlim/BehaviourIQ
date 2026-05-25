#!/usr/bin/env python3
"""Direct test of Claude API connection"""

from dotenv import load_dotenv
load_dotenv()

import os
import anthropic

print("=" * 60)
print("CLAUDE API CONNECTION TEST")
print("=" * 60)

# Check API key
api_key = os.getenv("ANTHROPIC_API_KEY")
print(f"\n1. API Key loaded: {'Yes' if api_key else 'No'}")
if api_key:
    print(f"   Key preview: {api_key[:20]}...{api_key[-10:]}")

# Try to create client
print(f"\n2. Creating Anthropic client...")
try:
    client = anthropic.Anthropic(api_key=api_key)
    print(f"   ✅ Client created successfully")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    exit(1)

# Try to call API
print(f"\n3. Calling Claude API...")
try:
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=100,
        messages=[{"role": "user", "content": "Say 'Hello' in one word"}]
    )
    print(f"   ✅ API call successful!")
    print(f"   Response: {response.content[0].text}")
except anthropic.APIError as e:
    print(f"   ❌ API Error: {e}")
    print(f"   Status: {e.status_code if hasattr(e, 'status_code') else 'N/A'}")
except Exception as e:
    print(f"   ❌ Error: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
