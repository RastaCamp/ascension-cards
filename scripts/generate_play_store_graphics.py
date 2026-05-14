"""
Generate Google Play listing graphics (icon, feature graphic, phone screenshots).
Card images are read from the newest app-release.aab (base/assets/cards/) when present,
so you do not need to re-run Gradle. Falls back to build intermediates or repo cards/.
Run from repo root: python scripts/generate_play_store_graphics.py
"""
from __future__ import annotations

import io
import os
import struct
import zipfile
import zlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]

OUT = ROOT / "store-listing" / "play-console"
OUT.mkdir(parents=True, exist_ok=True)


def find_release_aab() -> Path | None:
    """Newest .aab under bundle/release — same bits users upload; no Gradle run needed."""
    rel = ROOT / "android" / "app" / "build" / "outputs" / "bundle" / "release"
    if not rel.is_dir():
        return None
    aabs = sorted(rel.glob("*.aab"), key=lambda p: p.stat().st_mtime, reverse=True)
    return aabs[0] if aabs else None


def _filesystem_card_dirs() -> list[Path]:
    return [
        ROOT / "android" / "app" / "build" / "intermediates" / "assets" / "release" / "cards",
        ROOT / "android" / "app" / "build" / "generatedWebAssets" / "cards",
        ROOT / "cards",
    ]


def _open_card_from_aab(aab: Path, filename: str) -> Image.Image | None:
    prefix = "base/assets/cards/"
    variants = [prefix + filename, prefix + filename.replace("_", " ")]
    if filename.lower().endswith(".png"):
        variants.append(prefix + filename[:-4] + ".PNG")
    with zipfile.ZipFile(aab) as z:
        names = set(z.namelist())
        for v in variants:
            if v in names:
                return Image.open(io.BytesIO(z.read(v))).convert("RGBA")
        tail = filename.lower()
        for n in z.namelist():
            if n.lower().startswith(prefix) and n.lower().endswith(tail):
                return Image.open(io.BytesIO(z.read(n))).convert("RGBA")
    return None


def _open_card_from_disk(filename: str) -> Image.Image | None:
    for folder in _filesystem_card_dirs():
        for cand in (folder / filename, folder / filename.replace("_", " ")):
            if cand.exists():
                return Image.open(cand).convert("RGBA")
    return None


def describe_card_source() -> str:
    aab = find_release_aab()
    if aab:
        return f"AAB {aab.name}"
    for folder in _filesystem_card_dirs():
        if (folder / "queen_spades.png").exists():
            return f"folder {folder.relative_to(ROOT)}"
    return "unknown"

# Palette (matches index.html dark theme)
C_BG_TOP = (42, 31, 69)
C_BG_MID = (20, 16, 32)
C_BG_DEEP = (10, 6, 18)
C_TEAL = (126, 232, 220)
C_LILAC = (196, 165, 255)
C_GOLD = (240, 215, 140)
C_MUTED = (160, 150, 185)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    windir = os.environ.get("WINDIR", r"C:\Windows")
    names = ["segoeuib.ttf", "segoeui.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]
    for n in names:
        p = Path(windir) / "Fonts" / n
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def horizontal_gradient(
    size: tuple[int, int],
    left: tuple[int, int, int],
    right: tuple[int, int, int],
) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size)
    px = img.load()
    wm = max(w - 1, 1)
    for x in range(w):
        t = x / wm
        r = int(left[0] * (1 - t) + right[0] * t)
        g = int(left[1] * (1 - t) + right[1] * t)
        b = int(left[2] * (1 - t) + right[2] * t)
        for y in range(h):
            px[x, y] = (r, g, b)
    return img


def linear_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    base = Image.new("RGB", (w, h))
    pix = base.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        for x in range(w):
            pix[x, y] = (r, g, b)
    return base


def radial_vignette(base: Image.Image, strength: float = 0.45) -> Image.Image:
    w, h = base.size
    layer = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(layer)
    cx, cy = w // 2, h // 2
    max_r = int((w * w + h * h) ** 0.5 / 2) + 40
    for r in range(max_r, 0, -3):
        alpha = int(255 * (1 - strength * (1 - r / max_r)))
        alpha = max(0, min(255, alpha))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=alpha)
    vig = Image.new("RGB", (w, h), C_BG_DEEP)
    return Image.composite(base, vig, layer)


def load_card(name: str, max_h: int) -> Image.Image:
    im: Image.Image | None = None
    aab = find_release_aab()
    if aab:
        im = _open_card_from_aab(aab, name)
    if im is None:
        im = _open_card_from_disk(name)
    if im is None:
        raise FileNotFoundError(
            f"Card not found: {name}. Build an AAB once (app-release.aab) or keep PNGs under cards/."
        )
    w, h = im.size
    scale = max_h / h
    im = im.resize((int(w * scale), max_h), Image.Resampling.LANCZOS)
    return im


