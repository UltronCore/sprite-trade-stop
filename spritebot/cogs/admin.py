"""
/setup — auto-detect channel and role IDs from inside Discord and save them to
the database (overriding config), so the team doesn't hunt for IDs by hand.

Also hosts the background tasks: daily leaderboard auto-post + periodic
auto-list refresh.
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks

from .. import config, db, progression, settings
from .collection import rebuild_lists


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.periodic_refresh.start()
        self.daily_leaderboard.start()

    def cog_unload(self):
        self.periodic_refresh.cancel()
        self.daily_leaderboard.cancel()

    # ---- /setup ---------------------------------------------------------
    @app_commands.command(
        description="(Admin) Auto-detect channels & roles by name and save them.")
    async def setup(self, interaction: discord.Interaction):
        if not settings.is_admin(interaction.user):
            await interaction.response.send_message("Admins only.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        found, missing = [], []

        # Channels — match by configured name.
        for key, name in config.CHANNELS.items():
            ch = discord.utils.get(guild.text_channels, name=name) \
                if isinstance(name, str) else guild.get_channel(name)
            if ch:
                db.set_setting(f"channel:{key}", ch.id)
                found.append(f"#{ch.name} → `{key}`")
            else:
                missing.append(f"channel `{key}` (looking for “{name}”)")

        # Owner / Admin permission roles (resolved to IDs to prevent name spoofing).
        for key, role_name in (("owner", config.OWNER_ROLE_NAME),
                               ("admin", config.ADMIN_ROLE_NAME)):
            r = discord.utils.get(guild.roles, name=role_name)
            if r:
                db.set_setting(f"role:{key}", r.id)
                found.append(f"@{r.name} → {key}")
            # Not flagged as missing — these roles are optional.

        # Verified-trader role.
        vt = discord.utils.get(guild.roles, name=config.VERIFIED_TRADER_ROLE_NAME)
        if vt:
            db.set_setting("role:verified_trader", vt.id)
            found.append(f"@{vt.name} → verified_trader")
        else:
            missing.append(f"role `{config.VERIFIED_TRADER_ROLE_NAME}`")

        # Flair roles.
        for name in progression.all_flair_names():
            r = discord.utils.get(guild.roles, name=name)
            if r:
                db.set_setting(f"role:flair:{name}", r.id)
                found.append(f"@{r.name} → flair:{name}")
            else:
                missing.append(f"flair role `{name}`")

        # Sprite roles (base + gold).
        for sprite, spec in config.SPRITE_ROLES.items():
            for variant in ("base", "gold"):
                r = discord.utils.get(guild.roles, name=spec[variant])
                if r:
                    db.set_setting(f"role:sprite:{sprite}:{variant}", r.id)
                else:
                    missing.append(f"sprite role `{spec[variant]}`")

        # Keep each field under Discord's 1024-char limit while showing as much
        # as fits (there can be ~30 found entries: 7 channels + perms + flairs +
        # 14 sprite roles).
        def _clip(lines):
            out, total = [], 0
            for ln in lines:
                if total + len(ln) + 1 > 1000:
                    out.append(f"…and {len(lines) - len(out)} more")
                    break
                out.append(ln)
                total += len(ln) + 1
            return "\n".join(out) or "—"

        embed = discord.Embed(title="🔧 Setup results", color=discord.Color.green())
        embed.add_field(name=f"✅ Found ({len(found)})",
                        value=_clip(found), inline=False)
        if missing:
            embed.add_field(name=f"⚠️ Missing ({len(missing)})",
                            value=_clip(missing), inline=False)
            embed.set_footer(
                text="Create the missing channels/roles (matching the names in "
                     "config.py) and run /setup again.")
        embed.color = discord.Color.green() if not missing else discord.Color.orange()
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(description="(Admin) Post the leaderboard now.")
    async def postleaderboard(self, interaction: discord.Interaction):
        if not settings.is_admin(interaction.user):
            await interaction.response.send_message("Admins only.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        await post_leaderboard(self.bot, interaction.guild)
        await interaction.followup.send("Leaderboard posted.", ephemeral=True)

    # ---- background refresh (lists + daily-ish leaderboard) -------------
    @tasks.loop(minutes=config.LIST_REFRESH_MINUTES)
    async def periodic_refresh(self):
        for guild in self.bot.guilds:
            try:
                await rebuild_lists(guild)
            except Exception as e:  # never let the loop die
                print(f"[refresh] {guild.id}: {e}")

    @periodic_refresh.before_loop
    async def before_refresh(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=24)
    async def daily_leaderboard(self):
        for guild in self.bot.guilds:
            try:
                await post_leaderboard(self.bot, guild)
            except Exception as e:
                print(f"[leaderboard] {guild.id}: {e}")

    @daily_leaderboard.before_loop
    async def before_leaderboard(self):
        await self.bot.wait_until_ready()


async def post_leaderboard(bot, guild):
    ch = settings.get_channel(guild, "leaderboard")
    if not ch:
        return
    rows = db.leaderboard(10)
    if not rows:
        return
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    lines = []
    for i, r in enumerate(rows):
        m = guild.get_member(r["target_id"])
        name = m.display_name if m else f"User {r['target_id']}"
        lines.append(f"{medals[i]} **{name}** — {r['n']} vouches "
                     f"({progression.flair_for(r['n'])})")
    embed = discord.Embed(title="🏆 Daily Trader Leaderboard",
                          description="\n".join(lines),
                          color=discord.Color.gold())
    await ch.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Admin(bot))
