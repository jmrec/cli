import platform
import tempfile

import pypandoc
import typer

from jmrec.utils import pandoc_install_hint


def setup(
    version: str = typer.Option(
        "latest",
        "--version",
        "-V",
        help="Pandoc version to download, e.g. 3.6 (defaults to latest).",
    ),
) -> None:
    """Download Pandoc if it is not already available.

    Pandoc is only needed for `jmrec-cli convert doc2md`. This command is
    idempotent: it does nothing when a usable pandoc binary already exists.
    """
    typer.echo("Checking for Pandoc...")

    try:
        path = pypandoc.get_pandoc_path()
    except OSError:
        path = None

    if path is not None:
        typer.secho(f"Pandoc is already available: {path}", fg=typer.colors.GREEN)
        typer.echo(f"\tVersion: {pypandoc.get_pandoc_version()}")
        return

    if platform.system() == "Windows" and platform.machine().lower() in {"arm64", "aarch64"}:
        typer.secho(
            "Pandoc does not publish Windows ARM64 builds.",
            fg=typer.colors.RED,
            err=True,
        )
        typer.echo("\tInstall it manually: winget install JohnMacFarlane.Pandoc")
        raise typer.Exit(1)

    typer.echo("Pandoc was not found. Downloading the official binary...")

    try:
        pypandoc.download_pandoc(
            version=version,
            download_folder=tempfile.gettempdir(),
            delete_installer=True,
        )
        pypandoc.clean_pandocpath_cache()
        pypandoc.clean_version_cache()
        path = pypandoc.get_pandoc_path()
    except (OSError, RuntimeError) as exc:
        typer.secho(f"Could not install Pandoc: {exc}", fg=typer.colors.RED, err=True)
        typer.echo(f"\tInstall it manually: {pandoc_install_hint()}")
        typer.echo("\tOr set PYPANDOC_PANDOC to the full path of an existing binary.")
        raise typer.Exit(1) from exc

    typer.secho(f"Pandoc installed: {path}", fg=typer.colors.GREEN)
    typer.echo(f"\tVersion: {pypandoc.get_pandoc_version()}")
