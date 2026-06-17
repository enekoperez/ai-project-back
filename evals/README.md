# RAG retrieval evals

A tiny, **zero-dependency** harness that measures how well the RAG pipeline *retrieves*
the right source documents. It runs a golden set of questions through
`RagService.get_top_chunks()` against the live Qdrant collection and embedding API, then
reports standard retrieval metrics.

> Scope is **retrieval only** — did the right docs come back? Answer-text quality
> (faithfulness, relevancy) is intentionally out of scope here.

## Run it

From the repo root (so `webapp` is importable), with the `rag_chunks_hybrid` collection
synced and `GOOGLE_AI_API_KEY` set:

```bash
python -m evals.run_rag_eval
python -m evals.run_rag_eval --min-hit 0.8   # exit non-zero below threshold (CI)
```

Each run makes one embedding API call per question (~16 cheap calls).

## Files

- `rag_eval_dataset.json` — the golden set: `{"question", "expected_sources"}` pairs.
  `expected_sources` is the set of acceptable source files; a hit means **any** one of
  them was retrieved. Edit/extend this as docs grow.
- `run_rag_eval.py` — the runner (Python stdlib only).

## Metrics

Computed at the **source-document** level (retrieved chunks are deduped to source names,
preserving rank), where `k = _TOP_K` from `webapp/services/rag_service.py`:

- **hit@k** — was at least one expected source in the top-k? (the headline number)
- **MRR** — mean reciprocal rank: `1 / rank` of the first expected source (rewards
  ranking the right doc higher).
- **recall@k** — fraction of expected sources retrieved (matters for multi-source
  questions like "offside").

## Why no dependencies?

Retrieval metrics are pure counting over retrieved-vs-expected, so no library is needed.
The popular eval libraries — **RAGAS**, **DeepEval**, **TruLens**, **promptfoo** — target
*LLM-judged generation* quality (faithfulness, answer relevancy, context precision) and
pull in heavy dependency trees. They'd be the tool to reach for *later*, if/when we add
answer-quality evals — not for measuring retrieval.
