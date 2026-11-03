"""Render completely original, license-independent Enna meme cards.

No third-party images, fonts, fictional customer photos or celebrity memes.
This only makes an image asset. It never posts to Threads.
"""
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1080, 1350
BG = "#F9F3E9"
INK = "#312A24"
DARK = "#385D39"
LIGHT = "#DBE9CA"


def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if Path(path).is_file():
            return ImageFont.truetype(path, size=size)
    raise RuntimeError("Vietnamese-capable system font unavailable")


def wrap(draw, body, use_font, max_width):
    lines = []
    for paragraph in str(body).split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        line = ""
        for word in paragraph.split():
            attempt = word if not line else line + " " + word
            if line and draw.textbbox((0, 0), attempt, font=use_font)[2] > max_width:
                lines.append(line)
                line = word
            else:
                line = attempt
        if line:
            lines.append(line)
    return lines


def make_card(headline, punchline, *, series="ĐỒ HAY ĐI LÀM"):
    """Return PNG bytes for a reproducible original typography-only card."""
    if any(not isinstance(x, str) for x in (headline, punchline, series)):
        raise ValueError("Text fields must be strings")
    if not (12 <= len(headline) <= 120 and 12 <= len(punchline) <= 180):
        raise ValueError("Unexpected meme text length")
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle([55, 56, 1025, 1294], radius=58, fill="#FFFDF7", outline="#E7D9C4", width=4)
    draw.rounded_rectangle([100, 106, 980, 185], radius=35, fill=LIGHT)
    draw.text((145, 129), series, font=font(29,True), fill=DARK)
    draw.ellipse((790, 222, 967, 399), fill="#E6F0D6")
    draw.ellipse((828, 255, 864, 291), fill=DARK)
    draw.ellipse((900, 255, 936, 291), fill=DARK)
    draw.arc((825, 276, 942, 359), start=10, end=170, fill=DARK, width=7)
    headline_font = font(67, True)
    lines = wrap(draw, headline, headline_font, 820)
    if len(lines) > 5:
        headline_font = font(55, True)
        lines = wrap(draw, headline, headline_font, 820)
    y = 455
    for line in lines:
        draw.text((125, y), line, font=headline_font, fill=INK)
        y += 91 if headline_font.size > 60 else 76
    line_y = max(880, y + 52)
    draw.rounded_rectangle((105, line_y-35, 975, line_y + 245), radius=35, fill="#EBE4F6")
    punch_font = font(41, True)
    replies = wrap(draw, punchline, punch_font, 800)
    py = line_y
    for line in replies[:4]:
        draw.text((145, py), line, font=punch_font, fill="#4B3673")
        py += 58
    draw.text((125, 1220), "ENNA  /  MẸO VUI DÂN CÔNG SỞ", font=font(23, True), fill="#8A786A")
    out = BytesIO()
    image.save(out, format="PNG", optimize=True)
    result = out.getvalue()
    if len(result) > 5 * 1024 * 1024:
        raise ValueError("PNG exceeds safe upload cap")
    return result
