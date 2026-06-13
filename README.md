# KB Arena (Fork)

> This is a fork of the original [KB Arena](https://github.com/xmpuspus/kb-arena) project by Xavier Puspus.
> The original project benchmarks 9 retrieval architectures on your own documentation.
>
> This fork adds **Azure OpenAI** support for both the LLM (chat/generation) and the embeddings model, so you can run the full benchmark pipeline using your Azure OpenAI deployment — no Anthropic or standard OpenAI keys required.

---

## Installation

```bash
# From source (this fork)
pip install -r requirements.txt

# Or install the package in editable mode
pip install -e .
```

---

## Azure OpenAI Configuration

Copy `.env.example` to `.env` and fill in your Azure OpenAI details:

```bash
cp .env.example .env
```

Minimum required variables in `.env`:

```env
# ── Provider selection ────────────────────────────────────────
KB_ARENA_LLM_PROVIDER=azure_openai
KB_ARENA_EMBEDDING_PROVIDER=azure_openai

# ── Azure OpenAI — LLM / Chat ─────────────────────────────────
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1          # your chat deployment name
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_MODEL_NAME=gpt-4                 # used for cost estimation only

# ── Azure OpenAI — Embeddings ─────────────────────────────────
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_EMBEDDING_API_KEY=<your-api-key>  # can be same as above
AZURE_OPENAI_EMBEDDING_ENDPOINT=https://<your-resource>.openai.azure.com
```

### Variable reference

| Variable | Description |
|---|---|
| `KB_ARENA_LLM_PROVIDER` | Set to `azure_openai` to use Azure OpenAI for chat/generation |
| `KB_ARENA_EMBEDDING_PROVIDER` | Set to `azure_openai` to use Azure OpenAI embeddings |
| `AZURE_OPENAI_API_KEY` | API key for the Azure OpenAI chat resource |
| `AZURE_OPENAI_ENDPOINT` | Endpoint URL, e.g. `https://myresource.openai.azure.com` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Deployment name used for all LLM roles (generate / fast / judge) |
| `AZURE_OPENAI_API_VERSION` | API version, e.g. `2025-01-01-preview` |
| `AZURE_OPENAI_MODEL_NAME` | Logical model name for cost estimation (e.g. `gpt-4`, `gpt-4o`) |
| `AZURE_OPENAI_GENERATE_DEPLOYMENT` | *(optional)* Override deployment for generation role |
| `AZURE_OPENAI_FAST_DEPLOYMENT` | *(optional)* Override deployment for classification role |
| `AZURE_OPENAI_JUDGE_DEPLOYMENT` | *(optional)* Override deployment for evaluation role |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Deployment name for the embeddings model |
| `AZURE_OPENAI_EMBEDDING_API_KEY` | API key for the embedding resource (can be same as chat key) |
| `AZURE_OPENAI_EMBEDDING_ENDPOINT` | Endpoint URL for the embedding resource |
| `AZURE_OPENAI_EMBEDDING_API_VERSION` | *(optional)* API version for embeddings; defaults to `AZURE_OPENAI_API_VERSION` |

> **Tip:** All `AZURE_OPENAI_*` variables are accepted **without** the `KB_ARENA_` prefix, matching the convention used by Azure SDKs and tools. The prefixed form `KB_ARENA_AZURE_OPENAI_*` also works.

---

## Neo4j (for knowledge graph strategy)

The knowledge graph and hybrid strategies require Neo4j. Start it with Docker:

```bash
docker compose up neo4j -d
```

Add Neo4j credentials to your `.env`:

```env
KB_ARENA_NEO4J_URI=bolt://localhost:7687
KB_ARENA_NEO4J_USER=neo4j
KB_ARENA_NEO4J_PASSWORD=kbarena1
```

The vector, BM25, RAPTOR, and PageIndex strategies work **without** Neo4j.

---

## Running the Pipeline

### One-shot (recommended)

```bash
kb-arena init-corpus my-docs
cp /path/to/your/docs/*.md datasets/my-docs/raw/

kb-arena run --corpus my-docs        # runs all stages end-to-end
kb-arena run --corpus my-docs --resume   # resume if interrupted
```

### Step by step

```bash
# 1. Scaffold corpus directories
kb-arena init-corpus my-docs

# 2. Drop your docs into raw/  (supports .md .html .txt .pdf .docx .csv)
cp /path/to/docs/*.md datasets/my-docs/raw/

# 3. Parse documents into JSONL
kb-arena ingest datasets/my-docs/raw/ --corpus my-docs

# 4. Build knowledge graph in Neo4j (skip if no Neo4j)
kb-arena build-graph --corpus my-docs

# 5. Build vector indexes in ChromaDB
kb-arena build-vectors --corpus my-docs

# 6. Auto-generate benchmark questions
kb-arena generate-questions --corpus my-docs --count 50

# 7. Run the benchmark (all 9 strategies)
kb-arena benchmark --corpus my-docs

# 8. Launch the web UI
kb-arena serve
```

Open `http://localhost:8000` for the API and `http://localhost:3000` for the dashboard.

---

## CLI Command Reference

| Command | Description |
|---|---|
| `kb-arena demo` | Launch dashboard with pre-computed results (no API keys needed) |
| `kb-arena init-corpus <name>` | Scaffold `datasets/<name>/` directories |
| `kb-arena run --corpus <name>` | Run the full pipeline (ingest → build → generate → benchmark). Add `--resume` to continue from a checkpoint |
| `kb-arena ingest <path>` | Parse docs into JSONL. Accepts files, dirs, URLs, `github:owner/repo`. Options: `--corpus`, `--format`, `--dry-run` |
| `kb-arena build-graph --corpus <name>` | Extract entities/relationships into Neo4j |
| `kb-arena build-vectors --corpus <name>` | Build vector indexes + PageIndex tree. Option: `--strategy` |
| `kb-arena generate-questions --corpus <name>` | Auto-generate benchmark questions. Option: `--count` |
| `kb-arena label-chunks --corpus <name>` | Generate chunk-level ground truth for IR metrics |
| `kb-arena benchmark --corpus <name>` | Run full evaluation. Options: `--strategy`, `--tier`, `--dry-run`, `--no-parallel` |
| `kb-arena retriever-lab --corpus <name>` | Retrieval-only IR metrics (Recall@k, MRR, NDCG@k) — no LLM generation cost |
| `kb-arena optimize --corpus <name>` | Automated hyperparameter search. Options: `--strategies`, `--top-ks`, `--chunk-sizes`, `--embedding-providers`, `--metric`, `--dry-run` |
| `kb-arena generate-qa --corpus <name>` | Generate Q&A pairs as JSONL |
| `kb-arena audit --corpus <name>` | Find documentation gaps (strong / weak / gap classification) |
| `kb-arena fix --corpus <name>` | Generate fix recommendations with draft content. Option: `--max-fixes` |
| `kb-arena report --corpus <name>` | Generate report. Options: `--format` (rich / json / csv / html) |
| `kb-arena serve` | Launch API + frontend. Options: `--host`, `--port` |
| `kb-arena health` | Pipeline status. Option: `--format` (rich / json) |

### Useful flags

```bash
# Preview cost/queries before running (no API calls made)
kb-arena benchmark --corpus my-docs --dry-run
kb-arena optimize --corpus my-docs --dry-run

# Run only specific strategies
kb-arena benchmark --corpus my-docs --strategy naive_vector,bm25

# Limit cost (halts if cumulative spend exceeds $N)
kb-arena benchmark --corpus my-docs  # default cap: $10 (set KB_ARENA_BENCHMARK_COST_CAP_USD)

# JSON output for scripting / CI
kb-arena report --corpus my-docs --format json | jq '.corpora'
kb-arena health --format json

# Verbose / debug logging
kb-arena benchmark --corpus my-docs --verbose
```

---

## Other Supported LLM Providers

While this fork is focused on Azure OpenAI, the other providers from the original project still work:

```env
# Standard OpenAI
KB_ARENA_LLM_PROVIDER=openai
KB_ARENA_OPENAI_API_KEY=sk-...
KB_ARENA_EMBEDDING_PROVIDER=openai

# Anthropic
KB_ARENA_LLM_PROVIDER=anthropic
KB_ARENA_ANTHROPIC_API_KEY=sk-ant-...

# Ollama (free, local — no keys needed)
KB_ARENA_LLM_PROVIDER=ollama
KB_ARENA_EMBEDDING_PROVIDER=ollama
```

---

## License

MIT — see [LICENSE](LICENSE).

Original project: https://github.com/xmpuspus/kb-arena
