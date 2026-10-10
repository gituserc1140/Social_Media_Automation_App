from io import BytesIO

from PIL import Image

from pixel_art import convert_to_pixel_art, create_demo_animation, create_demo_pixel_art


def test_demo_art_is_a_valid_pixel_art_png():
    image_bytes = create_demo_pixel_art("a tiny moon garden")

    with Image.open(BytesIO(image_bytes)) as image:
        assert image.format == "PNG"
        assert image.size == (256, 256)


def test_uploaded_image_is_upscaled_as_pixel_art():
    source = BytesIO()
    Image.new("RGB", (12, 8), (200, 50, 100)).save(source, format="PNG")

    result = convert_to_pixel_art(source.getvalue(), grid_size=16)

    with Image.open(BytesIO(result)) as image:
        assert image.size == (128, 128)
        assert len(image.getcolors(maxcolors=128)) <= 24


def test_demo_animation_is_a_looping_gif():
    animation = create_demo_animation(create_demo_pixel_art("a pixel cat"))

    with Image.open(BytesIO(animation)) as image:
        assert image.format == "GIF"
        assert image.n_frames > 1
        assert image.info["loop"] == 0
