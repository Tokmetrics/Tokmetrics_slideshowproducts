# TokMetrics slideshow products

Daily TikTok Shop UK product picks from **@tikshop.uk / TokMetrics**, plus a Claude skill that turns
them into ready-to-post photo slideshows.

## products/
- `latest.json` – today's 30 picks, refreshed every morning (~6am UK).
  - 15 from the **GMV Max Radar** filter (fast-growing, affiliate-driven products)
  - 15 **top products of the last 30 days**
- `YYYY-MM-DD.json` – each day's list, kept as history.

Each product has `rank`, `list`, `product`, `productId`, `productUrl` (TikTok Shop UK link),
`priceHint` and `commission`. `priceHint` is only a guide – always check the live listing price.

## kit/ – the slideshow skill
- `SKILL.md` – instructions Claude follows
- `formats.json` – the two slideshow layouts (DEAL-FIRST, SNAP-CAPTION), measured from @tikshop.uk's posts
- `copy.json` – rotating on-screen text so every post reads differently
- `tools/` – `render.py` (adds the text, red price circle and CTA), `build_job.py`, `dealshot.js`

Install the skill from the zip you were sent (upload the zip in Claude's Skills settings), then just ask
Claude: **"Make 10 slideshows from the TokMetrics list."** You need the Claude desktop app, Claude in
Chrome, and to be signed in to ChatGPT in Chrome. Claude never posts for you.
