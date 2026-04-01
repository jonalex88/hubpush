from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

CYAN = "#19c2f0"
BLUE = "#0d57c6"
WHITE = "#ffffff"
TRANSPARENT = (255, 255, 255, 0)


def load_font(size: int, bold: bool = False):
    candidates = []
    if bold:
        candidates.extend([
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\bahnschrift.ttf",
        ])
    candidates.extend([
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
    ])
    for candidate in candidates:
        p = Path(candidate)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def draw_mark(draw: ImageDraw.ImageDraw, origin_x: int, origin_y: int, scale: float) -> None:
    # Approximate the supplied TJ monogram with rounded cyan bars.
    bar = int(24 * scale)
    radius = int(10 * scale)
    gap = int(6 * scale)
    mark_w = int(96 * scale)
    mark_h = int(96 * scale)

    # Top horizontal
    draw.rounded_rectangle(
        (origin_x, origin_y, origin_x + mark_w, origin_y + bar),
        radius=radius,
        fill=CYAN,
    )
    # Left vertical
    draw.rounded_rectangle(
        (origin_x, origin_y, origin_x + bar, origin_y + mark_h),
        radius=radius,
        fill=CYAN,
    )
    # Bottom hook for J
    draw.rounded_rectangle(
        (origin_x + int(38 * scale), origin_y + int(42 * scale), origin_x + int(62 * scale), origin_y + mark_h),
        radius=radius,
        fill=CYAN,
    )
    draw.rounded_rectangle(
        (origin_x + int(20 * scale), origin_y + mark_h - bar, origin_x + int(62 * scale), origin_y + mark_h),
        radius=radius,
        fill=CYAN,
    )
    # Middle cutout to imply the T/J split.
    draw.rounded_rectangle(
        (origin_x + bar + gap, origin_y + bar + gap, origin_x + mark_w - gap, origin_y + int(41 * scale)),
        radius=radius,
        fill=WHITE,
    )
    draw.rounded_rectangle(
        (origin_x + int(17 * scale), origin_y + int(45 * scale), origin_x + int(36 * scale), origin_y + int(70 * scale)),
        radius=radius,
        fill=WHITE,
    )


def build_logo():
    image = Image.new("RGBA", (760, 220), TRANSPARENT)
    draw = ImageDraw.Draw(image)
    draw_mark(draw, 16, 52, 1.35)

    tj_font = load_font(78, bold=True)
    line_font = load_font(76, bold=True)

    text_x = 188
    draw.text((text_x, 30), "TRANSACTION", font=tj_font, fill=BLUE)
    draw.text((text_x, 106), "JUNCTION", font=line_font, fill=BLUE)

    image.save(ASSETS / "tj_logo.png")


def build_favicon():
    base = Image.new("RGBA", (256, 256), WHITE)
    draw = ImageDraw.Draw(base)
    draw_mark(draw, 26, 26, 2.15)
    base.save(ASSETS / "tj_icon.png")
    base.save(ASSETS / "tj_icon.ico", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])


if __name__ == "__main__":
    build_logo()
    build_favicon()
    print("Generated assets:")
    print(ASSETS / "tj_logo.png")
    print(ASSETS / "tj_icon.png")
    print(ASSETS / "tj_icon.ico")
