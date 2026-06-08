"""
/insights — AI-FREE analytics. Scans recent channel history and reports pure
counts (no AI, no paid API): most-requested sprites, top traders, busiest
channels, open want-posts. Requires the Message Content Intent.
"""

import re
from collections import Counter

import discord
from discord import app_commands
from discord.ext import commands

from .. import config, db, settings

# Match sprite names + simple "want/need/LF" intent in plain text.
_WANT_RE = re.compile(r"\b(want|wtb|lf|looking for|need|needing)\b", re.IGNORECASE)


class Insights(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        description="(Admin) Pure-count analytics from recent messages. No AI.")
    @app_commands.describe(messages_per_channel="How many recent messages to scan per channel (default 200)")
    async def insights(self, interaction: discord.Interaction,
                       messages_per_channel: int = 200):
        if not settings.is_admin(interaction.user):
            await interaction.response.send_message("Admins only.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        sprite_names = list(config.SPRITE_ROLES) + config.STARTER_SPRITES
        sprite_mentions = Counter()
        want_mentions = Counter()
        channel_activity = Counter()
        author_activity = Counter()   # keyed by author id (avoids name collisions)
        author_names = {}
        open_wants = 0

        limit = max(20, min(messages_per_channel, 1000))
        for channel in interaction.guild.text_channels:
            perms = channel.permissions_for(interaction.guild.me)
            if not perms.read_message_history:
                continue
            try:
                async for msg in channel.history(limit=limit):
                    if msg.author.bot:
                        continue
                    channel_activity[channel.name] += 1
                    author_activity[msg.author.id] += 1
                    author_names[msg.author.id] = msg.author.display_name
                    content = msg.content
                    is_want = bool(_WANT_RE.search(content))
                    if is_want:
                        open_wants += 1
                    for s in sprite_names:
                        if re.search(rf"\b{re.escape(s)}\b", content, re.IGNORECASE):
                            sprite_mentions[s] += 1
                            if is_want:
                                want_mentions[s] += 1
            except discord.Forbidden:
                continue

        def fmt(counter, n=5, names=None):
            top = counter.most_common(n)
            return "\n".join(
                f"`{c}` {names.get(key, key) if names else key}"
                for key, c in top) or "—"

        embed = discord.Embed(
            title="📊 Server Insights (counts only — no AI)",
            description=f"Scanned up to {limit} msgs/channel.",
            color=discord.Color.blurple())
        embed.add_field(name="Most-mentioned sprites", value=fmt(sprite_mentions),
                        inline=False)
        embed.add_field(name="Most-requested (want/LF/need)",
                        value=fmt(want_mentions), inline=False)
        embed.add_field(name="Busiest channels", value=fmt(channel_activity),
                        inline=False)
        embed.add_field(name="Most active members",
                        value=fmt(author_activity, names=author_names),
                        inline=False)
        embed.add_field(name="Open want-posts (approx)", value=str(open_wants))
        # Trade/vouch totals straight from the DB.
        lb = db.leaderboard(3)
        top = "\n".join(
            f"`{r['n']}` <@{r['target_id']}>" for r in lb) or "—"
        embed.add_field(name="Top traders by vouches (DB)", value=top, inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Insights(bot))
