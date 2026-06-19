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
    "spritebot.cogs.collection_sync",
    "spritebot.cogs.queue",
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
        # Single-guild by design: all data is keyed by user id with no guild
        # column, so the bot must only operate in the configured guild. This
        # check makes cross-guild data bleed impossible if it's ever added to
        # another server. (No-op when GUILD_ID is 0, e.g. local dev.)
        async def _guild_guard(interaction: discord.Interaction) -> bool:
            if not config.GUILD_ID or interaction.guild_id == config.GUILD_ID:
                return True
            try:
                await interaction.response.send_message(
                    "This bot is configured for one specific server only.",
                    ephemeral=True)
            except discord.InteractionResponded:
                pass
            return False
        self.tree.interaction_check = _guild_guard
        self.tree.on_error = self._on_app_error

        # Persistent view so trade Confirm/Cancel buttons work after a restart.
        self.add_view(TradeConfirmView())

    async def _on_app_error(self, interaction: discord.Interaction, error):
        # Friendly, non-crashing handling for cooldowns / permission checks.
        from discord import app_commands
        msg = None
        if isinstance(error, app_commands.CommandOnCooldown):
            msg = f"⏳ Slow down — try again in {error.retry_after:.0f}s."
        elif isinstance(error, app_commands.MissingPermissions):
            msg = "You don't have permission to do that."
        elif isinstance(error, app_commands.CheckFailure):
            return  # handled by the check itself (e.g. guild guard)
        if msg is None:
            print(f"[app error] {type(error).__name__}: {error}")
            msg = "Something went wrong running that command."
        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except discord.HTTPException:
            pass
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
