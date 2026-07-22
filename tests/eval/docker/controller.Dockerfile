FROM node:22.17.1-alpine3.22@sha256:5539840ce9d013fa13e3b9814c9353024be7ac75aca5db6d039504a56c04ea59

RUN apk add --no-cache docker-cli git python3 \
    && node --version \
    && docker --version \
    && git --version \
    && python3 --version

WORKDIR /workspace
ENTRYPOINT ["python3", "tests/eval/compare.py"]
