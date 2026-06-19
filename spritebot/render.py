"""
Server-side image renderer (Pillow) — produces the same "My Collection" (green)
and "Looking For" (red) cards the web tracker exports, so the bot can post them
directly in Discord instead of asking members to screenshot the site.
"""

import io

from PIL import Image, ImageDraw, ImageFont

from . import sprites

RARITY_HEX = {
    "rare": (46, 164, 255), "epic": (177, 92, 255), "legendary": (255, 138, 42),
    "mythic": (255, 210, 58), "special": (40, 224, 200),
}


def _font(size, bold=True):
    # Try a few common system fonts; fall back to Pillow's default bitmap font.
    for name in ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
                 "Arial Bold.ttf", "Arial.ttf", "Helvetica.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def _rounded(draw, box, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _text_center(draw, cx, y, text, font, fill):
    w = draw.textlength(text, font=font)
    draw.text((cx - w / 2, y), text, font=font, fill=fill)


def _fit(draw, text, font, max_w):
    if draw.textlength(text, font=font) <= max_w:
        return text
    while len(text) > 3 and draw.textlength(text + "…", font=font) > max_w:
        text = text[:-1]
    return text + "…"


def render_collection(status: dict, display_name: str, mode: str = "collection") -> bytes:
    """mode: 'collection' (have+mastered, green) or 'missing' (red)."""
    collection = mode == "collection"
    rel = sprites.released()
    if collection:
        items = [s for s in rel if status.get(s["id"], 0) >= 1]
    else:
        items = [s for s in rel if status.get(s["id"], 0) == 0]
    if not items:
        items = []

    cols = max(1, min(6, len(items) or 1))
    rows = max(1, (len(items) + cols - 1) // cols)
    pad, cardW, cardH, gap, headerH, footerH = 22, 168, 196, 12, 60, 38
    W = pad * 2 + cols * cardW + (cols - 1) * gap
    H = headerH + pad + rows * cardH + (rows - 1) * gap + pad + footerH

    accent = (43, 208, 122) if collection else (255, 77, 94)
    img = Image.new("RGBA", (W, H), (11, 14, 19, 255))
    d = ImageDraw.Draw(img)

    f_title = _font(24)
    f_counts = _font(15)
    f_badge = _font(12)
    f_name = _font(15)
    f_foot = _font(15)

    # outer border + header
    d.rectangle([3, 3, W - 4, H - 4], outline=accent, width=6)
    d.rectangle([6, 6, W - 7, 6 + headerH], fill=(16, 20, 29, 255))
    title = (f"{display_name.upper()}: MY SPRITES" if collection
             else f"{display_name.upper()}: LOOKING FOR THESE")
    d.text((pad, 6 + headerH / 2 - 13), _fit(d, title, f_title, W - pad * 2 - 220),
           font=f_title, fill=accent)
    s = sprites.summarize(status)
    counts = f"COLLECTION {s['have']}/{s['total']}   MASTERY {s['mastered']}/{s['total']}"
    cw = d.textlength(counts, font=f_counts)
    d.text((W - pad - cw, 6 + headerH / 2 - 8), counts, font=f_counts, fill=(232, 237, 245, 255))

    for i, sp in enumerate(items):
        cx = pad + (i % cols) * (cardW + gap)
        cy = headerH + pad + (i // cols) * (cardH + gap)
        v = status.get(sp["id"], 0)
        border = (255, 207, 58) if v == 2 else (43, 208, 122) if v == 1 else (57, 65, 79)
        _rounded(d, [cx, cy, cx + cardW, cy + cardH], 12, fill=(22, 28, 40, 255))
        _rounded(d, [cx, cy, cx + cardW, cy + cardH], 12, outline=border, width=3)

        # art
        try:
            art = Image.open(sprites.image_path(sp["id"])).convert("RGBA")
            box = cardW - 28
            art.thumbnail((box, box), Image.LANCZOS)
            if not collection:  # dim wishlist art slightly
                alpha = art.split()[3].point(lambda p: int(p * 0.92))
                art.putalpha(alpha)
            ox = cx + (cardW - art.width) // 2
            img.paste(art, (ox, cy + 14), art)
        except Exception:  # noqa: BLE001
            pass

        # status badge
        if collection:
            label = "MASTERED" if v == 2 else "COLLECTED"
            bg = (255, 207, 58) if v == 2 else (43, 208, 122)
            _badge(d, cx + 8, cy + 8, label, f_badge, bg, (10, 13, 18))

        # rarity tag
        rc = RARITY_HEX.get(sp["rarity"].lower(), (40, 224, 200))
        _badge(d, cx + 8, cy + cardH - 52, sp["rarity"].upper(), f_badge, rc, (6, 18, 26))

        # name
        _text_center(d, cx + cardW / 2, cy + cardH - 22,
                     _fit(d, sp["name"].upper(), f_name, cardW - 16), f_name, (232, 237, 245, 255))

    _text_center(d, W / 2, H - footerH / 2 - 8, "Sprite Trade Stop · /tracker", f_foot,
                 (174, 184, 200, 255))

    out = io.BytesIO()
    img.convert("RGB").save(out, format="PNG")
    out.seek(0)
    return out.getvalue()


def _badge(d, x, y, text, font, bg, fg):
    w = d.textlength(text, font=font) + 14
    _rounded(d, [x, y, x + w, y + 18], 4, fill=bg)
    d.text((x + 7, y + 2), text, font=font, fill=fg)
