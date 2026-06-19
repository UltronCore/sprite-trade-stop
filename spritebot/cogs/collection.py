"""
Collection lookup — reads the EXISTING sprite roles (assigned via Discord
Onboarding) instead of tracking collection in the DB.

  /whohas <sprite> [gold]   — members holding that sprite role
  /whoneeds <sprite>        — members lacking it (trade targets)
  /match                    — pairs where one HAS what another NEEDS

Also keeps #sprite-list and #gold-zp-list auto-updated (the timed refresh loop
lives in the Admin cog; this cog exposes the rebuild + a slash to force it).
"""

import discord
from discord import app_commands
from discord.ext import commands

from .. import config, settings


def _sprite_choices():
    return [app_commands.Choice(name=s, value=s) for s in config.SPRITE_ROLES]


class Collection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def _ensure_chunked(guild: discord.Guild):
        """Guarantee the full member list is cached before reading role.members
        / guild.members, otherwise results would be silently incomplete."""
        if not guild.chunked:
            try:
                await guild.chunk()
            except Exception:
                pass

    @staticmethod
    def _participating_ids(guild: discord.Guild) -> set:
        """Members who hold at least one sprite role (i.e. completed onboarding).

        Used to scope 'who needs X' to real participants — a member who never
        picked any sprite role isn't genuinely 'missing everything', they just
        haven't onboarded, and listing them produces false trade targets."""
        ids = set()
        for sprite in config.SPRITE_ROLES:
            for gold in (False, True):
                role = settings.sprite_role(guild, sprite, gold=gold)
                if role:
                    ids.update(m.id for m in role.members if not m.bot)
        return ids

    @app_commands.command(description="List members who HAVE a sprite.")
    @app_commands.describe(sprite="Which sprite", gold="Gold variant?")
    @app_commands.choices(sprite=_sprite_choices())
    async def whohas(self, interaction: discord.Interaction,
                     sprite: str, gold: bool = False):
        await interaction.response.defer()
        await self._ensure_chunked(interaction.guild)
        role = settings.sprite_role(interaction.guild, sprite, gold=gold)
        label = f"{sprite}{' (Gold)' if gold else ''}"
        if not role:
            await interaction.followup.send(
                f"Role for {label} not found. Run `/setup` or check config.",
                ephemeral=True)
            return
        members = role.members
        if not members:
            await interaction.followup.send(f"Nobody has **{label}** yet.")
            return
        names = ", ".join(m.display_name for m in members[:50])
        more = f" …and {len(members) - 50} more" if len(members) > 50 else ""
        embed = discord.Embed(
            title=f"🟢 Holders of {label} ({len(members)})",
            description=names + more, color=discord.Color.green())
        await interaction.followup.send(embed=embed)

    @app_commands.command(description="List members who NEED a sprite (don't have it).")
    @app_commands.choices(sprite=_sprite_choices())
    async def whoneeds(self, interaction: discord.Interaction, sprite: str):
        await interaction.response.defer()
        await self._ensure_chunked(interaction.guild)
        role = settings.sprite_role(interaction.guild, sprite, gold=False)
        if not role:
            await interaction.followup.send(
                f"Role for {sprite} not found.", ephemeral=True)
            return
        haves = {m.id for m in role.members}
        participating = self._participating_ids(interaction.guild)
        # Only count members who've onboarded (hold ≥1 sprite role) as "needing"
        # it — avoids flagging everyone who never picked any roles.
        needs = [m for m in interaction.guild.members
                 if not m.bot and m.id not in haves and m.id in participating]
        names = ", ".join(m.display_name for m in needs[:50])
        more = f" …and {len(needs) - 50} more" if len(needs) > 50 else ""
        embed = discord.Embed(
            title=f"🔴 Need {sprite} ({len(needs)})",
            description=names or "Every active collector has it! 🎉",
            color=discord.Color.red())
        embed.set_footer(text=(more + " · " if more else "")
                         + "only members who picked sprite roles are shown")
        await interaction.followup.send(embed=embed)

    @app_commands.command(description="Find HAVE↔NEED matches for a sprite.")
    @app_commands.choices(sprite=_sprite_choices())
    async def match(self, interaction: discord.Interaction, sprite: str):
        await interaction.response.defer()
        await self._ensure_chunked(interaction.guild)
        role = settings.sprite_role(interaction.guild, sprite, gold=False)
        if not role:
            await interaction.followup.send(
                f"Role for {sprite} not found.", ephemeral=True)
            return
        haves = [m for m in role.members if not m.bot]
        have_ids = {m.id for m in haves}
        participating = self._participating_ids(interaction.guild)
        needs = [m for m in interaction.guild.members
                 if not m.bot and m.id not in have_ids and m.id in participating]
        if not haves or not needs:
            await interaction.followup.send(
                f"No matches possible for {sprite} right now "
                f"({len(haves)} have, {len(needs)} need).")
            return
        lines = []
        for i in range(min(len(haves), len(needs), 10)):
            lines.append(f"🤝 **{haves[i].display_name}** can help "
                         f"**{needs[i].display_name}**")
        embed = discord.Embed(
            title=f"🔁 {sprite} matches",
            description="\n".join(lines),
            color=discord.Color.blurple())
        embed.set_footer(text=f"{len(haves)} holders · {len(needs)} seekers")
        await interaction.followup.send(embed=embed)

    @app_commands.command(description="Open the web sprite collection tracker.")
    async def tracker(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎮 Sprites Collection Tracker",
            description=(
                f"Track every sprite — mark **Have / Missing / Mastered**, filter "
                f"by **Normal / Gold / Gummy / Galaxy**, and export a shareable "
                f"image of your collection or wishlist to post in the trade "
                f"channels.\n\n**[Open the tracker]({config.TRACKER_URL})**"
            ),
            color=discord.Color.green(),
        )
        embed.set_footer(text="No login — your collection saves in your browser + share link.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="(Admin) Rebuild the auto sprite lists now.")
    async def refreshlists(self, interaction: discord.Interaction):
        if not settings.is_admin(interaction.user):
            await interaction.response.send_message("Admins only.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        await rebuild_lists(interaction.guild)
        await interaction.followup.send("Lists refreshed.", ephemeral=True)


async def rebuild_lists(guild: discord.Guild):
    """Update #sprite-list and #gold-zp-list from current role membership."""
    # Full sprite holder summary
    sprite_ch = settings.get_channel(guild, "sprite_list")
    if sprite_ch:
        lines = []
        for sprite in config.SPRITE_ROLES:
            base = settings.sprite_role(guild, sprite, gold=False)
            gold = settings.sprite_role(guild, sprite, gold=True)
            bn = len(base.members) if base else 0
            gn = len(gold.members) if gold else 0
            lines.append(f"**{sprite}** — {bn} have · {gn} gold")
        embed = discord.Embed(
            title="📋 Sprite Holdings",
            description="\n".join(lines),
            color=discord.Color.teal())
        embed.set_footer(text="Auto-updated from onboarding roles")
        await _replace_pinned(sprite_ch, embed)

    # Gold Zero Point spotlight list
    gold_ch = settings.get_channel(guild, "gold_zp_list")
    if gold_ch:
        gold_zp = settings.sprite_role(guild, "Zero Point", gold=True)
        members = gold_zp.members if gold_zp else []
        desc = "\n".join(f"⭐ {m.display_name}" for m in members[:80]) \
            or "No Gold Zero Point holders yet."
        embed = discord.Embed(
            title=f"⭐ Gold Zero Point Holders ({len(members)})",
            description=desc, color=discord.Color.gold())
        await _replace_pinned(gold_ch, embed)


async def _replace_pinned(channel: discord.TextChannel, embed: discord.Embed):
    """Edit the bot's own last list message if present, else post a new one."""
    try:
        async for msg in channel.history(limit=20):
            if msg.author == channel.guild.me and msg.embeds:
                await msg.edit(embed=embed)
                return
    except discord.Forbidden:
        return
    await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Collection(bot))
