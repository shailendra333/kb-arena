# Changelog

All notable changes to KB Arena.

## [0.6.0] — 2026-05-02 — Hardening, 9th strategy, embedding providers, public leaderboard

### Added
- **Strategy #9: `rerank_vector`** — Naive Vector + cross-encoder reranking with three backends:
  `bge` (BAAI/bge-reranker-v2-m3, local, free, default), `cohere` (Rerank v3.5/v4),
  `voyage` (Rerank 2.5). Selects via `KB_ARENA_RERANKER_BACKEND`.
- **Embedding provider abstraction** — `KB_ARENA_EMBEDDING_PROVIDER` selects
  `openai` (default), `voyage` (current MTEB retrieval leader), `cohere`, `bge`
  (local, no key), `ollama` (local, no key), or `gemini`. All four vector
  strategies route through `get_embedding_function()` instead of hard-coded OpenAI.
- **`kb-arena run --corpus my-docs --resume`** — one-shot orchestrator that
  ingests, builds graph, builds vectors, generates questions, and benchmarks,
  with a checkpoint at `datasets/{corpus}/.pipeline_state.json` so a re-run
  with `--resume` skips finished stages.
- **Public read-only `/api/leaderboard`** + Next.js `/leaderboard` page —
  aggregates every benchmark run in `results/run_*` per (corpus, strategy)
  with mean accuracy, Recall@5, NDCG@5, cost, and latency. No auth.
- **Bearer-token auth** (`KB_ARENA_API_TOKEN`) on every LLM-triggering endpoint;
  bounded-deque rate limiter with optional trusted-proxy header support.
- **Demo mode** (`KB_ARENA_DEMO_MODE`) — auto-enabled when no API key is configured;
  every LLM-triggering endpoint returns 503 while the static dashboard,
  leaderboard, benchmark results, and corpora endpoints remain available.
- `kb-arena --version` flag.
- `deploy/vercel.json` and `deploy/huggingface_space.yaml` for hosted demos.
- `docs/tapes/hero-demo.tape`, `docs/tapes/retriever-lab.tape`, and
  `docs/tapes/record-ui.py` so demo GIFs regenerate deterministically.

### Changed
- **Hybrid strategy** — procedural branch now reranks **passages** (real
  `RetrievedChunk.content`) instead of previously-generated answer strings,
  and uses Reciprocal Rank Fusion (k=60) instead of LLM-pairwise rerank.
  Vector + graph queries now run via `asyncio.gather`. IntentRouter is wired
  in `get_strategy("hybrid")` so the advertised three-stage classification
  actually fires.
- **Knowledge graph extraction** — cross-section relationships are no longer
  dropped at section validation. A global FQN union check happens after every
  section has been extracted, restoring multi-hop graph queries.
- **Ground-truth labelling** — `expected_chunks.yaml` candidate pool widened
  from BM25 alone to BM25 ∪ naive_vector ∪ contextual_vector top-N when the
  vector indexes are built. Closes the circular-methodology critique.
- **Default `KB_ARENA_BENCHMARK_COST_CAP_USD` is 10.0** (was 0 / unlimited).
- **`SECURITY.md`** rewritten to match implementation; supported versions
  refreshed to 0.6.x.
- **Dockerfile** runs as non-root `kbarena` user with HEALTHCHECK and a
  default `KB_ARENA_DEMO_MODE=true` so a freshly built image cannot drain
  credits without explicit opt-in.
- **`docker-compose.yml`** fail-closes when `KB_ARENA_NEO4J_PASSWORD` is
  unset, binds Neo4j to 127.0.0.1, adds resource limits and api healthcheck.
- README hero rewritten with the question-frame pitch
  ("Should you use Graph RAG, Vector RAG, or Hybrid?") and a No-API-Keys
  Quick Start using Ollama.

### Fixed
- **Cross-tenant data leak** — `Strategy.last_*` fields were stomped by
  concurrent SSE consumers. Per-call metrics now travel with the streamed
  tokens via a `_kb_arena_meta` packet; the `last_*` fields stay only as a
  back-compat surface for plugins.
- **`bm25` strategy missing from bundled demo** — `kb_arena/data/aws-compute_bm25.json`
  is now shipped, plus a hatch `force-include` glob so future strategies are
  picked up automatically.
