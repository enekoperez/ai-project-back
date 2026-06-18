"""Zero-dependency retrieval eval harness for the RAG pipeline.

Runs each golden question through ``RagService.get_top_chunks()`` against the live
Qdrant collection + embedding API, then reports hit@k, MRR, and recall@k at the
source-document level for positive cases, plus abstention accuracy for negative
cases (off-topic questions that should return nothing). Retrieval quality only —
answer text is not judged.

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
    """Split the dataset into positive (a doc should be retrieved) and negative
    (nothing should be retrieved — abstention) cases, scoring each appropriately."""
    positives, negatives = [], []
    for item in dataset:
        ranked = _ranked_sources(service.get_top_chunks(question=item["question"]))
        if item["expected_sources"]:
            hit, reciprocal_rank, recall = _score(ranked, item["expected_sources"], top_k)
            positives.append({
                "question": item["question"],
                "expected": item["expected_sources"],
                "retrieved": ranked[:top_k],
                "hit": hit,
                "rr": reciprocal_rank,
                "recall": recall,
            })
        else:
            negatives.append({
                "question": item["question"],
                "retrieved": ranked[:top_k],
                "abstained": len(ranked) == 0,
            })
    return positives, negatives


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def print_report(positives, negatives, top_k):
    print(f"\nRAG retrieval eval - {len(positives)} positive + {len(negatives)} negative, k={top_k}\n")
    for result in positives:
        mark = "PASS" if result["hit"] else "FAIL"
        print(f"[{mark}] rr={result['rr']:.2f} recall={result['recall']:.2f} | {result['question']}")
        print(f"        expected={result['expected']} retrieved={result['retrieved']}")

    print(f"\n--- retrieval (positives) ---")
    print(f"hit@{top_k}:    {_mean([r['hit'] for r in positives]):.3f}")
    print(f"MRR:       {_mean([r['rr'] for r in positives]):.3f}")
    print(f"recall@{top_k}: {_mean([r['recall'] for r in positives]):.3f}")

    if negatives:
        correct = sum(n["abstained"] for n in negatives)
        print(f"\n--- abstention (negatives: should return nothing) ---")
        print(f"abstention: {correct}/{len(negatives)} correct")
        for n in negatives:
            mark = "OK  " if n["abstained"] else "LEAK"
            print(f"[{mark}] {n['question']}")
            if not n["abstained"]:
                print(f"        retrieved={n['retrieved']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the RAG retrieval eval.")
    parser.add_argument(
        "--min-hit",
        type=float,
        default=None,
        help=f"Exit non-zero if mean hit@{_TOP_K} over positive cases is below this threshold (for CI).",
    )
    args = parser.parse_args(argv)

    dataset = json.loads(_DATASET_PATH.read_text(encoding="utf-8"))
    positives, negatives = evaluate(dataset, RagService(), _TOP_K)
    print_report(positives, negatives, _TOP_K)

    if args.min_hit is not None:
        mean_hit = _mean([r["hit"] for r in positives])
        if mean_hit < args.min_hit:
            print(f"\nFAILED threshold: hit@{_TOP_K}={mean_hit:.3f} < {args.min_hit}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
