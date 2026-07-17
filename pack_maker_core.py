"""
Pack Maker — core image logic (framework-agnostic).
Upload a ZIP of product images, get packs of 2, 3, and 4.
"""

from PIL import Image, ImageChops

GAP = 1  # px between items
CROP_PAD = 6  # px of breathing room kept around the auto-cropped product
CROP_TOLERANCE = 12  # 0-255, how different from bg a pixel must be to count as product
MAX_SOURCE_DIM = 1600  # downscale huge source photos before processing, for speed
OUTPUT_MAX_SIDE = 3000  # px, the longer output side always maximizes to this


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


def _downscale_if_huge(img: Image.Image, max_dim: int = MAX_SOURCE_DIM) -> Image.Image:
    w, h = img.size
    longest = max(w, h)
    if longest <= max_dim:
        return img
    scale = max_dim / longest
    return img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)


def auto_crop_to_content(img: Image.Image, bg_color: tuple[int, int, int],
                         tol: int = CROP_TOLERANCE, pad: int = CROP_PAD) -> Image.Image:
    """Trim background padding so only the product (plus a small pad) remains."""
    rgba = img.convert("RGBA")
    alpha = rgba.split()[3]

    if alpha.getextrema()[0] < 255:
        # Image already carries real transparency — trust the alpha channel.
        bbox = alpha.point(lambda p: 255 if p > 8 else 0).getbbox()
    else:
        rgb = rgba.convert("RGB")
        flat_bg = Image.new("RGB", rgb.size, bg_color)
        diff = ImageChops.difference(rgb, flat_bg).convert("L")
        mask = diff.point(lambda p: 255 if p > tol else 0)
        # Knock out anything matching the photo's own background color so it
        # can't bleed through as a color cast — the pack canvas is always
        # pure white, so background pixels should be transparent, not baked in.
        rgba.putalpha(mask)
        bbox = mask.getbbox()

    if not bbox:
        return rgba

    left, top, right, bottom = bbox
    w, h = rgba.size
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(w, right + pad)
    bottom = min(h, bottom + pad)
    return rgba.crop((left, top, right, bottom))


def _build_pack_row(src: Image.Image, count: int,
                    bg_color: tuple[int, int, int]) -> Image.Image:
    """Lay items out side by side horizontally, with a slight depth
    scale/rise on each successive item for a shelf-like 3D look."""
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
        # depth-scale steps are tiny (<=~6%), so bilinear is visually indistinguishable
        # from LANCZOS here but noticeably faster across several resizes per image.
        card = src.resize((iw, ih), Image.BILINEAR) if scale != 1.0 else src.copy()
        x = i * step
        y = canvas_h - ih - int(h * depth_rise * depth)
        canvas.alpha_composite(card, dest=(x, y))

    return canvas


def _build_pack_grid(src: Image.Image, cols: int, rows: int,
                     bg_color: tuple[int, int, int]) -> Image.Image:
    """Lay items out in a cols x rows grid, no overlap. Each item is
    centered in a square cell (sized to its longer side) so an equal
    cols x rows grid — e.g. 2x2 — comes out an exact square canvas,
    with no padding or cropping needed to reach 1:1."""
    w, h = src.size
    cell = max(w, h)
    canvas_w = cols * cell + (cols - 1) * GAP
    canvas_h = rows * cell + (rows - 1) * GAP

    canvas = Image.new("RGBA", (canvas_w, canvas_h),
                       (bg_color[0], bg_color[1], bg_color[2], 255))

    for row in range(rows):
        for col in range(cols):
            cell_x = col * (cell + GAP)
            cell_y = row * (cell + GAP)
            x = cell_x + (cell - w) // 2
            y = cell_y + (cell - h) // 2
            canvas.alpha_composite(src, dest=(x, y))

    return canvas


def build_pack(source: Image.Image, count: int,
               bg_color: tuple[int, int, int]) -> Image.Image:
    src = source.convert("RGBA")

    if count == 4:
        canvas = _build_pack_grid(src, cols=2, rows=2, bg_color=bg_color)
    else:
        canvas = _build_pack_row(src, count, bg_color)

    bbox = canvas.getbbox()
    return canvas.crop(bbox) if bbox else canvas


def render_on_background(pack: Image.Image, bg_color: tuple[int, int, int],
                         max_side: int = OUTPUT_MAX_SIDE) -> Image.Image:
    """Resize the pack up to a resolution matching its own aspect ratio —
    no cropping, so no product is ever cut off. The longer side always
    maximizes to max_side (3000px); the shorter side follows the pack's
    own aspect ratio (so a square pack, e.g. the pack-of-4 grid, comes
    out an exact 3000x3000)."""
    w, h = pack.size
    aspect = max(w, h) / min(w, h)
    long_side = max_side
    short_side = max(1, round(long_side / aspect))
    size = (long_side, short_side) if w >= h else (short_side, long_side)

    fitted = pack.resize(size, Image.LANCZOS)
    bg = Image.new("RGB", size, bg_color)
    bg.paste(fitted, (0, 0), mask=fitted.split()[3])
    return bg


def process_image(img: Image.Image, stem: str,
                  pack_sizes: tuple[int, ...] = (2, 3, 4)) -> list[tuple[str, Image.Image]]:
    # sample_bg_color() only informs auto-crop's product-vs-background
    # detection; the pack canvas and fillers are always pure white,
    # regardless of the source photo's own background color.
    src_bg = sample_bg_color(img)
    cropped = auto_crop_to_content(_downscale_if_huge(img), src_bg)
    white = (255, 255, 255)
    return [
        (f"{stem}_packof{count}.png",
         render_on_background(build_pack(cropped, count, white), white))
        for count in pack_sizes
    ]
