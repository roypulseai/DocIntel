# DocIntel User Guide

A complete guide to using DocIntel for document intelligence — from installation to advanced usage.

---

## Table of Contents

1. [Installation](#installation)
2. [Getting a Free API Key](#getting-a-free-api-key)
3. [Using the Web GUI](#using-the-web-gui)
4. [Using the CLI](#using-the-cli)
5. [Programmatic Usage](#programmatic-usage)
6. [Document Types & Tips](#document-types--tips)
7. [Understanding the Results](#understanding-the-results)
8. [Troubleshooting](#troubleshooting)
9. [Docker Deployment](#docker-deployment)

---

## Installation

### Prerequisites

- **Python 3.11** (recommended; 3.12 also supported)
- **pip** (Python package manager)
- A **free Groq API key** ([get one here](https://console.groq.com))

### Install Steps

```bash
# Clone the repository
git clone https://github.com/roypulseai/DocIntel.git
cd DocIntel

# Install Python dependencies
pip install -r requirements.txt

# Download the spaCy NER model (~13 MB)
python -m spacy download en_core_web_sm
```

### Verify Installation

```bash
python -m pytest tests/ -q
```

You should see:

```
[PASS] NER extracted 7 real entities: [...]
[PASS] TF-IDF retrieval returned 1 chunk(s), top score=0.229
[PASS] Full LangGraph pipeline: classify -> extract_entities -> sentiment_topic -> build_index -> qa -> summarize
[OK] Semantic search ranking + persistence round-trip
All DocIntel tests passed.
```

---

## Getting a Free API Key

DocIntel uses **Groq** for LLM inference. Groq provides free access to GPT-OSS and Qwen models with no credit card required.

### Step-by-Step

1. **Visit** [console.groq.com](https://console.groq.com)
2. **Sign up** using Google, GitHub, or email (takes 30 seconds)
3. **Verify** your email if prompted
4. **Navigate** to **API Keys** in the left sidebar
5. **Click** "Create API Key"
6. **Name** your key (e.g., "DocIntel")
7. **Copy** the key — it starts with `gsk_` (e.g., `gsk_abc123...`)

> **Important:** Copy your key immediately — it's only shown once.

### Free Tier Limits

| Limit | Amount |
|-------|--------|
| Requests per day | 14,400 |
| Tokens per day | 500,000 |
| Cost | $0 |
| Credit card required | No |

This is more than enough for personal and development use.

---

## Using the Web GUI

### Launch

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

### Interface Overview

```
┌──────────────────────────────────────────────────────┐
│ 📄 DocIntel                                          │
│ Agentic document intelligence...                     │
├──────────┬───────────────────────────────────────────┤
│ SIDEBAR  │ MAIN AREA                                 │
│          │                                           │
│ 🧭 Nav   │ ┌────┬────┬────┬──────┬─────┬─────┐      │
│  New/    │ │Summ│Class│Entit│Senti │Index│ Ask │     │
│  History │ ├────┴────┴────┴──────┴─────┴─────┤      │
│ 🔑 API   │ │                                │      │
│    Key   │ │     Results display area        │      │
│ 📁 Doc   │ │                                │      │
│  Input   │ └────────────────────────────────┘      │
└──────────┴───────────────────────────────────────────┘
```

### Step 1: Enter API Key

In the **left sidebar**:

1. Click **"How to get your free API key"** to expand the guide
2. Paste your `gsk_...` key into the input field
   - Your key is entered here in the app each session and is **not saved to disk**. (If you set up a `.env` file, it's pre-filled for you instead.)
3. Click **"Save API Key"** to apply it
4. Optionally select a model from the dropdown:
   - `openai/gpt-oss-120b` — Best quality (recommended)
   - `openai/gpt-oss-20b` — Fastest responses
   - `qwen/qwen3.6-27b` — Balanced speed/quality

### Step 2: Provide a Document

Choose one of three methods in the sidebar:

#### Upload a File

- Click **"Upload a file"**
- Browse and select a `.txt`, `.md`, or `.csv` file
- The file content loads automatically
- You'll see a success message with the filename and character count

#### Paste Text

- Click **"Paste text"**
- Paste any document content into the text area
- Works with emails, reports, articles, contracts — anything

#### Try a Sample

- Click **"Try a sample"**
- Select from 3 built-in examples:
  - **Customer Complaint** — A billing dispute letter
  - **News Article** — AI regulation report
  - **Legal Contract** — A service agreement with SLA terms

### Step 3: Run & View Results

Once a document is loaded, click the **"🚀 Analyze Document"** button in the main area.
You'll see:

1. **Progress indicators** — Step-by-step status as each node executes
2. **Metrics bar** — 4 key metrics at a glance:
   - Category (e.g., "Customer Complaint")
   - Confidence (e.g., "94%")
   - Sentiment (e.g., "Negative")
   - Entities Found (e.g., "7")

3. **6 result tabs:**

#### 📝 Summary Tab

The first tab gives you the big picture at a glance:
- **Executive Summary** — A concise overview of the whole document
- **Key Insights** — The most important takeaways, listed as numbered highlights

#### 🏷️ Classification Tab

Shows how the document was classified:
- **Category** — The detected document type
- **Confidence** — How certain the model is (0-100%)
- **Rationale** — Explanation of why this category was chosen

#### 🔍 Entities Tab

Lists all named entities found by spaCy, grouped by type:

| Label | Meaning | Example |
|-------|---------|---------|
| `PERSON` | People's names | Maria Fontaine |
| `ORG` | Organizations | UBS, Google |
| `DATE` | Dates and time periods | 18 August 2026 |
| `MONEY` | Monetary values | CHF 340.00 |
| `GPE` | Geographic locations | Zurich |
| `CARDINAL` | Numbers | 67-33 |

Raw entity data is available in an expandable section.

#### 💭 Sentiment & Topics Tab

- **Sentiment** — positive, negative, neutral, or mixed
- **Polarity Score** — Numeric score from -1.0 (very negative) to +1.0 (very positive)
- **Topics** — Key topics automatically extracted from the document

#### 📚 Document Index Tab

Shows how the document was split into chunks for retrieval:
- Number of chunks created
- Expandable view of each chunk with word count
- Useful for understanding what the retrieval system "sees"

#### 💬 Ask Questions Tab

The RAG (Retrieval-Augmented Generation) Q&A interface:

1. Type a question in the input field, then click **"Ask"**
2. The system:
   - Finds the most relevant chunks using **semantic search (FAISS)** when embeddings are available, with TF-IDF as fallback
   - Sends them to the LLM with your question
   - Returns a grounded answer with source citations
3. **Sources** are shown below the answer so you can verify accuracy

#### 🌐 Cross-Document Semantic Search (multi-file)

When you analyze **2 or more documents at once**, a dedicated search panel appears:

- Type one question and search across **all** uploaded documents at once
- Results are ranked by **meaning** (semantic embeddings), not just keywords
- Each result shows which document and chunk it came from (source attribution)
- Uses FAISS + sentence-transformers (`all-MiniLM-L6-v2`) — fully local, no cost

#### 🕘 History

Every analysis is automatically saved to a local SQLite database:

- Switch to the **History** view in the sidebar to browse past analyses
- Open any past result to re-read its summary, classification, entities, sentiment, and ask follow-up questions
- Vector data is persisted too, so you can search historical documents semantically

**Example questions:**

| Document Type | Example Questions |
|--------------|-------------------|
| Customer Complaint | "What is the complaint reference number?" |
| | "How much was the disputed charge?" |
| | "What is the customer's contact information?" |
| News Article | "Who sponsored the bill?" |
| | "What was the Senate vote count?" |
| Legal Contract | "What is the monthly fee?" |
| | "What is the uptime SLA guarantee?" |
| | "What data protection regulations apply?" |

---

## Using the CLI

### Basic Usage

```bash
export GROQ_API_KEY=gsk_your_key_here    # Linux/macOS
set GROQ_API_KEY=gsk_your_key_here       # Windows CMD
$env:GROQ_API_KEY="gsk_your_key_here"    # Windows PowerShell

python run_demo.py
```

### Output Format

```
=== Classification ===
{
  "category": "Customer Complaint",
  "confidence": 0.94,
  "rationale": "Reports a billing dispute."
}

=== Named Entities (spaCy) ===
       PERSON | Maria Fontaine
          ORG | CHF 340.00
          ORG | TXN-88213-CH
          ORG | UBS Card Center
          GPE | Zurich
         DATE | 18 August 2026
         DATE | five business days

=== Sentiment & Topics ===
{
  "sentiment": "negative",
  "sentiment_score": -0.4,
  "topics": ["billing dispute", "refund delay"]
}

=== RAG QA (TF-IDF retrieval + grounded answer) ===
{
  "text": "The reference is TXN-88213-CH for CHF 340.00. [Chunk 0]",
  "sources": [0]
}
```

---

## Programmatic Usage

### Full Pipeline

```python
from docintel.graph import run_docintel

result = run_docintel(
    text="Your document text here...",
    question="What is the main topic?"
)

# Access individual results
print(result["classification"]["category"])
print(result["entities"])
print(result["sentiment_topic"]["sentiment"])
print(result["answer"]["text"])
```

### Individual Components

```python
# Named Entity Recognition
from docintel.ner import extract_entities

entities = extract_entities("Apple Inc. reported $394B revenue in 2024.")
# Returns: [{"text": "Apple Inc.", "label": "ORG", ...}, ...]

# Document Chunking
from docintel.retriever import chunk_text

chunks = chunk_text(long_document, max_words=200)
# Returns: ["chunk1 text...", "chunk2 text...", ...]

# TF-IDF Retrieval
from docintel.retriever import TfidfRetriever

retriever = TfidfRetriever(chunks)
results = retriever.retrieve("revenue figures", top_k=3)
# Returns: [RetrievalHit(text=..., score=0.85, index=0), ...]

# Document Classification
from docintel.analysis import classify_document

classification = classify_document("Your document text...")
# Returns: {"category": "...", "confidence": 0.9, "rationale": "..."}

# Sentiment & Topic Analysis
from docintel.analysis import sentiment_and_topics

sentiment = sentiment_and_topics("Your document text...")
# Returns: {"sentiment": "negative", "sentiment_score": -0.3, "topics": [...]}

# RAG Question Answering
from docintel.analysis import generate_answer

answer = generate_answer(document, "What is the refund policy?", retrieved_chunks)
# Returns: {"text": "...", "sources": [0, 2]}
```

---

## Document Types & Tips

DocIntel works with any text document. Here are some tips for best results:

### Supported Formats

| Format | Support | Notes |
|--------|---------|-------|
| Plain text (.txt) | Full | Best results |
| Markdown (.md) | Full | Markdown syntax is treated as text |
| CSV (.csv) | Full | Read as plain text |
| PDF | Not yet | Convert to .txt first |
| DOCX | Not yet | Copy-paste the text content |

### Tips for Better Results

1. **Keep documents focused** — One topic per document works best for classification
2. **Include context** — More text gives better sentiment/topic analysis
3. **Clear questions** — For QA, ask specific questions rather than vague ones
4. **Reasonable length** — Documents up to ~10,000 words work well; very long documents are truncated for LLM analysis but still fully indexed for retrieval

---

## Understanding the Results

### Confidence Scores

- **Classification confidence** (0-1): Higher means the model is more certain
- **Sentiment score** (-1 to +1): -1 = very negative, 0 = neutral, +1 = very positive
- **Retrieval scores** (0-1): Higher means more relevant to the query

### Entity Labels

spaCy uses standard NER labels:

| Label | Description |
|-------|-------------|
| `PERSON` | People's names |
| `ORG` | Organizations, companies |
| `GPE` | Countries, cities, states |
| `DATE` | Dates, time periods |
| `MONEY` | Monetary values |
| `CARDINAL` | Numerical values |
| `NORP` | Nationalities, groups |
| `EVENT` | Named events |
| `LAW` | Named laws/regulations |
| `PRODUCT` | Products |

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `Set GROQ_API_KEY before running` | Export the env var: `export GROQ_API_KEY=gsk_...` |
| `ModuleNotFoundError: spacy` | Run: `pip install spacy` |
| `OSError: [E050] Can't find model 'en_core_web_sm'` | Run: `python -m spacy download en_core_web_sm` |
| `Rate limit error from Groq` | You've hit the free tier limit — wait or use a different model |
| `streamlit: command not found` | Run: `pip install streamlit` |
| Blank page after opening localhost:8501 | Check terminal for errors; ensure `streamlit run app.py` is running |
| QA returns "No answer generated" | Make sure your question is specific and the document has relevant content |

### Getting Help

- **Issues:** [github.com/roypulseai/DocIntel/issues](https://github.com/roypulseai/DocIntel/issues)
- **Discussions:** [github.com/roypulseai/DocIntel/discussions](https://github.com/roypulseai/DocIntel/discussions)

---

## Docker Deployment

The repo ships with `docker-compose.yml` and `.dockerignore` already in place, so
Docker is truly one command.

### Docker Compose (recommended)

```bash
# 1. Create a local .env file with your key (git-ignored, never committed):
#    GROQ_API_KEY=gsk_your_key_here
# 2. Build and run in one command:
docker compose up
```

Compose reads `GROQ_API_KEY` from your local `.env`, serves the app on
`http://localhost:8501`, and keeps your analysis history in a named Docker
volume (`docintel_history`) so it survives container restarts and rebuilds.

To stop the container: `docker compose down`.
To reset the history volume: `docker compose down -v`.

### Manual build and run

```bash
# Build the image
docker build -t docintel .

# Run with your API key (no history persistence)
docker run -p 8501:8501 -e GROQ_API_KEY=gsk_your_key_here docintel
```

> Note: the Docker image uses **Python 3.11** and already bundles the spaCy
> name-detection model, so no first-run model download is needed inside the
> container.

---

## Architecture Deep Dive

For developers who want to understand or extend the pipeline:

### StateGraph Flow

```
Input Text
    │
    ▼
┌─────────┐
│  ingest  │  Accepts raw text, stores in state
└────┬────┘
     │
     ▼
┌──────────┐
│ classify  │  LLM call → {category, confidence, rationale}
└────┬─────┘
     │
     ▼
┌────────────────┐
│ extract_entities │  spaCy NER → [{text, label, start, end}, ...]
└────┬───────────┘
     │
     ▼
┌──────────────────┐
│ sentiment_topic   │  LLM call → {sentiment, sentiment_score, topics}
└────┬─────────────┘
     │
     ▼
┌─────────────┐
│ build_index  │  TF-IDF vectorization → chunks, retriever, hits
└────┬────────┘
     │
     ▼
┌──────┐
│  qa  │  LLM call with retrieved chunks → {text, sources}
└──┬───┘
   │
   ▼
  END
```

### Extending the Pipeline

To add a new node:

1. Create a function that takes `DocIntelState` and returns a dict of new state values
2. Add it to the graph with `g.add_node("name", your_function)`
3. Add edges to connect it to the pipeline

```python
# Example: Register a custom node and wire it into the pipeline
from docintel.analysis import summarize_document

def _summarize(state: DocIntelState) -> dict:
    return {"summary": summarize_document(state["text"])}

g.add_node("summarize", _summarize)
g.add_edge("qa", "summarize")
g.add_edge("summarize", END)
```

### Swapping Components

Each module is independent:

- **Swap the LLM:** Change `_get_llm()` in `analysis.py` to use any LangChain-compatible LLM
- **Swap NER:** Replace `ner.py` with a different NER system
- **Swap retrieval:** The per-document Q&A uses semantic search (`VectorStore`, FAISS) with a `TfidfRetriever` fallback; both live under `docintel/` and can be extended or swapped

---

*Last updated: August 2026*
