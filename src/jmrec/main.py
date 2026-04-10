import subprocess
import typer
from pathlib import Path
from typing import List
import img2pdf
from pypdf import PdfWriter
import io
from jmrec.commands import greet

app = typer.Typer()
app.add_typer(greet.app, name="greet", help="Commands related to greetings")

@app.command()
def merge(
    output: Path = typer.Option("merged_output.pdf", "--output", "-o", help="The filename of the resulting PDF."),
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
                typer.secho(f"⚠️ Skipping: {path} (File not found)", fg=typer.colors.YELLOW)
                continue

            ext = path.suffix.lower()

            try:
                if ext == ".pdf":
                    writer.append(path)
                elif ext in valid_extensions:
                    pdf_bytes = img2pdf.convert(str(path))
                    if pdf_bytes is None:
                        typer.secho(f"❌ Failed to convert image: {path.name}", fg=typer.colors.RED)
                        continue
                    img_pdf_stream = io.BytesIO(pdf_bytes)
                    writer.append(img_pdf_stream)
                else:
                    typer.secho(f"⚠️ Skipping: {path} (Unsupported extension)", fg=typer.colors.YELLOW)
            except Exception as e:
                typer.secho(f"❌ Error processing {path.name}: {e}", fg=typer.colors.RED)

    try:
        with open(output, "wb") as f:
            writer.write(f)
        typer.secho(f"\n✅ Combined PDF saved to: {output}", fg=typer.colors.GREEN, bold=True)
    except Exception as e:
        typer.secho(f"❌ Failed to save output: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    
@app.command()
def convert(
    filepath: Path = typer.Argument(..., help="Path to the .docx file", exists=True)
):
    """
    Convert a .docx file to Markdown and extract media.
    """
    filename_stem = filepath.stem 
    output_md = f"{filename_stem}.md"
    media_path = f"./attachments/{filename_stem}"

    cmd = [
        "pandoc",
        "-t", "markdown_strict",
        f"--extract-media={media_path}",
        str(filepath),
        "-o", output_md
    ]

    try:
        subprocess.run(cmd, check=True)
        typer.secho(f"Successfully converted '{filepath}' to '{output_md}'", fg=typer.colors.GREEN)
        typer.echo(f"Media extracted to '{media_path}/'")
    except subprocess.CalledProcessError as e:
        typer.secho(f"Error during conversion: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()