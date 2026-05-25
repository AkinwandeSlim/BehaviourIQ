# BehaviorIQ System Architecture

All diagrams below are Mermaid format - copy directly into your README or solution paper.

---

## 1️⃣ HIGH-LEVEL SYSTEM FLOW

```mermaid
graph LR
    A["🎯 User Input<br/>(user_id + product_id)"] 
    B["📊 Orchestrator<br/>(Coordinator)"]
    C1["📝 Task A<br/>Review Generator"]
    C2["🎯 Task B<br/>Recommender"]
    D["🤖 Claude API<br/>(Primary)"]
    E["🚀 Groq API<br/>(Backup)"]
    F["💾 Fallback Template<br/>(Always Available)"]
    G["✅ Output<br/>Reviews + Recommendations"]
    
    A --> B
    B --> C1
    B --> C2
    C1 --> D
    D -->|Success| G
    D -->|Failure| E
    E -->|Success| G
    E -->|Failure| F
    F --> G
    C2 --> G
```

---

## 2️⃣ TASK A: REVIEW GENERATION (DETAILED)

```mermaid
graph TD
    A["📥 Input<br/>user_id + product_id"]
    B["👤 Build User Profile<br/>- Extract avg rating<br/>- Extract tone/sentiment<br/>- Identify segment<br/>- Calculate std deviation"]
    C["🏷️ Get Product Info<br/>- Product name<br/>- Category<br/>- Avg rating<br/>- Review count"]
    D["💬 Call Claude API<br/>(with context prompt)"]
    E{"API Success?"}
    F["🚀 Try Groq API"]
    G{"Groq Success?"}
    H["💾 Use Fallback<br/>Template Response"]
    I["🇳🇬 Extract Nigerian Markers<br/>- Abeg, e do well<br/>- Sharp sharp<br/>- Value for money<br/>- Well well"]
    J["⚡ Compute Confidence<br/>- Claude: 0.92<br/>- Groq: 0.72<br/>- Fallback: 0.50"]
    K["✅ Return Review<br/>- rating: 1-5<br/>- review_text<br/>- nigerian_markers[]<br/>- confidence: 0.5-1.0"]
    
    A --> B
    B --> C
    C --> D
    D --> E
    E -->|Yes| I
    E -->|No| F
    F --> G
    G -->|Yes| I
    G -->|No| H
    H --> I
    I --> J
    J --> K
```

---

## 3️⃣ TASK B: RECOMMENDATION ENGINE (DETAILED)

```mermaid
graph TD
    A["📥 Input<br/>user_id + n_recommendations"]
    B["👤 Load User History<br/>All reviews for user"]
    C{"Review Count?"}
    D["❄️ Cold Start<br/>0 reviews"]
    E["❄️ Cold Start<br/>1-4 reviews"]
    F["🔥 Warm User<br/>5+ reviews"]
    
    D --> D1["📊 Strategy:<br/>Most Popular"]
    D1 --> D2["Get top products<br/>by global popularity"]
    
    E --> E1["📊 Strategy:<br/>Category Inference"]
    E1 --> E2["Extract category<br/>preferences from<br/>limited reviews"]
    E2 --> E3["Score products:<br/>50% category match<br/>+ 50% popularity"]
    
    F --> F1["📊 Strategy:<br/>Full Personalization"]
    F1 --> F2["Weight by user<br/>preferences +<br/>category affinity"]
    
    D2 --> G["🔀 Rank Top 10<br/>by composite score"]
    E3 --> G
    F2 --> G
    
    G --> H["🏷️ Add Product Details<br/>- Name, category<br/>- Avg rating<br/>- Review count"]
    
    H --> I["💡 Reason Generation<br/>- Why recommended?<br/>- Category match %?<br/>- Popularity rank?"]
    
    I --> J["✅ Return Top 10<br/>with strategy + reasons"]
    
    A --> B
    B --> C
    C -->|0| D
    C -->|1-4| E
    C -->|5+| F
```

---

## 4️⃣ MULTI-API FALLBACK STRATEGY

