/*
 * Sprite Trade Stop — Fortnite Sprites data sheet.
 *
 * To add a new sprite or flip an unreleased one live: edit this list and drop a
 * matching image at  sprites/<id>.png  (512x512 PNG, transparent background).
 *
 * Fields:
 *   id        - unique slug, also the image filename (sprites/<id>.png)
 *   name      - display name
 *   character - the base creature (used for "group by character")
 *   theme     - variant line key: basic | gold | candy | galaxy | gem | holofoil | rift
 *   rarity    - Rare | Epic | Legendary | Mythic | Special
 *   unreleased- true = not in game yet (hidden unless "show unreleased" is on)
 *
 * Sprite artwork © Epic Games — this is an unofficial fan-made collection tracker.
 *
 * Data verified against fortnite.gg/sprites (Chapter 7 Season 3 "Runners",
 * re-checked 2026-06-24): still 41 RELEASED (10 characters + Burnt Peanut), the
 * four live variant lines Normal/Gold/Gummy/Galaxy (Galaxy released 2026-06-18).
 * Upcoming characters (Striker/Fishy/Aura/Boss/Grim Reaper drop 2026-06-25;
 * John Wick TBD; Drifter/Ice/Seven datamine-only) are appended at the END as
 * unreleased — flip to released on launch day.
 * NOTE: game data also defines Cube (Dream/Punk/Zero Point) and Quack (Zero
 * Point) variant lines, but they have NO icons in-game yet, so they're omitted
 * here until art exists. Gem/Holofoil/Rift below are the unreleased lines that
 * already have art and show behind the "Show unreleased" toggle.
 */

// Variant lines, in display order. label is what users see; "released" lines
// are the four everyone collects today.
const THEMES = [
  { key: "basic",    label: "Normal",   released: true  },
  { key: "gold",     label: "Gold",     released: true  },
  { key: "candy",    label: "Gummy",    released: true  },
  { key: "galaxy",   label: "Galaxy",   released: true  },
  { key: "gem",      label: "Gem",      released: false },
  { key: "holofoil", label: "Holofoil", released: false },
  { key: "rift",     label: "Rift",     released: false },
];

