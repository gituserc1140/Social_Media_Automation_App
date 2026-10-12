from io import BytesIO

from PIL import Image

from pixel_art import convert_to_pixel_art


def test_uploaded_image_is_upscaled_as_pixel_art():
    source = BytesIO()
    Image.new("RGB", (12, 8), (200, 50, 100)).save(source, format="PNG")

    result = convert_to_pixel_art(source.getvalue(), grid_size=16)

    with Image.open(BytesIO(result)) as image:
        assert image.size == (128, 128)
        assert len(image.getcolors(maxcolors=128)) <= 24
