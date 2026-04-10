import io
import subprocess
from pathlib import Path
from typing import List

import img2pdf
import typer
from pypdf import PdfWriter

from jmrec.commands import convert, greet

app = typer.Typer()
app.add_typer(greet.app, name="greet", help="Commands related to greetings")
app.add_typer(convert.app, name="convert", help="Commands related to conversion")


@app.command()
def merge(
    output: Path = typer.Option(
        "merged_output.pdf", "--output", "-o", help="The filename of the resulting PDF."
    ),
    inputs: List[Path] = typer.Argument(..., help="List of images or PDFs to combine."),
):
    """
    Converts images to PDF and merges them with existing PDFs in the order provided.
    """
    writer = PdfWriter()
    valid_extensions = {".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".gif"}

    if not inputs:
        typer.secho("❌ No input files provided.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    with typer.progressbar(inputs, label="Processing files") as progress:
        for path in progress:
            if not path.exists():
                typer.secho(
                    f"⚠️ Skipping: {path} (File not found)", fg=typer.colors.YELLOW
                )
                continue

            ext = path.suffix.lower()

            try:
                if ext == ".pdf":
                    writer.append(path)
                elif ext in valid_extensions:
                    pdf_bytes = img2pdf.convert(str(path))
                    if pdf_bytes is None:
                        typer.secho(
                            f"❌ Failed to convert image: {path.name}",
                            fg=typer.colors.RED,
                        )
                        continue
                    img_pdf_stream = io.BytesIO(pdf_bytes)
                    writer.append(img_pdf_stream)
                else:
                    typer.secho(
                        f"⚠️ Skipping: {path} (Unsupported extension)",
                        fg=typer.colors.YELLOW,
                    )
            except Exception as e:
                typer.secho(
                    f"❌ Error processing {path.name}: {e}", fg=typer.colors.RED
                )

    try:
        with open(output, "wb") as f:
            writer.write(f)
        typer.secho(
            f"\n✅ Combined PDF saved to: {output}", fg=typer.colors.GREEN, bold=True
        )
    except Exception as e:
        typer.secho(f"❌ Failed to save output: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from e


@app.command(
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
        "help_option_names": [],
    },
    help="Raw passthrough to the underlying pandoc binary.",
)
def pandoc(ctx: typer.Context):
    """
    Run raw pandoc commands inside the container.
    Example: scripts pandoc --version
    """
    cmd = ["pandoc"] + ctx.args

    try:
        subprocess.run(cmd, shell=False) # noqa: S603
    except FileNotFoundError:
        typer.secho("❌ Pandoc binary not found in the container.", fg=typer.colors.RED)


if __name__ == "__main__":
    app()
