# JM's Collection of Scripts

A personal CLI toolkit built with Python and Typer. Install it once with [`uv`](https://docs.astral.sh/uv/) and run `jmrec-cli` from any directory.

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/)
- `git` (used by `uv` to install from the repository)

Pandoc is only required by `convert doc2md`; install it on demand with `jmrec-cli setup` (see [Pandoc](#pandoc)).

## Installation

```sh
uv tool install --from git+https://github.com/jmrec/cli.git jmrec-cli
```

`uv` creates an isolated environment and puts `jmrec-cli` on your `PATH`.

To update later:

```sh
uv tool install --force --from git+https://github.com/jmrec/cli.git jmrec-cli
```

## Usage

```sh
# View all commands and subcommands
jmrec-cli --help

# View help for a specific command group
jmrec-cli convert --help
```

## Commands

| Command | Description |
| --- | --- |
| `setup` | Download optional external tools such as Pandoc. |
| `merge` | Convert images to PDF and merge them with existing PDFs, in the order provided. |
| `convert doc2md` | Convert a `.docx` file to Markdown and extract its embedded media. |
| `convert csv2json` | Convert CSV files (or directories of CSVs) to minified JSON. |
| `canvas explore` | Open the Canvas LMS explorer TUI for courses, assignments, and announcements. |

### Environment Variables

Variables are read in the following order (the first one wins).

1. Variables already set in your shell.
2. `.env` in the current directory.
3. Per-user config file:
   - macOS/Linux: `~/.config/jmrec/.env`
   - Windows: `%APPDATA%\jmrec\.env`

## Pandoc

`convert doc2md` needs [Pandoc](https://pandoc.org/). Install it once:

```sh
jmrec-cli setup
```

The official binary is downloaded into:

| OS | Location |
| --- | --- |
| macOS | `~/Applications/pandoc` |
| Linux | `~/bin` |
| Windows | `%LOCALAPPDATA%\Pandoc` |

Re-running `jmrec-cli setup` does nothing when Pandoc is already available. Use `jmrec-cli setup --version 3.6` to pin a release.

Alternatively, install Pandoc with your package manager:

- macOS: `brew install pandoc`
- Windows: `winget install JohnMacFarlane.Pandoc`
- Linux: `sudo apt install pandoc` (or your distribution's package manager)

If you already have a binary elsewhere, point `PYPANDOC_PANDOC` at it. Windows ARM64 has no official Pandoc build, so use one of the manual options there.

## Development

Local development uses `uv` for the Python environment and [`just`](https://github.com/casey/just) for common tasks (`just` is optional).

```sh
uv sync --extra dev   # create .venv and install dependencies
just lint             # ruff format + ruff check
just fix              # ruff check --fix
just dev              # editable install: jmrec-cli runs this checkout
```

The `Justfile` also provides `just install`, `just update`, and `just setup`.
