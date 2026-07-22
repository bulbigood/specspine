FROM docker:29.1.5-cli@sha256:931f63d7100eb6734405d92d8bd9f4aa708c587510e5cc673bb9ac196a3d733f

RUN apk add --no-cache git python3

WORKDIR /workspace
ENTRYPOINT ["python3", "tests/eval/compare.py"]
