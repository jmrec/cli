FROM pandoc/minimal:3.1 AS pandoc-source
FROM python:3.12-alpine AS builder
WORKDIR /app
RUN apk add --no-cache build-base

COPY pyproject.toml .
RUN mkdir -p src/jmrec && \
    touch src/jmrec/__init__.py src/jmrec/main.py && \
    pip install --prefix=/install .

COPY src/ src/
RUN pip install --no-deps --prefix=/install .

FROM python:3.12-alpine

COPY --from=pandoc-source /pandoc /usr/local/bin/pandoc
COPY --from=builder /install /usr/local

WORKDIR /app
ENTRYPOINT ["jmrec-cli"]