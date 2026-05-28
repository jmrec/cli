FROM python:3.12-alpine AS builder
WORKDIR /app
RUN apk add build-base libxml2-dev libxslt-dev libffi-dev

COPY pyproject.toml .
COPY src/ src/

RUN pip install --prefix=/install .

FROM python:3.12-alpine
COPY --from=builder /install /usr/local

WORKDIR /app
ENTRYPOINT ["jmrec-cli"]