lint:
    ruff format .
    ruff check .

fix:
    ruff check --fix .

build-compose:
    docker compose build

build:
    docker build -t jmrec-cli .

tree:
    tree -I '.ruff_cache|.venv|__pycache__' --dirsfirst .
