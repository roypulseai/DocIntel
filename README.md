<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/langgraph-1.2+-yellow?logo=langchain&logoColor=white" alt="LangGraph">
  <img src="https://img.shields.io/badge/groq-free-green?logo=groq&logoColor=white" alt="Groq">
  <img src="https://img.shields.io/badge/spacy-3.8+-blueviolet?logo=spacy&logoColor=white" alt="spaCy">
  <img src="https://img.shields.io/badge/streamlit-1.44+-red?logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/github/license/roypulseai/DocIntel" alt="License">
</p>

<h1 align="center">📄 DocIntel</h1>

<p align="center">
  <strong>Agentic Document Intelligence Pipeline</strong><br>
  Classify, summarize, extract entities, analyze sentiment, and ask questions about any document — powered by open-source LLMs.
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-user-guide">User Guide</a> •
  <a href="#-api-reference">API</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

## Overview

**DocIntel** is a free, open-source document intelligence pipeline that processes any text document through a multi-step agentic workflow. It combines LLM-powered analysis with classical NLP techniques to deliver executive summaries and key insights, classification, named entity recognition, sentiment analysis, topic extraction, and retrieval-augmented question answering.

Built with **LangGraph** for orchestration, **Groq** (free tier with GPT-OSS) for LLM inference, **spaCy** for real NER, and **scikit-learn** for TF-IDF retrieval — everything runs without paid APIs.

### Why DocIntel?

| Problem | DocIntel Solution |
|---------|------------------|
| Paid API lock-in (OpenAI, Anthropic) | Uses Groq free tier — 14,400 requests/day, no credit card |
| LLM-simulated NER is unreliable | Real NER via spaCy's `en_core_web_sm` model |
| No grounding for QA answers | TF-IDF retrieval + cited chunk sources |
| Hard to use for non-developers | Streamlit web GUI with file upload |
| Vendor-specific, hard to swap | Modular LangGraph nodes — swap any component independently |

---

## Features

| Feature | How It Works | Cost |
|---------|-------------|------|
| **Document Summary & Insights** | Executive summary + key insights via GPT-OSS 120B | Free (Groq) |
| **Document Classification** | Zero-shot classification via GPT-OSS 120B | Free (Groq) |
| **Named Entity Recognition** | spaCy `en_core_web_sm` — persons, orgs, dates, money, locations | Free (local) |
| **Sentiment Analysis** | LLM-powered polarity scoring (-1.0 to +1.0) | Free (Groq) |
| **Topic Extraction** | Automatic key topic identification | Free (Groq) |
| **Retrieval-Augmented QA** | Semantic search (FAISS + sentence-transformers) with TF-IDF fallback → grounded answers with cited sources | Free (local + Groq) |
| **Cross-Document Semantic Search** | Embed all uploaded documents into one FAISS index; ask one question across all of them | Free (local) |
| **Analysis History** | Every analysis auto-saved to SQLite; review past results (including vectors) anytime | Free (local) |
| **Web GUI** | Streamlit interface with file upload, paste, and sample documents | Free |
| **CLI Mode** | Run the full pipeline from command line | Free |
| **Docker Support** | One-command containerized deployment | Free |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DocIntel Pipeline                        │
│                      (LangGraph StateGraph)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐   ┌────────────┐   ┌──────────┐   ┌───────────┐ │
│  │  Ingest   │──▶│  Classify  │──▶│   NER    │──▶│ Sentiment │ │
│  │          │   │ (GPT-OSS)  │   │ (spaCy)  │   │ (GPT-OSS) │ │
│  └──────────┘   └────────────┘   └──────────┘   └─────┬─────┘ │
│                                                        │       │
│                 ┌────────────────────────────────────┐ │       │
│  ┌──────────┐   │  QA (GPT-OSS)  ──▶  Summarize      │◀┘       │
│  │    END   │◀──│  RAG answer + exec summary/insights │         │
│  └──────────┘   └─────────────────────────────────────┘         │
│                         ▲                                       │
│                 ┌───────┴───────┐                               │
│                 │  Build Index  │                               │
│                 │ (TF-IDF/sklearn)                              │
│                 └───────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

### Pipeline Nodes

