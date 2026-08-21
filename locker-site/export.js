/* Canvas image export — saves a PNG of your locker (green) or your
 * Looking-For list (red), styled for posting in Discord. */

const EXPORT_SITE = "Sprite Stop Locker · sprite-trade-stop";

function imgFor(id) {
  return new Promise((resolve) => {
    const im = new Image();
    im.onload = () => resolve(im);
    im.onerror = () => resolve(null);
    im.src = `sprites/${id}.png`;
  });
}

async function exportImage(mode) {
  const collection = mode === "collection";
  const scope = scopeSprites();
  const items = collection
    ? scope.filter((s) => st(s.id) >= 1)
    : scope.filter((s) => st(s.id) === 0);

  if (!items.length) {
    window.sslToast(collection
      ? "You haven't marked any sprites yet — tap the ones you have first."
      : "Nothing missing — your locker is complete! 🎉");
    return;
  }
  window.sslToast("Building image…");

  const cols = Math.min(6, items.length);
  const rows = Math.ceil(items.length / cols);
  const pad = 22, cardW = 168, cardH = 196, gap = 12, headerH = 68, footerH = 40;
  const W = pad * 2 + cols * cardW + (cols - 1) * gap;
  const H = headerH + pad + rows * cardH + (rows - 1) * gap + pad + footerH;

  const canvas = document.createElement("canvas");
  canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext("2d");

  const accent = collection ? "#2bd07a" : "#ff4d5e";
  const p = progress();
  const who = ownerLabel();

  ctx.fillStyle = "#0a0d14"; ctx.fillRect(0, 0, W, H);
  ctx.lineWidth = 6; ctx.strokeStyle = accent;
  ctx.strokeRect(3, 3, W - 6, H - 6);

  ctx.fillStyle = "#10141d"; ctx.fillRect(6, 6, W - 12, headerH);
  ctx.fillStyle = accent;
  ctx.font = 'italic 700 26px "Oswald", sans-serif';
  ctx.textBaseline = "middle";
  const title = collection
    ? `SPRITE STOP LOCKER${who ? " — " + who.toUpperCase() : ""}`
    : `${who ? who.toUpperCase() + " IS" : "I'M"} LOOKING FOR THESE SPRITES!`;
  ctx.fillText(title, pad, 6 + headerH / 2);

  if (collection) {
    ctx.font = '700 15px "Oswald", sans-serif';
    ctx.textAlign = "right";
    ctx.fillStyle = "#e8edf5";
    ctx.fillText(`COLLECTED ${p.collected}/${p.total}   MASTERED ${p.mastered}/${p.total}`,
                 W - pad, 6 + headerH / 2);
    ctx.textAlign = "left";
  }

  const imgs = await Promise.all(items.map((s) => imgFor(s.id)));

  items.forEach((s, i) => {
    const cx = pad + (i % cols) * (cardW + gap);
    const cy = headerH + pad + Math.floor(i / cols) * (cardH + gap);
    const v = st(s.id);

    ctx.fillStyle = "#161c28";
    roundRect(ctx, cx, cy, cardW, cardH, 12); ctx.fill();
    ctx.lineWidth = 3;
    ctx.strokeStyle = v === 2 ? "#ffcf3a" : v === 1 ? "#2bd07a" : "#39414f";
    roundRect(ctx, cx, cy, cardW, cardH, 12); ctx.stroke();

    const im = imgs[i];
    const artBox = cardW - 28;
    if (im) {
      ctx.globalAlpha = collection ? 1 : 0.92;
      ctx.drawImage(im, cx + 14, cy + 12, artBox, artBox);
      ctx.globalAlpha = 1;
    }

    if (collection) {
      const label = v === 2 ? "MASTERED" : "COLLECTED";
      const bg = v === 2 ? "#ffcf3a" : "#2bd07a";
      badge(ctx, cx + 8, cy + 8, label, bg, v === 2 ? "#2a2000" : "#04331c");
      if (v === 2) { ctx.font = "20px serif"; ctx.fillText("👑", cx + cardW - 30, cy + 26); }
    }

    badge(ctx, cx + 8, cy + cardH - 52, s.rarity.toUpperCase(),
          RARITY_HEX[s.rarity.toLowerCase()] || "#28e0c8", "#06121a");

    ctx.fillStyle = "#e8edf5";
    ctx.font = '800 14px "Inter", sans-serif';
    ctx.textAlign = "center";
    ctx.fillText(fit(ctx, s.name.toUpperCase(), cardW - 16), cx + cardW / 2, cy + cardH - 18);
    ctx.textAlign = "left";
  });

  ctx.fillStyle = "#aeb8c8";
  ctx.font = '700 15px "Inter", sans-serif';
  ctx.textAlign = "center";
  ctx.fillText(EXPORT_SITE, W / 2, H - footerH / 2 - 2);
  ctx.textAlign = "left";

  const a = document.createElement("a");
  a.download = collection ? "my-sprite-locker.png" : "sprites-im-looking-for.png";
  a.href = canvas.toDataURL("image/png");
  a.click();
  window.sslToast("Image saved — post it in the server!");
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
function badge(ctx, x, y, text, bg, fg) {
  ctx.font = '700 11px "Oswald", sans-serif';
  const w = ctx.measureText(text).width + 14;
  ctx.fillStyle = bg; roundRect(ctx, x, y, w, 18, 4); ctx.fill();
  ctx.fillStyle = fg; ctx.textBaseline = "middle";
  ctx.fillText(text, x + 7, y + 10);
  ctx.textBaseline = "alphabetic";
}
function fit(ctx, text, maxW) {
  if (ctx.measureText(text).width <= maxW) return text;
  while (text.length > 3 && ctx.measureText(text + "…").width > maxW) text = text.slice(0, -1);
  return text + "…";
}
