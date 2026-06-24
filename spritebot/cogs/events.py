"""
Weekly Sprite events ("community days").

Surfaces Fortnite's confirmed weekly sprite cadence — Mastery Monday, New Sprite
Thursday, Saturday Power Hour — so members know when bonuses and new sprites
land. Times are ET; "today" is computed in US/Eastern when available.

Note: "Community Days" isn't an official Epic term — it maps to these weekly
events, so the embed says so plainly rather than inventing a mechanic.
"""

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from .. import config


def _eastern_now():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/New_York"))
    except Exception:  # noqa: BLE001 - tzdata missing → fall back to fixed EDT
        return datetime.now(timezone.utc).astimezone()


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Weekly Sprite events (a.k.a. community days).")
    @app_commands.checks.cooldown(3, 15.0)
    async def events(self, interaction: discord.Interaction):
        today = _eastern_now().strftime("%A")
        lines = []
        todays = []
        for ev in config.WEEKLY_EVENTS:
            here = ev["day"] == today
            mark = " ⬅️ **TODAY**" if here else ""
            lines.append(f"{ev['emoji']} **{ev['name']}** — {ev['day']} "
                         f"{ev['time_et']}{mark}\n   {ev['desc']}")
            if here:
                todays.append(ev["name"])
        header = (f"🎉 **Today ({today}): {', '.join(todays)}**\n\n"
                  if todays else "No special event today — here's the week:\n\n")
        embed = discord.Embed(
            title="📅 Weekly Sprite Events",
            description=header + "\n".join(lines),
            color=discord.Color.gold())
        embed.set_footer(
            text="Times are ET · \"community days\" = these weekly events · "
                 "new sprites drop on New Sprite Thursday")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Events(bot))