- **`kb-arena demo` zero-config gate** — lifespan tolerates missing API keys,
  enables `demo_mode`, and continues serving the dashboard.
- **Ollama free path** — `_preflight()` reads `settings.llm_provider` and
  skips Anthropic/OpenAI key checks when set to `ollama`.
- **APOC Cypher write bypass** — write regex now also rejects
  `apoc.create|merge|refactor|delete|remove|set|drop|iterate|cypher.runWrite|export|trigger`,
  and every read path opens the Neo4j session with `default_access_mode=READ_ACCESS`.
- **SSRF in `kb-arena ingest <url>`** — `WebParser` rejects `file://`, private,
  loopback, link-local, multicast, and reserved IPs (post-DNS); blocks AWS / GCE
  metadata hostnames; disables auto-redirect with per-hop validation.
- **Cost-bomb on chat / arena / tools** — every LLM-triggering endpoint is now
  rate-limited and `Field(max_length=4000)`-bounded; arena endpoints use
  Pydantic models instead of raw `request.json()`.
- **Benchmark runner retry** distinguishes retryable transients (rate limit,
  5xx, network, timeout) from permanent errors (auth, validation,
  missing model) — bad keys fail fast instead of burning 7 minutes per run.
- **Two sources of truth for version** — `chatbot/api.py` now reads
  `__version__` from `kb_arena` package metadata.

### Tests
- Test suite still 558 tests; updated 4 stale tests that asserted old contracts
  (cost cap default, cross-section edge dropping, health response shape,
  strategy count).

## [0.5.0] — 2026-04-26 — Retriever Lab

### Added
- Classical IR metrics computed for every benchmark query: Recall@k, Precision@k, Hit@k, MRR, NDCG@k.
- `RetrievalTrace` and `RetrievedChunk` models on `AnswerResult` — every strategy now exposes the chunks it surfaced with rank, score, and source strategy.
- `Question.expected_chunks` field; `load_questions()` merges `expected_chunks.yaml` automatically.
- `RetrievalMetrics` model attached to `AnswerRecord.retrieval_metrics`; `BenchmarkResult` gains aggregate `mean_recall_at_k`, `mean_precision_at_k`, `mean_hit_at_k`, `mean_mrr`, `mean_ndcg_at_k`.
- New CLI command `kb-arena retriever-lab` — retrieval-only benchmark with live Rich metrics table; ~10x cheaper than full `benchmark` because LLM generation is stubbed.
- New CLI command `kb-arena label-chunks` — generate `expected_chunks.yaml` ground truth via BM25 + Haiku judge. Idempotent and cost-capped.
- New `--top-k` flag on `kb-arena benchmark` (default 5).
- New web page `/retriever-lab` — aggregate metrics card per strategy, plus per-question drill-down with HIT/MISS chunk highlighting.
- New API endpoints `GET /api/retriever-lab/runs` and `GET /api/retriever-lab/{run_id}`.
- Hierarchical chunk-id matching: section-level expected IDs match sub-chunk retrievals (`doc::sec` matches `doc::sec::0`); strategy-namespace prefixes (`L0:`, `qna:`, `graph:`, `pageindex:`) are stripped before matching.
- Doc-level fallback in IR metrics: when chunk labels are absent, match against `chunk.doc_id ∈ ground_truth.source_refs`.

### Changed
- All 8 strategies now populate `AnswerResult.retrieval` with stable chunk IDs.
- Benchmark Markdown report gains a "Retrieval Quality (top-k)" section.
- Hybrid strategy preserves sub-strategy `source_strategy` per chunk during fusion.
- BM25 index format includes `chunk_ids` for stable identity across runs (older indexes still load with synthesized IDs).
- ChromaDB telemetry warnings suppressed in retriever-lab to keep terminal output clean.

### Fixed
- BM25 chunk identifiers now stable across runs (previously index-position only).
- `is_hit` flag in retriever-lab JSON now uses hierarchical matching so vector sub-chunks correctly tag as HIT against section-level labels.

### Tests
- Test suite grows from 514 to 558 tests; coverage adds `tests/test_ir_metrics.py`, `tests/test_retrieval_trace.py`, `tests/test_retriever_lab_runner.py`, `tests/test_label_chunks_cli.py`.
