# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.6.x   | Yes (active) |
| 0.5.x   | Critical fixes only |
| <= 0.4  | No |

Patches land on the latest minor; older minors get critical-only patches on best-effort.

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Email security concerns to xavier@xmpuspus.dev
3. Include a description of the vulnerability, steps to reproduce, and potential impact
4. You will receive a response within 48 hours

## Security Model

### API Authentication

- Every endpoint that triggers an LLM call is gated by `Depends(require_auth)`:
  `/chat`, `/chat/stream`, `/api/arena/match`, `/api/arena/vote`, `/api/tools/*`,
  `/api/graph/build`, `/api/debug/explain`.
- When `KB_ARENA_API_TOKEN` is set, requests must include
  `Authorization: Bearer <token>`. The comparison is constant-time (`hmac.compare_digest`).
- When `KB_ARENA_DEMO_MODE=true`, every LLM-triggering endpoint returns 503
  regardless of authentication. This is the default state when no API keys are
  configured, so a freshly installed instance cannot drain credits even if exposed.
- Read-only endpoints (`/api/leaderboard`, `/api/benchmark/results`, `/api/corpora`,
  `/api/retriever-lab/*`, `/health`, `/ready`) are intentionally unauthenticated —
  they read JSON from disk and never invoke the LLM.

### Input Validation

- `ChatRequest.query`, `ArenaMatchRequest.question` are capped at 4 000 chars.
- History list capped at 20 turns; corpus and strategy names are alphanumeric-only.
- Arena and tools endpoints use Pydantic models — no raw `request.json()` paths.
- All YAML loads use `yaml.safe_load`; no `pickle`, no `eval`, no `exec` on user input.

### Cypher Safety

- LLM-generated Cypher is rejected if it matches `_WRITE_CYPHER_RE`, which
  includes APOC write paths (`apoc.create`, `apoc.merge`, `apoc.refactor`,
  `apoc.cypher.runWrite`, `apoc.periodic.iterate`, `apoc.export`, etc.) and
  `LOAD CSV`.
- Defense in depth: every query path opens the Neo4j session with
  `default_access_mode=neo4j.READ_ACCESS`. The driver enforces read-only at the
  Bolt protocol level — the regex is the second line, not the only line.
- Production extraction (`build-graph`) uses parameterized Cypher only.

### URL Ingestion (SSRF)

- `WebParser` validates every URL before fetching. Schemes other than `http(s)`
  are rejected. Hosts are DNS-resolved and the resolved IP is checked against
  private, loopback, link-local, multicast, and reserved ranges.
- AWS instance metadata, GCE metadata, and EC2 instance-data hosts are blocked
  by name regardless of DNS.
- `follow_redirects` is disabled at the httpx client; redirects are validated
  per hop with a hard cap of 5.
- GitHub clones use `--depth 1 --single-branch` and a 120 s timeout.

### Cost Controls

- `KB_ARENA_BENCHMARK_COST_CAP_USD` defaults to **10.0** (was 0/unlimited).
  Benchmarks halt as soon as cumulative spend exceeds the cap.
- Demo mode (auto-enabled when no API key is configured) returns 503 from
  every LLM-triggering endpoint.
- The benchmark runner distinguishes retryable transients (rate limit, 5xx,
  network) from permanent errors (auth, validation) — bad keys fail fast
  instead of burning 7 minutes of retries per run.

### Rate Limiting

- 60 req/min per client, bounded-memory deque per IP, with eviction at 10 000
  cold keys to prevent memory growth.
- `KB_ARENA_TRUSTED_PROXY_HEADER` may be set to honour `X-Forwarded-For` first
  hop when running behind nginx / Cloudflare.

### Network

- CORS is configured via `KB_ARENA_CORS_ORIGINS`; the default localhost list
  never expands to `*`.
- The bundled `docker-compose.yml` binds Neo4j to `127.0.0.1` and refuses to
  start without `KB_ARENA_NEO4J_PASSWORD`.

### Container

- `Dockerfile` runs as a non-root `kbarena` user (UID 1000).
- `HEALTHCHECK` polls `/health` every 15 s.
- `KB_ARENA_DEMO_MODE=true` is set by default in the image — public deploys
  cannot accidentally enable chat without explicitly overriding it AND setting
  an API token.

### Dependencies

- All direct dependencies pinned to exact `==` versions in `pyproject.toml`.
- `uv.lock` is checked in; CI is being migrated to `uv sync --frozen` so
  transitive deps are reproducible. (Tracked in our roadmap.)

### Input Validation

- All API request bodies are validated by Pydantic v2 with strict type checking
- Strategy names are validated against the registry — unknown strategies return a structured error
- Question YAML files are validated against the `Question` Pydantic model at load time

## Known Limitations

- In-memory rate limiter resets on process restart. For production behind a
  load balancer use a Redis-backed limiter (open issue).
- LLM responses are escaped by React's built-in rendering, but custom
  integrations should sanitize before rendering as HTML.
- `/api/debug/explain` is gated behind `KB_ARENA_DEBUG=true`. Don't enable
  debug mode in production.
