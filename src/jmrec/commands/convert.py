import json
from pathlib import Path
from typing import Iterable, List

import pypandoc
import tablib
import typer
from rich.table import Table

from jmrec.utils import console

app = typer.Typer()


@app.command()
def doc2md(
    filepath: Path = typer.Argument(..., help="Path to the .docx file", exists=True),
):
    """
    Convert a .docx file to Markdown and extract media using pypandoc.
    """
    output_md = filepath.with_suffix(".md")
    media_path = Path("./attachments") / filepath.stem

    try:
        pypandoc.convert_file(
            str(filepath),
            "markdown_strict",
            outputfile=str(output_md),
            extra_args=[f"--extract-media={media_path}"],
        )
        typer.secho(
            f"✅ Converted '{filepath.name}' to '{output_md.name}'",
            fg=typer.colors.GREEN,
        )
        typer.echo(f"📁 Media extracted to '{media_path}/'")
    except Exception as e:
        typer.secho(f"❌ Conversion failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e


@app.command()
def csv2json(
    inputs: List[Path] = typer.Argument(..., help="CSV files or directories containing CSVs."),
):
    """
    Convert CSV files to minified JSON using tablib.
    """
    files_to_process: List[Path] = []

    for path in inputs:
        if path.is_dir():
            files_to_process.extend(list(path.glob("*.csv")))
        elif path.suffix.lower() == ".csv":
            files_to_process.append(path)

    if not files_to_process:
        typer.secho("❌ No valid CSV files found.", fg=typer.colors.RED)
        raise typer.Exit(1)

    table = Table(title="Conversion Summary", show_header=True, header_style="bold magenta")
    table.add_column("File Name", style="dim")
    table.add_column("Status", justify="right")
    table.add_column("Size Change", justify="right")
    with typer.progressbar(files_to_process, label="Processing") as progress:
        progress: Iterable[Path]

        for csv_path in progress:
            # try:
            try:
                with open(csv_path, "r", encoding="utf-8-sig") as f:
                    data = tablib.Dataset().load(f.read(), format="csv")
            except Exception as e:
                typer.secho(
                    f"❌ Error reading {csv_path.name}: {type(e).__name__}: {e}",
                    fg=typer.colors.RED,
                    err=True,
                )
                continue

            try:
                json_obj = json.loads(data.export("json"))
                with open(csv_path.with_suffix(".json"), "w", encoding="utf-8") as f:
                    json.dump(json_obj, f, separators=(",", ":"))
            except Exception as e:
                typer.secho(
                    f"❌ Error writing {csv_path.name}: {type(e).__name__}: {e}",
                    fg=typer.colors.RED,
                    err=True,
                )
                continue

            orig_size = csv_path.stat().st_size
            new_size = csv_path.with_suffix(".json").stat().st_size
            diff = (new_size / orig_size) * 100

            table.add_row(csv_path.name, "[success]SUCCESS[/success]", f"{diff:.1f}%")
            # except Exception as e:
            # table.add_row(csv_path.name, f"[error]FAILED[/error]", str(e))
            # typer.secho(f"\nError in {csv_path.name}: {e}", fg=typer.colors.RED)

    # typer.secho(
    #     f"\n✅ Done! Processed {len(files_to_process)} files.",
    #     fg=typer.colors.GREEN,
    #     bold=True,
    # )
    console.print(table)