const SPRITES = [
  // Water
  { id: "water_basic",  name: "Water",        character: "Water", theme: "basic",  rarity: "Rare",    unreleased: false },
  { id: "water_gold",   name: "Gold Water",   character: "Water", theme: "gold",   rarity: "Special", unreleased: false },
  { id: "water_candy",  name: "Gummy Water",  character: "Water", theme: "candy",  rarity: "Special", unreleased: false },
  { id: "water_galaxy", name: "Galaxy Water", character: "Water", theme: "galaxy", rarity: "Special", unreleased: false },
  { id: "water_gem",      name: "Gem Water",      character: "Water", theme: "gem",      rarity: "Special", unreleased: true },
  { id: "water_holofoil", name: "Holofoil Water", character: "Water", theme: "holofoil", rarity: "Special", unreleased: true },

  // Earth
  { id: "earth_basic",  name: "Earth",        character: "Earth", theme: "basic",  rarity: "Rare",    unreleased: false },
  { id: "earth_gold",   name: "Gold Earth",   character: "Earth", theme: "gold",   rarity: "Special", unreleased: false },
  { id: "earth_candy",  name: "Gummy Earth",  character: "Earth", theme: "candy",  rarity: "Special", unreleased: false },
  { id: "earth_galaxy", name: "Galaxy Earth", character: "Earth", theme: "galaxy", rarity: "Special", unreleased: false },
  { id: "earth_gem",    name: "Gem Earth",    character: "Earth", theme: "gem",    rarity: "Special", unreleased: true },

  // Fire
  { id: "fire_basic",  name: "Fire",        character: "Fire", theme: "basic",  rarity: "Rare",    unreleased: false },
  { id: "fire_gold",   name: "Gold Fire",   character: "Fire", theme: "gold",   rarity: "Special", unreleased: false },
  { id: "fire_candy",  name: "Gummy Fire",  character: "Fire", theme: "candy",  rarity: "Special", unreleased: false },
  { id: "fire_galaxy", name: "Galaxy Fire", character: "Fire", theme: "galaxy", rarity: "Special", unreleased: false },
  { id: "fire_holofoil", name: "Holofoil Fire", character: "Fire", theme: "holofoil", rarity: "Special", unreleased: true },

  // Duck
  { id: "duck_basic",  name: "Duck",        character: "Duck", theme: "basic",  rarity: "Epic",    unreleased: false },
  { id: "duck_gold",   name: "Gold Duck",   character: "Duck", theme: "gold",   rarity: "Special", unreleased: false },
  { id: "duck_candy",  name: "Gummy Duck",  character: "Duck", theme: "candy",  rarity: "Special", unreleased: false },
  { id: "duck_galaxy", name: "Galaxy Duck", character: "Duck", theme: "galaxy", rarity: "Special", unreleased: false },
  { id: "duck_gem",    name: "Gem Duck",    character: "Duck", theme: "gem",    rarity: "Special", unreleased: true },

  // Ghost
  { id: "ghost_basic",  name: "Ghost",        character: "Ghost", theme: "basic",  rarity: "Epic",    unreleased: false },
  { id: "ghost_gold",   name: "Gold Ghost",   character: "Ghost", theme: "gold",   rarity: "Special", unreleased: false },
  { id: "ghost_candy",  name: "Gummy Ghost",  character: "Ghost", theme: "candy",  rarity: "Special", unreleased: false },
  { id: "ghost_galaxy", name: "Galaxy Ghost", character: "Ghost", theme: "galaxy", rarity: "Special", unreleased: false },
  { id: "ghost_holofoil", name: "Holofoil Ghost", character: "Ghost", theme: "holofoil", rarity: "Special", unreleased: true },

  // Dream
  { id: "dream_basic",  name: "Dream",        character: "Dream", theme: "basic",  rarity: "Legendary", unreleased: false },
  { id: "dream_gold",   name: "Gold Dream",   character: "Dream", theme: "gold",   rarity: "Special",   unreleased: false },
  { id: "dream_candy",  name: "Gummy Dream",  character: "Dream", theme: "candy",  rarity: "Special",   unreleased: false },
  { id: "dream_galaxy", name: "Galaxy Dream", character: "Dream", theme: "galaxy", rarity: "Special",   unreleased: false },
  { id: "dream_rift",   name: "Rift Dream",   character: "Dream", theme: "rift",   rarity: "Special",   unreleased: true },

  // Demon
  { id: "demon_basic",  name: "Demon",        character: "Demon", theme: "basic",  rarity: "Epic",    unreleased: false },
  { id: "demon_gold",   name: "Gold Demon",   character: "Demon", theme: "gold",   rarity: "Special", unreleased: false },
  { id: "demon_candy",  name: "Gummy Demon",  character: "Demon", theme: "candy",  rarity: "Special", unreleased: false },
  { id: "demon_galaxy", name: "Galaxy Demon", character: "Demon", theme: "galaxy", rarity: "Special", unreleased: false },
  { id: "demon_gem",    name: "Gem Demon",    character: "Demon", theme: "gem",    rarity: "Special", unreleased: true },

  // Punk
  { id: "punk_basic",  name: "Punk",        character: "Punk", theme: "basic",  rarity: "Legendary", unreleased: false },
  { id: "punk_gold",   name: "Gold Punk",   character: "Punk", theme: "gold",   rarity: "Special",   unreleased: false },
  { id: "punk_candy",  name: "Gummy Punk",  character: "Punk", theme: "candy",  rarity: "Special",   unreleased: false },
  { id: "punk_galaxy", name: "Galaxy Punk", character: "Punk", theme: "galaxy", rarity: "Special",   unreleased: false },
  { id: "punk_gem",    name: "Gem Punk",    character: "Punk", theme: "gem",    rarity: "Special",   unreleased: true },
  { id: "punk_rift",   name: "Rift Punk",   character: "Punk", theme: "rift",   rarity: "Special",   unreleased: true },

  // King
  { id: "king_basic",  name: "King",        character: "King", theme: "basic",  rarity: "Epic",    unreleased: false },
  { id: "king_gold",   name: "Gold King",   character: "King", theme: "gold",   rarity: "Special", unreleased: false },
  { id: "king_candy",  name: "Gummy King",  character: "King", theme: "candy",  rarity: "Special", unreleased: false },
  { id: "king_galaxy", name: "Galaxy King", character: "King", theme: "galaxy", rarity: "Special", unreleased: false },
  { id: "king_holofoil", name: "Holofoil King", character: "King", theme: "holofoil", rarity: "Special", unreleased: true },

  // Zero Point
  { id: "zeropoint_basic",  name: "Zero Point",        character: "Zero Point", theme: "basic",  rarity: "Mythic",  unreleased: false },
  { id: "zeropoint_gold",   name: "Gold Zero Point",   character: "Zero Point", theme: "gold",   rarity: "Special", unreleased: false },
  { id: "zeropoint_candy",  name: "Gummy Zero Point",  character: "Zero Point", theme: "candy",  rarity: "Special", unreleased: false },
  { id: "zeropoint_galaxy", name: "Galaxy Zero Point", character: "Zero Point", theme: "galaxy", rarity: "Special", unreleased: false },
  { id: "zeropoint_gem",      name: "Gem Zero Point",      character: "Zero Point", theme: "gem",      rarity: "Special", unreleased: true },
  { id: "zeropoint_holofoil", name: "Holofoil Zero Point", character: "Zero Point", theme: "holofoil", rarity: "Special", unreleased: true },

  // Special mascot
  { id: "theburntpeanut_basic", name: "Burnt Peanut", character: "Burnt Peanut", theme: "basic", rarity: "Mythic", unreleased: false },

  // --- Upcoming characters (appended at the END so existing share codes stay
  // valid). The "Gone Wild" drop lands 2026-06-25; John Wick date TBD;
  // Drifter/Ice/Seven are datamine-only. All kept unreleased until live —
  // flip unreleased:false on release day and the bot auto-announces them.
  { id: "striker_basic", name: "Striker",     character: "Striker",     theme: "basic",  rarity: "Rare",    unreleased: true },
  { id: "fishy_basic",   name: "Fishy",       character: "Fishy",       theme: "basic",  rarity: "Rare",    unreleased: true },
  { id: "aura_basic",    name: "Aura",        character: "Aura",        theme: "basic",  rarity: "Rare",    unreleased: true },
  { id: "boss_basic",    name: "Boss",        character: "Boss",        theme: "basic",  rarity: "Rare",    unreleased: true },
  { id: "reaper_basic",  name: "Grim Reaper", character: "Grim Reaper", theme: "basic",  rarity: "Rare",    unreleased: true },
  { id: "reaper_galaxy", name: "Galaxy Grim Reaper", character: "Grim Reaper", theme: "galaxy", rarity: "Special", unreleased: true },
  { id: "wick_basic",    name: "John Wick",   character: "John Wick",   theme: "basic",  rarity: "Rare",    unreleased: true },
  { id: "drifter_basic", name: "Drifter",     character: "Drifter",     theme: "basic",  rarity: "Rare",    unreleased: true },
  { id: "ice_basic",     name: "Ice",         character: "Ice",         theme: "basic",  rarity: "Rare",    unreleased: true },
  { id: "seven_basic",   name: "Seven",       character: "Seven",       theme: "basic",  rarity: "Rare",    unreleased: true },
];

// Stable id order used to pack/unpack the share code (so URLs stay valid as long
// as this order doesn't change; append new sprites at the END to preserve codes).
const SHARE_ORDER = SPRITES.map((s) => s.id);
