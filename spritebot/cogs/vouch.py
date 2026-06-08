"""
Vouch + reputation + profile + leaderboard.

Commands:
  /vouch @user [proof] [note]   — vouch for someone (also: +rep @user)
  /profile [@user]              — vouches, trust, XP/rank, flair, trade history
  /rank [@user]                 — current flair, XP, next tier
  /editvouch <id> ...           — admin: edit a vouch's note/proof
  /removevouch <id>             — admin: remove a vouch (soft delete)
  /leaderboard                  — top traders by vouches
A daily leaderboard auto-posts to the leaderboard channel (see tasks.py).
"""

import discord
from discord import app_commands
from discord.ext import commands

from .. import db, helpers, progression, settings


class Vouch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---- core vouch logic shared by /vouch and +rep --------------------
    async def _do_vouch(self, guild, voucher: discord.Member,
                        target: discord.Member, proof=None, note=None):
        if target.id == voucher.id:
            return "You can't vouch for yourself."
        if target.bot:
            return "You can't vouch for a bot."

        ok, reason = helpers.eligible_to_vouch(voucher)
        if not ok:
            return reason
        ok, reason = helpers.eligible_to_vouch(target)
        if not ok:
            return f"Target not eligible: {reason}"
        if db.already_vouched(voucher.id, target.id):
            return f"You've already vouched for {target.display_name}."

        vouch_id = db.add_vouch(voucher.id, target.id, note=note, proof=proof)
        summary = await helpers.apply_progression(target)

        # Announce in the vouch-trades channel if configured.
        ch = settings.get_channel(guild, "vouch_trades")
        if ch:
            embed = discord.Embed(
                title="✅ New Vouch",
                description=f"{voucher.mention} vouched for {target.mention}",
                color=discord.Color.green(),
            )
            embed.add_field(name="Vouch ID", value=f"`{vouch_id}`")
            embed.add_field(name="Total vouches", value=str(summary["vouches"]))
            embed.add_field(name="Flair", value=summary["flair"])
            if note:
                embed.add_field(name="Note", value=note[:512], inline=False)
            if proof:
                embed.add_field(name="Proof", value=proof[:512], inline=False)
            await ch.send(embed=embed)

        extra = " — now **verified-trader** 🛡️" if summary["verified"] else ""
        return (f"Vouched for {target.mention}! Vouch `#{vouch_id}`. "
                f"They now have **{summary['vouches']}** vouches "
                f"({summary['flair']}){extra}.")

    @app_commands.command(description="Vouch for a trader you completed a trade with.")
    @app_commands.describe(user="Who you're vouching for",
                           proof="Optional link to proof (screenshot, etc.)",
                           note="Optional short note")
    async def vouch(self, interaction: discord.Interaction,
                    user: discord.Member, proof: str = None, note: str = None):
        msg = await self._do_vouch(interaction.guild, interaction.user, user,
                                   proof=proof, note=note)
        await interaction.response.send_message(msg, ephemeral=True)

    # +rep @user  text alias
    @commands.command(name="rep")
    async def rep_alias(self, ctx: commands.Context, user: discord.Member,
                        *, note: str = None):
        msg = await self._do_vouch(ctx.guild, ctx.author, user, note=note)
        await ctx.reply(msg)

    @app_commands.command(description="Show a trader's reputation profile.")
    async def profile(self, interaction: discord.Interaction,
                      user: discord.Member = None):
        user = user or interaction.user
        vouches = db.vouch_count(user.id)
        xp = progression.xp_for(vouches)
        flair = progression.flair_for(vouches)
        trades = db.completed_trade_count(user.id)

        embed = discord.Embed(
            title=f"📇 {user.display_name}",
            color=discord.Color.blurple(),
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Vouches", value=str(vouches))
        embed.add_field(name="XP", value=str(xp))
        embed.add_field(name="Flair", value=flair)
        embed.add_field(name="Verified",
                        value="🛡️ Yes" if progression.is_verified_trader(vouches) else "No")
        embed.add_field(name="Completed trades", value=str(trades))
        if db.is_blacklisted(user.id):
            embed.add_field(name="⚠️", value="Blacklisted", inline=False)

        recent = db.vouches_for(user.id, limit=5)
        if recent:
            lines = []
            for v in recent:
                voucher = interaction.guild.get_member(v["voucher_id"])
                vn = voucher.display_name if voucher else f"User {v['voucher_id']}"
                note = f" — {v['note']}" if v["note"] else ""
                lines.append(f"`#{v['id']}` from **{vn}**{note}")
            embed.add_field(name="Recent vouches", value="\n".join(lines),
                            inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Your flair, XP, and progress to the next tier.")
    async def rank(self, interaction: discord.Interaction,
                   user: discord.Member = None):
        user = user or interaction.user
        vouches = db.vouch_count(user.id)
        flair = progression.flair_for(vouches)
        nxt = progression.next_tier(vouches)
        desc = (f"**Flair:** {flair}\n**Vouches:** {vouches}\n"
                f"**XP:** {progression.xp_for(vouches)}")
        if nxt:
            name, threshold = nxt
            desc += f"\n**Next:** {name} at {threshold} vouches " \
                    f"({threshold - vouches} to go)"
        else:
            desc += "\n🏆 **Max tier reached!**"
        embed = discord.Embed(title=f"🎖️ {user.display_name}'s rank",
                              description=desc, color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Top traders by vouches.")
    async def leaderboard(self, interaction: discord.Interaction):
        rows = db.leaderboard(10)
        if not rows:
            await interaction.response.send_message(
                "No vouches yet — be the first to vouch a good trader!",
                ephemeral=True)
            return
        medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
        lines = []
        for i, r in enumerate(rows):
            m = interaction.guild.get_member(r["target_id"])
            name = m.display_name if m else f"User {r['target_id']}"
            lines.append(f"{medals[i]} **{name}** — {r['n']} vouches "
                         f"({progression.flair_for(r['n'])})")
        embed = discord.Embed(title="🏆 Trader Leaderboard",
                              description="\n".join(lines),
                              color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)

    # ---- admin: edit / remove ------------------------------------------
    @app_commands.command(description="(Admin) Edit a vouch's note/proof.")
    async def editvouch(self, interaction: discord.Interaction, vouch_id: int,
                        note: str = None, proof: str = None):
        if not settings.is_admin(interaction.user):
            await interaction.response.send_message("Admins only.", ephemeral=True)
            return
        if not db.get_vouch(vouch_id):
            await interaction.response.send_message(
                f"No vouch `#{vouch_id}`.", ephemeral=True)
            return
        if db.edit_vouch(vouch_id, note=note, proof=proof):
            await interaction.response.send_message(
                f"Vouch `#{vouch_id}` updated.", ephemeral=True)
        else:
            await interaction.response.send_message(
                "Nothing to change (pass note and/or proof).", ephemeral=True)

    @app_commands.command(description="(Admin) Remove a vouch by ID.")
    async def removevouch(self, interaction: discord.Interaction, vouch_id: int):
        if not settings.is_admin(interaction.user):
            await interaction.response.send_message("Admins only.", ephemeral=True)
            return
        v = db.get_vouch(vouch_id)
        if not v:
            await interaction.response.send_message(
                f"No vouch `#{vouch_id}`.", ephemeral=True)
            return
        db.remove_vouch(vouch_id)
        # Recompute the target's roles (they may drop a tier).
        target = interaction.guild.get_member(v["target_id"])
        if target:
            await helpers.apply_progression(target)
        await interaction.response.send_message(
            f"Vouch `#{vouch_id}` removed and roles recalculated.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Vouch(bot))
