"""
Two-party trade flow with anti-scam confirmation.

/trade @user give_you give_them
  -> posts an embed in #trade-portal with Confirm buttons for BOTH parties.
  -> the trade only counts as complete once BOTH confirm.
  -> on completion, both are prompted to /vouch each other.

The Confirm view is persistent (custom_id + timeout=None) so buttons keep
working after a restart; state is looked up from the trades table by message ID.
"""

import discord
from discord import app_commands
from discord.ext import commands

from .. import config, db, settings


class TradeConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _finish_if_ready(self, interaction, trade):
        if trade["a_confirm"] and trade["b_confirm"]:
            db.set_trade_status(trade["id"], "complete")
            a = interaction.guild.get_member(trade["party_a"])
            b = interaction.guild.get_member(trade["party_b"])
            embed = _trade_embed(interaction.guild, db.get_trade(trade["id"]))
            for c in self.children:
                c.disabled = True
            await interaction.message.edit(embed=embed, view=self)
            am = a.mention if a else "Party A"
            bm = b.mention if b else "Party B"
            await interaction.channel.send(
                f"✅ Trade `#{trade['id']}` complete! {am} and {bm}, please "
                f"`/vouch` each other to build trust. {config.NO_VBUCKS_RULE}"
            )

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success,
                       custom_id="trade_confirm")
    async def confirm(self, interaction: discord.Interaction, button):
        trade = db.get_trade_by_message(interaction.message.id)
        if not trade or trade["status"] != "pending":
            await interaction.response.send_message(
                "This trade is closed.", ephemeral=True)
            return
        uid = interaction.user.id
        if uid == trade["party_a"]:
            db.confirm_trade(trade["id"], "a")
        elif uid == trade["party_b"]:
            db.confirm_trade(trade["id"], "b")
        else:
            await interaction.response.send_message(
                "Only the two traders can confirm this.", ephemeral=True)
            return
        trade = db.get_trade(trade["id"])
        embed = _trade_embed(interaction.guild, trade)
        await interaction.response.edit_message(embed=embed, view=self)
        await self._finish_if_ready(interaction, trade)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger,
                       custom_id="trade_cancel")
    async def cancel(self, interaction: discord.Interaction, button):
        trade = db.get_trade_by_message(interaction.message.id)
        if not trade or trade["status"] != "pending":
            await interaction.response.send_message(
                "This trade is closed.", ephemeral=True)
            return
        if interaction.user.id not in (trade["party_a"], trade["party_b"]) \
                and not settings.is_admin(interaction.user):
            await interaction.response.send_message(
                "Only the traders or an admin can cancel.", ephemeral=True)
            return
        db.set_trade_status(trade["id"], "cancelled")
        for c in self.children:
            c.disabled = True
        embed = _trade_embed(interaction.guild, db.get_trade(trade["id"]))
        await interaction.response.edit_message(embed=embed, view=self)


def _trade_embed(guild, trade) -> discord.Embed:
    a = guild.get_member(trade["party_a"])
    b = guild.get_member(trade["party_b"])
    status = {"pending": "🟡 Awaiting confirmation",
              "complete": "✅ Complete",
              "cancelled": "❌ Cancelled"}[trade["status"]]
    e = discord.Embed(title=f"🔁 Trade #{trade['id']}", color=discord.Color.orange())
    e.add_field(name=f"{a.display_name if a else 'Party A'} gives",
                value=trade["give_a"] or "—", inline=True)
    e.add_field(name=f"{b.display_name if b else 'Party B'} gives",
                value=trade["give_b"] or "—", inline=True)
    e.add_field(name="Status", value=status, inline=False)
    e.add_field(name="Confirmed",
                value=f"{'✅' if trade['a_confirm'] else '⬜'} "
                      f"{a.display_name if a else 'A'}  ·  "
                      f"{'✅' if trade['b_confirm'] else '⬜'} "
                      f"{b.display_name if b else 'B'}",
                inline=False)
    e.set_footer(text="Sprites for sprites only — never V-Bucks.")
    return e


class Trades(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Open a two-party sprite trade.")
    @app_commands.describe(user="The other trader",
                           you_give="What you will drop/give",
                           they_give="What they will drop/give")
    async def trade(self, interaction: discord.Interaction,
                    user: discord.Member, you_give: str, they_give: str):
        if user.id == interaction.user.id or user.bot:
            await interaction.response.send_message(
                "Pick another (human) trader.", ephemeral=True)
            return
        if db.is_blacklisted(user.id) or db.is_blacklisted(interaction.user.id):
            await interaction.response.send_message(
                "One of you is blacklisted from trading.", ephemeral=True)
            return

        trade_id = db.create_trade(interaction.user.id, user.id,
                                   you_give, they_give)
        portal = settings.get_channel(interaction.guild, "trade_portal") \
            or interaction.channel
        embed = _trade_embed(interaction.guild, db.get_trade(trade_id))
        msg = await portal.send(
            content=f"{interaction.user.mention} ⇄ {user.mention} — both press "
                    f"**Confirm** once the in-game drop is done.",
            embed=embed, view=TradeConfirmView())
        db.set_trade_message(trade_id, msg.id)
        await interaction.response.send_message(
            f"Trade `#{trade_id}` opened in {portal.mention}.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Trades(bot))
