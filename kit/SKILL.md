---
name: tokmetrics-slideshows
description: Make TikTok Shop UK slideshows from today's TokMetrics list - as many as the person asks for. Picks the top products, gets ChatGPT to make the photos, adds the text, saves the slides to this computer and gives the product links in chat. Use when asked for TokMetrics slideshows.
---

# TokMetrics slideshows

Makes ready-to-post TikTok Shop UK photo slideshows in @tikshop.uk's two proven formats, from
**today's TokMetrics list** (30 hand-picked UK products, refreshed every morning) at:

- Products: `https://raw.githubusercontent.com/Tokmetrics/Tokmetrics_slideshowproducts/main/products/latest.json`
- Latest formats + rotating text: `.../main/kit/formats.json` and `.../main/kit/copy.json`
  (same repo). If these can't be read, use the copies bundled in this skill folder.

**How many:** the person says how many slideshows they want ("make 10", "do 25"). If they didn't say,
ask once ("How many slideshows would you like today?"); if no answer comes, make 10. Each slideshow
takes about 4–6 minutes, mostly waiting for ChatGPT, so say roughly how long the batch will take.
Always call the source "the TokMetrics list" — don't describe where TokMetrics gets its products.

**Never post anything to TikTok.** The person posts manually. Never type passwords.