def paste_center(bg: Image.Image, fg: Image.Image, xy: tuple[int, int]) -> None:
    x, y = xy
    w, h = fg.size
    bg.paste(fg, (x - w // 2, y - h // 2), fg)


def draw_shadow_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    shadow: tuple[int, int, int] = (18, 10, 38),
) -> None:
    x, y = xy
    for ox, oy in ((4, 4), (2, 2), (1, 1)):
        draw.text((x + ox, y + oy), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)


def paste_rotated_card_with_shadow(
    canvas: Image.Image,
    card_rgba: Image.Image,
    cx: int,
    cy: int,
    angle: float,
    *,
    shadow_offset: tuple[int, int] = (14, 20),
    blur_radius: int = 14,
) -> None:
    """Paste a rotated card + soft drop shadow (canvas RGB or RGBA)."""
    rot = card_rgba.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    w, h = rot.size
    left = cx - w // 2
    top = cy - h // 2
    alpha = rot.split()[3]
    shadow_rgb = (16, 10, 36)
    tint = Image.new("RGB", (w, h), shadow_rgb)
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh.paste(tint, (0, 0), alpha.point(lambda a: min(255, int(a * 0.48))))
    if blur_radius > 0:
        sh = sh.filter(ImageFilter.GaussianBlur(blur_radius))
    sx, sy = shadow_offset
    canvas.paste(sh, (left + sx, top + sy), sh)
    canvas.paste(rot, (left, top), rot)


def write_rgb_png_minimal(path: Path, width: int, height: int, rgb_bytes: bytes) -> None:
    """
    PNG with only required chunks (IHDR, IDAT, IEND) — no pHYs, gAMA, text, etc.
    Some upload validators mis-read optional metadata as 'wrong' canvas size.
    """
    if len(rgb_bytes) != width * height * 3:
        raise ValueError("rgb_bytes length mismatch")
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)

    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        body = chunk_type + data
        crc = zlib.crc32(body) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + body + struct.pack(">I", crc)

    raw_scanlines = b"".join(
        b"\x00" + rgb_bytes[y * width * 3 : (y + 1) * width * 3] for y in range(height)
    )
    compressed = zlib.compress(raw_scanlines, 9)
    blob = signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")
    path.write_bytes(blob)


def save_play_feature_for_upload(rgb: Image.Image) -> None:
    """Exact 1024x500, pixel clone, minimal PNG + baseline JPEG without DPI metadata."""
    w, h = 1024, 500
    if rgb.size != (w, h):
        raise ValueError(f"expected {(w, h)}, got {rgb.size}")
    raw = rgb.convert("RGB").tobytes()
    clean = Image.frombytes("RGB", (w, h), raw)
    png_path = OUT / "feature-graphic-1024x500.png"
    jpg_path = OUT / "feature-graphic-1024x500.jpg"
    write_rgb_png_minimal(png_path, w, h, raw)
    clean.save(
        jpg_path,
        "JPEG",
        quality=92,
        subsampling=0,
        progressive=False,
        optimize=False,
    )
    print("Wrote", png_path, "(minimal PNG chunks)")
    print("Wrote", jpg_path, "(baseline JPEG, no DPI kwarg)")


def feature_graphic_fill_canvas(source: Image.Image, canvas_w: int = 1024, canvas_h: int = 500) -> Image.Image:
    """
    New RGB canvas exactly (canvas_w, canvas_h). Uniform scale source so it fully
    covers the canvas, then center-crop (no letterboxing). Play-safe 24-bit RGB.
    """
    src = source.convert("RGB")
    sw, sh = src.size
    scale = max(canvas_w / sw, canvas_h / sh)
    nw = max(canvas_w, int(round(sw * scale)))
    nh = max(canvas_h, int(round(sh * scale)))
    resized = src.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - canvas_w) // 2
    top = (nh - canvas_h) // 2
    cropped = resized.crop((left, top, left + canvas_w, top + canvas_h))
    canvas = Image.new("RGB", (canvas_w, canvas_h))
    canvas.paste(cropped, (0, 0))
    return canvas


def draw_star(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, fill: tuple[int, int, int]) -> None:
    import math

    pts = []
    for i in range(10):
        ang = math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r // 2
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    draw.polygon(pts, fill=fill)


