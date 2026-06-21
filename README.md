# Customer Retention Intelligence — Multi-Agent System

 A multi-agent orchestration pipeline using LangGraph to automatically classify at-risk customers, retrieve appropriate retention playbooks via RAG (Retrieval-Augmented Generation), and synthesise personalised Next Best Actions (NBA).

---

##  Key Features

1. **Multi-Agent Orchestration**: Uses LangGraph's Centralized Supervisor Pattern to coordinate three specialised sub-agents:
    - **Customer Profiler**: Fetches and formats customer data.
    - **Churn Diagnostician**: Classifies customers using a deterministic, auditable rule engine.
    - **Retention Strategist**: Retrieves the correct retention playbook using RAG via ChromaDB.
2. **Deterministic Risk Classification**: Business rules are strictly coded rather than relying on LLM probability, ensuring 100% auditability and consistency.
3. **LLM-as-Judge Evaluation**: Built-in evaluation pipeline using `gpt-4o` to grade agent responses against human-authored references across four dimensions, plus semantic similarity checks.
4. **CLI Interface**: Process single customers interactively or batch-process entire datasets.

---

##  Project Structure

```
retention-ai-agent/
├── main.py                  # CLI entry point
├── requirements.txt         # Dependencies
├── .env.example             # Environment variable template
├── config/                  # LLM and embedding client configuration
├── schemas/                 # Pydantic domain models (Customer, Playbook, Risk)
├── bl/                      # Core Business Logic (Deterministic Classifier, Tier Resolution)
├── prompts/                 # System prompts for all agents
├── tools/                   # LangChain @tool wrappers
├── orchestrator/            # LangGraph StateGraph, Nodes, and Agent factories
├── evaluation/              # LLM-as-Judge evaluation logic
├── data/                    # Datasets
│   └── sample/              # Synthetic sample data for testing
└── output/                  # Runtime-generated outputs (.csv)
```

---

##  Setup & Installation

**1. Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure Environment Variables**
Copy `.env.example` to `.env` and fill in your Azure OpenAI credentials:
```bash
cp .env.example .env
```
Ensure you provide:
- `MODEL_ENDPOINT`
- `CHAT_MODEL_NAME` (e.g., `gpt-4o`)
- `AZURE_OPENAI_API_KEY`
- `EMBEDDING_MODEL_NAME` (e.g., `text-embedding-ada-002`)

---

##  Usage

The CLI (`main.py`) provides two primary workflows: `review` and `evaluate`.

### 1. Retention Review (Single Customer)
Run the multi-agent pipeline for a specific customer.
```bash
python main.py review --customer-id S001 --data-dir ./data/sample
```

### 2. Retention Review (Batch Processing)
Process an entire dataset and output the results to a CSV file.
```bash
python main.py review --all --data-dir ./data/sample --output ./output/results.csv
```

### 3. LLM-as-Judge Evaluation
Evaluate the generated agent responses against a human-authored reference set. (Requires running the batch review first).
```bash
python main.py evaluate --results-file ./output/results.csv --data-dir ./data/sample --output ./output/quality_judgments.csv
```

---

##  Data Directory Convention

To run the pipeline on your own data, create a new folder (e.g., `data/custom/`) and ensure it contains:
1. `customer_records.json` (The customer pool)
2. `risk_segments.json` (Segment definitions and priority rules)
3. `retention_playbooks.json` (Playbooks for RAG)
4. *(Optional)* `validation_results.csv` (Reference responses, required only for the `evaluate` command)

Then pass your folder path to the CLI:
```bash
python main.py review --all --data-dir ./data/custom/
```

> **Note:** The `data/sample/` folder contains synthetic customer data to demonstrate the system without exposing PII.

---

##  System Architecture

The pipeline follows a deterministic flow orchestrated by a Supervisor:

1. **Input**: A `customer_id` is passed to the Supervisor.
2. **Profiler Node**: Extracts the customer's raw signals (Recency, App Sessions, Email Open Rate, NPS, Support Tickets).
3. **Diagnostician Node**: Runs the deterministic rule engine (`bl/classifier.py`) to map the signals to a Risk Segment (e.g., *Support-Fatigued*).
4. **Strategist Node**: Uses ChromaDB to fetch the corresponding Retention Playbook for the classified segment.
5. **Supervisor Node**: Resolves tier-conditional language in the playbook (e.g., offering a call for Platinum users vs an email for Bronze users) and tasks the LLM with drafting a concise, 2-sentence rationale.
6. **Output**: A structured, 6-field retention decision.

---
