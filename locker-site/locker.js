/* Sprite Stop Locker — locker state, rendering, share codes, Discord posts.
 * Vanilla JS, no build step. Share code format is IDENTICAL to the
 * UltronCore/sprite-tracker site and the sprite-trade-stop bot:
 * 2 bits per sprite (0 missing / 1 have / 2 mastered) in SHARE_ORDER,
 * packed 4 per byte, base64url, no padding. */

const STATUS = { MISSING: 0, HAVE: 1, MASTERED: 2 };
const STORAGE_KEY = "sts_sprite_locker_v1";

const state = {
  status: {},          // sprite id -> 0|1|2
  owner: "",           // display name used on exports and Discord posts
  lineFilter: "all",   // theme key or "all"
  showUnreleased: false,
};

const THEME_BY_KEY = Object.fromEntries(THEMES.map((t) => [t.key, t]));
// Short variant tags for compact Discord posts (legend printed in the post).
const THEME_TAG = {
  basic: "N", gold: "G", candy: "Gu", galaxy: "Gx",
  gem: "Gem", holofoil: "Ho", rift: "R",
};
const RARITY_HEX = {
  rare: "#2ea4ff", epic: "#b15cff", legendary: "#ff8a2a",
  mythic: "#ffd23a", special: "#28e0c8",
};

// ---- persistence ---------------------------------------------------------
function load() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    if (saved && typeof saved === "object") {
      state.status = saved.status || {};
      state.owner = saved.owner || "";
      if (saved.showUnreleased) state.showUnreleased = true;
    }
  } catch (_) { /* corrupted storage — start fresh */ }
  // A pasted share link wins over storage so ?c= URLs always show that locker.
  const code = new URLSearchParams(location.search).get("c");
  if (code) {
    const status = unpackCode(code);
    if (status) state.status = status;
  }
}

function save() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    status: state.status, owner: state.owner, showUnreleased: state.showUnreleased,
  }));
}

