#!/usr/bin/env python3
"""
Cyber Range Labs — Social Media Post Generator
Place this file at: /root/Desktop/crl_poster.py

Usage:
    python3 /root/Desktop/crl_poster.py '<json_string>'

JSON input fields:
    template    : 1 | 2 | 3
    headline    : str  (use \\n for explicit line breaks, or auto-wrapped)
    badge       : str  (e.g. "CRITICAL CVE", "SECURITY UPDATE", "GUIDE")
    pills       : list[str]  (e.g. ["CVE-2024-1234", "CVSS: 9.8"])
    body        : str  (template 2 — short 1-2 sentence body text)
    description : str  (template 3 — 2-3 sentence description)
    image_url   : str  (optional — article image, composited to fill space)
    output_path : str  (default: /root/Desktop/crl_output.png)

Output:
    Saves a 1080x1080 PNG to output_path.
    Prints the output path to stdout on success.
    Exits with code 1 and prints error to stderr on failure.
"""

import sys
import json
import os
import io
import urllib.request
import urllib.error
import ssl
import traceback

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# ── Constants ──────────────────────────────────────────────────────────────────
SIZE        = 1080
PAD         = 68
FOOTER_H    = 96
STRIPE_H    = 28

# ── Palette ────────────────────────────────────────────────────────────────────
PURPLE       = (108,  43, 180)
PURPLE_DARK  = ( 55,  15, 110)
PURPLE_MID   = ( 80,  28, 150)
RED          = (214,  48,  84)
WHITE        = (255, 255, 255)
OFF_WHITE    = (251, 250, 254)
DARK         = ( 15,  12,  35)
BODY_COL     = ( 85,  78, 110)
RULE_COL     = (215, 205, 238)
C_CYBER      = ( 22,  30,  75)
C_RANGE      = (108,  43, 180)
C_LABS       = (150, 140, 172)

# ── Font loader ────────────────────────────────────────────────────────────────
INTER_PATH = os.path.expanduser(
    "~/Desktop/Inter Hinted for Windows/Desktop/Inter-{}.ttf"
)
_FALLBACK = (
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
)

def load_font(size, weight="Regular"):
    path = INTER_PATH.format(weight)
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    for fb in _FALLBACK:
        if os.path.exists(fb):
            try:
                return ImageFont.truetype(fb, size)
            except Exception:
                pass
    return ImageFont.load_default()

# ── Measurement helpers ────────────────────────────────────────────────────────
def text_w(draw, text, font):
    return int(draw.textlength(text, font=font))