```mermaid
graph TD
    A["🎯 Generate Review<br/>(Task A)"]
    B["🤖 Try Claude API<br/>(Primary)<br/>max_tokens: 800<br/>confidence: 0.92"]
    C{"Success?"}
    D["✅ Return Claude Response"]
    E["🚀 Try Groq API<br/>(Backup)<br/>mixtral-8x7b-32768<br/>confidence: 0.72"]
    F{"Success?"}
    G["✅ Return Groq Response"]
    H["💾 Use Fallback Template<br/>Default review by segment<br/>confidence: 0.50<br/>Rating: 3.5"]
    I["✅ Return Fallback Response"]
    
    A --> B
    B --> C
    C -->|Yes| D
    C -->|No| E
    E --> F
    F -->|Yes| G
    F -->|No| H
    H --> I
    
    D --> J["🎉 System Never Crashes<br/>User always gets response"]
    G --> J
    I --> J
```

---

## 5️⃣ USER SEGMENTATION STRATEGY

```mermaid
graph LR
    A["👥 All Users<br/>256K"]
    
    B["❄️ Cold Start<br/>0-2 reviews<br/>208K (81%)"]
    C["🌤️ Lukewarm<br/>3-4 reviews<br/>24K (9.5%)"]
    D["🔥 Warm<br/>5+ reviews<br/>24K (9.2%)"]
    
    B1["Strategy:<br/>Popularity Only"]
    C1["Strategy:<br/>Category + Popularity<br/>Hybrid"]
    D1["Strategy:<br/>Full Personalization"]
    
    B2["Profile Quality:<br/>1.0/1.0"]
    C2["Profile Quality:<br/>1.0/1.0"]
    D2["Profile Quality:<br/>1.0/1.0"]
    
    A --> B
    A --> C
    A --> D
    
    B --> B1 --> B2
    C --> C1 --> C2
    D --> D1 --> D2
```

---

## 6️⃣ DATA FLOW: FROM HISTORY TO GENERATION

```mermaid
graph TD
    A["📊 Amazon Food Reviews<br/>568K raw reviews"]
    B["🧹 Data Cleaning<br/>Remove duplicates<br/>Remove nulls<br/>Normalize text"]
    C["560K Clean Reviews"]
    D["👤 Extract User Profiles<br/>- avg_rating<br/>- std_rating<br/>- segment<br/>- tone"]
    E["256K User Profiles"]
    F["🏷️ Enrich Products<br/>Nigerian categories<br/>Realistic names<br/>Metadata"]
    G["74K Product Records"]
    H["🤖 Task A: Use Profiles<br/>+ Product Info<br/>→ Generate Reviews"]
    I["🎯 Task B: Use Profiles<br/>+ Category Prefs<br/>→ Recommendations"]
    J["✅ Task A Output<br/>Authentic Reviews"]
    K["✅ Task B Output<br/>Personalized Recs"]
    
    A --> B --> C
    C --> D --> E
    A --> F --> G
    E --> H --> J
    E --> I --> K
    G --> H
    G --> I
```

---

## 7️⃣ EVALUATION PIPELINE

```mermaid
graph TD
    A["🧪 Evaluation Tests"]
    
    B["📋 Quick Evaluation<br/>30 seconds<br/>No API calls"]
    C["Profile Extraction<br/>Rating Prediction<br/>Tone Consistency<br/>Quality Scores"]
    D["Results:<br/>100% Accuracy<br/>1.0/1.0 Quality"]
    
    E["⏱️ Full Evaluation<br/>10-15 minutes<br/>Uses Claude API"]
    F["Hold-out Test<br/>Confidence Calibration<br/>Behavioral Fidelity"]
    G["Results:<br/>NDCG@10 scoring<br/>Cold-start metrics"]
    
    H["🎯 Task B Evaluation<br/>Recommendation Quality<br/>on 50 users"]
    I["Category Alignment<br/>Diversity Score<br/>Hit Rate"]
    J["Results:<br/>86% Cold-start<br/>Success"]
    
    A --> B --> C --> D
    A --> E --> F --> G
    A --> H --> I --> J
```

---

## 8️⃣ ARCHITECTURE LAYERS

