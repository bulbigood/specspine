FROM node:22.17.1-bookworm-slim@sha256:2fa754a9ba4d7adbd2a51d182eaabbe355c82b673624035a38c0d42b08724854

ARG CODEX_CLI_VERSION=0.144.4

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       git \
       python3 \
       ripgrep \
    && npm install --global "@openai/codex@${CODEX_CLI_VERSION}" \
    && rm -rf /var/lib/apt/lists/* /root/.npm

RUN groupadd --gid 10001 eval \
    && useradd --uid 10001 --gid 10001 --home-dir /home/eval --create-home eval \
    && mkdir -p /opt/specspine

COPY tests/eval/adapters/codex.py /opt/specspine/codex.py
COPY tests/eval/docker/preflight.sh /usr/local/bin/specspine-preflight

RUN chmod 0555 /opt/specspine/codex.py /usr/local/bin/specspine-preflight

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    OPENSSL_CONF=/dev/null \
    PYTHONDONTWRITEBYTECODE=1 \
    SPECSPINE_EVAL_RUNTIME_DIR=/runtime

USER 10001:10001
WORKDIR /workspace
ENTRYPOINT ["python3", "/opt/specspine/codex.py"]
