"""
Shared sprite data + share-code decoder.

The web tracker (UltronCore/sprite-tracker) encodes a member's whole collection
into a short code: 2 bits per sprite (0=missing, 1=have, 2=mastered) in a fixed
`share_order`, packed 4 sprites per byte, base64url, no padding.

`spritebot/assets/sprites.json` is generated FROM the web app's data.js, so the
order and encoding are guaranteed identical on both sides — paste a code from
the site into /synccollection and it decodes to the exact same collection.
"""

import base64
import json
import re
from pathlib import Path

_ASSETS = Path(__file__).parent / "assets"
_DATA = json.loads((_ASSETS / "sprites.json").read_text())

SHARE_ORDER: list[str] = _DATA["share_order"]
THEMES: list[dict] = _DATA["themes"]
SPRITES: list[dict] = _DATA["sprites"]
BY_ID: dict[str, dict] = {s["id"]: s for s in SPRITES}

# theme key -> display label (basic->Normal, candy->Gummy, ...)
THEME_LABEL = {t["key"]: t["label"] for t in THEMES}

MISSING, HAVE, MASTERED = 0, 1, 2

SPRITE_IMAGE_DIR = _ASSETS / "sprites"


def released() -> list[dict]:
    return [s for s in SPRITES if not s.get("unreleased")]


def image_path(sprite_id: str) -> Path:
    return SPRITE_IMAGE_DIR / f"{sprite_id}.png"


def extract_code(text: str) -> str:
    """Accept a raw code OR a full share URL (…/?c=CODE)."""
    text = text.strip()
    if "c=" in text:
        text = text.split("c=", 1)[1]
    # strip any trailing query/hash junk
    for sep in ("&", "#", " "):
        text = text.split(sep, 1)[0]
    return text


# A valid code packs exactly len(SHARE_ORDER) statuses at 4 per byte.
_EXPECTED_BYTES = (len(SHARE_ORDER) + 3) // 4
_CODE_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def decode(code: str) -> dict[str, int]:
    """Decode a share code into {sprite_id: status}, with STRICT validation.

    Rejects anything that isn't a real tracker code: wrong charset, wrong
    decoded length, or impossible status values (only 0/1/2 are valid). This
    keeps garbage like 'abc' or '!!!!' from being stored as a collection.
    """
    code = extract_code(code)
    if not code or not _CODE_RE.match(code):
        raise ValueError("not a valid sync code")
    b64 = code.replace("-", "+").replace("_", "/")
    b64 += "=" * (-len(b64) % 4)
    try:
        raw = base64.b64decode(b64, validate=True)
    except Exception as e:  # noqa: BLE001
        raise ValueError("not a valid sync code") from e
    if len(raw) != _EXPECTED_BYTES:
        raise ValueError(
            f"sync code has the wrong length (got {len(raw)} bytes, "
            f"expected {_EXPECTED_BYTES})")

    status: dict[str, int] = {}
    for i, sid in enumerate(SHARE_ORDER):
        v = (raw[i >> 2] >> ((i % 4) * 2)) & 0b11
        if v == 3:  # 3 is never produced by the tracker (statuses are 0/1/2)
            raise ValueError("sync code contains an invalid status value")
        status[sid] = v
    return status


def encode(status: dict[str, int]) -> str:
    """Encode {sprite_id: status} back into a share code (mirrors the web)."""
    vals = [status.get(sid, 0) & 0b11 for sid in SHARE_ORDER]
    out = bytearray()
    for i in range(0, len(vals), 4):
        b = 0
        for j in range(4):
            if i + j < len(vals):
                b |= vals[i + j] << (j * 2)
        out.append(b)
    return base64.b64encode(bytes(out)).decode().replace("+", "-").replace("/", "_").rstrip("=")


def summarize(status: dict[str, int]) -> dict:
    """Counts over RELEASED sprites only (matches the site's x/41 bars)."""
    rel = released()
    total = len(rel)
    have = sum(1 for s in rel if status.get(s["id"], 0) >= HAVE)
    mastered = sum(1 for s in rel if status.get(s["id"], 0) == MASTERED)
    return {"total": total, "have": have, "mastered": mastered}