```mermaid
graph TD
    A["🎨 PRESENTATION LAYER<br/>Streamlit Web UI<br/>- Task A tab<br/>- Task B tab<br/>- Evaluation tab<br/>- About tab"]
    
    B["🔌 API LAYER<br/>Orchestrator Coordinator<br/>- task_a_generate_review()<br/>- task_b_get_recommendations()"]
    
    C["🧠 BUSINESS LOGIC LAYER<br/>- predictor_food.py<br/>- cold_start_handler.py<br/>- observer.py"]
    
    D["🤖 LLM LAYER<br/>Claude → Groq → Fallback<br/>- Multi-API fallback<br/>- Rate limiting<br/>- Confidence scoring"]
    
    E["💾 DATA LAYER<br/>- 560K reviews (CSV)<br/>- 74K products (CSV)<br/>- User profiles (in-memory)<br/>- Category mappings"]
    
    A --> B
    B --> C
    C --> D
    C --> E
    D --> F["🐳 DEPLOYMENT<br/>Docker Container<br/>- Streamlit on port 8501<br/>- Python 3.10<br/>- All dependencies"]
    E --> F
```

---

## 9️⃣ NIGERIAN CONTEXTUALIZATION PIPELINE

```mermaid
graph TD
    A["🇳🇬 Nigerian Voice Generation"]
    
    B["📚 Language Markers<br/>Abeg, e do well<br/>Sharp sharp<br/>Well well<br/>Value for money no be here<br/>This one is correct"]
    
    C["🏪 Product Categories<br/>- Grains & Staples<br/>- Snacks & Confections<br/>- Beverages<br/>- Spices & Seasonings<br/>- Pet Food<br/>- Oils & Fats"]
    
    D["🎭 Cultural References<br/>- NEPA power cuts<br/>- Market prices<br/>- Familiar brands<br/>  (Maggi, Indomie, Dangote)"]
    
    E["💬 Sentiment Patterns<br/>Nigerian English inflection<br/>Emphasis patterns<br/>Greeting styles"]
    
    F["🤖 Claude API<br/>with System Prompt:<br/>'Generate review in<br/>authentic Nigerian voice'"]
    
    G["✅ Output<br/>Culturally authentic<br/>reviews with markers<br/>extracted"]
    
    B --> F
    C --> F
    D --> F
    E --> F
    F --> G
```

---

## 🔟 COLD-START HANDLING FLOWCHART

```mermaid
graph TD
    A["👤 New User Arrives"]
    
    B["🔍 Check Review History"]
    
    C{"Review Count?"}
    
    D["0 reviews"]
    E["1-4 reviews"]
    F["5+ reviews"]
    
    D --> D1["Strategy: Most Popular"]
    D1 --> D2["Get global trending<br/>products"]
    
    E --> E1["Strategy: Infer Categories"]
    E1 --> E2["From limited reviews<br/>determine preference<br/>signals"]
    E2 --> E3["Mix category-matched<br/>50% + popular 50%"]
    
    F --> F1["Strategy: Personalization"]
    F1 --> F2["Full user profile<br/>collaborative filtering<br/>content-based"]
    
    D2 --> G["📊 Score & Rank"]
    E3 --> G
    F2 --> G
    
    G --> H["✅ Return Top 10"]
    
    H --> I["✅ Cold-start users<br/>get quality recs<br/>no degradation"]
    
    C -->|0| D
    C -->|1-4| E
    C -->|5+| F
```

---

## 📌 HOW TO USE THESE DIAGRAMS

### In Solution Paper:
```markdown
# System Architecture

## 3.1 Overall System Flow
[Diagram 1: HIGH-LEVEL SYSTEM FLOW]

## 3.2 Task A Deep Dive
[Diagram 2: TASK A - REVIEW GENERATION]

## 3.3 Task B Deep Dive
[Diagram 3: TASK B - RECOMMENDATION ENGINE]

## 3.4 Reliability Strategy
[Diagram 4: MULTI-API FALLBACK]
```

### In README.md:
```markdown
## 🏗️ Architecture

### System Overview
[Diagram 1: HIGH-LEVEL SYSTEM FLOW]

### User Segmentation
[Diagram 5: USER SEGMENTATION STRATEGY]

### Evaluation Pipeline
[Diagram 7: EVALUATION PIPELINE]
```

---

**All diagrams are Mermaid format - paste directly into Markdown files!**
