// Run with javascript_tool on a TikTok Shop listing tab (https://shop.tiktok.com/gb/pdp/<productId>)
// AFTER the page has loaded. It tidies the page for a clean screenshot and returns:
//  - price: the live sale price, was-price, discount %, title, sold count (read from the page)
//  - region: the screen rectangle to capture with computer{action:"zoom", region, scale:1, save_to_disk:true}
//  - image_box / info_box / price_box: screen rectangles for render.py's "dealshot" (pass with "region")
// If ok:false, read "why" and don't build a deal slide for this product.
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  document.body.style.zoom = '0.8';
  document.querySelectorAll('[class*="overflow-y"]').forEach(e => (e.scrollTop = 0));
  scrollTo(0, 0);
  await sleep(700);
  // hide the sticky breadcrumb bar and any cookie/app banners that sit over the content
  document.querySelectorAll('.sticky.top-0').forEach(e => (e.style.visibility = 'hidden'));
  document.querySelectorAll('[class*="cookie"],[class*="Cookie"],[class*="banner"],[class*="Banner"]').forEach(e => {
    const p = getComputedStyle(e).position; if (p === 'fixed' || p === 'sticky') e.style.display = 'none';
  });
  await sleep(300);
  const R = e => { const b = e.getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom].map(v => Math.round(v)); };
  const leaves = [...document.querySelectorAll('body *')].filter(e => e.children.length === 0 && e.offsetParent);
  const vis = e => { const b = e.getBoundingClientRect(); return b.top >= 0 && b.bottom <= innerHeight && b.width > 0; };
  // discount % at the top of the info column (the first one on screen)
  const pctEl = leaves.find(e => /^-\d{1,2}%$/.test(e.textContent.trim()) && vis(e) && parseFloat(getComputedStyle(e).fontSize) * 1 >= 20);
  const hero = [...document.querySelectorAll('img')].filter(i => i.naturalWidth >= 600 && vis(i) || (i.naturalWidth >= 600 && i.getBoundingClientRect().top < innerHeight && i.getBoundingClientRect().top >= 0))[0];
  if (!hero) return JSON.stringify({ ok: false, why: 'no product image on screen' });
  const hb = R(hero);
  // the price row: the biggest '£'-number on screen to the right of the image
  const nums = leaves.filter(e => /^\d+$/.test(e.textContent.trim()) && vis(e) && e.getBoundingClientRect().left > hb[2]);
  nums.sort((a, b) => parseFloat(getComputedStyle(b).fontSize) - parseFloat(getComputedStyle(a).fontSize));
  const intEl = nums[0];
  if (!intEl) return JSON.stringify({ ok: false, why: 'price not found on screen' });
  const ib = R(intEl);
  const sameRow = leaves.filter(e => vis(e) && Math.abs(e.getBoundingClientRect().top + e.getBoundingClientRect().height / 2 - (ib[1] + ib[3]) / 2) < 30 && e.getBoundingClientRect().left > hb[2]);
  const pound = sameRow.find(e => e.textContent.trim() === '£' && e.getBoundingClientRect().right <= ib[0] + 3);
  const cents = sameRow.find(e => /^\.\d\d$/.test(e.textContent.trim()) && e.getBoundingClientRect().left >= ib[2] - 3);
  const wasEl = sameRow.find(e => /^£[\d.,]+$/.test(e.textContent.trim()) && getComputedStyle(e).textDecorationLine.includes('line-through'));
  const pb = [pound ? R(pound)[0] : ib[0], ib[1], cents ? R(cents)[2] : ib[2], ib[3]];
  const price = '£' + intEl.textContent.trim() + (cents ? cents.textContent.trim() : '');
  // info column: from the price row down to the Buy now button (or the bottom of the screen)
  const buy = [...document.querySelectorAll('button,div')].find(e => e.textContent.trim() === 'Buy now' && vis(e));
  const colLeft = Math.min(pctEl ? R(pctEl)[0] : pb[0], pb[0]) - 6;
  const colRight = Math.min(innerWidth - 10, Math.max(...(buy ? [R(buy)[2]] : [pb[2] + 500]))) + 6;
  const infoBottom = buy ? R(buy)[3] + 8 : innerHeight - 4;
  const region = [Math.max(0, hb[0] - 8), Math.max(0, Math.min(hb[1], pb[1]) - 8), colRight, Math.min(innerHeight, Math.max(hb[3], infoBottom))];
  const title = (document.querySelector('h1') || {}).textContent || document.title;
  const soldEl = leaves.find(e => /sold$/i.test(e.textContent.trim()) && vis(e));
  return JSON.stringify({
    ok: true,
    price, was: wasEl ? wasEl.textContent.trim() : null, pct: pctEl ? pctEl.textContent.trim() : null,
    title: title.trim().slice(0, 200), sold: soldEl ? soldEl.textContent.trim() : null,
    region,
    image_box: [hb[0], hb[1], hb[2], Math.min(hb[3], region[3])],
    info_box: [colLeft, pb[1] - 10, colRight, infoBottom],
    price_box: pb,
    note: 'Capture with computer zoom region=' + JSON.stringify(region) + ' scale 1 save_to_disk true; pass these boxes plus "region" to render.py'
  });
})()
