"""
Welcome new members: assign the Newbie flair and post a friendly intro
covering onboarding roles, safe trading, the no-V-Bucks rule, and vouching.
"""

import discord
from discord.ext import commands

from .. import config, settings


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        # Assign Newbie flair (first tier).
        newbie = settings.flair_role(member.guild, config.FLAIR_TIERS[0][0])
        if newbie:
            try:
                await member.add_roles(newbie, reason="Joined — Newbie flair")
            except discord.Forbidden:
                pass

        channel = settings.get_channel(member.guild, "welcome")
        if not channel:
            return
        embed = discord.Embed(
            title=f"👋 Welcome to Sprite Trade Stop, {member.display_name}!",
            color=discord.Color.blurple(),
            description=(
                "We're a **sprite trading** community. Here's the quick start:\n\n"
                "**1. Pick your sprite roles** via the server's Onboarding "
                "questions — that's how the bot knows what you have and need.\n"
                "**2. Find trades:** `/whohas`, `/whoneeds`, and `/match` show "
                "who has what.\n"
                "**3. Trade safely:** use `/trade @them` — both sides press "
                "**Confirm** so nobody gets scammed.\n"
                "**4. Build trust:** after a good trade, `/vouch` each other "
                "(or `+rep @user`). Vouches raise your flair: "
                "Newbie → Trader → Verified Trader → Veteran → Max Helper.\n\n"
                f"{config.NO_VBUCKS_RULE}\n"
                "See a scammer? `/reportscammer`."
            ),
        )
        await channel.send(content=member.mention, embed=embed)


async def setup(bot):
    await bot.add_cog(Welcome(bot))
