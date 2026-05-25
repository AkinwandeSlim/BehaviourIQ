"""
Multi-API Configuration: Claude + Groq + Fallback

Priority:
1. Claude Sonnet 4.5 (primary)
2. Groq (free backup)
3. Fallback template (no API)
"""

import os
from dotenv import load_dotenv

load_dotenv()

# CLAUDE CONFIGURATION
CLAUDE_ENABLED = True
CLAUDE_MODEL = "claude-sonnet-4-5"
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MAX_TOKENS = 800

# GROQ CONFIGURATION (FREE BACKUP)
GROQ_ENABLED = True
GROQ_MODEL = "mixtral-8x7b-32768"  # Free tier available
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Try to import clients
try:
    import anthropic
    ANTHROPIC_AVAILABLE = CLAUDE_API_KEY != ""
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  anthropic library not available - Claude disabled")

try:
    from groq import Groq
    GROQ_AVAILABLE = GROQ_API_KEY != ""
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️  groq library not installed - Groq disabled")

# Fallback responses (used if all APIs fail)
FALLBACK_RESPONSES = {
    'cold': {
        'rating': 5,
        'review_text': 'This product is excellent quality. Very satisfied with my purchase. Would definitely recommend to others.',
        'confidence': 0.5
    },
    'lukewarm': {
        'rating': 4,
        'review_text': 'Good product, meets expectations. Some minor issues but overall solid quality. Would buy again.',
        'confidence': 0.5
    },
    'warm': {
        'rating': 5,
        'review_text': 'Outstanding! This is exactly what I was looking for. Superior quality and great value. Highly recommended.',
        'confidence': 0.5
    }
}

print("""
╔════════════════════════════════════════════════════════════════╗
║            API CONFIGURATION & STATUS                         ║
╚════════════════════════════════════════════════════════════════╝

PRIMARY API: Claude Sonnet 4.5
  Status: {'✅ ENABLED' if ANTHROPIC_AVAILABLE else '❌ DISABLED'}
  Model: {CLAUDE_MODEL}
  API Key: {'✓ Configured' if CLAUDE_API_KEY else '✗ Missing (.env)'}

BACKUP API: Groq (Free)
  Status: {'✅ ENABLED' if GROQ_AVAILABLE else '❌ DISABLED'}
  Model: {GROQ_MODEL}
  API Key: {'✓ Configured' if GROQ_API_KEY else '✗ Missing (.env)'}

FALLBACK: Template Responses
  Status: ✅ ALWAYS AVAILABLE
  Behavior: Returns realistic default review if APIs fail

════════════════════════════════════════════════════════════════
""")

# API Selection Priority
def get_available_apis():
    """Returns list of available APIs in priority order"""
    apis = []
    if ANTHROPIC_AVAILABLE:
        apis.append('claude')
    if GROQ_AVAILABLE:
        apis.append('groq')
    apis.append('fallback')
    return apis

print(f"\nAPI PRIORITY ORDER: {' → '.join(get_available_apis()).upper()}\n")
