"""
DocIntel — Streamlit GUI
Run with: streamlit run app.py
"""

import os
import sys
import json
import re

from dotenv import load_dotenv

import streamlit as st

# Load API key / model from a local .env file if present (used by the
# one-click launchers), without overriding any real environment variables.
sys.path.insert(0, os.path.dirname(__file__))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

st.set_page_config(
    page_title="DocIntel — Document Intelligence",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .block-container { padding-top: 1.5rem; }
    div[data-testid="stSidebar"] { background-color: #161b22; }
    h1, h2, h3 { color: #e6edf3 !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border-radius: 6px 6px 0 0;
        padding: 8px 20px;
        color: #8b949e;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f6feb !important;
        color: white !important;
    }
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px 16px;
    }
    .entity-badge {
        display: inline-block;
        background-color: #1f6feb22;
        border: 1px solid #1f6feb;
        border-radius: 12px;
        padding: 2px 10px;
        margin: 2px 4px;
        font-size: 0.85em;
        color: #e6edf3;
    }
    .entity-label {
        font-weight: bold;
        color: #58a6ff;
        margin-right: 4px;
    }
    .qa-source {
        background-color: #161b22;
        border-left: 3px solid #1f6feb;
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 0 6px 6px 0;
        font-size: 0.9em;
        color: #8b949e;
    }
    .step-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 10px 16px;
        margin: 6px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .step-done { border-left: 3px solid #3fb950; }
    .step-running { border-left: 3px solid #f0883e; }
    .step-pending { border-left: 3px solid #30363d; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔑 Groq API Key (Free)")

    # Expandable guide for getting the key
    with st.expander("How to get your free API key", expanded=not bool(os.environ.get("GROQ_API_KEY", ""))):
        st.markdown("""
        **3 easy steps — takes 60 seconds:**

        1. Go to **[console.groq.com](https://console.groq.com)**
        2. Sign up / Log in (free, no credit card)
        3. Click **API Keys** → **Create API Key** → Copy it

        Paste your key below. It starts with `gsk_`.
        """)
        st.image("https://groq.com/wp-content/uploads/2024/03/Groq-logo-v2-4x-1.png", width=120)

    groq_key = st.text_input(
        "Paste your Groq API key",
        type="password",
        value=os.environ.get("GROQ_API_KEY", ""),
        placeholder="gsk_xxxxxxxxxxxxxxxx",
        help="Get yours free at console.groq.com",
    )
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key

    model = st.selectbox(
        "Model",
        ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"],
        index=0,
        help="120B = best quality | 20B = fastest",
    )
    os.environ["GROQ_MODEL"] = model

    st.divider()

    # ── Document Input ──────────────────────────────────────────────────────
    st.markdown("## 📁 Document Input")

    upload_method = st.radio(
        "How would you like to provide a document?",
        ["Upload a file", "Paste text", "Try a sample"],
        horizontal=True,
        label_visibility="visible",
    )

    document_text = ""

    if upload_method == "Upload a file":
        st.markdown("Supports `.txt`, `.md`, `.csv` files")
        uploaded = st.file_uploader(
            "Choose a document",
            type=["txt", "md", "csv"],
            label_visibility="collapsed",
        )
        if uploaded:
            document_text = uploaded.read().decode("utf-8", errors="replace")
            st.success(f"Loaded: {uploaded.name} ({len(document_text)} chars)")

    elif upload_method == "Paste text":
        document_text = st.text_area(
            "Paste your document text here",
            height=220,
            placeholder="Paste any document, report, email, complaint, article...",
        )

    else:
        sample_options = st.selectbox(
            "Choose a sample document",
            ["Customer Complaint", "News Article", "Legal Contract"],
        )
        samples = {
            "Customer Complaint": """
CUSTOMER COMPLAINT — Reference #CC-2026-4471

Submitted by: Maria Fontaine, Account Holder
Date: 24 August 2026
Branch: UBS Card Center, Zurich

I am writing to raise a formal complaint regarding a duplicate charge of
CHF 340.00 posted to my credit card account on 18 August 2026. The
transaction reference is TXN-88213-CH. I contacted the customer service
line on 20 August and was told a reversal would be processed within five
business days, but as of today the amount has not been refunded.

I have been a UBS customer since 2014 and have not experienced this issue
before. I would appreciate a prompt investigation and confirmation of the
refund timeline. I can be reached at maria.fontaine@example.ch or
+41 79 555 1122.

Regards,
Maria Fontaine
""",
            "News Article": """
TECHNOLOGY REPORT — AI Regulation Bill Advances in Senate

Washington, D.C. — August 28, 2026

The U.S. Senate voted 67-33 on Wednesday to advance the Artificial
Intelligence Accountability Act, moving closer to establishing the first
comprehensive federal framework for AI regulation.

Senator Maria Chen (D-CA), the bill's lead sponsor, called it "a
landmark moment for responsible innovation." The bill would require
companies deploying AI systems in critical infrastructure — healthcare,
finance, law enforcement — to conduct impact assessments and provide
transparency reports.

Tech industry groups including the Information Technology Industry
Foundation (ITIF) expressed concern that compliance costs could burden
startups. "We support responsible AI, but this legislation risks
stifling the very innovation that keeps America competitive," said
ITIF president Robert Atkinson.

The bill now moves to the House, where Speaker James Walker has
indicated bipartisan support but flagged potential amendments around
enforcement mechanisms. A final vote is expected before the end of
the year.
""",
            "Legal Contract": """
SERVICE AGREEMENT

Effective Date: 15 June 2026
Parties: CloudVault Inc. ("Provider") and Meridian Health Systems ("Client")

1. SCOPE OF SERVICES
Provider shall deliver cloud hosting, data backup, and 24/7 technical
support services for Client's electronic health records (EHR) platform
across three data centers located in Frankfurt, Dublin, and Singapore.

2. TERM
This Agreement shall commence on 1 July 2026 and continue for a period
of 36 months, unless terminated earlier in accordance with Section 9.

3. SERVICE LEVEL AGREEMENT (SLA)
Provider guarantees 99.95% uptime measured monthly. Failure to meet
this threshold entitles Client to service credits equal to 10% of
monthly fees per 0.1% below the guarantee, capped at 50% of the
monthly fee.

4. DATA PROTECTION
Provider shall comply with GDPR, HIPAA, and all applicable data
protection regulations. All data at rest shall be encrypted using
AES-256. Cross-border data transfers shall rely on Standard
Contractual Clauses (SCCs).

5. FEES
Client shall pay USD 48,000 per month, invoiced quarterly in advance.
Late payments accrue interest at 1.5% per month.
""",
        }
        document_text = samples[sample_options]
        st.caption(f"Sample loaded: {sample_options} ({len(document_text)} chars)")

    st.divider()
    st.markdown(
        "**Powered by** [Groq](https://groq.com) (free) + "
        "[LangGraph](https://github.com/langchain-ai/langgraph) + "
        "[spaCy](https://spacy.io)"
    )


# ── Main content ────────────────────────────────────────────────────────────
st.markdown("# 📄 DocIntel")
st.markdown("*Agentic document intelligence — classify, extract, analyze, and ask questions about any document.*")

# ── Empty state ─────────────────────────────────────────────────────────────
if not groq_key:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 👋 Welcome to DocIntel")
        st.markdown("""
        Get started in **2 steps**:

        1. **Get a free Groq API key** at [console.groq.com](https://console.groq.com) (no credit card needed)
        2. **Paste it in the sidebar** on the left

        Then upload a document or try the sample!
        """)
        st.info("**What DocIntel does:**\n"
                "- Classifies your document automatically\n"
                "- Extracts named entities (people, orgs, dates, money)\n"
                "- Analyzes sentiment and key topics\n"
                "- Lets you ask questions about the document")
    st.stop()

if not document_text.strip():
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 📁 No document loaded")
        st.markdown("Use the **sidebar** to upload a file, paste text, or try a sample document.")
    st.stop()


# ── Run pipeline ────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, hash_funcs={type(document_text): id})
def run_pipeline(text: str) -> dict:
    from docintel.graph import run_docintel
    return run_docintel(text=text, question="")


# Progress display
st.markdown("---")
progress_placeholder = st.empty()

with progress_placeholder.container():
    st.markdown("#### ⚡ Running Pipeline...")
    steps = ["Classifying document", "Extracting entities (NER)", "Analyzing sentiment & topics", "Building search index"]
    step_containers = []
    for i, step in enumerate(steps):
        c = st.empty()
        step_containers.append(c)
        c.markdown(f'<div class="step-box step-running">⏳ {step}...</div>', unsafe_allow_html=True)

    result = run_pipeline(document_text)

    for i, step in enumerate(steps):
        step_containers[i].markdown(f'<div class="step-box step-done">✅ {step}</div>', unsafe_allow_html=True)

progress_placeholder.empty()


# ── Results ─────────────────────────────────────────────────────────────────
classification = result.get("classification", {})
sentiment = result.get("sentiment_topic", {})
entities = result.get("entities", [])
chunks = result.get("chunks", [])

# Top-level metrics row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Category", classification.get("category", "N/A"))
with col2:
    score = classification.get("confidence", 0)
    st.metric("Confidence", f"{score:.0%}")
with col3:
    sent = sentiment.get("sentiment", "N/A")
    st.metric("Sentiment", sent.title() if isinstance(sent, str) else sent)
with col4:
    st.metric("Entities Found", len(entities))

st.divider()

# Tabs
tab_classify, tab_entities, tab_sentiment, tab_index, tab_qa = st.tabs(
    ["🏷️ Classification", "🔍 Entities", "💭 Sentiment & Topics", "📚 Document Index", "💬 Ask Questions"]
)

with tab_classify:
    st.subheader("Document Classification")
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.markdown(f"**Category:** `{classification.get('category', 'N/A')}`")
        rationale = classification.get("rationale", "")
        if rationale:
            st.markdown(f"**Rationale:** {rationale}")
    with col_b:
        score = classification.get("confidence", 0)
        st.metric("Confidence", f"{score:.0%}")

with tab_entities:
    st.subheader("Named Entities (spaCy NER)")
    if entities:
        # Group by label
        from collections import defaultdict
        grouped = defaultdict(list)
        for ent in entities:
            grouped[ent["label"]].append(ent["text"])

        for label, texts in sorted(grouped.items()):
            st.markdown(f"**{label}:**")
            for t in texts:
                st.markdown(
                    f'<span class="entity-badge">'
                    f'<span class="entity-label">{label}</span>{t}'
                    f'</span>',
                    unsafe_allow_html=True,
                )
        st.divider()
        with st.expander("View raw entity data"):
            st.json(entities)
    else:
        st.info("No entities detected in this document.")

with tab_sentiment:
    st.subheader("Sentiment & Topic Analysis")
    col_a, col_b = st.columns([1, 1])
    with col_a:
        sent = sentiment.get("sentiment", "N/A")
        score = sentiment.get("sentiment_score", 0)
        st.metric("Sentiment", sent.title() if isinstance(sent, str) else sent)
        st.metric("Polarity Score", f"{score:+.2f}")
    with col_b:
        topics = sentiment.get("topics", [])
        if topics:
            st.markdown("**Extracted Topics:**")
            for t in topics:
                st.markdown(f"- `{t}`")
    with st.expander("View raw data"):
        st.json(sentiment)

with tab_index:
    st.subheader("Document Chunks (TF-IDF Index)")
    st.caption(f"Document split into {len(chunks)} chunks for retrieval")
    for i, chunk in enumerate(chunks):
        with st.expander(f"Chunk {i} ({len(chunk.split())} words)"):
            st.text(chunk)

with tab_qa:
    st.subheader("Ask Questions About This Document")
    st.caption("Type any question — the AI will search relevant parts of the document and give a grounded answer with sources.")

    question = st.text_input(
        "Your question",
        placeholder="e.g. What is the transaction reference number?",
        label_visibility="collapsed",
    )

    if question:
        with st.spinner("Searching document and generating answer..."):
            from docintel.retriever import TfidfRetriever, chunk_text
            from docintel.analysis import generate_answer

            _chunks = chunk_text(document_text)
            _retriever = TfidfRetriever(_chunks)
            _hits = _retriever.retrieve(question, top_k=5)
            _chunk_texts = [h.text for h in _hits]
            qa_result = generate_answer(document_text, question, _chunk_texts)

        answer_text = qa_result.get("text", "No answer generated.")
        sources = qa_result.get("sources", [])

        st.markdown("#### Answer")
        st.markdown(answer_text)

        if sources:
            st.markdown("#### Sources")
            for idx in sources:
                if isinstance(idx, int) and idx < len(_chunks):
                    st.markdown(
                        f'<div class="qa-source"><strong>Chunk {idx}:</strong> {_chunks[idx][:300]}...</div>',
                        unsafe_allow_html=True,
                    )
