# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install torch BEFORE copying requirements.txt so this layer stays cached
# even when requirements.txt changes later
RUN pip install --no-cache-dir \
    torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# curl is needed in THIS stage for the HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Pre-download embedding model at build time
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2'); print('Embedding model cached')"

# Copy project source
COPY . .

# Streamlit config — written as separate echo commands (no backslash issues)
RUN mkdir -p /root/.streamlit
RUN echo '[general]'                          > /root/.streamlit/config.toml
RUN echo 'email = ""'                        >> /root/.streamlit/config.toml
RUN echo '[server]'                          >> /root/.streamlit/config.toml
RUN echo 'headless = true'                   >> /root/.streamlit/config.toml
RUN echo 'port = 8501'                       >> /root/.streamlit/config.toml
RUN echo 'address = "0.0.0.0"'              >> /root/.streamlit/config.toml
RUN echo 'enableCORS = false'               >> /root/.streamlit/config.toml
RUN echo '[browser]'                         >> /root/.streamlit/config.toml
RUN echo 'gatherUsageStats = false'         >> /root/.streamlit/config.toml

EXPOSE 8501

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py"]