| Node | Module | Technology | What It Does |
|------|--------|-----------|--------------|
| `ingest` | `graph.py` | — | Accepts raw text input |
| `classify` | `analysis.py` | GPT-OSS via Groq | Zero-shot document classification with confidence score |
| `extract_entities` | `ner.py` | spaCy `en_core_web_sm` | Extracts named entities (PERSON, ORG, DATE, MONEY, GPE, etc.) |
| `sentiment_topic` | `analysis.py` | GPT-OSS via Groq | Sentiment polarity + key topic extraction |
| `build_index` | `retriever.py` | scikit-learn TF-IDF | Sentence-aware chunking + vector index |
| `qa` | `analysis.py` | GPT-OSS via Groq | Answer questions grounded in retrieved chunks with source citations |
| `summarize` | `analysis.py` | GPT-OSS via Groq | Executive summary + key insights extraction |

---

## Quick Start

### No technical skills needed → Double-click to run

DocIntel ships with **one-click launchers** that handle everything — they check
for Python, install all requirements, download the language model, ask for your
free API key once, start the app, and open your browser. No commands required.

| Your OS | Start (double-click) | Stop (double-click) |
|---------|----------------------|---------------------|
| **Windows** | `start.bat` | `stop.bat` |
| **macOS** | `Start.command` | `Stop.command` |
| **Linux** | `Start.sh` (or `bash Start.sh`) | `Stop.sh` (or `bash Stop.sh`) |
| **Any OS** | `python start.py` | `python start.py stop` |

*On macOS, if you see "cannot be opened because it is from an unidentified
developer", right-click the file → **Open** → **Open** once.*

### What you'll see (first run)

1. A **dark window** opens showing a numbered checklist `[1/4] → [4/4]` as
   every component is checked and installed.
2. If you don't have an API key yet, the window **explains exactly how to get
   a free one** (60 seconds at console.groq.com) and then asks you to paste it.
   You only do this once.
3. When everything is ready, the window says **"DocIntel is running!"** and your
   **browser opens automatically** to the app.
4. If the browser doesn't open, the window tells you to type
   **`http://localhost:8501`**.

> **Keep the dark window open** while using DocIntel. To quit, double-click the
> `Stop` file for your OS (or just close the window).

---

### Option 1: Web GUI (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/roypulseai/DocIntel.git
cd DocIntel

# 2. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 3. Launch the web interface
streamlit run app.py
```

Open **http://localhost:8501** in your browser. Enter your free Groq API key in the sidebar and upload a document.

> For most users, just double-clicking `start.bat` / `Start.command` /
> `Start.sh` is enough — no manual setup required.

### Option 2: CLI Demo

```bash
# Set your Groq API key
export GROQ_API_KEY=gsk_your_key_here    # Linux/macOS
set GROQ_API_KEY=gsk_your_key_here       # Windows CMD
$env:GROQ_API_KEY="gsk_your_key_here"    # Windows PowerShell

# Run the demo
python run_demo.py
```

### Option 3: Docker

```bash
docker build -t docintel .
docker run -p 8501:8501 -e GROQ_API_KEY=gsk_your_key_here docintel
```

---

## Getting Your Free Groq API Key

DocIntel uses [Groq](https://groq.com) for free LLM inference. No credit card required.

1. Go to **[console.groq.com](https://console.groq.com)**
2. Sign up for a free account (Google, GitHub, or email)
3. Navigate to **API Keys** in the left sidebar
4. Click **Create API Key**
5. Copy the key (starts with `gsk_`)
6. Paste it into DocIntel's sidebar or set it as an environment variable

**Free tier limits:** 14,400 requests/day, 500K tokens/day — more than enough for personal use.

---

## User Guide

### Using the Web GUI

#### Step 1: Enter Your API Key

When you first open DocIntel, you'll see a welcome screen. In the **left sidebar**:

1. Expand **"How to get your free API key"** for step-by-step instructions
2. Paste your Groq API key into the input field, then click **"Save API Key"**
3. Optionally select a model:
   - **GPT-OSS 120B** (default) — best quality, slightly slower
   - **GPT-OSS 20B** — fastest responses
   - **Qwen 3.6 27B** — good balance

#### Step 2: Provide a Document

Choose one of three input methods:

| Method | How To | Best For |
|--------|--------|----------|
| **Upload a file** | Click "Upload a file" → choose a `.txt`, `.md`, or `.csv` file | Documents you already have |
| **Paste text** | Click "Paste text" → paste any document content | Quick analysis of snippets |
| **Try a sample** | Click "Try a sample" → pick from 3 built-in examples | First-time exploration |

#### Step 3: View Results

Once a document is loaded, click the **"🚀 Analyze Document"** button. Results appear in:

- **Metrics bar** — Category, Confidence, Sentiment, Entity count at a glance
- **6 result tabs:**
  - 📝 **Summary** — Executive summary and key insights at a glance
  - 🏷️ **Classification** — Document category with confidence score and rationale
  - 🔍 **Entities** — Extracted entities grouped by type (PERSON, ORG, DATE, MONEY, etc.)
  - 💭 **Sentiment & Topics** — Sentiment polarity score and extracted key topics
  - 📚 **Document Index** — How the document was chunked for retrieval
  - 💬 **Ask Questions** — Type any question about the document

#### Step 4: Ask Questions (RAG Q&A)

1. Click the **💬 Ask Questions** tab
2. Type a question about the document and click **"Ask"**
3. The system retrieves the most relevant document chunks and generates a grounded answer
4. Sources are shown below the answer so you can verify accuracy

**Example questions:**
- "What is the transaction reference number?"
- "Who is the complainant and what is their contact information?"
- "What are the SLA terms in this contract?"

### Using the CLI

```bash
# Set API key
export GROQ_API_KEY=gsk_your_key_here

