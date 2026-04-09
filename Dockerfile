FROM python:3.12-alpine AS builder

WORKDIR /app

RUN apk add --no-cache build-base

COPY pyproject.toml .

RUN mkdir -p src/jmrec && \
    touch src/jmrec/__init__.py src/jmrec/main.py && \
    pip install --prefix=/install .

FROM python:3.12-alpine

# This is where you would add any runtime dependencies your application needs.
# For example, if you need pandoc to convert .docx to markdown, you can install it here.
RUN apk add --no-cache pandoc

WORKDIR /app

COPY --from=builder /install /usr/local
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-deps .

ENTRYPOINT ["jmrec-cli"]