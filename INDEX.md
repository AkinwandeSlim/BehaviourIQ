# BehaviorIQ Documentation Index

> Complete guide to what's been built and how to use it

---

## 📚 Documentation Map

### 🎯 Start Here
**`GETTING_STARTED.md`** ← **You are here!**
- Quick overview of what you have
- How to use the system
- Common tasks and examples
- FAQ and troubleshooting

### 📦 What's Built?
**`BUILD.md`** - Complete build summary
- Architecture overview
- 6 core components explained
- API reference
- Highlights and innovations

### 🧪 How to Test & Improve?
**`TESTING.md`** - Testing strategies and improvement roadmap
- 4 testing levels (2 min → 30 min)
- Evaluation metrics (ROUGE, NDCG)
- Improvement roadmap (Quick wins → Advanced)
- Code examples for each

### 📖 Main Documentation
**`README.md`** - Full reference
- Setup and installation
- Task descriptions
- Nigerian contextualisation
- Module reference
- Docker deployment

---

## 🚀 Quick Navigation by Task

### "I want to see a demo"
→ Read `GETTING_STARTED.md` **Quick Start** section  
→ Run: `streamlit run app_food.py`

### "I want to understand the architecture"
→ Read `BUILD.md`  
→ Skim `app_food.py` and `agents/orchestrator_food.py`

### "I want to evaluate the system"
→ Read `TESTING.md` **Evaluation Metrics** section  
→ Run scripts in `TESTING.md`

### "I want to improve it"
→ Read `TESTING.md` **Improvement Roadmap** section  
→ Pick a quick win
→ Implement and measure

### "I want to deploy it"
→ Read `README.md` **Docker Deployment** section  
→ Run: `docker-compose up`

### "Something broke"
→ Read `README.md` **Troubleshooting** section  
→ Run: `python verify.py`

---

## 📁 File Organization

```
behavioriq_V2/
│
├── Documentation (Read these!)
│   ├── GETTING_STARTED.md       ← You are here
│   ├── BUILD.md                 ← Architecture & what's built
│   ├── TESTING.md               ← How to test & improve
│   ├── README.md                ← Full reference
│   └── INDEX.md                 ← This file
│
├── Code (The system)
│   ├── app_food.py              ← Streamlit UI (start here for demo)
│   ├── agents/
│   │   ├── predictor_food.py    ← Task A: Review generator
│   │   ├── cold_start_handler.py ← Task B: Recommender
│   │   └── orchestrator_food.py  ← Unified API
│   └── data/
│       ├── food_reviews.csv     ← 560K reviews
│       ├── products_metadata.csv ← 74K products
│       └── config.py            ← Constants
│
├── Testing (Verify it works)
│   ├── verify.py                ← Quick 2-min check
│   ├── test_integration.py      ← Component tests
│   └── test_e2e.py              ← End-to-end tests
│
└── Config (Deployment)
    ├── requirements.txt         ← Python packages
    ├── Dockerfile              ← Container image
    └── docker-compose.yml      ← Multi-container setup
```

---

## 🎯 Reading Order

### For First-Time Users
1. Read this file (INDEX.md)
2. Skim `GETTING_STARTED.md` quick start
3. Run `streamlit run app_food.py`
4. Play with Task A and Task B
5. Read `BUILD.md` to understand architecture

