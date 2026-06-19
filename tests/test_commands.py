"""Guard test: every cog loads and the full expected slash-command set
registers. Catches structural regressions (e.g. a method accidentally moved
out of its cog class so its command silently stops registering)."""

import asyncio
import os
import tempfile

import discord
from discord.ext import commands

from spritebot import config, db

os.environ.setdefault("DISCORD_TOKEN", "dummy")

COGS = ["vouch", "trades", "scam", "collection", "collection_sync",
        "insights", "welcome", "admin"]

EXPECTED = {
    # vouch
    "vouch", "profile", "rank", "leaderboard", "editvouch", "removevouch",
    # trades / scam
    "trade", "reportscammer", "blacklist", "unblacklist",
    # collection (role-based)
    "whohas", "whoneeds", "match", "refreshlists", "tracker",
    # collection sync
    "synccollection", "mycollection", "missing", "holders", "spriteinfo",
    "spriteset", "spriteprivacy", "guildprogress", "spritematch",
    # insights / admin
    "insights", "setup", "postleaderboard", "digest", "announcenew",
}


def _load_and_collect():
    async def run():
        db_path = tempfile.mktemp(suffix=".db")
        config.DB_PATH = db_path
        db._conn = None
        db.setup()
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        bot = commands.Bot(command_prefix="+", intents=intents,
                           allowed_mentions=discord.AllowedMentions.none())
        from spritebot.cogs.trades import TradeConfirmView
        bot.add_view(TradeConfirmView())
        for c in COGS:
            await bot.load_extension(f"spritebot.cogs.{c}")
        names = {c.name for c in bot.tree.get_commands()}
        prefix = {c.name for c in bot.commands}
        await bot.close()
        db._conn = None
        if os.path.exists(db_path):
            os.remove(db_path)
        return names, prefix

    return asyncio.run(run())


def test_all_expected_commands_register():
    names, prefix = _load_and_collect()
    missing = EXPECTED - names
    assert not missing, f"commands missing from tree: {sorted(missing)}"
    assert "rep" in prefix, "+rep prefix alias missing"
