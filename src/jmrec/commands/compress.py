"""Compress images to a target file size."""

import io
from pathlib import Path

import typer
from PIL import Image, ImageOps

from jmrec.utils import console

app = typer.Typer()

EXTENSIONS = {"jpeg": "JPEG", "jpg": "JPEG", "png": "PNG", "webp": "WEBP"}
UNITS = {"b": 1, "k": 1024, "kb": 1024, "m": 1024**2, "mb": 1024**2, "g": 1024**3, "gb": 1024**3}
MAX_QUALITY = 95
MIN_DIMENSION = 32


def parse_size(value: str) -> int:
    """Parse ``200KB``, ``1.5MB`` or a raw byte count."""
    text = value.strip().lower().replace(" ", "")
    for suffix in sorted(UNITS, key=len, reverse=True):
        if text.endswith(suffix):
            return int(float(text[: -len(suffix)]) * UNITS[suffix])
    return int(text)


def format_size(num_bytes: int) -> str:
    """Render a byte count using the largest sensible unit."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def get_format(path: Path) -> str | None:
    """Return the Pillow format name for *path*, if recognised."""
    return EXTENSIONS.get(path.suffix.lower().lstrip("."))


def prepare(image: Image.Image, fmt: str) -> Image.Image:
    """Apply EXIF orientation and flatten transparency for formats without alpha."""
    image = ImageOps.exif_transpose(image)
    if fmt not in ("JPEG", "WEBP"):
        return image
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        image = Image.new("RGB", rgba.size, "white")
        image.paste(rgba, mask=rgba.getchannel("A"))
        return image
    return image.convert("RGB")


def encode(image: Image.Image, fmt: str, quality: int = 85, colors: int | None = None) -> bytes:
    """Serialise *image* in *fmt*."""
    buffer = io.BytesIO()
    if fmt == "JPEG":
        image.save(buffer, "JPEG", quality=quality, optimize=True, progressive=True)
    elif fmt == "WEBP":
        image.save(buffer, "WEBP", quality=quality, method=6)
    elif colors:
        image.quantize(colors=colors).save(buffer, "PNG", optimize=True)
    else:
        image.save(buffer, "PNG", optimize=True)
    return buffer.getvalue()


def fit(image: Image.Image, fmt: str, limit: int, min_quality: int) -> tuple[bytes, int] | None:
    """Return the best encoding that fits *limit* bytes, without downscaling."""
    if fmt == "PNG":
        for colors in (None, 256, 64, 16):
            data = encode(image, "PNG", colors=colors)
            if len(data) <= limit:
                return data, 0
        return None

    low, high = min_quality, MAX_QUALITY
    best: tuple[bytes, int] | None = None
    while low <= high:
        quality = (low + high) // 2
        data = encode(image, fmt, quality)
        if len(data) <= limit:
            best = (data, quality)
            low = quality + 1
        else:
            high = quality - 1
    return best


def compress(
    image: Image.Image, fmt: str, limit: int, min_quality: int
) -> tuple[bytes, int] | None:
    """Encode under *limit*, downscaling until it fits."""
    while True:
        result = fit(image, fmt, limit, min_quality)
        if result is not None:
            return result
        if min(image.size) <= MIN_DIMENSION:
            return None
        image = image.resize(
            (image.width * 3 // 4, image.height * 3 // 4), Image.Resampling.LANCZOS
        )


@app.command()
def image(
    source: Path = typer.Argument(..., exists=True, dir_okay=False, help="Image to compress."),
    target: str = typer.Option(..., "--target", "-t", help="Target size, e.g. 200KB or 1.5MB."),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file."),
    min_quality: int = typer.Option(
        20, "--min-quality", min=1, max=MAX_QUALITY, help="Quality floor before downscaling."
    ),
):
    """Compress an image so it fits within a target file size."""
    try:
        limit = parse_size(target)
    except ValueError as exc:
        raise typer.BadParameter(str(exc), param_hint="--target") from exc

    fmt = (get_format(output) if output else get_format(source)) or "JPEG"
    out_path = output or source.with_name(f"{source.stem}-compressed.{fmt.lower()}")
    if not out_path.parent.is_dir():
        raise typer.BadParameter(
            f"directory does not exist: {out_path.parent}", param_hint="--output"
        )

    before = source.stat().st_size
    if before <= limit and get_format(source) == fmt:
        out_path.write_bytes(source.read_bytes())
        console.print(f"[success]✓[/success] {out_path} already fits ({format_size(before)}).")
        return

    try:
        with Image.open(source) as handle:
            result = compress(prepare(handle, fmt), fmt, limit, min_quality)
    except Exception as exc:
        console.print(f"[error]Cannot read {source.name}: {exc}[/error]")
        raise typer.Exit(1) from exc

    if result is None:
        console.print(f"[error]Cannot reach {format_size(limit)} without going below 32px.[/error]")
        raise typer.Exit(1)

    data, quality = result
    out_path.write_bytes(data)
    after = out_path.stat().st_size
    detail = f"quality {quality}" if quality else "image optimized"
    console.print(
        f"[success]✓[/success] {out_path} {format_size(after)} "
        f"({detail}, {format_size(before)} → {100 - after / before * 100:.0f}% smaller)"
    )
