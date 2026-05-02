FROM python:3.12-slim

# Non-root user — ASI09 / SOC2 baseline. UID 1000 matches typical k8s securityContext.
RUN useradd -m -u 1000 kbarena && mkdir -p /app /data && chown -R kbarena:kbarena /app /data

WORKDIR /app

# Layer 1: deps. Copy pyproject first so dep resolution is cached across code changes.
COPY --chown=kbarena:kbarena pyproject.toml README.md ./

# curl is used by HEALTHCHECK; build deps for hatchling are already in the slim image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY --chown=kbarena:kbarena kb_arena/ kb_arena/
COPY --chown=kbarena:kbarena cypher/ cypher/
# Note: datasets/ are mounted at runtime, NOT baked into the image — keeps the
# image small and avoids shipping internal sample data when users build privately.

RUN pip install --no-cache-dir .

USER kbarena

EXPOSE 8000

# Tell users their default state — public Space deploys MUST keep demo_mode=true.
ENV KB_ARENA_DEMO_MODE=true \
    KB_ARENA_DATASETS_PATH=/data/datasets \
    KB_ARENA_RESULTS_PATH=/data/results

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "kb_arena.chatbot.api:app", "--host", "0.0.0.0", "--port", "8000"]
