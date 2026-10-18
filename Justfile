lint:
    uv run ruff format .
    uv run ruff check .

fix:
    uv run ruff check --fix .

install:
    uv tool install --from git+https://github.com/jmrec/cli.git jmrec-cli

update:
    uv tool install --force --from git+https://github.com/jmrec/cli.git jmrec-cli

dev:
    uv tool install --editable . --force

setup:
    jmrec-cli setup

tree:
    tree -I '.ruff_cache|.venv|__pycache__' --dirsfirst .
