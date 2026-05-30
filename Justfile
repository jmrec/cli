lint:
    ruff format .
    ruff check .

fix:
    ruff check --fix .

build-compose:
    docker compose build

build:
    docker build -t jmrec-cli .

build-linux:
    docker buildx build --platform linux/amd64 -t ghcr.io/jmrec/cli:latest --push .

tree:
    tree -I '.ruff_cache|.venv|__pycache__' --dirsfirst .
