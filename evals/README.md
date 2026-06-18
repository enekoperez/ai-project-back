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

Each run makes one embedding API call per question (~24 cheap calls), plus a reranker
LLM call for any question whose hybrid search returns more than `_TOP_K` candidates.

## Files

- `rag_eval_dataset.json` — the golden set: `{"question", "expected_sources"}` pairs
  (optional `_note` keys group related cases and are ignored by the runner).
  `expected_sources` is the set of acceptable source files; a hit means **any** one of
  them was retrieved. The set deliberately mixes case types so the harness can actually
  *discriminate* retrieval designs, not just rubber-stamp easy lookups:
  - **single-doc** — straightforward keyword lookups.
  - **rare/exact-token** (e.g. "leg before wicket", "scrum", "icing") — terms in exactly
    one doc, where lexical BM25 matching earns its keep over pure semantics.
  - **distractor/precision** (e.g. "How many points is a try worth?") — wording overlaps
    many docs but only one is correct; rewards ranking the right doc first.
  - **multi-source** (e.g. "offside rule") — several docs are acceptable; tests recall.
  - **negative/abstention** (`expected_sources: []`) — off-topic questions that should
    return nothing.
  Edit/extend this as docs grow.
- `run_rag_eval.py` — the runner (Python stdlib only).

## Metrics

Computed at the **source-document** level (retrieved chunks are deduped to source names,
preserving rank), where `k = _TOP_K` from `webapp/services/rag_service.py`. Positive and
negative cases are scored and reported separately:

Positive cases (a doc *should* come back):

- **hit@k** — was at least one expected source in the top-k? (the headline number)
- **MRR** — mean reciprocal rank: `1 / rank` of the first expected source (rewards
  ranking the right doc higher).
- **recall@k** — fraction of expected sources retrieved (matters for multi-source
  questions like "offside").

Negative cases (nothing should come back):

- **abstention** — how many off-topic questions correctly returned nothing.

> **Abstention gate:** retrieval answers only when at least one chunk clears the cosine
> floor (`_MIN_SCORE`). Off-topic questions that merely share an incidental token with the
> corpus (e.g. "capital of **France**", "chemical symbol for **gold**") no longer leak —
> the dense branch finds nothing relevant, so `get_top_chunks` returns nothing instead of
> answering from BM25 keyword overlap. Trade-off: a query that is a *purely lexical* match
> (the embedding misses it but BM25 would hit) also abstains; that is the intended
> default for a trust-first system, tunable via `_MIN_SCORE`.

## Why no dependencies?

Retrieval metrics are pure counting over retrieved-vs-expected, so no library is needed.
The popular eval libraries — **RAGAS**, **DeepEval**, **TruLens**, **promptfoo** — target
*LLM-judged generation* quality (faithfulness, answer relevancy, context precision) and
pull in heavy dependency trees. They'd be the tool to reach for *later*, if/when we add
answer-quality evals — not for measuring retrieval.
