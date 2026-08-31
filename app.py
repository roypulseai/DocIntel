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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --bg: #0d1117;
        --bg-2: #161b22;
        --bg-3: #1c2128;
        --border: #30363d;
        --text: #e6edf3;
        --muted: #8b949e;
        --accent: #58a6ff;
        --accent-2: #1f6feb;
        --success: #3fb950;
        --warn: #f0883e;
        --purple: #bc8cff;
        --pink: #ff7b72;
    }

    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

    .stApp { background: radial-gradient(1200px 800px at 85% -10%, #1f6feb14, transparent 60%),
                    radial-gradient(900px 700px at -10% 110%, #bc8cff0d, transparent 55%),
                    linear-gradient(180deg, var(--bg) 0%, #0a0d12 100%); }

    .block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 1150px; }
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #11161d 0%, #0d1117 100%);
        border-right: 1px solid var(--border);
    }
    div[data-testid="stSidebar"] .block-container { padding-top: 1.2rem; }

    h1, h2, h3, h4 { color: var(--text) !important; letter-spacing: -0.01em; }
    h1 { font-weight: 800; }
    p, li { color: var(--text); }

    /* ── Hero title ── */
    .hero {
        background: linear-gradient(100deg, #1f6feb22, #bc8cff1a);
        border: 1px solid #1f6feb33;
        border-radius: 16px;
        padding: 22px 26px;
        margin-bottom: 24px;
    }
    .hero h1 { font-size: 2.1rem; margin: 0 0 6px 0; }
    .hero-title-grad {
        background: linear-gradient(90deg, #58a6ff, #bc8cff, #58a6ff);
        -webkit-background-clip: text; background-clip: text;
        -webkit-text-fill-color: transparent; color: transparent;
    }
    .hero p { color: var(--muted); margin: 0; font-size: 1.05rem; }

    /* ── Buttons ── */
    .stButton > button, .stFormSubmitButton > button {
        border-radius: 10px;
        font-weight: 600;
        border: 1px solid var(--border) !important;
        transition: all .15s ease;
    }
    .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
        background: linear-gradient(90deg, #1f6feb, #2f81f7);
        border: none !important;
        color: white;
        box-shadow: 0 4px 14px #1f6feb33;
    }
    .stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px #1f6feb55;
    }

    /* ── Metrics ── */
    div[data-testid="stMetric"] {
        background: linear-gradient(160deg, var(--bg-2), var(--bg-3));
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 2px 10px #00000022;
    }
    div[data-testid="stMetricLabel"] { color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: .04em; }
    div[data-testid="stMetricValue"] { color: var(--text); font-weight: 700; font-size: 1.35rem; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 1px solid var(--border); }
    .stTabs [data-baseweb="tab"] {
        background: var(--bg-2);
        border: 1px solid var(--border);
        border-radius: 10px 10px 0 0;
        padding: 10px 18px;
        color: var(--muted);
        font-weight: 600;
        transition: all .15s ease;
    }
    .stTabs [data-baseweb="tab"]:hover { color: var(--text); background: var(--bg-3); }
    .stTabs [aria-selected="true"] {
        background: var(--accent-2) !important;
        border-color: var(--accent-2) !important;
        color: white !important;
    }

    /* ── Summary card ── */
    .summary-card {
        background: linear-gradient(150deg, #1f6feb18, #bc8cff12);
        border: 1px solid #1f6feb44;
        border-left: 5px solid var(--accent);
        border-radius: 14px;
        padding: 18px 22px;
        font-size: 1.05rem;
        line-height: 1.65;
        color: var(--text);
        margin-bottom: 20px;
    }
    .insight-row {
        display: flex; align-items: flex-start; gap: 12px;
        background: var(--bg-2);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 12px 16px;
        margin: 8px 0;
    }
    .insight-num {
        flex-shrink: 0; width: 26px; height: 26px;
        border-radius: 50%;
        background: linear-gradient(135deg, #1f6feb, #bc8cff);
        color: white; font-weight: 700; font-size: 0.85rem;
        display: flex; align-items: center; justify-content: center;
    }

    /* ── Entities ── */
    .entity-badge {
        display: inline-block;
        background: #1f6feb1f;
        border: 1px solid #1f6feb;
        border-radius: 100px;
        padding: 4px 12px;
        margin: 3px 4px;
        font-size: 0.85em;
        color: var(--text);
    }
    .entity-label { font-weight: 700; color: var(--accent); margin-right: 6px; }

    /* ── QA ── */
    .qa-source {
        background: var(--bg-2);
        border-left: 3px solid var(--accent-2);
        padding: 10px 14px;
        margin: 6px 0;
        border-radius: 0 10px 10px 0;
        font-size: 0.9em;
        color: var(--muted);
    }
    .answer-card {
        background: var(--bg-2);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 16px 18px;
        font-size: 1.02rem;
        line-height: 1.6;
    }

    /* ── Pipeline steps ── */
    .step-box {
        background: var(--bg-2);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 11px 16px;
        margin: 6px 0;
        display: flex; align-items: center; gap: 10px;
        font-weight: 500;
        transition: all .2s ease;
    }
    .step-done { border-left: 4px solid var(--success); color: var(--text); }
    .step-running { border-left: 4px solid var(--warn); color: var(--text); animation: pulse 1.2s ease-in-out infinite; }
    .step-pending { border-left: 4px solid var(--border); color: var(--muted); }
    @keyframes pulse { 0%,100% {opacity:1;} 50% {opacity:.55;} }

    /* ── Topic pills ── */
    .topic-pill {
        display: inline-block;
        background: #bc8cff1c;
        border: 1px solid #bc8cff55;
        color: var(--purple);
        border-radius: 100px;
        padding: 5px 14px;
        margin: 3px 5px;
        font-weight: 600;
        font-size: 0.9em;
    }

    /* ── Cards / info boxes ── */
    div[data-testid="stExpander"] {
        background: var(--bg-2);
        border: 1px solid var(--border);
        border-radius: 12px;
        overflow: hidden;
    }
    div[data-testid="stFileUploaderDropzone"] {
        background: var(--bg-2);
        border: 1px dashed var(--accent-2);
        border-radius: 12px;
    }
    .stCaption, [data-testid="stCaptionContainer"] p { color: var(--muted); }

    /* Sidebar headers */
    [data-testid="stSidebar"] h2 { font-size: 1.1rem; }
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

    with st.form("api_key_form", clear_on_submit=False):
        groq_key = st.text_input(
            "Paste your Groq API key",
            type="password",
            value=os.environ.get("GROQ_API_KEY", ""),
            placeholder="gsk_xxxxxxxxxxxxxxxx",
            help="Get yours free at console.groq.com. Click 'Save API Key' to apply it.",
        )
        save_key = st.form_submit_button("Save API Key")
        if save_key and groq_key:
            os.environ["GROQ_API_KEY"] = groq_key
            st.success("API key saved!")
    if not groq_key and save_key:
        st.warning("Please paste your API key before saving.")

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
st.markdown("""
<div class="hero">
    <h1><span class="hero-title-grad">📄 DocIntel</span></h1>
    <p>Agentic document intelligence — summarize, classify, extract, analyze, and ask questions about any document.</p>
</div>
""", unsafe_allow_html=True)

# ── Empty state ─────────────────────────────────────────────────────────────
if not groq_key:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        st.markdown("### 👋 Welcome to DocIntel")
        st.markdown("Get started in **2 quick steps**:")
        st.markdown("""
        1. **Get a free Groq API key** at [console.groq.com](https://console.groq.com) — no credit card needed
        2. **Paste it in the sidebar** on the left, then click **Save API Key**
        """)
        st.markdown("Then upload a document or try the sample, and hit **Analyze Document**!")
        st.info("**What DocIntel does:**\n"
                "- ✨ Summarizes the document & extracts key insights\n"
                "- 🏷️ Classifies your document automatically\n"
                "- 🔍 Extracts named entities (people, orgs, dates, money)\n"
                "- 💭 Analyzes sentiment and key topics\n"
                "- 💬 Lets you ask questions about the document")
    st.stop()

if not document_text.strip():
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        st.markdown("### 📁 No document loaded")
        st.markdown("Use the **sidebar** to upload a file, paste text, or try a sample document, then click **Analyze Document**.")
    st.stop()


# ── Run pipeline (triggered by the Analyze button) ──────────────────────────
st.markdown("---")
col_btn, col_hint = st.columns([1, 3])
with col_btn:
    analyze_clicked = st.button(
        "🚀 Analyze Document",
        type="primary",
        help="Run summary, classification, entities, sentiment, and indexing on the loaded document.",
    )
with col_hint:
    if not analyze_clicked:
        st.caption("Your document is loaded and ready. Click **Analyze Document** to run the full analysis.")

if not analyze_clicked:
    st.stop()


@st.cache_data(show_spinner=False, hash_funcs={type(document_text): id})
def run_pipeline(text: str) -> dict:
    from docintel.graph import run_docintel
    return run_docintel(text=text, question="")


# Progress display
progress_placeholder = st.empty()

with progress_placeholder.container():
    st.markdown("#### ⚡ Running Pipeline...")
    steps = ["Classifying document", "Extracting entities (NER)", "Analyzing sentiment & topics", "Building search index", "Summarizing key insights"]
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
summary = result.get("summary", {})

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
tab_summary, tab_classify, tab_entities, tab_sentiment, tab_index, tab_qa = st.tabs(
    ["📝 Summary", "🏷️ Classification", "🔍 Entities", "💭 Sentiment & Topics", "📚 Document Index", "💬 Ask Questions"]
)

with tab_summary:
    st.subheader("Executive Summary & Key Insights")
    sum_text = summary.get("summary", "")
    if sum_text:
        st.markdown(f'<div class="summary-card">{sum_text}</div>', unsafe_allow_html=True)
    insights = summary.get("key_insights", [])
    if insights:
        st.markdown("#### 🔑 Key Insights")
        for i, ins in enumerate(insights, 1):
            st.markdown(f'<div class="insight-row"><span class="insight-num">{i}</span>{ins}</div>', unsafe_allow_html=True)
    if not sum_text and not insights:
        st.info("No summary was generated for this document.")

with tab_classify:
    st.subheader("Document Classification")
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.markdown(
            f'<div class="summary-card" style="border-left:5px solid var(--purple);">'
            f'<strong>Category:</strong> {classification.get("category", "N/A")}'
            f'</div>',
            unsafe_allow_html=True,
        )
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
            pills = "".join(f'<span class="topic-pill">{t}</span>' for t in topics)
            st.markdown(f'<div>{pills}</div>', unsafe_allow_html=True)
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

    with st.form("qa_form"):
        question = st.text_input(
            "Your question",
            placeholder="e.g. What is the transaction reference number?",
            label_visibility="collapsed",
        )
        ask = st.form_submit_button("💬 Ask")

    if question and ask:
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
        st.markdown(f'<div class="answer-card">{answer_text}</div>', unsafe_allow_html=True)

        if sources:
            st.markdown("#### Sources")
            for idx in sources:
                if isinstance(idx, int) and idx < len(_chunks):
                    st.markdown(
                        f'<div class="qa-source"><strong>Chunk {idx}:</strong> {_chunks[idx][:300]}...</div>',
                        unsafe_allow_html=True,
                    )
