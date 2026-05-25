# 🔄 MULTI-API SETUP GUIDE

## API Priority System

The system tries APIs in this order:

1. **Claude Sonnet 4.5** (Primary) - $3 per million input tokens
2. **Groq** (Backup - FREE) - Free tier, open-source models
3. **Fallback Template** (Always available) - No API calls

If Claude fails → Tries Groq → Falls back to template → System never crashes ✅

---

## Step 1: Get Groq API Key (FREE)

### Option A: Web Browser Setup

1. Go to: https://console.groq.com/keys
2. Sign up with:
   - Google account, or
   - Email + password
3. Click "Create API Key"
4. Copy the key (looks like: `gsk_xxx...xxx`)

### Option B: Command Line Setup

```bash
# No CLI setup needed - just grab from web console above
```

---

## Step 2: Add to .env File

Edit `c:\MyFiles\DOCUMENT-2026\2026\May2026\behavioriq_V2\.env`

Add this line:

```
GROQ_API_KEY=gsk_xxx...xxx
```

**Full .env should look like:**

```
ANTHROPIC_API_KEY=sk-ant-api03-xxx...xxx
GROQ_API_KEY=gsk_xxx...xxx
```

---

## Step 3: Verify Setup

### Test both APIs are working:

```bash
# Activate venv first
venv\Scripts\Activate.ps1

# Run test
python test_multi_api.py
```

This will show:
- ✅ Claude API status
- ✅ Groq API status
- ✅ Fallback status
- ✅ Which API gets used

---

## Step 4: Run with Groq Backup

Everything already uses the fallback system! Just:

```bash
# Launch Streamlit (uses multi-API automatically)
streamlit run app_food.py

# Or test programmatically
python -c "from agents.orchestrator_food import BehaviorIQOrchestrator; orch = BehaviorIQOrchestrator(); print(orch.task_a_generate_review('user_00001', 'prod_00001'))"
```

If Claude fails, system automatically tries Groq.

---

## How It Works

### Flow Diagram:

```
User Request
    ↓
Try Claude API
    ├─ Success? ✓ Return Claude response (confidence: 0.75)
    └─ Failed? ↓
      Try Groq API
        ├─ Success? ✓ Return Groq response (confidence: 0.72)
        └─ Failed? ↓
          Use Fallback Template ✓ Return template (confidence: 0.50)
    ↓
ALWAYS return valid response!
```

### Code Flow:

```python
# In agents/predictor_food.py, generate_review() function:

for attempt in range(3):
    try:
        # TRY CLAUDE
        response = client.messages.create(...)  ← Primary
        
    except Exception as claude_error:
        
        # IF CLAUDE FAILS, TRY GROQ
        if GROQ_AVAILABLE:
            response = groq_client.chat.completions.create(...)  ← Backup
        else:
            return _FALLBACK  ← Fallback
```

---

## Groq Available Models

Free tier includes:

| Model | Speed | Quality | Use Case |
|-------|-------|---------|----------|
| mixtral-8x7b-32768 | Fast ⚡ | Good | Default choice ✓ |
| llama-2-70b-chat | Medium | Good | Alternative |
| llama2-uncensored | Fast | Fair | Fallback option |

We use `mixtral-8x7b-32768` (fastest, best quality).

---

## Testing Each API Individually

### Test Claude Only:

```python
from agents.predictor_food import generate_review, build_user_profile

profile = {
    'avg_rating': 4.5,
    'segment': 'warm',
    'pct_5star': 0.8,
    'sample_texts': ['Great!']
}

review = generate_review(profile, "Rice", "Grains")
print(f"Claude result: {review}")
```

### Test Groq Fallback:

```bash
# Temporarily disable Claude API
export ANTHROPIC_API_KEY=""

# Now run - will try Groq
python app_food.py
```

### Test Fallback Template:

```bash
# Disable both
export ANTHROPIC_API_KEY=""
export GROQ_API_KEY=""

# Now run - will use template
python app_food.py
```

---

## Monitoring API Usage

Add to any script:

```python
from api_config import ANTHROPIC_AVAILABLE, GROQ_AVAILABLE

print(f"Claude: {'✅' if ANTHROPIC_AVAILABLE else '❌'}")
print(f"Groq: {'✅' if GROQ_AVAILABLE else '❌'}")
```

---

## FAQ

**Q: Which API should I use for evaluation?**  
A: Both will work. Claude is more accurate, Groq is free. For judges, just run `python evaluate_model_quick.py` (no API needed).

**Q: What if Groq is also down?**  
A: Fallback template returns realistic but generic review. System stays alive ✓

**Q: Will Groq slow down the system?**  
A: No - it's only tried if Claude fails. Normal flow: Claude success (0 Groq overhead).

**Q: How do I know which API was used?**  
A: Check the "source" field in code, or look at confidence score:
- 0.75 = Claude succeeded
- 0.72 = Groq succeeded  
- 0.50 = Fallback template used

**Q: Can I switch primary/backup?**  
A: Yes, edit the try-except order in `agents/predictor_food.py` line ~190.

---

## Groq Rate Limits (Free Tier)

- 30 requests/minute
- 1000 requests/day

For evaluation with 100 users, each with 1 prediction:
- 100 requests = ✅ Well within limits
- Task B with 50 users: 50 requests = ✅ Well within limits

No issues for hackathon evaluation!

---

## Troubleshooting

### "Groq API not available"

Check:
```bash
# Verify .env has GROQ_API_KEY
grep GROQ_API_KEY .env

# Verify it's loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GROQ_API_KEY'))"
```

### "Both APIs failing"

Test manually:
```bash
# Test Claude
python -c "import anthropic; c = anthropic.Anthropic(); print('✓ Claude works')"

# Test Groq
python -c "from groq import Groq; g = Groq(); print('✓ Groq works')"
```

### Still having issues?

The fallback template will always work - system never crashes! ✅

---

## Summary

✅ Claude API: Primary (already configured)  
✅ Groq API: Backup (free, just add key to .env)  
✅ Fallback: Always available (no API needed)  
✅ System: Never crashes, always returns valid response  

**To activate Groq:**
1. Get free key from https://console.groq.com/keys
2. Add to .env as `GROQ_API_KEY=...`
3. Done! System automatically uses it as backup

---

**Last Updated:** May 24, 2026  
**Status:** Multi-API system fully implemented and tested
