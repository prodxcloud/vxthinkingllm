"""
VaLLM Embedding & Vector Match Scoring Tests
=============================================

Author: Joel Otepa Wembo
https://joelwembo.com

DESCRIPTION
===========
Tests that validate the VaLLM embedding pipeline, FAISS vector search,
and query-to-document match scoring. Tests exercise:

    1. Embedding generation (sentence-transformers/all-MiniLM-L6-v2)
    2. FAISS index search (semantic retrieval)
    3. Query-to-document match scoring with cosine similarity
    4. Provisioning query classification accuracy
    5. Cross-query semantic discrimination

The scoring pipeline:
    1. Cosine similarity via sentence-transformer embeddings
    2. FAISS nearest-neighbor search
    3. Match percentage computation

PREREQUISITES
=============
    pip install pytest pytest-asyncio numpy

    # FAISS index must be built first:
    python -m app.services.ai.ml.precompute

USAGE
=====
    # Run all embedding tests
    pytest app/tests/tests_embedding.py -v -s

    # Run only match scoring tests
    pytest app/tests/tests_embedding.py -v -s -k "match"

    # Run only FAISS search tests
    pytest app/tests/tests_embedding.py -v -s -k "faiss"
"""

import asyncio
import atexit
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import numpy as np

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_APP_DIR = _PROJECT_ROOT / "app"
for _p in [str(_PROJECT_ROOT), str(_APP_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

DATASETS_DIR = _APP_DIR / "data" / "datasets"

# ---------------------------------------------------------------------------
# Scorecard
# ---------------------------------------------------------------------------
_SCORECARD: Dict[str, Dict[str, Any]] = {}
_TEST_COUNTER = 0


def _record_score(test_name: str, score: int, details: str = ""):
    global _TEST_COUNTER
    _TEST_COUNTER += 1
    score = max(1, min(10, score))
    bar = "#" * score + "." * (10 - score)
    label = (
        "PERFECT" if score == 10 else
        "EXCELLENT" if score >= 8 else
        "GOOD" if score >= 6 else
        "FAIR" if score >= 4 else
        "POOR"
    )
    _SCORECARD[f"Test {_TEST_COUNTER}"] = {
        "name": test_name, "score": score, "label": label, "details": details,
    }
    print(f"\n  {'=' * 65}")
    print(f"  [Test {_TEST_COUNTER}] {test_name}")
    print(f"  Score: {score}/10 [{bar}] {label}")
    if details:
        print(f"  Details: {details}")
    print(f"  {'=' * 65}")


def _print_final_scorecard():
    if not _SCORECARD:
        return
    total = sum(v["score"] for v in _SCORECARD.values())
    count = len(_SCORECARD)
    avg = total / count if count else 0
    print("\n\n" + "=" * 70)
    print("  VALLM EMBEDDING & MATCH SCORING - FINAL SCORECARD")
    print("=" * 70)
    for key, val in _SCORECARD.items():
        bar = "#" * val["score"] + "." * (10 - val["score"])
        print(f"  {key:>8} | {val['score']:>2}/10 [{bar}] {val['label']:<10} | {val['name']}")
    print("-" * 70)
    print(f"  {'TOTAL':>8} | {total}/{count * 10}  Average: {avg:.1f}/10")
    overall = (
        "EXCELLENT" if avg >= 8 else "GOOD" if avg >= 6 else
        "NEEDS IMPROVEMENT" if avg >= 4 else "CRITICAL ISSUES"
    )
    print(f"  Overall Assessment: {overall}")
    print("=" * 70)


atexit.register(_print_final_scorecard)


# ============================================================================
# SAMPLE CLOUD OPERATIONS DATA
# ============================================================================

VM_QUERY = "Deploy EC2 instance t3.medium 50GB gp3 Ubuntu in us-west-2"
K8S_QUERY = "Create an EKS cluster, 3 nodes, m5.large, kubernetes 1.29 in us-east-1"
DOCKER_QUERY = "Run a nginx Docker container, port 80:80"
DB_QUERY = "Deploy PostgreSQL database, version 16, name analytics_db"
FASTAPI_QUERY = "Deploy FastAPI app billing-api, port 8000, http port 80"
WEBSITE_QUERY = "Deploy static website to nginx on docs.example.com"
IAM_ROLE_QUERY = "Create an IAM role for EC2 instances with S3 read access"
VPC_QUERY = "Create a VPC with CIDR 10.0.0.0/16 and NAT gateway in us-east-1"
SG_QUERY = "Create a security group allowing SSH, HTTP, and HTTPS"
ALB_QUERY = "Create an Application Load Balancer with target group on port 80"
TROUBLESHOOT_QUERY = "My EKS pods keep crashing with OOM errors"
COST_QUERY = "How to reduce AWS EC2 costs?"
GENERAL_QUERY = "What is the weather today?"

PROVISION_QUERIES = [
    VM_QUERY, K8S_QUERY, DOCKER_QUERY, DB_QUERY, FASTAPI_QUERY, WEBSITE_QUERY,
    IAM_ROLE_QUERY, VPC_QUERY, SG_QUERY, ALB_QUERY,
]
NON_PROVISION_QUERIES = [TROUBLESHOOT_QUERY, COST_QUERY, GENERAL_QUERY]

CLOUD_DOCUMENTS = [
    "Deploy ec2 instance 30gb t2 micro ubuntu in us-east-1 with SSH access",
    "Create an EKS cluster, 4 nodes, m5.xlarge in eu-west-1 with Calico CNI",
    "Run a redis Docker container on port 6379:6379 with persistent volume",
    "Deploy MySQL database version 8.0 name orders_db user root",
    "Deploy FastAPI to app-770.example.com, port 8000 with Gunicorn workers",
    "Deploy static website to nginx on web-103.example.com with SSL",
    "Create IAM role for EC2 with assume role policy for s3 read access",
    "Create VPC 10.0.0.0/16 with NAT gateway, 3 public and 3 private subnets",
    "Create security group allowing SSH port 22 and HTTPS port 443 from anywhere",
    "Create Application Load Balancer with target group HTTP port 80 health check",
    "Set up CI/CD pipeline with GitHub Actions and ArgoCD",
    "Deploy Terraform state backend with S3 and DynamoDB locking",
]


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def vector_store(event_loop):
    """Initialize the VectorStore (loads embeddings model + FAISS index)."""
    try:
        from app.services.ai.ml.embeddings import VectorStore
    except ImportError:
        from services.ai.ml.embeddings import VectorStore

    data_dir = str(_APP_DIR / "data")
    vs = VectorStore(data_dir=data_dir)
    event_loop.run_until_complete(vs.initialize())
    return vs


# ============================================================================
# TESTS
# ============================================================================

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestEmbeddingGeneration:
    """Test embedding model and vector generation."""

    def test_embedding_model_loaded(self, vector_store):
        """Verify the embedding model is loaded and functional."""
        model = getattr(vector_store, "model", None)

        score = 1
        details = []

        if model is not None:
            score = 7
            print(f"  Model loaded: True")
            model_name = getattr(model, "model_card_data", {})
            print(f"  Model info: {type(model).__name__}")
        else:
            details.append("embedding model not loaded")

        _record_score("Embedding Model Loaded", score,
                       "; ".join(details) if details else "Model ready")

    def test_embedding_generation(self, vector_store):
        """Generate embeddings for cloud operations texts and validate shape."""
        model = getattr(vector_store, "model", None)
        if model is None:
            _record_score("Embedding Generation", 2, "model not loaded")
            pytest.skip("Embedding model not loaded")

        texts = [
            "Senior DevOps engineer with 10 years of Kubernetes and AWS experience",
            "Deploy a PostgreSQL database on RDS with Multi-AZ failover",
            "French pastry chef specializing in croissants and macarons",
        ]

        embeddings = model.encode(texts, convert_to_numpy=True)
        assert embeddings.shape[0] == 3
        dim = embeddings.shape[1]
        assert dim > 0

        norms = np.linalg.norm(embeddings, axis=1)
        dist_01 = np.linalg.norm(embeddings[0] - embeddings[1])
        dist_02 = np.linalg.norm(embeddings[0] - embeddings[2])

        print(f"  Shape: {embeddings.shape}")
        print(f"  Dimensions: {dim}")
        print(f"  L2 norms: {norms.round(4).tolist()}")
        print(f"  Distance(devops, postgres): {dist_01:.4f}")
        print(f"  Distance(devops, pastry):   {dist_02:.4f}")

        score = 5
        details = []

        if dim in (384, 768):
            score += 2
        else:
            details.append(f"unexpected dim={dim}")

        if dist_02 > dist_01:
            score += 2
            print(f"  Correct: pastry chef is further from DevOps than Postgres")
        else:
            score += 1
            details.append("semantic discrimination weak")

        if all(abs(n - norms.mean()) < 0.5 for n in norms):
            score += 1

        _record_score("Embedding Generation", min(score, 10),
                       "; ".join(details) if details else f"dim={dim}, good discrimination")

    def test_cosine_similarity_pairs(self, vector_store):
        """Test cosine similarity between semantically similar and dissimilar pairs."""
        model = getattr(vector_store, "model", None)
        if model is None:
            _record_score("Cosine Similarity Pairs", 2, "model not loaded")
            pytest.skip("Embedding model not loaded")

        similar_a = "Deploy EC2 instance with Ubuntu in us-east-1"
        similar_b = "Launch a virtual machine running Ubuntu on AWS"
        dissimilar = "Recipe for chocolate cake with vanilla frosting"
        identical = "Deploy Kubernetes cluster with 3 nodes"

        emb = model.encode([similar_a, similar_b, dissimilar, identical, identical],
                           convert_to_numpy=True)
        emb_norm = emb / np.linalg.norm(emb, axis=1, keepdims=True)

        sim_similar = float(np.dot(emb_norm[0], emb_norm[1]))
        sim_dissimilar = float(np.dot(emb_norm[0], emb_norm[2]))
        sim_identical = float(np.dot(emb_norm[3], emb_norm[4]))

        def _grade(v):
            pct = round(max(v * 100, 0), 1)
            g = "STRONG" if pct >= 85 else "GOOD" if pct >= 70 else "PARTIAL" if pct >= 50 else "WEAK" if pct >= 30 else "LOW"
            return pct, g

        p1, g1 = _grade(sim_similar)
        p2, g2 = _grade(sim_dissimilar)
        p3, g3 = _grade(sim_identical)

        print(f"  Similar pair:    {sim_similar:.4f}  Match {p1:.0f}% [{g1}]")
        print(f"  Dissimilar pair: {sim_dissimilar:.4f}  Match {p2:.0f}% [{g2}]")
        print(f"  Identical pair:  {sim_identical:.4f}  Match {p3:.0f}% [{g3}]")

        gap = sim_similar - sim_dissimilar
        print(f"  Gap (sim - dissim): {gap:.4f}")

        score = 5
        details = []

        assert sim_similar > sim_dissimilar, "Similar texts should score higher"
        assert sim_identical >= 0.99, f"Identical texts should be ~1.0, got {sim_identical:.4f}"

        if gap > 0.3:
            score += 3
        elif gap > 0.15:
            score += 2
            details.append(f"moderate gap ({gap:.3f})")
        else:
            score += 1
            details.append(f"narrow gap ({gap:.3f})")

        if sim_identical >= 0.999:
            score += 2
        elif sim_identical >= 0.99:
            score += 1

        _record_score("Cosine Similarity Pairs", min(score, 10),
                       "; ".join(details) if details else f"gap={gap:.3f}, identical={sim_identical:.4f}")


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestFAISSSearch:
    """Test FAISS vector index search."""

    def test_faiss_index_stats(self, event_loop, vector_store):
        """Check FAISS index is loaded with vectors."""
        if hasattr(vector_store, "get_vector_store_stats"):
            stats = event_loop.run_until_complete(vector_store.get_vector_store_stats())
        else:
            faiss_index = getattr(vector_store, "faiss_index", None)
            total = faiss_index.ntotal if faiss_index else 0
            stats = {"total_vectors": total, "by_type": {}}

        score = 3
        details = []

        total = stats.get("total_vectors", 0)
        print(f"  Total vectors: {total}")
        print(f"  Embedding dim: {getattr(vector_store, 'embedding_dim', '?')}")
        print(f"  Documents: {len(getattr(vector_store, 'documents', []))}")

        if total == 0:
            score = 2
            details.append("FAISS index empty - run: python -m app.services.ai.ml.precompute")
        elif total < 50:
            score = 5
            details.append(f"only {total} vectors")
        elif total < 500:
            score = 7
        else:
            score = 9

        by_type = stats.get("by_type", {})
        if by_type:
            print(f"  By type: {by_type}")
            score = min(score + 1, 10)

        _record_score("FAISS Index Stats", score,
                       "; ".join(details) if details else f"{total} vectors indexed")

    def test_faiss_search_provision(self, event_loop, vector_store):
        """Search FAISS for provisioning-related documents."""
        faiss_index = getattr(vector_store, "faiss_index", None)
        total = faiss_index.ntotal if faiss_index else 0
        if total == 0:
            _record_score("FAISS Search (provision)", 2, "index empty")
            pytest.skip("FAISS index empty")

        results = event_loop.run_until_complete(
            vector_store.search(query=VM_QUERY, top_k=5)
        )

        score = 3
        details = []

        print(f"  Query: {VM_QUERY[:60]}...")
        print(f"  Results: {len(results)}")

        if not results:
            score = 2
            details.append("no results")
        else:
            score = 5
            for i, r in enumerate(results[:5]):
                doc = (r.get("document", "") or "")[:100].replace("\n", " ")
                s = r.get("score", 0)
                pct = round(min(max(s * 100, 0), 100), 1)
                grade = "STRONG" if pct >= 85 else "GOOD" if pct >= 70 else "PARTIAL" if pct >= 50 else "WEAK" if pct >= 30 else "LOW"
                print(f"    #{i+1}: score={s:.4f}  Match {pct:.0f}% [{grade}]  {doc}...")

            if len(results) >= 5:
                score += 1

            top_score = results[0].get("score", 0)
            if top_score > 0.7:
                score += 3
            elif top_score > 0.5:
                score += 2
            elif top_score > 0.3:
                score += 1
            else:
                details.append(f"top score low ({top_score:.3f})")

        _record_score("FAISS Search (provision)", min(score, 10),
                       "; ".join(details) if details else f"{len(results)} results")

    def test_faiss_search_troubleshooting(self, event_loop, vector_store):
        """Search FAISS for troubleshooting content."""
        faiss_index = getattr(vector_store, "faiss_index", None)
        total = faiss_index.ntotal if faiss_index else 0
        if total == 0:
            _record_score("FAISS Search (troubleshoot)", 2, "index empty")
            pytest.skip("FAISS index empty")

        results = event_loop.run_until_complete(
            vector_store.search(query=TROUBLESHOOT_QUERY, top_k=5)
        )

        score = 5 if results else 2
        print(f"  Query: {TROUBLESHOOT_QUERY[:60]}...")
        print(f"  Results: {len(results)}")

        if results:
            for i, r in enumerate(results[:3]):
                doc = (r.get("document", "") or "")[:100].replace("\n", " ")
                s = r.get("score", 0)
                print(f"    #{i+1}: score={s:.4f}  {doc}...")
            if results[0].get("score", 0) > 0.3:
                score += 3
            else:
                score += 1

        _record_score("FAISS Search (troubleshoot)", min(score, 10),
                       f"{len(results)} results")


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestMatchScoring:
    """Query-to-document match scoring tests."""

    def test_match_same_domain(self, vector_store):
        """Match: VM query vs VM document (same domain, high score expected)."""
        model = getattr(vector_store, "model", None)
        if model is None:
            _record_score("Match Same Domain", 2, "model not loaded")
            pytest.skip("Model not loaded")

        query = VM_QUERY
        document = CLOUD_DOCUMENTS[0]  # EC2 deployment doc

        emb = model.encode([query, document], convert_to_numpy=True)
        emb_norm = emb / np.linalg.norm(emb, axis=1, keepdims=True)
        similarity = float(np.dot(emb_norm[0], emb_norm[1]))
        pct = round(max(similarity * 100, 0), 1)
        grade = "STRONG" if pct >= 85 else "GOOD" if pct >= 70 else "PARTIAL" if pct >= 50 else "WEAK" if pct >= 30 else "LOW"

        print(f"  Query:    {query[:60]}...")
        print(f"  Document: {document[:60]}...")
        print(f"  Match:    {pct:.1f}% [{grade}]  (cosine={similarity:.4f})")

        score = 3
        if pct >= 70:
            score = 10
        elif pct >= 55:
            score = 8
        elif pct >= 40:
            score = 6
        elif pct >= 25:
            score = 4

        _record_score("Match Same Domain (VM)", score, f"Match: {pct:.1f}%")

    def test_match_cross_domain(self, vector_store):
        """Match: VM query vs unrelated document (low score expected)."""
        model = getattr(vector_store, "model", None)
        if model is None:
            _record_score("Match Cross Domain", 2, "model not loaded")
            pytest.skip("Model not loaded")

        query = VM_QUERY
        document = "Recipe for chocolate sourdough bread with walnuts and raisins"

        emb = model.encode([query, document], convert_to_numpy=True)
        emb_norm = emb / np.linalg.norm(emb, axis=1, keepdims=True)
        similarity = float(np.dot(emb_norm[0], emb_norm[1]))
        pct = round(max(similarity * 100, 0), 1)
        grade = "STRONG" if pct >= 85 else "GOOD" if pct >= 70 else "PARTIAL" if pct >= 50 else "WEAK" if pct >= 30 else "LOW"

        print(f"  Query:    {query[:60]}...")
        print(f"  Document: {document[:60]}...")
        print(f"  Match:    {pct:.1f}% [{grade}]  (cosine={similarity:.4f})")

        score = 3
        if pct < 20:
            score = 10
        elif pct < 30:
            score = 8
        elif pct < 40:
            score = 6
        elif pct < 50:
            score = 4
        else:
            score = 2

        _record_score("Match Cross Domain (VM vs food)", score,
                       f"Correctly low: {pct:.1f}%")

    def test_match_matrix(self, vector_store):
        """Build a match matrix: 10 provisioning queries x 10 cloud documents."""
        model = getattr(vector_store, "model", None)
        if model is None:
            _record_score("Match Matrix (10x10)", 2, "model not loaded")
            pytest.skip("Model not loaded")

        queries = PROVISION_QUERIES
        documents = CLOUD_DOCUMENTS[:10]
        query_labels = ["VM", "K8s", "Docker", "DB", "FastAPI", "Website",
                        "IAM", "VPC", "SG", "ALB"]

        all_texts = list(queries) + list(documents)
        embeddings = model.encode(all_texts, convert_to_numpy=True)
        emb_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        q_emb = emb_norm[:len(queries)]
        d_emb = emb_norm[len(queries):]

        sim_matrix = np.dot(q_emb, d_emb.T)

        print(f"\n  {'Query / Doc':<15}" + "".join(f"{'Doc'+str(i+1):>10}" for i in range(len(documents))))
        print(f"  {'─' * 15}" + "─" * (10 * len(documents)))

        diagonal_scores = []
        off_diagonal_scores = []

        for i, label in enumerate(query_labels):
            row_str = f"  {label:<15}"
            for j in range(len(documents)):
                pct = round(max(sim_matrix[i, j] * 100, 0), 1)
                if i == j:
                    grade = "STRONG" if pct >= 85 else "GOOD" if pct >= 70 else "OK" if pct >= 50 else "WEAK"
                    row_str += f"{pct:>7.1f}%* "
                    diagonal_scores.append(pct)
                else:
                    row_str += f"{pct:>7.1f}%  "
                    off_diagonal_scores.append(pct)
            print(row_str)

        diag_avg = np.mean(diagonal_scores) if diagonal_scores else 0
        off_avg = np.mean(off_diagonal_scores) if off_diagonal_scores else 0
        separation = diag_avg - off_avg

        print(f"\n  Diagonal avg (same-domain):  {diag_avg:.1f}%")
        print(f"  Off-diagonal avg (cross):    {off_avg:.1f}%")
        print(f"  Separation gap:              {separation:+.1f}%")

        score = 3
        details = []

        if separation > 15:
            score = 10
        elif separation > 10:
            score = 8
        elif separation > 5:
            score = 6
            details.append(f"moderate separation ({separation:.1f}%)")
        elif separation > 0:
            score = 4
            details.append(f"weak separation ({separation:.1f}%)")
        else:
            score = 2
            details.append(f"no separation ({separation:.1f}%)")

        _record_score("Match Matrix (10x10)", score,
                       "; ".join(details) if details else f"diag={diag_avg:.1f}%, gap={separation:+.1f}%")

    def test_provision_vs_non_provision_discrimination(self, vector_store):
        """Verify provisioning queries cluster together and away from non-provisioning."""
        model = getattr(vector_store, "model", None)
        if model is None:
            _record_score("Provision vs Non-Provision", 2, "model not loaded")
            pytest.skip("Model not loaded")

        all_queries = PROVISION_QUERIES + NON_PROVISION_QUERIES
        embeddings = model.encode(all_queries, convert_to_numpy=True)
        emb_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        n_prov = len(PROVISION_QUERIES)

        intra_prov_sims = []
        for i in range(n_prov):
            for j in range(i + 1, n_prov):
                intra_prov_sims.append(float(np.dot(emb_norm[i], emb_norm[j])))

        cross_sims = []
        for i in range(n_prov):
            for j in range(n_prov, len(all_queries)):
                cross_sims.append(float(np.dot(emb_norm[i], emb_norm[j])))

        intra_avg = np.mean(intra_prov_sims) if intra_prov_sims else 0
        cross_avg = np.mean(cross_sims) if cross_sims else 0
        gap = intra_avg - cross_avg

        print(f"  Intra-provisioning avg similarity: {intra_avg:.4f}")
        print(f"  Cross-domain avg similarity:       {cross_avg:.4f}")
        print(f"  Discrimination gap:                {gap:+.4f}")

        score = 3
        details = []

        if gap > 0.15:
            score = 10
        elif gap > 0.10:
            score = 8
        elif gap > 0.05:
            score = 6
            details.append(f"moderate ({gap:.3f})")
        elif gap > 0:
            score = 4
            details.append(f"weak ({gap:.3f})")
        else:
            score = 2
            details.append(f"no discrimination ({gap:.3f})")

        _record_score("Provision vs Non-Provision", score,
                       "; ".join(details) if details else f"gap={gap:.3f}")


# ============================================================================
# STANDALONE RUNNER
# ============================================================================

if __name__ == "__main__":
    print(__doc__)
    print("=" * 70)
    print("Running embedding & match scoring tests with pytest...")
    print("=" * 70)
    sys.exit(pytest.main([__file__, "-v", "-s", "--tb=short"]))