def text_h(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[3] - b[1]

def measure_pill(draw, text, font, px=24, py=13):
    return (int(draw.textlength(text, font=font) + px * 2),
            int(text_h(draw, text, font) + py * 2))

def wrap_text(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if text_w(draw, test, font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

# ── Drawing helpers ────────────────────────────────────────────────────────────
def rr(draw, box, r, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)

def draw_pill(draw, text, x, y, bg, fg, font, px=24, py=13):
    w, h = measure_pill(draw, text, font, px, py)
    rr(draw, (x, y, x + w, y + h), r=h // 2, fill=bg)
    tb = draw.textbbox((0, 0), text, font=font)
    draw.text((x + px, y + py - tb[1]), text, font=font, fill=fg)
    return w, h

def draw_outline_pill(draw, text, x, y, fg, border, font, px=20, py=11):
    w, h = measure_pill(draw, text, font, px, py)
    rr(draw, (x, y, x + w, y + h), r=h // 2, fill=None, outline=border, width=2)
    tb = draw.textbbox((0, 0), text, font=font)
    draw.text((x + px, y + py - tb[1]), text, font=font, fill=fg)
    return w, h

def draw_brand(draw, x, y, size=36, on_dark=False):
    parts = [
        ("Cyber ", WHITE        if on_dark else C_CYBER),
        ("Range ", (215, 190, 255) if on_dark else C_RANGE),
        ("Labs",   (195, 175, 235) if on_dark else C_LABS),
    ]
    font = load_font(size, "SemiBold")
    cx = x
    for t, c in parts:
        draw.text((cx, y), t, font=font, fill=c)
        cx += text_w(draw, t, font)

def draw_logo(draw, x, y, sz=72, on_dark=False):
    bg  = (75, 48, 138) if on_dark else (232, 224, 252)
    bdr = (155, 128, 208) if on_dark else (198, 178, 230)
    fg  = WHITE if on_dark else PURPLE
    rr(draw, (x, y, x + sz, y + sz), r=12, fill=bg, outline=bdr, width=2)
    font = load_font(int(sz * 0.30), "ExtraBold")
    lw   = text_w(draw, "CRL", font)
    lh   = text_h(draw, "CRL", font)
    draw.text((x + (sz - lw) // 2, y + (sz - lh) // 2), "CRL", font=font, fill=fg)

def draw_footer(draw, on_dark=False):
    fy = SIZE - FOOTER_H
    lc = (190, 165, 225) if on_dark else RULE_COL
    draw.line([(PAD, fy), (SIZE - PAD, fy)], fill=lc, width=1)
    draw_brand(draw, PAD, fy + 16, on_dark=on_dark)
    draw_logo(draw, SIZE - PAD - 72, fy + 4, on_dark=on_dark)

def vcenter(content_h, top=0, bottom=None):
    bottom = bottom or (SIZE - FOOTER_H)
    available = bottom - top
    return top + max(0, (available - content_h) // 2)

# ── Image download & prep ──────────────────────────────────────────────────────
def fetch_image(url, timeout=8):
    """Download image from URL, return PIL Image or None on failure."""
    if not url:
        return None
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; CRLBot/1.0)"}
        )
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            data = resp.read()
        img = Image.open(io.BytesIO(data)).convert("RGB")
        return img
    except Exception:
        return None

def crop_center(img, w, h):
    """Crop image to w×h from center."""
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    x = (nw - w) // 2
    y = (nh - h) // 2
    return img.crop((x, y, x + w, y + h))

def darken(img, factor=0.45):
    return ImageEnhance.Brightness(img).enhance(factor)

def tint_purple(img):
    """Overlay semi-transparent purple on image."""
    overlay = Image.new("RGBA", img.size, (*PURPLE_MID, 160))
    base = img.convert("RGBA")
    merged = Image.alpha_composite(base, overlay)
    return merged.convert("RGB")

# ── Purple gradient background ─────────────────────────────────────────────────
def make_gradient(w=SIZE, h=SIZE):
    img  = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for i in range(h):
        t = i / h
        r = int(PURPLE[0] * (1 - t) + PURPLE_DARK[0] * t)
        g = int(PURPLE[1] * (1 - t) + PURPLE_DARK[1] * t)
        b = int(PURPLE[2] * (1 - t) + PURPLE_DARK[2] * t)
        draw.line([(0, i), (w, i)], fill=(r, g, b))
    return img

# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATE 1 — CRITICAL ALERT
# purple gradient bg • red badge • white headline • outline pills
# if image_url: composited as a blurred/darkened right-side panel
# ══════════════════════════════════════════════════════════════════════════════
def render_t1(data):
    headline  = data.get("headline", "VULNERABILITY\nDETECTED")
    badge     = data.get("badge",    "CRITICAL CVE")
    pills     = data.get("pills",    [])
    image_url = data.get("image_url", "")

    img  = make_gradient()
    draw = ImageDraw.Draw(img)

    # ── Optional article image as right-panel ─────────────────────────────────
    art = fetch_image(image_url)
    if art:
        panel_w = int(SIZE * 0.38)
        panel_h = SIZE - FOOTER_H - STRIPE_H
        art_crop = crop_center(art, panel_w, panel_h)
        art_crop = darken(art_crop, 0.5)
        art_crop = tint_purple(art_crop)
        # blend into right side with a soft left edge
        art_rgba = art_crop.convert("RGBA")
        mask = Image.new("L", (panel_w, panel_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        fade = 80  # px fade width
        for px_i in range(fade):
            alpha = int(220 * (px_i / fade))
            mask_draw.line([(px_i, 0), (px_i, panel_h)], fill=alpha)
        mask_draw.rectangle([fade, 0, panel_w, panel_h], fill=220)
        art_rgba.putalpha(mask)
        img.paste(art_crop, (SIZE - panel_w, 0), mask=mask)
        draw = ImageDraw.Draw(img)  # refresh after paste

    # ── Fonts ─────────────────────────────────────────────────────────────────
    bf  = load_font(30, "Bold")
    hf  = load_font(96, "ExtraBold")
    pf  = load_font(26, "SemiBold")

    # ── Measure content block ─────────────────────────────────────────────────
    bw, bh = measure_pill(draw, badge, bf, 28, 14)
    h_lines = headline.split("\n")
    h_lh    = max(text_h(draw, l, hf) for l in h_lines) + 8
    head_h  = h_lh * len(h_lines)
    ph      = measure_pill(draw, pills[0], pf, 22, 11)[1] if pills else 0
    content_h = bh + 54 + head_h + (50 + ph if pills else 0)
    y = vcenter(content_h, top=PAD, bottom=SIZE - FOOTER_H - 20)

    # ── Badge ─────────────────────────────────────────────────────────────────
    draw_pill(draw, badge, PAD, y, RED, WHITE, bf, px=28, py=14)
    y += bh + 54

    # ── Headline ──────────────────────────────────────────────────────────────
    max_head_w = int(SIZE * 0.58) - PAD if art else SIZE - PAD * 2
    for line in h_lines:
        # auto-wrap if line too wide
        sub = wrap_text(draw, line, hf, max_head_w)
        for sl in sub:
            draw.text((PAD, y), sl, font=hf, fill=WHITE)
            y += h_lh
    y += 50

    # ── Outline pills ─────────────────────────────────────────────────────────
    if pills:
        cx = PAD
        for p in pills[:3]:
            pw, _ = draw_outline_pill(draw, p, cx, y, WHITE, (200, 178, 240), pf, 22, 11)
            cx += pw + 16

    draw_footer(draw, on_dark=True)
    return img


# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATE 2 — NEWS / UPDATE
# white bg • purple border • pill badge • headline • body • tag pills
# if image_url: right-side image panel (40% width)
# ══════════════════════════════════════════════════════════════════════════════
def render_t2(data):
    headline  = data.get("headline", "SECURITY UPDATE")
    badge     = data.get("badge",    "SECURITY UPDATE")
    body      = data.get("body",     "")
    pills     = data.get("pills",    [])
    image_url = data.get("image_url", "")

    img  = Image.new("RGB", (SIZE, SIZE), OFF_WHITE)
    draw = ImageDraw.Draw(img)

    # ── Optional article image — right panel ──────────────────────────────────
    has_image = False
    panel_w   = 0
    art = fetch_image(image_url)
    if art:
        has_image = True
        panel_w   = int(SIZE * 0.40)
        inner_h   = SIZE - FOOTER_H - 30
        art_crop  = crop_center(art, panel_w - 14, inner_h - 14)
        # paste with rounded mask
        mask  = Image.new("L", art_crop.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [0, 0, art_crop.width, art_crop.height], radius=12, fill=255
        )
        base = Image.new("RGB", (SIZE, SIZE), OFF_WHITE)
        base.paste(art_crop, (SIZE - panel_w + 7, 15), mask=mask)
        img.paste(base, (0, 0))
        draw = ImageDraw.Draw(img)

    # Border
    rr(draw, (14, 14, SIZE - 14, SIZE - 14), r=22, fill=None, outline=PURPLE, width=5)

    # ── Fonts ─────────────────────────────────────────────────────────────────
    bf  = load_font(27, "Bold")
    hf  = load_font(88, "ExtraBold")
    df  = load_font(32, "Regular")
    tf  = load_font(23, "SemiBold")

    max_w = (SIZE - panel_w - PAD * 2 - 20) if has_image else (SIZE - PAD * 2)

    # ── Measure ───────────────────────────────────────────────────────────────
    bw, bh  = measure_pill(draw, badge, bf, 26, 13)
    h_lines = headline.split("\n")
    # auto-wrap long lines
    h_lines_all = []
    for l in h_lines:
        h_lines_all.extend(wrap_text(draw, l, hf, max_w))
    h_lh    = max(text_h(draw, l, hf) for l in h_lines_all) + 10
    head_h  = h_lh * len(h_lines_all)
    body_lines = wrap_text(draw, body, df, max_w) if body else []
    b_lh    = (text_h(draw, body_lines[0], df) + 10) if body_lines else 0
    body_h  = b_lh * len(body_lines)
    ph      = (measure_pill(draw, pills[0], tf, 18, 10)[1] + 32 + 2) if pills else 0
    content_h = bh + 52 + head_h + (36 + body_h if body_h else 0) + ph
    y = vcenter(content_h, top=PAD + 8)

    # ── Badge ─────────────────────────────────────────────────────────────────
    draw_pill(draw, badge, PAD, y, PURPLE, WHITE, bf, px=26, py=13)
    y += bh + 52

    # ── Headline ──────────────────────────────────────────────────────────────
    for line in h_lines_all:
        draw.text((PAD, y), line, font=hf, fill=DARK)
        y += h_lh
    y += 36

    # ── Body ──────────────────────────────────────────────────────────────────
    if body_lines:
        for line in body_lines:
            draw.text((PAD, y), line, font=df, fill=BODY_COL)
            y += b_lh
        y += 30

    # ── Rule ──────────────────────────────────────────────────────────────────
    if pills:
        draw.line([(PAD, y), (SIZE - PAD, y)], fill=RULE_COL, width=2)
        y += 30
        cx = PAD
        for p in pills[:4]:
            pw, _ = draw_outline_pill(draw, p, cx, y, PURPLE, (175, 145, 215), tf, 18, 10)
            cx += pw + 14

    draw_footer(draw)
    return img


# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATE 3 — EDUCATIONAL / GUIDE
# white bg • top+bottom stripe • icon • GUIDE pill • headline • description
# if image_url: composited as a full-width band between icon and headline
# ══════════════════════════════════════════════════════════════════════════════
def render_t3(data):
    headline    = data.get("headline",    "SECURITY GUIDE")
    description = data.get("description", "")
    badge       = data.get("badge",       "GUIDE")
    image_url   = data.get("image_url",   "")

    img  = Image.new("RGB", (SIZE, SIZE), OFF_WHITE)
    draw = ImageDraw.Draw(img)

    # Stripes
    draw.rectangle([0, 0,      SIZE, 16],           fill=PURPLE)
    draw.rectangle([0, 16,     SIZE, STRIPE_H],      fill=RED)
    draw.rectangle([0, SIZE - STRIPE_H, SIZE, SIZE - 16], fill=RED)
    draw.rectangle([0, SIZE - 16,       SIZE, SIZE], fill=PURPLE)

    # ── Fonts ─────────────────────────────────────────────────────────────────
    gf  = load_font(27, "Bold")
    hf  = load_font(80, "ExtraBold")
    df  = load_font(30, "Regular")
    MAX_W = SIZE - PAD * 2 - 60

    # ── Article image band ────────────────────────────────────────────────────
    art = fetch_image(image_url)
    img_band_h = 0
    if art:
        img_band_h = 220
        band = crop_center(art, SIZE - PAD * 2, img_band_h)
        mask = Image.new("L", band.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [0, 0, band.width, band.height], radius=14, fill=255
        )
        img.paste(band, (PAD, STRIPE_H + 14), mask=mask)
        draw = ImageDraw.Draw(img)

    # Stripes re-drawn on top to cover any image bleed
    draw.rectangle([0, 0,      SIZE, 16],           fill=PURPLE)
    draw.rectangle([0, 16,     SIZE, STRIPE_H],      fill=RED)
    draw.rectangle([0, SIZE - STRIPE_H, SIZE, SIZE - 16], fill=RED)
    draw.rectangle([0, SIZE - 16,       SIZE, SIZE], fill=PURPLE)

    # ── Shield icon ───────────────────────────────────────────────────────────
    ICON_SZ = 100
    icon_top = STRIPE_H + 14 + img_band_h + (14 if img_band_h else 0)

    # ── Measure content below icon ────────────────────────────────────────────
    gpw, gph  = measure_pill(draw, f"  {badge}  ", gf, 6, 13)
    h_lines   = headline.split("\n")
    h_lines_w = []
    for l in h_lines:
        h_lines_w.extend(wrap_text(draw, l, hf, MAX_W))
    h_lh      = max(text_h(draw, l, hf) for l in h_lines_w) + 8
    head_h    = h_lh * len(h_lines_w)
    desc_lines = wrap_text(draw, description, df, MAX_W) if description else []
    d_lh       = (text_h(draw, desc_lines[0], df) + 8) if desc_lines else 0
    desc_h     = d_lh * len(desc_lines)
    below_icon = gph + 32 + head_h + (24 + desc_h if desc_h else 0)
    total_h    = ICON_SZ + 20 + below_icon

    content_start = vcenter(
        total_h,
        top=icon_top,
        bottom=SIZE - FOOTER_H - 20
    )
    y = content_start

    # Draw icon
    icx = (SIZE - ICON_SZ) // 2
    rr(draw, (icx, y, icx + ICON_SZ, y + ICON_SZ), r=16,
       fill=(232, 224, 252), outline=(198, 178, 232), width=2)
    sx, sy = icx + ICON_SZ // 2, y + ICON_SZ // 2
    draw.polygon([
        (sx,     sy - 30), (sx + 24, sy - 17),
        (sx + 24, sy +  7), (sx,     sy + 28),
        (sx - 24, sy +  7), (sx - 24, sy - 17),
    ], fill=PURPLE)
    draw.text((sx - 15, sy - 12), "</>", font=load_font(21, "Bold"), fill=WHITE)
    y += ICON_SZ + 20

    # GUIDE pill centred
    draw_pill(draw, f"  {badge}  ", (SIZE - gpw) // 2, y, PURPLE, WHITE, gf, px=6, py=13)
    y += gph + 32

    # Headline centred
    for line in h_lines_w:
        lw = text_w(draw, line, hf)
        draw.text(((SIZE - lw) // 2, y), line, font=hf, fill=DARK)
        y += h_lh
    y += 24

    # Description centred
    for line in desc_lines:
        lw = text_w(draw, line, df)
        draw.text(((SIZE - lw) // 2, y), line, font=df, fill=BODY_COL)
        y += d_lh

    draw_footer(draw)
    return img


# ── Entry point ────────────────────────────────────────────────────────────────
RENDERERS = {1: render_t1, 2: render_t2, 3: render_t3}

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 crl_poster.py '<json>'", file=sys.stderr)
        sys.exit(1)

    try:
        arg = sys.argv[1]
        # Accept base64-encoded JSON (prefix "base64:") to avoid shell-quoting issues
        # when called from n8n's Execute Command node.
        if arg.startswith('base64:'):
            import base64 as _b64
            data = json.loads(_b64.b64decode(arg[7:]).decode('utf-8'))
        else:
            data = json.loads(arg)
    except Exception as e:
        print(f"Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    template    = int(data.get("template", 1))
    output_path = data.get("output_path", "/root/Desktop/crl_output.png")

    if template not in RENDERERS:
        print(f"Unknown template {template}, defaulting to 1", file=sys.stderr)
        template = 1

    try:
        img = RENDERERS[template](data)
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        img.save(output_path, "PNG", optimize=False)
        # Print base64-encoded PNG to stdout for n8n Execute Command integration.
        # The Execute Command node captures stdout and passes it to the next Code node,
        # eliminating the need for fs.readFileSync (which is blocked in n8n's sandbox).
        import base64 as _b64, io as _io
        buf = _io.BytesIO()
        img.save(buf, "PNG", optimize=False)
        buf.seek(0)
        print(_b64.b64encode(buf.read()).decode('ascii'))
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        print(f"Failed to generate image: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
