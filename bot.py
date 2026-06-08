"""
Sprite Trade Stop — entry point.

Run with:  python bot.py
The token is read from a .env file (DISCORD_TOKEN), never hardcoded.

What this file does:
  1. loads .env + sets up the database
  2. registers persistent button views (trade confirm buttons survive restarts)
  3. loads every cog (feature module) in spritebot/cogs/
  4. syncs slash commands and connects
"""

import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from spritebot import config, db
from spritebot.cogs.trades import TradeConfirmView

# Intents. members + message_content must ALSO be enabled in the Developer
# Portal (members = welcome/role logic; message_content = +rep alias + /insights).
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

COGS = [
    "spritebot.cogs.vouch",
    "spritebot.cogs.trades",
    "spritebot.cogs.scam",
    "spritebot.cogs.collection",
    "spritebot.cogs.insights",
    "spritebot.cogs.welcome",
    "spritebot.cogs.admin",
]


class SpriteTradeBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=config.COMMAND_PREFIX,
            intents=intents,
            help_command=None,
            # Security: never let user-supplied text (vouch notes, trade items,
            # report reasons) trigger @everyone/@here/role pings. Commands that
            # intentionally ping pass their own allowed_mentions.
            allowed_mentions=discord.AllowedMentions.none(),
        )

    async def setup_hook(self):
        db.setup()
        # Persistent view so trade Confirm/Cancel buttons work after a restart.
        self.add_view(TradeConfirmView())
        for ext in COGS:
            await self.load_extension(ext)
        # Sync slash commands. If GUILD_ID is set, sync to that guild for
        # instant availability; otherwise sync globally (can take ~1 hour).
        if config.GUILD_ID:
            guild = discord.Object(id=config.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self):
        print(f"Logged in as {self.user} (id: {self.user.id})")
        print("Sprite Trade Stop is ready.")


def main():
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit(
            "DISCORD_TOKEN missing. Copy .env.example to .env and paste your "
            "bot token.")
    bot = SpriteTradeBot()
    bot.run(token)


if __name__ == "__main__":
    main()
