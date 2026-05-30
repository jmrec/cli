FROM python:3.12-alpine AS builder
WORKDIR /app
RUN apk add --no-cache build-base libxml2-dev libxslt-dev libffi-dev

COPY pyproject.toml README.md ./
RUN mkdir -p src/jmrec && touch src/jmrec/__init__.py
RUN pip install --prefix=/install .

COPY src/ src/
RUN pip install --prefix=/install --no-deps .

FROM python:3.12-alpine
COPY --from=builder /install /usr/local

WORKDIR /app
ENTRYPOINT ["jmrec-cli"]