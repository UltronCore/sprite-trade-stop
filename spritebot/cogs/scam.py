"""
Scam protection: report scammers to modlog, and admin blacklist controls.
(The minimum-account-age check lives in helpers.eligible_to_vouch.)
"""

import discord
from discord import app_commands
from discord.ext import commands

from .. import db, settings


class Scam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Report a scammer to the mod team.")
    @app_commands.describe(user="The suspected scammer",
                           proof="Link/description of what happened")
    async def reportscammer(self, interaction: discord.Interaction,
                            user: discord.Member, proof: str):
        db.add_scam_report(interaction.user.id, user.id, proof)
        modlog = settings.get_channel(interaction.guild, "modlog")
        if modlog:
            embed = discord.Embed(
                title="🚨 Scam Report",
                color=discord.Color.red(),
                description=f"**Reported:** {user.mention} (`{user.id}`)\n"
                            f"**By:** {interaction.user.mention}",
            )
            embed.add_field(name="Proof", value=proof[:1024], inline=False)
            embed.add_field(name="Their vouches",
                            value=str(db.vouch_count(user.id)))
            await modlog.send(embed=embed)
        await interaction.response.send_message(
            "Thanks — your report was sent to the mod team. 🛡️", ephemeral=True)

    @app_commands.command(description="(Admin) Block a user from the trade system.")
    async def blacklist(self, interaction: discord.Interaction,
                        user: discord.Member, reason: str = "No reason given"):
        if not settings.is_admin(interaction.user):
            await interaction.response.send_message("Admins only.", ephemeral=True)
            return
        db.add_blacklist(user.id, reason)
        modlog = settings.get_channel(interaction.guild, "modlog")
        if modlog:
            await modlog.send(
                f"⛔ {user.mention} blacklisted by {interaction.user.mention} "
                f"— {reason}")
        await interaction.response.send_message(
            f"{user.mention} blacklisted.", ephemeral=True)

    @app_commands.command(description="(Admin) Remove a user from the blacklist.")
    async def unblacklist(self, interaction: discord.Interaction,
                          user: discord.Member):
        if not settings.is_admin(interaction.user):
            await interaction.response.send_message("Admins only.", ephemeral=True)
            return
        ok = db.remove_blacklist(user.id)
        await interaction.response.send_message(
            f"{user.mention} {'removed from' if ok else 'was not on'} the blacklist.",
            ephemeral=True)


async def setup(bot):
    await bot.add_cog(Scam(bot))
