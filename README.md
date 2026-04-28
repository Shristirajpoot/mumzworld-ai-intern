# Mumzworld AI Gift Concierge 🎁

An AI-native agent that turns natural language queries into structured, personalized gift recommendations for mothers and babies.

## 🚀 Setup & Run (Under 5 minutes)

### Prerequisites
- Python 3.9+
- An API key for OpenAI or OpenRouter (free tier is fine).

### Installation

1. **Clone the repository and enter the directory**
   ```bash
   git clone <your-repo-url>
   cd mumzworld-gift-finder
   ```

2. **Set up a virtual environment (Optional but recommended)**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   Copy the example `.env` file and add your API key.
   ```bash
   cp .env.example .env
   ```
   *Edit `.env` and set `OPENAI_API_KEY`. If using OpenRouter, uncomment the OpenRouter variables in the file.*

### Running the Agent

You can run the agent in interactive mode:
```bash
python src/agent.py
```

Or pass a single query directly:
```bash
python src/agent.py --query "I need a thoughtful gift for a friend with a 6-month-old, under 200 AED."
```

### Running Evals
```bash
python src/evals.py
```

---

## 📊 Evals (EVALS.md)

### Rubric
I evaluate the agent based on 4 criteria:
1. **Constraint Satisfaction (Hard Criteria):** Did the selected products respect the user's budget (max AED) and the child's age range?
2. **Graceful Failure (Uncertainty):** Does the agent correctly refuse to recommend things outside of its domain (e.g., "What is the capital of France?", or "Laptops for 5000 AED")?
3. **Multilingual Quality:** Does the Arabic output read naturally and contextually (not just a literal translation)?
4. **Structured Schema Validation:** Did the LLM output conform to our expected Pydantic schema without missing required fields?

### Test Cases & Scores
I created a test suite of 10 cases in `src/evals.py`, combining happy paths, adversarial queries, and edge cases (like twins, baby showers, or out-of-scope requests). 

- **Score:** 10/10 (100% Pass Rate).
- **Failure Modes Caught During Dev:** Initially, the LLM tried to recommend products that exceeded the budget if they were "highly relevant". I fixed this by using a hybrid architecture: LLM extracts structured constraints -> Python rigidly filters the catalog -> LLM selects the final best from the filtered subset. This guarantees the budget and age constraints are never violated.

---

## ⚖️ Tradeoffs (TRADEOFFS.md)

### Why this problem?
I chose the **Gift Finder for Moms** because it perfectly represents the messy reality of e-commerce search. Users rarely search using rigid filters ("Category: Toys, Age: 6-12m, Price: <200"); they search using context ("gift for a friend's 1-year-old, around 150 dirhams"). This problem requires:
1. Translating messy intent into structured data.
2. Cross-referencing against hard constraints (we cannot show a 500 AED item if the budget is 200 AED).
3. Providing personalized, multilingual rationale for the purchase.

**What I rejected:**
I rejected the "Customer Service Email Triage" because while useful, it's mostly a text-classification problem. The Gift Finder touches more core e-commerce infrastructure (catalog retrieval, pricing, user intent, localization) and directly impacts revenue.

### Architecture Choice
I used a **Hybrid RAG/Filtering Approach** instead of pure LLM generation. 
1. **LLM Structured Output:** Parses intent (Budget, Age, Keywords).
2. **Deterministic Code:** Filters the catalog to ensure zero hallucinations on price or safety (age ratings).
3. **LLM Reasoning:** Selects the top 3 and writes localized sales copy.

**Why?** Pure LLMs are bad at math and absolute filtering. If you ask an LLM to "only pick items under 200 AED", it will sometimes hallucinate a price or pick a 250 AED item because it "looks close". By forcing the LLM to output a JSON constraint schema, and executing the filter in Python, we guarantee 100% accuracy on hard constraints.

### Handling Uncertainty
The schema includes an `is_valid_gift_query` boolean. If the user asks for a laptop or a weather update, the LLM flags it as false in step 1, saving computation and failing gracefully. If the Python filter returns 0 items (e.g., "Car seat under 50 AED"), the system immediately tells the user no products match those exact criteria, rather than hallucinating a fake product.

### What I would build next
1. **Vector Embeddings:** For a catalog of 1M+ items, the Python loop wouldn't scale. I would embed the product descriptions into a vector DB (like Qdrant or Pinecone) and use the extracted keywords for semantic search after pre-filtering by price/age metadata.
2. **Conversation Memory:** Allow users to say "Actually, make it under 150 AED" after the first recommendation.

---

## 🛠️ Tooling

### Stack & Harnesses
- **Frameworks:** Python, Pydantic (for reliable schema validation).
- **Models:** Built using the `openai` SDK to leverage `gemini-2.5-flash` (via Google AI Studio's OpenAI-compatible endpoint). I used structured outputs (`response_format`) to guarantee the JSON schema.
- **AI Assistants Used:** Antigravity (Google DeepMind advanced agentic coding model) acting as a pair-programmer. 

### How I used AI
1. **Scaffolding:** Used the AI assistant to generate the boilerplate `catalog.json` with realistic dummy data for baby products, complete with age ranges and prices.
2. **Architecture Brainstorming:** Prompted the assistant to help me decide between pure LLM filtering vs. Hybrid Python filtering. We concluded Python filtering was safer for e-commerce pricing.
3. **Eval Writing:** Used the AI to help generate 10 adversarial and happy-path test cases for `evals.py`.

### What worked & What didn't
- **Worked:** Pydantic structured outputs were flawless for constraint extraction. 
- **Didn't Work:** Asking the LLM to evaluate if a product was "age appropriate" purely via prompt engineering was inconsistent. Moving the age check to a deterministic Python `if min_age <= requested_age <= max_age` logic fixed all edge cases instantly.

---

## 🤖 AI Usage Note
- **Models:** `gemini-2.5-flash` (via Google AI Studio) for structured intent extraction and multilingual reasoning generation.
- **Builders/Assistants:** Google DeepMind's Antigravity agent was used as a pair-programmer within the IDE to scaffold the python boilerplate, generate the mock JSON data, and write the evaluation tests. 
- **Workflow:** Prompted the agent to debate architecture (Pure LLM vs Hybrid), generated the mock catalog, and iterated on the Pydantic schema until constraints passed reliably.

## ⏱️ Time Log (Total: ~3.5 Hours)
- **Discovery & Architecture Planning:** 45 minutes
- **Mock Data Generation (`catalog.json`):** 15 minutes
- **Agent Logic & Pydantic Schemas (`agent.py`):** 1 hour 30 minutes
- **Evaluation Writing & Debugging (`evals.py`):** 45 minutes
- **Documentation & README:** 15 minutes
