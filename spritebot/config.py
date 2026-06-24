"""
============================================================================
 SPRITE TRADE STOP — OWNER CONFIG
============================================================================
Edit the values in this file to match your server. You can fill IDs in by
hand, OR run the in-Discord /setup command (admin only) which auto-detects
channels and roles by name and saves their IDs into the database — those saved
IDs then override whatever is set here, so you don't have to hunt for IDs.

How IDs are resolved at runtime (see settings.py):
    database override (from /setup)  >  the value set here  >  unset (0)

You can refer to channels/roles by NAME here (strings) and let /setup resolve
them, or paste numeric IDs directly. Numeric IDs are the most reliable.
----------------------------------------------------------------------------
"""

# Your server (guild) ID. Right-click the server icon -> Copy Server ID
# (enable Developer Mode in Discord settings first).
GUILD_ID = 0

# ---------------------------------------------------------------------------
# People with elevated permissions
# ---------------------------------------------------------------------------
# Owner ("Frosty") + admins, by user ID. These users can run admin commands
# even without the Owner/Admin *roles* below. Add as many as you need.
OWNER_IDS = [
    0,  # <- Frosty's user ID
]
ADMIN_IDS = [
    # 111111111111111111,
]

# Static roles that also grant admin permissions. The bot NEVER auto-strips
# these. Matched by name (case-insensitive) if no ID is given.
OWNER_ROLE_NAME = "Owner"
ADMIN_ROLE_NAME = "Admin"

# ---------------------------------------------------------------------------
# Channels (by name; /setup resolves to IDs, or paste IDs into settings)
# ---------------------------------------------------------------------------
CHANNELS = {
    "trade_portal": "trade-portal",     # where /trade embeds are posted
    "vouch_trades": "vouch-trades",     # where vouches are announced
    "modlog": "modlog",                 # scam reports / admin audit
    "leaderboard": "leaderboard",       # daily leaderboard auto-post
    "sprite_list": "sprite-list",       # auto-maintained holders list
    "gold_zp_list": "gold-zp-list",     # auto-maintained Gold Zero Point list
    "welcome": "welcome",               # welcome messages on join
    "digest": "sprite-digest",          # optional weekly guild digest channel
    "news": "news",                     # where "new sprite released" announcements post
    "queue": "sprite-queue",            # where queue boards + "you're up" pings post
}

# ---------------------------------------------------------------------------
# Sprite roles (the server already creates these via Discord Onboarding)
# ---------------------------------------------------------------------------
# 7 collectible sprites, each with a base + "(Gold)" variant. The bot READS
# these roles; it does not create them. Fire/Earth/Water are starters (no role).
# Values are role NAMES; /setup resolves them to IDs. You may also hardcode IDs
# in settings if names are ambiguous.
SPRITE_ROLES = {
    "Zero Point": {"base": "Zero Point", "gold": "Zero Point (Gold)"},
    "Dream":      {"base": "Dream",      "gold": "Dream (Gold)"},
    "Punk":       {"base": "Punk",       "gold": "Punk (Gold)"},
    "King":       {"base": "King",       "gold": "King (Gold)"},
    "Ghost":      {"base": "Ghost",      "gold": "Ghost (Gold)"},
    "Demon":      {"base": "Demon",      "gold": "Demon (Gold)"},
    "Duck":       {"base": "Duck",       "gold": "Duck (Gold)"},
}

# Starter sprites with no role (for reference / messages).
STARTER_SPRITES = ["Fire", "Earth", "Water"]

# ---------------------------------------------------------------------------
# Trust / verified trader
# ---------------------------------------------------------------------------
VERIFIED_TRADER_ROLE_NAME = "verified-trader"
# Number of (non-removed) vouches received to auto-assign verified-trader.
VERIFIED_TRADER_THRESHOLD = 5

# ---------------------------------------------------------------------------
# Sprite hand-off queues
# ---------------------------------------------------------------------------
# Staff who fulfil queues. Distributors (and admins) can run /queue next/done.
DISTRIBUTOR_ROLE_NAME = "Distributor"
# Max distinct queues one member can be in at once (anti queue-everything).
MAX_QUEUES_PER_USER = 6
# The special "general / any sprite" queue id + label.
QUEUE_GENERAL_ID = "general"
QUEUE_GENERAL_LABEL = "General (any sprite)"

# ---------------------------------------------------------------------------
# Flair ladder (auto-assigned by progression). All thresholds tunable.
# A member holds exactly ONE flair role at a time (the highest they qualify
# for). Newbie is assigned on join. Thresholds are measured in VOUCHES RECEIVED.
# ---------------------------------------------------------------------------
FLAIR_TIERS = [
    # (flair role name, min vouches received to reach it)
    ("Newbie",          0),
    ("Trader",          1),
    ("Verified Trader", 5),
    ("Veteran",         15),
    ("Max Helper",      40),
]

# ---------------------------------------------------------------------------
# XP (vouch-driven only — NO chat XP)
# ---------------------------------------------------------------------------
XP_PER_VOUCH = 10          # XP granted per vouch received