# Run with default sample document
python run_demo.py

# Use programmatically in your own code
from docintel.graph import run_docintel

result = run_docintel(
    text="Your document text here...",
    question="What is the main topic?"
)

print(result["classification"])     # Category + confidence
print(result["entities"])           # Extracted entities
print(result["sentiment_topic"])    # Sentiment + topics
print(result["answer"])             # QA answer with sources
```

### Programmatic Usage

```python
from docintel.ner import extract_entities
from docintel.retriever import chunk_text, TfidfRetriever
from docintel.analysis import classify_document, sentiment_and_topics, generate_answer

# Individual components can be used standalone
entities = extract_entities("Apple Inc. reported $394B revenue in 2024.")
# → [{"text": "Apple Inc.", "label": "ORG", ...}, {"text": "$394B", "label": "MONEY", ...}]

chunks = chunk_text(long_document)
retriever = TfidfRetriever(chunks)
results = retriever.retrieve("revenue figures", top_k=3)
```

---

## Project Structure

```
DocIntel/
├── app.py                      # Streamlit web GUI
├── run_demo.py                 # CLI demo script
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container build configuration
├── .env.example                # Environment variable template
├── .gitignore                  # Git ignore rules
├── LICENSE                     # MIT License
├── GUIDE.md                    # Detailed user guide
│
├── start.bat                   # Windows one-click launcher
├── stop.bat                    # Windows one-click stopper
├── Start.command               # macOS one-click launcher
├── Stop.command                # macOS/Linux one-click stopper
├── Start.sh                    # Linux one-click launcher
├── Stop.sh                     # Linux one-click stopper
├── start.py                    # Cross-platform launcher (python start.py)
│
├── docintel/                   # Core package
│   ├── __init__.py             # Package exports
│   ├── graph.py                # LangGraph StateGraph pipeline
│   ├── analysis.py             # LLM-backed analysis (classification, sentiment, QA)
│   ├── ner.py                  # Named Entity Recognition via spaCy
│   ├── retriever.py            # TF-IDF chunking and retrieval
│   ├── vector_store.py         # FAISS + sentence-transformers semantic search
│   ├── storage.py              # SQLite analysis-history persistence
│   └── tools/
│       └── stop_server.py      # Cross-platform server stopper
│
├── tests/
│   ├── test_graph.py           # Full graph orchestration + NER + retrieval
│   └── test_vector_store.py    # Semantic search + persistence round-trip
│
└── .github/
    └── workflows/
        └── ci.yml              # GitHub Actions CI pipeline
