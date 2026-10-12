"""Pixel-art image processing."""

from io import BytesIO

from PIL import Image, ImageOps


def convert_to_pixel_art(image_bytes: bytes, grid_size: int = 64) -> bytes:
    """Reduce an image to a small color palette and upscale it with hard edges."""
    with Image.open(BytesIO(image_bytes)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")

    image.thumbnail((grid_size, grid_size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (grid_size, grid_size), (21, 24, 45))
    canvas.paste(image, ((grid_size - image.width) // 2, (grid_size - image.height) // 2))
    palette = canvas.quantize(colors=24, method=Image.Quantize.MEDIANCUT)
    pixel_image = palette.convert("RGB").resize(
        (grid_size * 8, grid_size * 8),
        Image.Resampling.NEAREST,
    )
    return _png_bytes(pixel_image)


def _png_bytes(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
