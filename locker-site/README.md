# 🧬 Sprite Stop Locker — Fortnite Sprites

A **locker-style** Fortnite Sprites collection site for the **Sprite Trade Stop**
Discord — in the spirit of sprite-locker checklist sites, built on our own data
and bot integration. Tap the sprites you've extracted, then:

- 🖼️ **Save an image** of your locker (green) or your **Looking For** list (red)
  to post in `#show-collection` / `#trade-portal`.
- 💬 **Copy for Discord** — one click builds a ready-to-paste post (locker
  summary, Looking-For list, or a full trade post) that stays under Discord's
  2000-character limit.
- 🔁 **Sync code** — the same 2-bit code as the
  [Sprites Tracker](https://github.com/UltronCore/sprite-tracker); paste it into
  the [Sprite Trade Stop bot](https://github.com/UltronCore/sprite-trade-stop)'s
  `/synccollection` and share links work in both tools.

No accounts, no backend — your locker lives in `localStorage` and in the
`?c=…` share link.

## Run locally

It's a static site; any web server works:

```bash
python3 -m http.server 8080
# open http://localhost:8080
```

(Or just open `index.html` — everything except font loading works offline.)

## Move to its own repo

This folder is fully standalone. To give it its own repository:

1. Create an empty repo on GitHub named `sprite-stop-locker` (no README).
2. From this folder: `git init && git add -A && git commit -m "Initial locker site"`
   then `git remote add origin <repo url> && git push -u origin main`.
3. The Pages workflow below deploys it on the first push.

## Deploy

Pushing to `main` deploys to GitHub Pages via
`.github/workflows/pages.yml` (first run enables Pages automatically).

## How it fits the ecosystem

| Piece | Repo | Role |
|---|---|---|
| **This locker** | `sprite-stop-locker` | Locker showcase: image exports + Discord posts |
| Sprites Tracker | [`UltronCore/sprite-tracker`](https://github.com/UltronCore/sprite-tracker) | Dense checklist editor |
| Discord bot | [`UltronCore/sprite-trade-stop`](https://github.com/UltronCore/sprite-trade-stop) | Trust economy, trades, `/synccollection` |

All three share one sprite manifest (`data.js` here ⇄ the bot's
`spritebot/assets/sprites.json`) and one share-code format:
2 bits per sprite (0 missing / 1 have / 2 mastered) in `SHARE_ORDER`,
packed 4 per byte, base64url, no padding. **Append new sprites at the END of
`data.js`** so existing codes stay valid, and drop a matching
`sprites/<id>.png` (512×512, transparent).

## ⚖️ Disclaimer

Unofficial **fan-made** tool. **Sprite artwork © Epic Games, Inc.** Not
affiliated with or endorsed by Epic Games, and not affiliated with any other
sprite checklist site. No personal data is collected or uploaded.

MIT licensed (code only; sprite images are Epic's property).
