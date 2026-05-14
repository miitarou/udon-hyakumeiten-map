#!/usr/bin/env python3
"""Generate the social preview image for the site."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WIDTH = 1200
HEIGHT = 630


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc" if bold else "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for path in candidates:
        if not path:
            continue
        try:
            if Path(path).exists():
                return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_background() -> Image.Image:
    bg = Image.new("RGB", (WIDTH, HEIGHT), "#12151e")
    pixels = bg.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            tx = x / (WIDTH - 1)
            ty = y / (HEIGHT - 1)
            r = int(17 + 25 * tx + 8 * ty)
            g = int(20 + 20 * tx + 14 * ty)
            b = int(29 + 12 * (1 - tx) + 14 * ty)
            pixels[x, y] = (r, g, b)

    accents = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(accents)
    draw.ellipse((700, -180, 1320, 430), fill=(214, 174, 88, 30))
    draw.ellipse((-180, 350, 520, 860), fill=(61, 107, 140, 34))
    accents = accents.filter(ImageFilter.GaussianBlur(70))
    return Image.alpha_composite(bg.convert("RGBA"), accents)


def main() -> None:
    image = make_background()
    draw = ImageDraw.Draw(image)

    icon = Image.open(ROOT / "icon.png").convert("RGBA").resize((330, 330), Image.LANCZOS)
    shadow = Image.new("RGBA", (366, 366), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((18, 18, 348, 348), radius=68, fill=(0, 0, 0, 95))
    shadow = shadow.filter(ImageFilter.GaussianBlur(16))
    image.alpha_composite(shadow, (62, 132))
    image.alpha_composite(icon, (80, 145))

    white = (247, 248, 250, 255)
    muted = (218, 222, 230, 255)
    gold = (218, 176, 83, 255)
    ink = (8, 12, 20, 255)
    x0 = 500

    draw.text((x0, 118), "うどん・そば百名店 MAP", font=load_font(56, True), fill=white)
    draw.text((x0, 220), "2017-2025 非公式参考ツール", font=load_font(38, True), fill=muted)

    badge_text = "地図・検索・訪問状況"
    badge_font = load_font(31, True)
    bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    badge_width = (bbox[2] - bbox[0]) + 92
    badge_x, badge_y = x0, 316
    draw.rounded_rectangle((badge_x, badge_y, badge_x + badge_width, badge_y + 58), radius=18, fill=gold)
    draw.text((badge_x + 46, badge_y + 12), badge_text, font=badge_font, fill=ink)

    body_font = load_font(30, True)
    draw.text((x0, 430), "公開情報をもとに個人が整理した、", font=body_font, fill=muted)
    draw.text((x0, 482), "うどん・そば名店探索マップ。", font=body_font, fill=muted)
    draw.text((x0, 544), "年度・地域・特徴・現在地から、", font=load_font(27, True), fill=muted)
    draw.text((x0, 586), "次に行きたいお店を探せます", font=load_font(27, True), fill=muted)

    image.save(ROOT / "og-image.png")


if __name__ == "__main__":
    main()
