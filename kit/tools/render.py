#!/usr/bin/env python3
"""
TokMetrics slideshow renderer.
Adds TikTok-style text, a hand-drawn red price circle and the CTA to text-free
photos, and builds the "deal screenshot" slide from a real listing screenshot.

Usage:  python3 render.py job.json
Every position is a fraction of the slide height (y) or width (x), measured from
@tikshop.uk's own slides, so layouts carry over to any resolution (1080x1920).

job.json:
{
  "fonts_dir": "<path to kit/fonts>",
  "slides": [
    {"in": "photo.png", "out": "slide-01.png", "blocks": [ ...blocks... ]},
    {"dealshot": {"shot": "listing.png", "image_box": [x0,y0,x1,y1],
                  "info_box": [x0,y0,x1,y1], "price_box": [x0,y0,x1,y1]},
     "out": "slide-02.png", "blocks": [ ... ]}
  ]
}
Block styles:
  box     TikTok highlight boxes, one per line, merged (yellow or red theme)
  plain   centred text with optional outline (stroke)
  snapbar full-width translucent black caption bar (Snapchat-style caption)
  circle  hand-drawn red loop around a box given in fractions [x0,y0,x1,y1];
          on a dealshot slide use "target": "price" to circle the live price.
"""
import json, math, os, random, re, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W0, H0 = 1080, 1920
EMOJI_RE = re.compile(
    "(?:[\\U0001F1E6-\\U0001F1FF]{2}"
    "|[\\u2190-\\u21FF\\u2300-\\u23FF\\u2460-\\u27BF\\u2900-\\u297F\\u2B00-\\u2BFF\\u3030\\u303D\\u3297\\u3299"
    "\\U0001F000-\\U0001FAFF]"
    "(?:\\uFE0F|[\\U0001F3FB-\\U0001F3FF])?"
    "(?:\\u200D[\\u2600-\\u27BF\\U0001F000-\\U0001FAFF](?:\\uFE0F)?)*\\uFE0F?)"
)

FONTS = {}

def font_path(fonts_dir, name):
    p = os.path.join(fonts_dir, name)
    if os.path.exists(p):
        return p
    for alt in ["/usr/share/fonts/truetype/noto/" + name,
                "/usr/share/fonts/truetype/liberation/" + name]:
        if os.path.exists(alt):
            return alt
    raise SystemExit("Missing font: " + name)


class Typesetter:
    def __init__(self, text_font, emoji_font, size):
        self.size = int(round(size))
        self.font = ImageFont.truetype(text_font, self.size)
        self.efont = ImageFont.truetype(emoji_font, 109) if emoji_font else None
        self.epx = int(self.size * 1.08)

    def segs(self, s):
        out, i = [], 0
        for m in EMOJI_RE.finditer(s):
            if m.start() > i:
                out.append(("t", s[i:m.start()]))
            out.append(("e", m.group()))
            i = m.end()
        if i < len(s):
            out.append(("t", s[i:]))
        return out

    def width(self, s):
        w = 0
        for k, seg in self.segs(s):
            w += self.font.getlength(seg) if k == "t" else self.epx + self.size * 0.06
        return w

    def draw(self, img, x, y, s, fill, stroke=0, stroke_fill="#000000"):
        """y = top of the line box (ascender line)."""
        d = ImageDraw.Draw(img)
        asc, desc = self.font.getmetrics()
        for k, seg in self.segs(s):
            if k == "t":
                d.text((x, y), seg, font=self.font, fill=fill,
                       stroke_width=int(round(stroke)), stroke_fill=stroke_fill)
                x += self.font.getlength(seg)
            else:
                if self.efont:
                    tmp = Image.new("RGBA", (180, 160), (0, 0, 0, 0))
                    ImageDraw.Draw(tmp).text((0, 0), seg, font=self.efont, embedded_color=True)
                    bb = tmp.getbbox()
                    if bb:
                        tmp = tmp.crop(bb)
                        tmp = tmp.resize((self.epx, max(1, int(self.epx * tmp.height / tmp.width))), Image.LANCZOS)
                        ey = int(y + asc - tmp.height * 0.92)
                        img.alpha_composite(tmp, (int(x + self.size * 0.03), ey))
                x += self.epx + self.size * 0.06


def greedy(ts, text, max_px):
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if ts.width(t) <= max_px or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def wrap(ts, text, max_px):
    out = []
    for para in text.split("\n"):
        out += greedy(ts, para, max_px)
    return out


# ---------------------------------------------------------------- styles

