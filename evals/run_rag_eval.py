"""Zero-dependency retrieval eval harness for the RAG pipeline.

Runs each golden question through ``RagService.get_top_chunks()`` against the live
Qdrant collection + embedding API, then reports hit@k, MRR, and recall@k at the
source-document level. Retrieval quality only — answer text is not judged.

Usage (from the repo root, so ``webapp`` is importable):
    python -m evals.run_rag_eval
    python -m evals.run_rag_eval --min-hit 0.8   # exit non-zero below threshold (CI)
"""
import argparse
import json
import sys
from pathlib import Path

from webapp.services.rag_service import RagService, _TOP_K

_DATASET_PATH = Path(__file__).with_name("rag_eval_dataset.json")


def _ranked_sources(chunks):
    """Deduplicate retrieved chunks down to source names, preserving rank order."""
    ranked = []
    for chunk in chunks:
        source = chunk["source_name"]
        if source not in ranked:
            ranked.append(source)
    return ranked


def _score(ranked_sources, expected_sources, top_k):
    """Compute (hit@k, reciprocal_rank, recall@k) for one question."""
    top = ranked_sources[:top_k]
    expected = set(expected_sources)

    hit = any(source in expected for source in top)

    reciprocal_rank = 0.0
    for rank, source in enumerate(top, start=1):
        if source in expected:
            reciprocal_rank = 1.0 / rank
            break

    recall = len(set(top) & expected) / len(expected) if expected else 0.0
    return hit, reciprocal_rank, recall


def evaluate(dataset, service, top_k):
    results = []
    for item in dataset:
        ranked = _ranked_sources(service.get_top_chunks(question=item["question"]))
        hit, reciprocal_rank, recall = _score(ranked, item["expected_sources"], top_k)
        results.append({
            "question": item["question"],
            "expected": item["expected_sources"],
            "retrieved": ranked[:top_k],
            "hit": hit,
            "rr": reciprocal_rank,
            "recall": recall,
        })
    return results


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def print_report(results, top_k):
    print(f"\nRAG retrieval eval - {len(results)} questions, k={top_k}\n")
    for result in results:
        mark = "PASS" if result["hit"] else "FAIL"
        print(f"[{mark}] rr={result['rr']:.2f} recall={result['recall']:.2f} | {result['question']}")
        print(f"        expected={result['expected']} retrieved={result['retrieved']}")

    print("\n--- aggregate ---")
    print(f"hit@{top_k}:    {_mean([r['hit'] for r in results]):.3f}")
    print(f"MRR:       {_mean([r['rr'] for r in results]):.3f}")
    print(f"recall@{top_k}: {_mean([r['recall'] for r in results]):.3f}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the RAG retrieval eval.")
    parser.add_argument(
        "--min-hit",
        type=float,
        default=None,
        help=f"Exit non-zero if mean hit@{_TOP_K} is below this threshold (for CI).",
    )
    args = parser.parse_args(argv)

    dataset = json.loads(_DATASET_PATH.read_text(encoding="utf-8"))
    results = evaluate(dataset, RagService(), _TOP_K)
    print_report(results, _TOP_K)

    if args.min_hit is not None:
        mean_hit = _mean([r["hit"] for r in results])
        if mean_hit < args.min_hit:
            print(f"\nFAILED threshold: hit@{_TOP_K}={mean_hit:.3f} < {args.min_hit}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
