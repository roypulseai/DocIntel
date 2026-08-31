"""Quick smoke test for the VectorStore module."""
import os
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

from docintel.vector_store import VectorStore

vs = VectorStore()
vs.add_document(
    "I was charged CHF 340.00 twice. Please refund the duplicate amount.", "complaint.txt"
)
vs.add_document(
    "The Senate voted 67-33 to advance the AI Accountability Act.", "news.txt"
)
vs.add_document(
    "CloudVault agrees to 99.95% uptime SLA for health records.", "contract.txt"
)
vs.build_index()
print(f"[OK] Indexed {len(vs)} chunks from 3 documents")

# Semantic search — "refund" should match complaint, not news/contract
hits = vs.search("refund money", top_k=3)
print(f"\nQuery: 'refund money' ({len(hits)} hits)")
for h in hits:
    print(f"  [{h.score:.3f}] {h.source}: {h.text[:70]}...")
assert hits[0].source == "complaint.txt", f"Expected complaint first, got {hits[0].source}"
print("\n[OK] Semantic ranking correct: complaint ranked first")

# Round-trip persistence
db_data = vs.to_db()
restored = VectorStore.from_db(db_data)
h2 = restored.search("uptime SLA", top_k=1)
assert h2 and h2[0].source == "contract.txt", f"Expected contract, got {h2}"
print("[OK] Persistence round-trip works")

# Merge test
vs2 = VectorStore()
vs2.add_document("The provider guarantees AES-256 encryption.", "policy.txt")
vs2.build_index()
merged = VectorStore.merge([vs, vs2])
h3 = merged.search("encryption", top_k=1)
assert h3 and h3[0].source == "policy.txt"
print(f"[OK] Merged index works ({len(merged)} chunks)")

print("\nAll VectorStore tests passed.")