### For Evaluators
1. Read `BUILD.md` (architecture + what's built)
2. Read `TESTING.md` (evaluation strategies)
3. Run `python verify.py` (quick check)
4. Run evaluation scripts from `TESTING.md`
5. Reference `README.md` for details

### For Developers Improving the System
1. Read `BUILD.md` (understand current approach)
2. Read `TESTING.md` (see improvement ideas)
3. Pick a quick win
4. Modify `agents/predictor_food.py` or `agents/cold_start_handler.py`
5. Test with `verify.py` and `streamlit run app_food.py`
6. Measure impact using `TESTING.md` evaluation scripts

---

## 📊 Key Sections by Document

### BUILD.md
- ✅ What's been built (6 components)
- ✅ Architecture overview
- ✅ API reference for both tasks
- ✅ Key innovations
- ✅ Highlights + what to improve

### TESTING.md
- ✅ 4 testing levels with code examples
- ✅ Task A evaluation (ROUGE/BERTScore)
- ✅ Task B evaluation (NDCG@10)
- ✅ Improvement roadmap (4 phases)
- ✅ Weekly improvement workflow
- ✅ A/B testing framework

### GETTING_STARTED.md
- ✅ What you have (summary)
- ✅ How to use it (3 options)
- ✅ Testing & improvement
- ✅ Common tasks with code
- ✅ Architecture decisions explained
- ✅ FAQ + troubleshooting
- ✅ Pre-submission checklist

### README.md
- ✅ Overview (2 tasks + Nigerian context)
- ✅ Quick start (installation + running)
- ✅ Data description
- ✅ Architecture and data flow
- ✅ Agent architecture details
- ✅ Module reference
- ✅ Evaluation metrics
- ✅ Configuration options
- ✅ Example usage
- ✅ Key innovations

---

## 🎓 Learning Paths

### Path 1: Understanding (30 minutes)
1. Read `BUILD.md` (architecture overview)
2. Skim code: `agents/orchestrator_food.py` (main entry point)
3. Review `README.md` (tasks explained)
4. Understand: How data flows, what each component does

### Path 2: Using (45 minutes)
1. Read `GETTING_STARTED.md` quick start
2. Run `python verify.py`
3. Launch `streamlit run app_food.py`
4. Test Task A and Task B manually
5. Try different user/product IDs

### Path 3: Evaluating (1-2 hours)
1. Read `TESTING.md` evaluation section
2. Run ROUGE/BERTScore scripts (Task A)
3. Run NDCG@10 scripts (Task B)
4. Analyze results
5. Identify bottlenecks

### Path 4: Improving (2-4 hours)
1. Read `TESTING.md` improvement roadmap
2. Pick a "quick win" task
3. Read relevant code section
4. Implement improvement
5. Measure impact
6. Repeat

### Path 5: Production Ready (4-8 hours)
1. Read full `README.md`
2. Review `TESTING.md` performance optimization
3. Implement caching/batching
4. Run full evaluation suite
5. Docker setup and test
6. Create deployment instructions

---

## 💡 Example Workflows

### Demo for Stakeholders (10 minutes)
```bash
# 1. Launch Streamlit
streamlit run app_food.py

# 2. Demo Task A
#    - Enter user_00001, prod_00001
#    - Show rating + review text
#    - Point out Nigerian markers ("e do well")

# 3. Demo Task B
#    - Enter user_00001
#    - Show recommendations + reasons
#    - Explain cold-start strategy
```

### Evaluation for Metrics (30 minutes)
```bash
# 1. Run verification
python verify.py

# 2. Run evaluation scripts (from TESTING.md)
python -c "
# Task A evaluation
# Compute ROUGE/BERTScore
"

python -c "
# Task B evaluation
# Compute NDCG@10
"

# 3. Analyze results
# Check if meets thresholds
```

### Quick Win Implementation (1-2 hours)
```bash
# 1. Pick improvement from TESTING.md
# 2. Edit agents/predictor_food.py or agents/cold_start_handler.py
# 3. Test with streamlit
streamlit run app_food.py
# 4. Measure impact
python evaluate_task_a.py  # or evaluate_task_b.py
```

---

## 🔗 Cross-References

### If you want to understand...

**How Task A works:**
- Architecture: `BUILD.md` → Task A section
- Code: `agents/predictor_food.py`
- Testing: `TESTING.md` → Level 2 and 4
- Setup: `README.md` → Task A section

**How Task B works:**
- Architecture: `BUILD.md` → Task B section
- Code: `agents/cold_start_handler.py`
- Testing: `TESTING.md` → Level 2 and 4
- Cold-start: `TESTING.md` → Phase 1 improvements

**How to improve:**
- Roadmap: `TESTING.md` → Improvement Roadmap (Phases 1-4)
- Ideas: `GETTING_STARTED.md` → Improvement Roadmap
- Examples: `TESTING.md` → Code examples for each phase

**How to deploy:**
- Docker: `README.md` → Docker Deployment
- Setup: `GETTING_STARTED.md` → Production deployment
- Config: `data/config.py` (environment variables)

**How to evaluate:**
- Task A metrics: `TESTING.md` → Evaluation Metrics → Task A
- Task B metrics: `TESTING.md` → Evaluation Metrics → Task B
- Code: Scripts in `TESTING.md` with full examples

---

## ✅ Verification Checklist

Before diving in:

- [ ] All files present? Run: `python verify.py`
- [ ] Dependencies installed? `pip install -r requirements.txt`
- [ ] API key set? `export ANTHROPIC_API_KEY="..."`
- [ ] Data loaded? `python -c "import pandas; print(len(pandas.read_csv('data/food_reviews.csv')))"`
- [ ] System works? `streamlit run app_food.py`

If any fails, see `README.md` troubleshooting section.

---

## 🎯 Document Quick References

**How do I...?**

| Question | Answer |
|----------|--------|
| See a quick demo? | `GETTING_STARTED.md` → Quick Start |
| Understand the architecture? | `BUILD.md` or `README.md` |
| Evaluate the system? | `TESTING.md` → Evaluation Metrics |
| Improve it? | `TESTING.md` → Improvement Roadmap |
| Deploy it? | `README.md` → Docker, or `GETTING_STARTED.md` → Deployment |
| Fix an error? | `README.md` → Troubleshooting |
| Add a new feature? | `TESTING.md` → Code examples |
| Understand the code? | `BUILD.md` → API Reference, then read code |
| Track metrics? | `TESTING.md` → Evaluation Metrics + Code |

---

## 🚀 Getting Started (TL;DR)

```bash
# 1. Activate venv
source venv/bin/activate  # Windows: venv\Scripts\Activate.ps1

# 2. Verify it works
python verify.py

# 3. Launch interactive demo
streamlit run app_food.py

# 4. Read documentation
# Open BUILD.md in your editor
```

Then:
- **Want to understand?** → Read `BUILD.md`
- **Want to improve?** → Read `TESTING.md` Improvement Roadmap
- **Want to evaluate?** → Read `TESTING.md` Evaluation Metrics
- **Want to deploy?** → Read `README.md` Docker section

---

## 📞 Still Lost?

1. Check this document (INDEX.md) - you're reading it!
2. Search in `BUILD.md`, `README.md`, or `TESTING.md`
3. Look at code comments in `agents/` directory
4. Run `python verify.py` to confirm setup
5. Try `streamlit run app_food.py` to see it in action

---

**Project Status:** ✅ Complete and Ready  
**Documentation:** ✅ Comprehensive  
**Code Quality:** ✅ Well-commented  
**Testing:** ✅ Multiple levels  

**Next Step:** Pick a reading path above and start! 🚀

---

**Last Updated:** May 24, 2026  
**Documents:** 5 (INDEX, BUILD, TESTING, GETTING_STARTED, README)  
**Code Files:** 8 (3 agents, 1 UI, 3 tests, 1 config)  
**Total Documentation:** ~50 KB  
**Total Code:** ~35 KB  
**Total Data:** ~287 MB (reviews + products)
