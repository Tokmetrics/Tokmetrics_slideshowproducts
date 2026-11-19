#!/usr/bin/env python3
"""
Turn a short slideshow plan into a render.py job.

Usage: python3 build_job.py plan.json job.json
plan.json:
{
  "format": "DEAL-FIRST" | "SNAP-CAPTION",
  "theme": "yellow" | "red",              (optional: format default)
  "photo": "/abs/path/product-photo.png", (ChatGPT photo, no text)
  "dealshot": {"shot": "/abs/listing.png", "image_box": [...], "info_box": [...], "price_box": [...]},
  "text": {"deal_hook": "...", "deal_sub": "...", "product_main": "...", ... , "cta": "Discount link\\n⬇️⬇️"},
  "out_dir": "/abs/output/folder",
  "fonts_dir": "/abs/kit/fonts"
}
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main(plan_path, job_path):
    plan = json.load(open(plan_path))
    fm = json.load(open(plan.get("formats") or os.path.join(HERE, "..", "formats.json")))
    f = fm["formats"][plan["format"]]
    theme = fm["themes"][plan.get("theme") or f["default_theme"]]
    slides = []
    for key in ("slide1", "slide2", "slide3"):
        if key not in f:
            continue
        sd = f[key]
        blocks = []
        for b in sd["blocks"]:
            b = dict(b)
            slot = b.pop("slot", None)
            if slot:
                if slot not in plan["text"]:
                    raise SystemExit(f"plan.text is missing '{slot}'")
                b["text"] = plan["text"][slot]
            if b["style"] == "box":
                b.setdefault("box", theme["box"])
                b.setdefault("color", theme["color"])
            if b.get("stroke_color") == "{theme.sub_outline}":
                b["stroke_color"] = theme.get("sub_outline", "#1A1A1A")
            blocks.append(b)
        n = len(slides) + 1
        s = {"out": os.path.join(plan["out_dir"], f"slide-{n:02d}.png"), "blocks": blocks}
        if sd["type"] == "dealshot":
            s["dealshot"] = plan["dealshot"]
        else:
            s["in"] = plan["photo"]
        slides.append(s)
    job = {"fonts_dir": plan.get("fonts_dir") or os.path.join(HERE, "..", "fonts"), "slides": slides}
    json.dump(job, open(job_path, "w"), indent=2, ensure_ascii=False)
    print("job written:", job_path, len(slides), "slides")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
