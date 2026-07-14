"""
Pack Maker — core image logic (framework-agnostic).
Upload a ZIP of product images, get packs of 2, 3, and 4.
"""

from PIL import Image

GAP = 1  # px between items


def sample_bg_color(img: Image.Image) -> tuple[int, int, int]:
    rgba = img.convert("RGBA")
    w, h = rgba.size
    corners = [
        rgba.getpixel((0, 0)),
        rgba.getpixel((w - 1, 0)),
        rgba.getpixel((0, h - 1)),
        rgba.getpixel((w - 1, h - 1)),
    ]
    opaque = [(r, g, b) for r, g, b, a in corners if a > 200]
    if not opaque:
        return (255, 255, 255)
    return (
        sum(c[0] for c in opaque) // len(opaque),
        sum(c[1] for c in opaque) // len(opaque),
        sum(c[2] for c in opaque) // len(opaque),
    )


def build_pack(source: Image.Image, count: int,
               bg_color: tuple[int, int, int]) -> Image.Image:
    src = source.convert("RGBA")
    w, h = src.size

    depth_scale = 0.02
    depth_rise  = 0.01
    step        = w + GAP
    canvas_w    = w + (count - 1) * step
    canvas_h    = h + int(h * depth_scale * (count - 1))

    canvas = Image.new("RGBA", (canvas_w, canvas_h),
                       (bg_color[0], bg_color[1], bg_color[2], 255))

    for i in range(count - 1, -1, -1):
        depth = count - 1 - i
        scale = 1.0 - depth * depth_scale
        iw, ih = max(1, int(w * scale)), max(1, int(h * scale))
        card = src.resize((iw, ih), Image.LANCZOS) if scale != 1.0 else src.copy()
        x = i * step
        y = canvas_h - ih - int(h * depth_rise * depth)
        canvas.alpha_composite(card, dest=(x, y))

    bbox = canvas.getbbox()
    return canvas.crop(bbox) if bbox else canvas


def render_on_background(pack: Image.Image, bg_color: tuple[int, int, int]) -> Image.Image:
    bg = Image.new("RGB", pack.size, bg_color)
    bg.paste(pack, mask=pack.split()[3])
    return bg


def process_image(img: Image.Image, stem: str) -> list[tuple[str, Image.Image]]:
    bg = sample_bg_color(img)
    return [
        (f"{stem}_packof{count}.png",
         render_on_background(build_pack(img, count, bg), bg))
        for count in (2, 3, 4)
    ]