def make_icon_512() -> None:
    size = 512
    base = linear_gradient((size, size), C_BG_TOP, C_BG_MID)
    base = radial_vignette(base, 0.35)
    draw = ImageDraw.Draw(base)
    draw_star(draw, 256, 110, 36, C_TEAL)
    draw_star(draw, 256, 110, 18, C_LILAC)

    q = load_card("queen_spades.png", 340)
    paste_center(base, q, (256, 300))

    # subtle rim
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle((8, 8, size - 9, size - 9), radius=64, outline=(*C_LILAC, 90), width=3)
    base = base.convert("RGBA")
    base = Image.alpha_composite(base, overlay)
    base = base.convert("RGB")

    path = OUT / "app-icon-512.png"
    base.save(path, "PNG", optimize=True)
    print("Wrote", path)


def make_feature_1024x500() -> None:
    """
    Play feature graphic: 2x internal resolution, vibrant gradient, glow, legible type,
    three-Queen fan with shadows — export to exact 1024×500.
    """
    s = 2
    w, h = 1024 * s, 500 * s

    # Background: horizontal depth + slight vertical wash (stays vivid; not grey mud)
    bg = horizontal_gradient((w, h), (72, 48, 108), (22, 14, 42))
    wash = linear_gradient((w, h), (45, 32, 78), (28, 18, 52))
    bg = Image.blend(bg, wash, 0.28)

    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((int(w * 0.42), int(-h * 0.22), int(w * 1.02), int(h * 0.72)), fill=(120, 220, 205, 70))
    gd.ellipse((int(w * 0.58), int(h * 0.25), int(w * 1.12), int(h * 1.08)), fill=(190, 150, 255, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(max(28, 22 * s)))
    layer = bg.convert("RGBA")
    layer = Image.alpha_composite(layer, glow)
    base = layer.convert("RGB")

    draw = ImageDraw.Draw(base)
    x0 = 56 * s
    eyebrow_f = _font(23 * s, bold=True)
    title_f = _font(78 * s, bold=True)
    sub_f = _font(30 * s)
    hint_f = _font(22 * s)

    draw_shadow_text(draw, (x0, 46 * s), "ORACLE  ·  CARD GAME", eyebrow_f, C_TEAL, shadow=(12, 8, 35))
    draw_shadow_text(draw, (x0, 82 * s), "ASCENSION", title_f, C_GOLD, shadow=(20, 12, 45))

    draw.rectangle([x0, 168 * s, x0 + 340 * s, 168 * s + max(4, 3 * s)], fill=C_TEAL)

    draw.text((x0, 188 * s), "Easy ESP training — find the Queen of Spades", font=sub_f, fill=(235, 230, 252))
    draw.text(
        (x0, 238 * s),
        "Three-card shuffle · Grimoire & toolkit · Plays offline",
        font=hint_f,
        fill=C_MUTED,
    )

    # Fanned Queens on the right (back to front)
    hero = base.convert("RGBA")
    cx = int(w * 0.74)
    cy = int(h * 0.52)
    spread = 108 * s
    card_h = int(355 * s)
    blur = max(10, 9 * s)

    qd = load_card("queen_diamonds.png", card_h)
    qh = load_card("queen_hearts.png", card_h)
    qs = load_card("queen_spades.png", int(card_h * 1.06))

    paste_rotated_card_with_shadow(
        hero, qd, cx - spread, cy, -14.0, shadow_offset=(12 * s, 16 * s), blur_radius=blur
    )
    paste_rotated_card_with_shadow(
        hero, qh, cx, cy, 0.0, shadow_offset=(14 * s, 18 * s), blur_radius=blur
    )
    paste_rotated_card_with_shadow(
        hero, qs, cx + spread, cy, 14.0, shadow_offset=(16 * s, 20 * s), blur_radius=blur
    )

    merged = hero.convert("RGB")
    final = merged.resize((1024, 500), Image.Resampling.LANCZOS)
    save_play_feature_for_upload(final)


def phone_frame() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    w, h = 1080, 1920
    base = linear_gradient((w, h), C_BG_TOP, C_BG_DEEP)
    base = radial_vignette(base, 0.4)
    return base, ImageDraw.Draw(base)


def shot_title() -> Image.Image:
    base, draw = phone_frame()
    draw_star(draw, 540, 320, 52, C_TEAL)
    draw_star(draw, 540, 320, 26, C_LILAC)
    tf = _font(86, True)
    sf = _font(34)
    t = "✦ ASCENSION ✦"
    tw = draw.textlength(t, font=tf)
    draw.text((540 - tw / 2, 420), t, font=tf, fill=C_GOLD)
    st = "Easy ESP Training Card Game"
    sw = draw.textlength(st, font=sf)
    draw.text((540 - sw / 2, 530), st, font=sf, fill=C_TEAL)

    q = load_card("queen_spades.png", 420)
    paste_center(base, q, (540, 980))

    def pill(y: int, label: str) -> None:
        bw, bh = 880, 88
        x0 = 540 - bw // 2
        overlay = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rounded_rectangle((0, 0, bw, bh), radius=22, fill=(30, 22, 48, 230), outline=(*C_LILAC, 120), width=2)
        base.paste(overlay, (x0, y), overlay)
        f = _font(32)
        lw = draw.textlength(label, font=f)
        draw.text((540 - lw / 2, y + bh // 2 - 20), label, font=f, fill=(230, 225, 245))

    pill(1320, "Play the game")
    pill(1425, "Grimoire & help")
    pill(1530, "Records & achievements")

    foot = _font(22)
    ft = "Standalone — data stays on this device"
    fw = draw.textlength(ft, font=foot)
    draw.text((540 - fw / 2, 1780), ft, font=foot, fill=C_MUTED)
    return base


def shot_game() -> Image.Image:
    base, draw = phone_frame()
    f = _font(40, True)
    draw.text((60, 100), "Find the Queen of Spades", font=f, fill=C_GOLD)
    hf = _font(26)
    draw.text((60, 165), "Watch the swap — trust your first read", font=hf, fill=C_TEAL)

    hud = "Streak 3   ·   Wins 12   ·   Rank: Apprentice"
    draw.text((60, 240), hud, font=hf, fill=C_MUTED)

    back = load_card("back.png", 420)
    x = 540
    for off in (-280, 0, 280):
        paste_center(base, back.copy(), (x + off, 920))

    hint = _font(24)
    ht = "Tap the card you tracked"
    draw.text((540 - draw.textlength(ht, font=hint) / 2, 1280), ht, font=hint, fill=C_LILAC)
    return base


def shot_grimoire() -> Image.Image:
    base, draw = phone_frame()
    f = _font(44, True)
    draw.text((60, 100), "The Path", font=f, fill=C_GOLD)
    sf = _font(26)
    body = (
        "Developing ESP is often about removing the static that blocks\n"
        "intuitive perception. Grounding and chi work are the foundation.\n\n"
        "Open each part when you are ready — then play the oracle to\n"
        "practice first impressions in a low-stakes way."
    )
    y = 200
    for line in body.split("\n"):
        draw.text((60, y), line, font=sf, fill=(210, 205, 228))
        y += 44

    draw.rounded_rectangle((60, 620, 1020, 900), radius=20, outline=C_TEAL, width=2)
    draw.text((90, 650), "P1 — Grounding & the energy body", font=_font(28, True), fill=C_TEAL)
    draw.text((90, 710), "P2 — Chi / prana", font=_font(28, True), fill=C_TEAL)
    draw.text((90, 770), "P3 — ESP exercises", font=_font(28, True), fill=C_TEAL)
    draw.text((90, 830), "Session toolkit: breath, log, checklist", font=_font(24), fill=C_MUTED)
    return base


def shot_records() -> Image.Image:
    base, draw = phone_frame()
    f = _font(44, True)
    draw.text((60, 100), "Records & achievements", font=f, fill=C_GOLD)
    rows = [
        ("First round", "Finish a Queen round", True),
        ("Found her", "Win once (Queen of Spades)", True),
        ("Apprentice", "Reach a 3-win streak", True),
        ("Master", "Reach a 6-win streak", False),
    ]
    y = 220
    for title, desc, done in rows:
        draw.rounded_rectangle((50, y, 1030, y + 120), radius=18, fill=(28, 22, 45), outline=(*C_LILAC, 80), width=1)
        draw.text((90, y + 22), title, font=_font(30, True), fill=C_GOLD if done else C_MUTED)
        draw.text((90, y + 68), desc, font=_font(22), fill=C_TEAL if done else C_MUTED)
        if done:
            draw.text((930, y + 40), "Unlocked", font=_font(22), fill=C_TEAL)
        y += 140

    note = _font(22)
    nt = "All stats stored locally on your device"
    draw.text((540 - draw.textlength(nt, font=note) / 2, 1750), nt, font=note, fill=C_MUTED)
    return base


def main() -> None:
    try:
        load_card("queen_spades.png", 64)
    except FileNotFoundError as e:
        raise SystemExit(f"{e}\nTip: ensure android/app/build/outputs/bundle/release/*.aab exists, or run Gradle once.")
    print("Card art source:", describe_card_source())
    make_icon_512()
    make_feature_1024x500()
    for i, fn in enumerate([shot_title, shot_game, shot_grimoire, shot_records], start=1):
        img = fn()
        path = OUT / f"phone-screenshot-0{i}-1080x1920.png"
        img.save(path, "PNG", optimize=True)
        print("Wrote", path)


if __name__ == "__main__":
    main()
