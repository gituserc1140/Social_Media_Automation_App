"""Pixel-art image processing and key-free demo assets."""

from hashlib import sha256
from io import BytesIO

from PIL import Image, ImageDraw, ImageOps


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


def create_demo_pixel_art(prompt: str) -> bytes:
    """Create a small prompt-inspired pixel-art scene without external services."""
    digest = sha256(prompt.encode("utf-8")).digest()
    sky = (17 + digest[0] % 35, 20 + digest[1] % 35, 55 + digest[2] % 55)
    accent = (150 + digest[3] % 90, 90 + digest[4] % 100, 130 + digest[5] % 100)
    image = Image.new("RGB", (32, 32), sky)
    draw = ImageDraw.Draw(image)

    for x, y in ((5, 6), (21, 4), (25, 12), (10, 14)):
        draw.rectangle((x, y, x + 1, y + 1), fill=(245, 231, 165))

    draw.rectangle((2, 24, 29, 31), fill=(38, 71, 74))
    draw.rectangle((6, 18, 25, 24), fill=accent)
    draw.rectangle((10, 14, 21, 20), fill=accent)
    draw.rectangle((13, 11, 18, 16), fill=(246, 201, 110))
    draw.rectangle((12, 17, 13, 18), fill=(20, 25, 42))
    draw.rectangle((18, 17, 19, 18), fill=(20, 25, 42))
    draw.rectangle((14, 21, 17, 22), fill=(247, 233, 190))
    draw.rectangle((3, 26, 8, 27), fill=(87, 137, 99))
    draw.rectangle((23, 28, 28, 29), fill=(87, 137, 99))
    return _png_bytes(image.resize((256, 256), Image.Resampling.NEAREST))


def create_demo_animation(image_bytes: bytes) -> bytes:
    """Make a small looping GIF from an image for the no-key demo."""
    with Image.open(BytesIO(image_bytes)) as source:
        base = source.convert("RGB").resize((256, 256), Image.Resampling.NEAREST)

    frames = []
    for offset in (0, 3, 6, 3):
        frame = Image.new("RGB", base.size, (21, 24, 45))
        frame.paste(base, (offset, 0))
        frames.append(frame)

    output = BytesIO()
    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=180,
        loop=0,
        optimize=False,
    )
    return output.getvalue()


def _png_bytes(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
