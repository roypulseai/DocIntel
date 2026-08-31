import json
import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from docintel.graph import run_docintel

SAMPLE_DOC = """
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
"""

if __name__ == "__main__":
    if not os.environ.get("GROQ_API_KEY"):
        print("Set GROQ_API_KEY before running. Get a free key at https://console.groq.com")
        sys.exit(1)

    result = run_docintel(
        text=SAMPLE_DOC,
        question="What is the transaction reference number and how much was the duplicate charge?",
    )

    print("=== Classification ===")
    print(json.dumps(result["classification"], indent=2))

    print("\n=== Named Entities (spaCy) ===")
    for ent in result["entities"]:
        print(f"  {ent['label']:>10} | {ent['text']}")

    print("\n=== Sentiment & Topics ===")
    print(json.dumps(result["sentiment_topic"], indent=2))

    print("\n=== RAG QA (TF-IDF retrieval + grounded answer) ===")
    print(json.dumps(result["answer"], indent=2))
