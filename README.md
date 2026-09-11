# JM's Collection of Scripts

A containerized CLI toolkit built with Python, Typer, and Docker. This setup allows you to run scripts (like document conversion) from any directory without needing to install dependencies like Pandoc or Python locally.

## Prerequisites

- Docker

## Usage

1. Pull the Docker Image

   Before running the scripts for the first time (or to update them), pull the latest version of the image:

   ```sh
   docker pull ghcr.io/jmrec/cli:latest
   ```

2. Set up the Terminal Alias

   To use the `scripts` command (or another alias) from any folder on your machine, add the following function to your shell configuration file (`~/.zshrc` for Mac/Zsh or `~/.bashrc` for Linux/Bash):

   ```sh
    # Replace 'scripts' with any alias of your liking
    scripts() {
        export UID=$UID
        export GID=$(id -g)

        # Replace with the actual absolute path to your project
        docker compose -f /Users/jmrecondo/Documents/projects/cli/compose.yml run --rm jmrec-cli "$@"
    }
    ```

    After adding, run `source ~/.zshrc` to activate it.

3. General Commands

    ```sh
    # View all commands and subcommands
    scripts --help

    # View help for a specific command group
    scripts convert --help
    ```

## Commands

| Command | Description |
| --- | --- |
| `merge` | Convert images to PDF and merge them with existing PDFs, in the order provided. |
| `convert doc2md` | Convert a `.docx` file to Markdown and extract its embedded media. |
| `convert csv2json` | Convert CSV files (or directories of CSVs) to minified JSON. |
| `canvas explore` | Open the Canvas LMS explorer TUI for courses, assignments, and announcements. |

### Canvas credentials

`canvas explore` reads credentials from a `.env` file alongside `compose.yml`:

```sh
CANVAS_API_URL=https://your-institution.instructure.com
CANVAS_API_KEY=your-api-key
```

## Development

Local development uses [`uv`](https://docs.astral.sh/uv/) for the Python environment and [`just`](https://github.com/casey/just) for common tasks.

```sh
uv sync --extra dev   # create .venv and install dependencies
just lint             # ruff format + ruff check
just fix              # ruff check --fix
```

Container builds (`just build`, `just build-all`) are defined in the `Justfile`.