// ---- share code (bot-compatible; see spritebot/sprites.py) ---------------
function packCode() {
  const vals = SHARE_ORDER.map((id) => state.status[id] || 0);
  const bytes = [];
  for (let i = 0; i < vals.length; i += 4) {
    bytes.push((vals[i] || 0) | ((vals[i + 1] || 0) << 2) |
               ((vals[i + 2] || 0) << 4) | ((vals[i + 3] || 0) << 6));
  }
  let bin = "";
  bytes.forEach((b) => { bin += String.fromCharCode(b); });
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

// Strict decode mirroring the bot: reject wrong charset, impossible status
// values (3), or codes shorter than the released roster / longer than the full
// one. Returns {id: status} or null.
function unpackCode(raw) {
  let code = String(raw || "").trim();
  if (code.includes("c=")) code = code.split("c=").pop();
  code = code.split(/[&#\s]/)[0];
  if (!code || !/^[A-Za-z0-9_-]+$/.test(code)) return null;
  let bin;
  try { bin = atob(code.replace(/-/g, "+").replace(/_/g, "/")); }
  catch (_) { return null; }
  const expected = Math.ceil(SHARE_ORDER.length / 4);
  const maxReleasedIdx = SHARE_ORDER.reduce(
    (m, id, i) => (spriteById(id).unreleased ? m : i), 0);
  const minBytes = (maxReleasedIdx >> 2) + 1;
  if (bin.length < minBytes || bin.length > expected) return null;
  const status = {};
  for (let i = 0; i < SHARE_ORDER.length; i++) {
    const byte = bin.charCodeAt(i >> 2) || 0;
    const v = (byte >> ((i % 4) * 2)) & 0b11;
    if (v === 3) return null;
    status[SHARE_ORDER[i]] = v;
  }
  return status;
}

// ---- helpers -------------------------------------------------------------
const BY_ID = Object.fromEntries(SPRITES.map((s) => [s.id, s]));
function spriteById(id) { return BY_ID[id]; }
function st(id) { return state.status[id] || 0; }
function inScope(s) { return state.showUnreleased || !s.unreleased; }
function scopeSprites() { return SPRITES.filter(inScope); }

function progress() {
  const scope = scopeSprites();
  return {
    total: scope.length,
    collected: scope.filter((s) => st(s.id) >= 1).length,
    mastered: scope.filter((s) => st(s.id) === 2).length,
  };
}

function characters() {
  return [...new Set(SPRITES.map((s) => s.character))];
}

function ownerLabel() { return (state.owner || "").trim(); }
function lockerTitle() {
  const n = ownerLabel();
  return n ? `${n}'s Sprite Locker` : "My Sprite Locker";
}

// ---- rendering -----------------------------------------------------------
const lockerEl = document.getElementById("locker");

function slotHTML(s) {
  const v = st(s.id);
  const cls = v === 2 ? "mastered" : v === 1 ? "have" : "missing";
  const crown = v === 2 ? '<span class="crown">👑</span>' : "";
  const soon = s.unreleased ? '<span class="soon">SOON</span>' : "";
  const line = THEME_BY_KEY[s.theme] ? THEME_BY_KEY[s.theme].label : s.theme;
  return `
    <button class="slot ${cls}" data-id="${s.id}"
            title="${s.name} · ${s.rarity} — click to change"
            style="--rarity:${RARITY_HEX[s.rarity.toLowerCase()] || "#28e0c8"}">
      <img src="sprites/${s.id}.png" alt="${s.name}" loading="lazy"
           onerror="this.style.visibility='hidden'">
      ${crown}${soon}
      <span class="line-tag">${line}</span>
    </button>`;
}

function render() {
  const p = progress();
  document.getElementById("collectedCount").textContent = `${p.collected} / ${p.total}`;
  document.getElementById("masteredCount").textContent = `${p.mastered} / ${p.total}`;
  document.getElementById("collectedBar").style.width = p.total ? (p.collected / p.total * 100) + "%" : "0";
  document.getElementById("masteredBar").style.width = p.total ? (p.mastered / p.total * 100) + "%" : "0";

  let html = "";
  characters().forEach((char) => {
    const all = SPRITES.filter((s) => s.character === char && inScope(s));
    if (!all.length) return;
    const shown = all.filter((s) => state.lineFilter === "all" || s.theme === state.lineFilter);
    if (!shown.length) return;
    const have = all.filter((s) => st(s.id) >= 1).length;
    const full = have === all.length;
    html += `
      <section class="shelf ${full ? "complete" : ""}">
        <div class="shelf-head">
          <span class="char-name">${char}</span>
          <span class="char-count">${have}/${all.length}${full ? " ✦ COMPLETE" : ""}</span>
        </div>
        <div class="slots">${shown.map(slotHTML).join("")}</div>
      </section>`;
  });
  lockerEl.innerHTML = html || '<p class="empty">Nothing matches this filter.</p>';
  updateChipCounts();
}

function buildLineChips() {
  const wrap = document.getElementById("lineChips");
  const chips = [{ key: "all", label: "All lines" }].concat(
    THEMES.filter((t) => t.released || state.showUnreleased)
          .map((t) => ({ key: t.key, label: t.label })));
  wrap.innerHTML = chips.map((c) =>
    `<button class="chip ${c.key === state.lineFilter ? "active" : ""}" data-line="${c.key}">
       ${c.label}<span class="count" data-count="${c.key}"></span></button>`).join("");
}

function updateChipCounts() {
  document.querySelectorAll("[data-count]").forEach((el) => {
    const key = el.getAttribute("data-count");
    const pool = scopeSprites().filter((s) => key === "all" || s.theme === key);
    const have = pool.filter((s) => st(s.id) >= 1).length;
    el.textContent = pool.length ? `${have}/${pool.length}` : "";
  });
}

// ---- Discord post builder (the "Copy for Discord" feature) ---------------
// Compact per-character summary: "Water N·G·Gu·Gx*" (* = mastered variant).
function haveSummary() {
  const parts = [];
  characters().forEach((char) => {
    const owned = SPRITES.filter((s) => s.character === char && inScope(s) && st(s.id) >= 1);
    if (!owned.length) return;
    const tags = owned.map((s) => (THEME_TAG[s.theme] || "?") + (st(s.id) === 2 ? "*" : ""));
    parts.push(`${char} ${tags.join("·")}`);
  });
  return parts;
}

function missingNames() {
  return scopeSprites().filter((s) => st(s.id) === 0).map((s) => s.name);
}

// Keep posts safely under Discord's 2000-char message limit.
function clampList(names, budget) {
  let out = "";
  let used = 0;
  for (let i = 0; i < names.length; i++) {
    const piece = (i ? ", " : "") + names[i];
    if (out.length + piece.length > budget) {
      return out + ` …+${names.length - used} more`;
    }
    out += piece;
    used++;
  }
  return out;
}

function discordPost(mode) {
  const p = progress();
  const code = packCode();
  const legend = "(N Normal · G Gold · Gu Gummy · Gx Galaxy · * mastered)";
  const syncLine = `🔁 Sync code: \`${code}\` → paste into **/synccollection**`;
  const lines = [];

  if (mode === "locker") {
    lines.push(`🧬 **${lockerTitle()}** — Sprite Trade Stop`);
    lines.push(`📦 Collected **${p.collected}/${p.total}** · 👑 Mastered **${p.mastered}/${p.total}**`);
    const have = haveSummary();
    if (have.length) {
      lines.push(`✅ ${clampList(have, 1500)}`);
      lines.push(legend);
    }
    lines.push(syncLine);
  } else if (mode === "looking") {
    const miss = missingNames();
    lines.push(`🔎 **${lockerTitle()} — LOOKING FOR** (${miss.length})`);
    lines.push(miss.length ? `❌ ${clampList(miss, 1600)}` : "Nothing — locker complete! 🎉");
    lines.push("Ping me in #trade-portal if you can help!");
    lines.push(syncLine);
  } else { // trade
    const miss = missingNames();
    lines.push(`🤝 **${lockerTitle()} — TRADE POST**`);
    lines.push(`📦 ${p.collected}/${p.total} collected · 👑 ${p.mastered} mastered`);
    const have = haveSummary();
    if (have.length) {
      lines.push(`✅ Have: ${clampList(have, 900)}`);
      lines.push(legend);
    }
    lines.push(miss.length ? `❌ Need: ${clampList(miss, 700)}` : "❌ Need: nothing — dupes only!");
    lines.push(syncLine);
  }
  return lines.join("\n");
}

async function copyText(text, doneMsg) {
  try { await navigator.clipboard.writeText(text); toast(doneMsg); }
  catch (_) { prompt("Copy this:", text); }
}

// ---- interactions --------------------------------------------------------
lockerEl.addEventListener("click", (e) => {
  const slot = e.target.closest(".slot");
  if (!slot) return;
  const id = slot.getAttribute("data-id");
  state.status[id] = (st(id) + 1) % 3;
  save(); render();
});

document.getElementById("lineChips").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  state.lineFilter = chip.getAttribute("data-line");
  document.querySelectorAll("#lineChips .chip").forEach((c) =>
    c.classList.toggle("active", c === chip));
  render();
});

document.getElementById("showUnreleased").addEventListener("change", (e) => {
  state.showUnreleased = e.target.checked;
  if (!state.showUnreleased && THEME_BY_KEY[state.lineFilter] &&
      !THEME_BY_KEY[state.lineFilter].released) state.lineFilter = "all";
  buildLineChips(); save(); render();
});

document.getElementById("ownerName").addEventListener("input", (e) => {
  state.owner = e.target.value; save();
});

document.getElementById("resetBtn").addEventListener("click", () => {
  if (!confirm("Reset your whole locker?")) return;
  state.status = {}; save(); render(); toast("Locker reset");
});

// share / sync
document.getElementById("shareBtn").addEventListener("click", () => {
  const url = `${location.origin}${location.pathname}?c=${packCode()}`;
  copyText(url, "Share link copied!");
});
document.getElementById("syncBtn").addEventListener("click", () => {
  copyText(packCode(), "Sync code copied — paste into /synccollection");
});

// import
const importDialog = document.getElementById("importDialog");
document.getElementById("importBtn").addEventListener("click", () => {
  document.getElementById("importText").value = "";
  importDialog.showModal();
});
importDialog.addEventListener("close", () => {
  if (importDialog.returnValue !== "ok") return;
  const status = unpackCode(document.getElementById("importText").value);
  if (!status) { toast("That doesn't look like a valid code 😕"); return; }
  state.status = status; save(); render(); toast("Collection imported!");
});

// Copy for Discord
document.getElementById("copyLockerBtn").addEventListener("click", () =>
  copyText(discordPost("locker"), "Locker post copied — paste it in Discord!"));
document.getElementById("copyLookingBtn").addEventListener("click", () =>
  copyText(discordPost("looking"), "Looking-For post copied — paste it in Discord!"));
document.getElementById("copyTradeBtn").addEventListener("click", () =>
  copyText(discordPost("trade"), "Trade post copied — paste it in Discord!"));

// save images (export.js)
document.getElementById("saveLockerBtn").addEventListener("click", () => exportImage("collection"));
document.getElementById("saveLookingBtn").addEventListener("click", () => exportImage("missing"));

// toast
let toastTimer;
function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg; t.classList.add("show");
  clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove("show"), 2400);
}
window.sslToast = toast;

// ---- boot ----------------------------------------------------------------
load();
document.getElementById("showUnreleased").checked = state.showUnreleased;
document.getElementById("ownerName").value = state.owner;
buildLineChips();
render();