def render_box(img, b, F):
    """TikTok text-with-background. line_h = box height per line (fraction of H)."""
    W, H = img.size
    line_h = b["line_h"] * H
    size = line_h / 1.36
    ts = Typesetter(F[b.get("font", "box")], F["emoji"], size)
    pad = size * 0.32
    lines = b["text"].split("\n") if b.get("nowrap") else wrap(ts, b["text"], b.get("max_w", 0.8) * W - 2 * pad)
    widths = [ts.width(l) + 2 * pad for l in lines]
    total = line_h * len(lines)
    top = (b["y1"] * H - total) if b.get("anchor") == "bottom" else b["y0"] * H
    top = max(top, b.get("_min_top", 0))
    align = b.get("align", "center")
    rows = []
    for i, (l, w) in enumerate(zip(lines, widths)):
        if align == "left":
            x = b["x0"] * W + ((max(widths) - w) / 2 if b.get("center_lines") else 0)
        else:
            x = b.get("x_center", 0.5) * W - w / 2
        x = min(max(x, W * 0.02), W * 0.98 - w)
        rows.append((x, top + i * line_h, w, l))
    d = ImageDraw.Draw(img)
    r = int(size * 0.30)
    for x, y, w, l in rows:
        d.rounded_rectangle([x, y, x + w, y + line_h + 1], radius=r, fill=b["box"])
    asc, desc = ts.font.getmetrics()
    for x, y, w, l in rows:
        ty = y + (line_h - (asc + desc)) / 2 + size * 0.02
        ts.draw(img, x + pad, ty, l, b["color"])
    return (min(r_[0] for r_ in rows), top, max(r_[0] + r_[2] for r_ in rows), top + total)


def render_plain(img, b, F):
    """Centred text, optional outline. size = font size as fraction of H; pitch = line spacing."""
    W, H = img.size
    size = b["size"] * H
    ts = Typesetter(F[b.get("font", "plain")], F["emoji"], size)
    lines = b["text"].split("\n") if b.get("nowrap") else wrap(ts, b["text"], b.get("max_w", 0.75) * W)
    pitch = b.get("pitch", b["size"] * 1.35) * H
    top = max(b["y0"] * H, b.get("_min_top", 0))
    cx = b.get("x_center", 0.5) * W
    stroke = b.get("stroke", 0) * size
    widest = 0
    for i, l in enumerate(lines):
        w = ts.width(l)
        widest = max(widest, w)
        x = min(max(cx - w / 2, W * 0.03), W * 0.97 - w)
        if b.get("shadow"):
            sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ts.draw(sh, x, top + i * pitch + size * 0.04, l, (0, 0, 0, 150))
            img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(size * 0.06)))
        ts.draw(img, x, top + i * pitch, l, b.get("color", "#FFFFFF"), stroke, b.get("stroke_color", "#000000"))
    return (cx - widest / 2, top, cx + widest / 2, top + len(lines) * pitch)


def render_snapbar(img, b, F):
    """Snapchat-style caption: full-width black bar ~55% opacity, white centred text."""
    W, H = img.size
    size = b.get("size", 0.0235) * H
    ts = Typesetter(F["snap"], F["emoji"], size)
    lines = wrap(ts, b["text"], W * 0.86)
    pitch = size * 1.32
    pad = size * 0.42
    h = len(lines) * pitch + 2 * pad
    cy = b.get("y_center", 0.151) * H
    top = cy - h / 2
    bar = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(bar).rectangle([0, top, W, top + h], fill=(0, 0, 0, int(255 * b.get("alpha", 0.58))))
    img.alpha_composite(bar)
    asc, desc = ts.font.getmetrics()
    for i, l in enumerate(lines):
        w = ts.width(l)
        ts.draw(img, (W - w) / 2, top + pad + i * pitch + (pitch - asc - desc) / 2, l, "#FFFFFF")
    return (0, top, W, top + h)


def render_circle(img, b, F):
    """Hand-drawn red pen loop around box [x0,y0,x1,y1] (fractions)."""
    W, H = img.size
    x0, y0, x1, y1 = b["box"]
    cx, cy = (x0 + x1) / 2 * W, (y0 + y1) / 2 * H
    rx = (x1 - x0) / 2 * W * b.get("grow_x", 1.6)
    ry = (y1 - y0) / 2 * H * b.get("grow_y", 2.4)
    width = int(b.get("width", 0.0085) * W)
    col = b.get("color", "#E8161E")
    rnd = random.Random(b.get("seed", 7))
    layer = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # one loop and a bit, slightly wobbly, starting top-right like a pen stroke
    start = rnd.uniform(-1.2, -0.6)
    sweep = 2 * math.pi * rnd.uniform(1.08, 1.16)
    wob = [rnd.uniform(0, 2 * math.pi) for _ in range(3)]
    pts = []
    n = 220
    for i in range(n + 1):
        t = start - sweep * i / n
        k = 1 + 0.035 * math.sin(3 * t + wob[0]) + 0.02 * math.sin(5 * t + wob[1])
        drift = 1 + 0.07 * i / n            # second pass slightly wider, like a real pen loop
        tilt = math.radians(rnd.uniform(-1, 1) if i == 0 else 0) + math.radians(-4)
        ex = rx * k * drift * math.cos(t)
        ey = ry * k * drift * math.sin(t)
        px = cx + ex * math.cos(tilt) - ey * math.sin(tilt)
        py = cy + ex * math.sin(tilt) + ey * math.cos(tilt)
        pts.append((px * 2, py * 2))
    for i in range(len(pts) - 1):
        taper = 0.55 + 0.45 * math.sin(math.pi * i / len(pts))
        d.line([pts[i], pts[i + 1]], fill=col, width=max(2, int(width * 2 * taper)), joint="curve")
        d.ellipse([pts[i][0] - width * taper, pts[i][1] - width * taper,
                   pts[i][0] + width * taper, pts[i][1] + width * taper], fill=col)
    layer = layer.resize((W, H), Image.LANCZOS)
    img.alpha_composite(layer)
    return None


