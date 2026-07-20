# Offline Evaluation

The evaluation suite runs the current M2A TF-IDF and rule-rerank pipeline against anonymized fixtures. It defaults to `use_llm=False`, writes only aggregate and per-case metrics, and uses a temporary SQLite database so the project database is not changed.

Run it with:

```bash
python -m evals.run_evals
```

Run the two retrieval strategies separately for a baseline comparison:

```bash
python -m evals.run_evals --retrieval tfidf
python -m evals.run_evals --retrieval hybrid
```

TF-IDF remains the default. Hybrid requires an OpenAI-compatible endpoint and
is otherwise reported as the controlled `tfidf_fallback` strategy. Configure it
only in the environment (never in fixture files):

```env
EMBEDDING_ENABLED=true
EMBEDDING_MODEL=text-embedding-model
EMBEDDING_BASE_URL=https://example.invalid/v1
EMBEDDING_API_KEY=your-key
```

The evaluator writes `evals/results/latest.json` for TF-IDF and
`evals/results/latest-hybrid.json` for hybrid. Result files contain metrics and
strategy metadata only, never keys or raw model responses.

Reviewed evidence can be exported as a sanitized candidate dataset:

```bash
python -m evals.export_reviewed_feedback --database jobmatch.db
```

Only `corrected` and `rejected` reviews are exported. The output contains the
requirement skill, candidate keywords, review status and timestamp; it never
contains full resume text, JD text, snippets, raw model output or API keys.
Rejected rows have `needs_manual_label=true` because a rejection alone does
not define the replacement expected status. Review the generated file and
manually merge approved rows into `fixtures/` and `expected/`; the exporter
never overwrites those directories.

Use `--use-llm` only when a configured model is intentionally available:

```bash
python -m evals.run_evals --use-llm
```

Metrics include requirement precision/recall, Evidence Recall@3, judge accuracy, false-support rate, degraded rate, and average stage latency. Fixtures and expected labels are synthetic and contain no identity, contact, company, or real resume data.

With the default `use_llm=False`, the pipeline intentionally uses its deterministic fallback, so `degraded_rate` reports the proportion of cases that did not run LLM stages. It is expected to be 100% for the offline baseline; use the explicit `--use-llm` run to measure configured model availability separately.