## What this needs (check first, say plainly what's missing)
1. **Claude desktop app** open on the person's computer, with an output folder connected. Default
   folder `~/Documents/TikTok Slideshows` (ask for access with `device_request_folder_access`; if it
   doesn't exist, ask for `~/Documents` and create it there). Also ask once for `~/Downloads`
   (ChatGPT images download there).
2. **Claude in Chrome** connected, with the person **signed in to chatgpt.com** in Chrome.
   Load the Chrome tools in one ToolSearch call: `tabs_context_mcp, tabs_create_mcp, navigate,
   computer, find, javascript_tool, upload_image, get_page_text, tabs_close_mcp`. Work in 2 tabs you
   create (listing tab + ChatGPT tab) and close them at the end.
3. The first time ChatGPT images download, Chrome may ask to **"Allow multiple downloads"** for
   chatgpt.com — ask the person to click Allow.

## Hard rules (every slideshow)
1. **Faceless.** No face or head ever. First-person POV (hands, arms, lap, feet) or the product on its
   own. Say "faceless, no face or head visible" in every ChatGPT prompt.
2. **Product must match the listing exactly** — shape, colour, logos, label text, what's included.
   Always attach the real listing image to ChatGPT and compare every photo with it. Ask for a fix if
   anything differs (max 2 retries), otherwise skip that product and say why.
3. **ChatGPT makes photos only, with NO text** (except the real printing on the product). All slide
   text, the red circle and the CTA are added by `tools/render.py`, so fonts, sizes, colours and
   positions match @tikshop.uk's slides exactly. Never let ChatGPT write on-screen text.
4. **Photos are vertical 9:16**, realistic casual iPhone photos in a natural setting.
5. **The deal slide is a real screenshot** of the live listing (never redrawn or edited); only the
   red circle and text are added on top. Prices, discounts and sold counts must be today's real ones.
6. **CTA position never moves** (bottom-left, bottom edge y 0.785) so it sits just above TikTok's
   product-link sticker without covering it.
7. **Honest hooks:** "typo / who f*cked up / why TF are you paying full price" style hooks only when
   the listing shows a real discount of 20% or more. With a smaller or no discount, use lines that
   don't claim a mistake ("Ok I'm obsessed", "Swipe for the price…").

## The two formats (layouts are in formats.json — always build through tools/build_job.py)
- **DEAL-FIRST** (2 slides): 1) real listing screenshot, sale price circled in red, hook
  (`deal_hook`) + sub-line (`deal_sub`) in TikTok text boxes over the product image;
  2) ChatGPT product photo + `product_main` + `product_sub` + `cta`. Default theme yellow
  (cream box #FEF5A5, brown text #AC6629). Needs a real discount.
- **SNAP-CAPTION** (2 slides): 1) ChatGPT product photo with a Snapchat-style caption bar
  (`snap_caption`, as if sending it to friends) + big white outlined line (`snap_main`);
  2) real listing screenshot, price circled, `deal_main` + `deal_sub2` + `cta`. Default theme red
  (box #E74041, white text).
- Alternate formats product by product. You may swap the theme (yellow/red) for variety.

## Rotating text (copy.json)
- Pick one line per slot. Keep a log at `<output folder>/_used-lines.json` (create it if missing):
  never reuse a line used in the same batch or in the last 2 days until that slot's bank is used up.
- About 1 in 3 times, write a fresh line in exactly the same voice instead (clickbaity, casual, 1–3 of
  the style emojis, censored swears like f*cked / TF) — so no two posts read the same.
- Choose the audience bank (`him`, `her`, `self`, `home`, `kids`) from the product: a men's
  product → `him` (girlfriend POV, e.g. "just won the best girlfriend award, he's going to love this");
  beauty/fashion for women → `self` or `her`; household → `home`; toys → `kids`.
- Fill `{sale}` (BLACK FRIDAY in Nov, CHRISTMAS in Dec, JANUARY SALE in Jan, otherwise "sale"),
  `{product}` (2–4 natural words) and `{price}` (today's live price).

---

## Step 1 — Get today's products
1. In Chrome, open the products URL above and read it with `get_page_text`; parse the JSON. Check its
   `date` — if it's older than 2 days, tell the person the list hasn't been refreshed but carry on.
   Also read `kit/formats.json` and `kit/copy.json` the same way (fallback: bundled copies).
2. Read `<output folder>/_done.json` if it exists (product IDs made in the last 7 days) and skip those.
3. Go down the TokMetrics list in `rank` order and take as many products as slideshows requested. If they ask for
   more slideshows than products available, make 2 per product (one of each format).

## Step 2 — For each product
**a. Listing + deal screenshot** (listing tab):
- Open `https://shop.tiktok.com/gb/pdp/<productId>` and wait ~3 s. If it says "not available in this
  country or region", reload once; if still unavailable, skip the product and take the next one.
- Run `tools/dealshot.js` with `javascript_tool` (read the file, pass its contents). It returns the
  live `price`, `was`, `pct`, `title`, `sold`, the screen `region` and boxes.
- Move the mouse out of the way (`computer` hover at the bottom-right corner), then
  `computer` zoom with that `region`, `scale: 1`, `save_to_disk: true`. Copy the saved PNG to the
  work folder as `listing.png`. Look at it: price row fully visible, nothing covering it.
- Product reference for ChatGPT: overlay the hero image full-screen (the `img` with
  naturalWidth >= 600 that is the product, not a banner), take a `screenshot` and keep its ID.

**b. Photo in ChatGPT** (ChatGPT tab, a NEW chat per product):
- `find` the hidden "Attach photos"/file input and `upload_image` the product reference screenshot.
  Check the thumbnail shows in the composer before sending.
- Prompt (fill the brackets):
  "The attached image is the exact product: [describe every item, colour, logo and label text].
  Reproduce it exactly — don't redesign it and don't include any banners or badges from the image.
  Make a realistic casual iPhone photo, vertical 9:16, of [scene]. Faceless: no face or head visible,
  [only a hand / no people]. No text anywhere except the real printing on the product. Keep the top
  30% of the image fairly plain (soft background) so text can go there, and keep the lower-left
  corner fairly plain."
- Scenes (pick one that fits and vary them): laid flat on a made bed with cosy fairy lights; on a
  kitchen countertop by a window; on a wooden table with a coffee; held in one hand at arm's length;
  on a sofa next to a blanket; next to wrapping paper, ribbon and scissors (gift products, Nov/Dec);
  on a bathroom shelf (beauty); in a hallway/living room in use (home products).
- Wait ~60 s; it's done when no button has a "stop" aria-label. Scroll to the bottom, fetch the newest
  `img[alt*="Generated image"]` (naturalWidth > 800) as a blob and click a temporary
  `<a download="tm-<productId>.png">`. Copy it from `~/Downloads` into the work folder with the device
  tools, stage it, and **look at it**: product matches the listing, no face, no added text, 9:16.
- If ChatGPT says an image limit was reached, stop, save progress, and tell the person.

**c. Text + render** (in your own workspace with Bash; the scripts and fonts are in this skill folder):
- Write `plan.json` (see the top of `tools/build_job.py`) with the format, theme, photo path, the
  dealshot `{shot, region, image_box, info_box, price_box}`, the chosen lines and `out_dir`, then:
  `python3 tools/build_job.py plan.json job.json && python3 tools/render.py job.json`
  (fonts: `fonts/` in this skill; the emoji font is the system Noto Color Emoji).
- Look at both slides. Text readable, nothing important covered, circle around the sale price, CTA
  bottom-left. Fix the plan and re-render if needed.
- Write `post.txt`: a short caption in the same voice, 3–4 hashtags (#tiktokmademebuyit + season tag
  like #blackfriday + brand + niche), the product name and link, "Price when made: £X (check before
  posting)", and "Turn on the AI-generated content label when posting (photo made with AI)".

**d. Save to the computer:** copy `slide-01.png`, `slide-02.png`, `post.txt` into
`<output folder>/<YYYY-MM-DD>/<NN> - <short product name> - <FORMAT>/` with `device_commit_files`.
Update `_used-lines.json` and `_done.json`.

## Step 3 — Finish
1. Make a contact sheet (`preview.jpg`, all slideshows in rows), save it in the day folder, and show it.
2. **In the chat, list every slideshow with its product link** so the person can add it when posting:
   ```
   1. Henry Quick corded stick vacuum (DEAL-FIRST) — £95.99, was £159.99
      https://www.tiktok.com/shop/gb/pdp/1729964096493754827
      Folder: 2026-11-19/01 - Henry vacuum - DEAL-FIRST
   2. ...
   ```
   Use the short product name, the format, today's price (and was-price if there is one), the
   `productUrl` from the TokMetrics list, and the folder name. Also write the same list to
   `<day folder>/links.txt`.
3. Say how many are ready, where they are, and anything that needs the person (skipped products,
   ChatGPT limits, Downloads to tidy). Close the tabs you opened.