# ---------------------------------------------------------------- deal screenshot

def build_dealshot(spec, size=(W0, H0)):
    """Real listing screenshot -> 9:16 slide: product image on top, the real
    price / title / sold block underneath. Returns (image, price_box_fraction)."""
    W, H = size
    shot = Image.open(spec["shot"]).convert("RGBA")
    if spec.get("region"):
        # boxes are screen coordinates from dealshot.js; convert to screenshot pixels
        rx0, ry0, rx1, ry1 = spec["region"]
        k = shot.width / float(rx1 - rx0)
        conv = lambda b: [int((b[0] - rx0) * k), int((b[1] - ry0) * k), int((b[2] - rx0) * k), int((b[3] - ry0) * k)]
        spec = dict(spec, image_box=conv(spec["image_box"]), info_box=conv(spec["info_box"]),
                    price_box=conv(spec["price_box"]), region=None)
    slide = Image.new("RGBA", (W, H), spec.get("bg", "#FFFFFF"))
    # product image
    ib = spec["image_box"]
    im = shot.crop(tuple(ib))
    iw = W
    ih = int(im.height * iw / im.width)
    max_ih = int(H * spec.get("image_frac", 0.56))
    if ih > max_ih:
        ih = max_ih
        iw = int(im.width * ih / im.height)
    im = im.resize((iw, ih), Image.LANCZOS)
    top = int(H * spec.get("top", 0.045))
    slide.alpha_composite(im, ((W - iw) // 2, top))
    # info block (price row first)
    nb = spec["info_box"]
    info = shot.crop(tuple(nb))
    scale = (W * 0.94) / info.width
    info_r = info.resize((int(info.width * scale), int(info.height * scale)), Image.LANCZOS)
    iy = top + ih + int(H * 0.02)
    ix = int(W * 0.03)
    room = H - iy
    if info_r.height > room:
        info_r = info_r.crop((0, 0, info_r.width, room))
    slide.alpha_composite(info_r, (ix, iy))
    pb = spec["price_box"]
    px0 = ix + (pb[0] - nb[0]) * scale
    py0 = iy + (pb[1] - nb[1]) * scale
    px1 = ix + (pb[2] - nb[0]) * scale
    py1 = iy + (pb[3] - nb[1]) * scale
    return slide, [px0 / W, py0 / H, px1 / W, py1 / H]


# ---------------------------------------------------------------- main

def main(job_path):
    job = json.load(open(job_path))
    base = os.path.dirname(os.path.abspath(job_path))
    fd = job.get("fonts_dir") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")
    F = {
        "box": font_path(fd, "TikTokSans_24pt-Medium.ttf"),
        "plain": font_path(fd, "TikTokSans_24pt-Medium.ttf"),
        "semibold": font_path(fd, "TikTokSans_24pt-SemiBold.ttf"),
        "snap": font_path(fd, "LiberationSans-Regular.ttf"),
        "emoji": font_path(fd, "NotoColorEmoji.ttf"),
    }
    P = lambda p: p if os.path.isabs(p) else os.path.join(base, p)
    for s in job["slides"]:
        price_box = None
        if s.get("dealshot"):
            ds = dict(s["dealshot"])
            ds["shot"] = P(ds["shot"])
            img, price_box = build_dealshot(ds)
        else:
            img = Image.open(P(s["in"])).convert("RGBA")
            # cover-crop to 9:16
            r = img.width / img.height
            if abs(r - 9 / 16) > 0.01:
                if r > 9 / 16:
                    nw = int(img.height * 9 / 16)
                    img = img.crop(((img.width - nw) // 2, 0, (img.width - nw) // 2 + nw, img.height))
                else:
                    nh = int(img.width * 16 / 9)
                    img = img.crop((0, (img.height - nh) // 2, img.width, (img.height - nh) // 2 + nh))
            img = img.resize((W0, H0), Image.LANCZOS)
        placed = []
        for b in s.get("blocks", []):
            st = b["style"]
            if st == "circle" and b.get("target") == "price":
                if not price_box:
                    continue
                b = dict(b, box=price_box)
            # push a block down if it would overlap one already placed above it
            if st in ("box", "plain") and b.get("anchor") != "bottom":
                y = b["y0"] * img.height
                for (rx0, ry0, rx1, ry1) in placed:
                    if ry0 <= y < ry1 + img.height * 0.004:
                        b["_min_top"] = max(b.get("_min_top", 0), ry1 + img.height * 0.008)
            fn = {"box": render_box, "plain": render_plain, "snapbar": render_snapbar, "circle": render_circle}[st]
            rect = fn(img, b, F)
            if rect and st != "snapbar":
                placed.append(rect)
        out = P(s["out"])
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        img.convert("RGB").save(out, "PNG")
        print("wrote", out, "price_box" if price_box else "", price_box or "")


if __name__ == "__main__":
    main(sys.argv[1])