```

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM** | [GPT-OSS 120B](https://github.com/openai/gpt-oss) via [Groq](https://groq.com) | Classification, sentiment, QA — free tier |
| **Orchestration** | [LangGraph](https://github.com/langchain-ai/langgraph) | Agentic workflow with typed state |
| **NER** | [spaCy](https://spacy.io) `en_core_web_sm` | Real named entity recognition (not LLM-simulated) |
| **Retrieval** | [scikit-learn](https://scikit-learn.org) TF-IDF + [FAISS](https://github.com/facebookresearch/faiss) / [sentence-transformers](https://sbert.net) | Classical + semantic retrieval, cross-document search |
| **Web GUI** | [Streamlit](https://streamlit.io) | Interactive web interface |
| **Integration** | [LangChain](https://github.com/langchain-ai/langchain) | LLM abstraction layer |

---

## API Reference

### `run_docintel(text, question="")`

Execute the full pipeline. Returns a dict with all pipeline outputs.

**Parameters:**
- `text` (str): The document text to analyze
- `question` (str, optional): A question to answer about the document

**Returns:**

```python
{
    "classification": {
        "category": "Customer Complaint",       # Document category
        "confidence": 0.94,                      # Confidence score (0-1)
        "rationale": "Reports a billing dispute" # Why this classification
    },
    "entities": [
        {"text": "Maria Fontaine", "label": "PERSON", "start": 12, "end": 26},
        {"text": "Zurich", "label": "GPE", "start": 100, "end": 106}
    ],
    "sentiment_topic": {
        "sentiment": "negative",                 # positive|negative|neutral|mixed
        "sentiment_score": -0.4,                 # Polarity (-1.0 to 1.0)
        "topics": ["billing dispute", "refund delay"]
    },
    "chunks": ["chunk1 text...", "chunk2 text..."],
    "hits": [RetrievalHit(text=..., score=0.85, index=0)],
    "answer": {
        "text": "The reference is TXN-88213-CH. [Chunk 0]",
        "sources": [0]                           # Cited chunk indices
    }
}
```

### Individual Functions

```python
from docintel.ner import extract_entities
from docintel.retriever import chunk_text, TfidfRetriever
from docintel.analysis import classify_document, sentiment_and_topics, generate_answer
```

| Function | Input | Output |
|----------|-------|--------|
| `extract_entities(text)` | Document string | `list[dict]` with `text`, `label`, `start`, `end` |
| `chunk_text(text, max_words=200)` | Document string | `list[str]` of sentence-aware chunks |
| `TfidfRetriever(chunks)` | List of chunks | Retriever object with `.retrieve(query, top_k)` |
| `classify_document(text)` | Document string | `dict` with `category`, `confidence`, `rationale` |
| `sentiment_and_topics(text)` | Document string | `dict` with `sentiment`, `sentiment_score`, `topics` |
| `generate_answer(text, question, chunks)` | Doc, question, chunks | `dict` with `text`, `sources` |

---

## Testing

```bash
python -m pytest tests/ -q
```

The test suite covers:

| Test | What It Validates | LLM Mocked? |
|------|-------------------|-------------|
| `test_ner_runs_for_real` | spaCy NER extracts correct entity types | No |
| `test_chunking_and_retrieval_run_for_real` | TF-IDF chunking and cosine similarity retrieval | No |
| `test_full_graph_orchestration` | Complete LangGraph pipeline with state passing | Yes |
| `test_vector_store.py` | Semantic search ranking + JSON-safe persistence round-trip | No |

LLM-backed nodes are mocked for deterministic CI execution. NER, chunking, retrieval, semantic search, and graph orchestration run for real.

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes | — | Your Groq API key (starts with `gsk_`) |
| `GROQ_MODEL` | No | `openai/gpt-oss-120b` | Groq model to use |

### `.env` File

```bash
cp .env.example .env
# Edit .env with your API key
```

---

## Roadmap

- [ ] PDF and DOCX file support
- [x] Embedding-based retrieval (FAISS + sentence-transformers) & cross-document search
- [ ] Multi-language document support
- [ ] Batch document processing
- [ ] Export results as JSON/CSV/PDF
- [ ] Custom classification categories
- [ ] Conversation history for multi-turn Q&A
- [ ] Ollama support for fully offline usage

---

## Contributing

Contributions are welcome! Here's how:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Setup

```bash
git clone https://github.com/roypulseai/DocIntel.git
cd DocIntel
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python tests/test_graph.py  # Verify everything works
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Author

**Roy Pulse AI** — [roypulse.ai@gmail.com](mailto:roypulse.ai@gmail.com)

GitHub: [@roypulseai](https://github.com/roypulseai)

---

<p align="center">
  Built with ❤️ using open-source technologies<br>
  <sub>GPT-OSS • LangGraph • spaCy • Streamlit • Groq</sub>
</p>