# ---------------------------------------------------------------------------
# Anti-scam
# ---------------------------------------------------------------------------
MIN_ACCOUNT_AGE_DAYS = 7   # minimum Discord account age to give/receive vouches
MIN_GUILD_TENURE_HOURS = 24  # how long a member must be IN the server before vouching
MAX_VOUCHES_PER_DAY = 10   # max vouches one member can GIVE per 24h (anti-farming)
# Repeat vouches between the SAME pair are allowed, but only once per this
# window — so regular trading partners keep building trust without ring-farming.
VOUCH_PAIR_COOLDOWN_HOURS = 24

# ---------------------------------------------------------------------------
# Collector roles — AUTO-ASSIGNED from a member's synced collection.
# Maps to the milestone roles the Sprite Trade Stop server already hands out by
# hand. Edit `role` to your EXACT Discord role name; /setup binds it by name.
# Set COLLECTOR_ROLES = [] to turn the whole feature off.
# Rules (evaluated over RELEASED sprites only):
#   all_theme  + theme   → has every sprite of that variant line (have or mastered)
#   all_rarity + rarity  → has every sprite of that rarity
#   has        + id      → has a specific sprite
#   all_have             → has every released sprite (full collection)
#   all_mastered         → has mastered every released sprite
#   mastered_count + n   → has mastered at least n sprites
# ---------------------------------------------------------------------------
COLLECTOR_ROLES = [
    {"role": "All Gold",                "rule": "all_theme",  "theme": "gold"},
    {"role": "Galaxy Sprite Collector", "rule": "all_theme",  "theme": "galaxy"},
    {"role": "Gummy Sprite Collector",  "rule": "all_theme",  "theme": "candy"},
    {"role": "Mythic Sprite Collector", "rule": "all_rarity", "rarity": "Mythic"},
    {"role": "Epic Sprite Collector",   "rule": "all_rarity", "rarity": "Epic"},
    {"role": "Peanut Collector",        "rule": "has",        "id": "theburntpeanut_basic"},
    {"role": "Superior Sprite Collector", "rule": "all_have"},
    {"role": "Mastered Em' All",        "rule": "all_mastered"},
    {"role": "15 Sprites Mastered",     "rule": "mastered_count", "n": 15},
    # Optional "pro traders" gate (Goose's suggestion): auto-role for members
    # missing ≤3 sprites. Rename/remove to taste; /setup only binds it if the
    # role exists. Gate a #pro-traders channel by this role.
    {"role": "Almost Complete",         "rule": "missing_at_most", "n": 3},
]
SCAM_REPORT_COOLDOWN_SECONDS = 60  # min seconds between a user's scam reports
TRADE_COOLDOWN_SECONDS = 30        # min seconds between opening trades (anti-spam)

# /insights: channels to skip when scanning (names, case-insensitive). Keeps
# staff/private channels out of the aggregate even if the bot can read them.
INSIGHTS_EXCLUDED_CHANNELS = ["mod-chat", "staff", "admin", "logs", "modlog"]

# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------
DB_PATH = "sprite_trade_stop.db"
COMMAND_PREFIX = "+"       # enables the  +rep @user  vouch alias

# ---------------------------------------------------------------------------
# Feature toggles
# ---------------------------------------------------------------------------
# Cog modules to NOT load. Use this if another bot already covers a feature —
# e.g. if the server runs its OWN vouch bot, set:
#     DISABLED_COGS = ["vouch", "scam"]
# to run only the collection / queue / panel / events side and avoid overlap.
# (Leave empty to run everything.)
DISABLED_COGS = []

# ---------------------------------------------------------------------------
# Weekly Sprite events (Epic-confirmed cadence; some call them "community days").
# Times are US Eastern (ET). Surfaced by /events. Edit if Epic changes them.
# ---------------------------------------------------------------------------
WEEKLY_EVENTS = [
    {"day": "Monday",   "name": "Mastery Monday",
     "time_et": "9:00 AM ET", "emoji": "🌟",
     "desc": "2× Mastery Points & Sprite Dust, boosted Legendary/Mythic spawns (24h)."},
    {"day": "Thursday", "name": "New Sprite Thursday",
     "time_et": "9:00 AM ET", "emoji": "🆕",
     "desc": "A new sprite/variant joins the loot pool permanently."},
    {"day": "Saturday", "name": "Saturday Power Hour",
     "time_et": "3:30 PM & 9:30 PM ET", "emoji": "⚡",
     "desc": "Featured-variant boosted spawns + stacking multipliers."},
]

# Web collection tracker (mark Have/Missing/Mastered, filter by line, export
# shareable trade images). Surfaced via /tracker and the welcome message.
# NOTE: the server officially uses Rickventure's tracker
# (https://staticvacant.github.io/fnsprites/) — the bot decodes its share codes
# identically, so point members there if you prefer it over this fork.
TRACKER_URL = "https://ultroncore.github.io/sprite-tracker/"

# Optional role to ping when new sprites are announced (community-requested
# "Sprite News" ping). Leave "" to ping no one. Bound by /setup if it exists.
NEWS_PING_ROLE_NAME = ""
LIST_REFRESH_MINUTES = 30  # how often the auto-maintained sprite lists refresh
                           # (the daily leaderboard is a separate 24h loop)
DIGEST_INTERVAL_HOURS = 168  # weekly guild sprite digest (opt-in, low-noise).
                             # Posts to the #sprite-digest channel if /setup found
                             # one, else the leaderboard channel. Off until enabled.
NO_VBUCKS_RULE = (
    "💰 **Server rule:** Sprites are traded for sprites only — **never** sold "
    "for V-Bucks or real money."
)
