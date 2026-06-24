"""
/setup — auto-detect channel and role IDs from inside Discord and save them to
the database (overriding config), so the team doesn't hunt for IDs by hand.

Also hosts the background tasks: daily leaderboard auto-post + periodic
auto-list refresh.
"""

from datetime import time as dt_time
from datetime import timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

from .. import config, db, progression, settings, sprites
from .collection import rebuild_lists
from .collection_sync import build_progress_embed


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.periodic_refresh.start()
        self.daily_leaderboard.start()
        self.weekly_digest.start()
        self.announce_new_releases_once.start()

    def cog_unload(self):
        self.periodic_refresh.cancel()
        self.daily_leaderboard.cancel()
        self.weekly_digest.cancel()
        self.announce_new_releases_once.cancel()

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

        # Distributor role (queue staff) — optional.
        dist = discord.utils.get(guild.roles, name=config.DISTRIBUTOR_ROLE_NAME)
        if dist:
            db.set_setting("role:distributor", dist.id)
            found.append(f"@{dist.name} → distributor")

        # Sprite-news ping role — optional.
        if config.NEWS_PING_ROLE_NAME:
            npr = discord.utils.get(guild.roles, name=config.NEWS_PING_ROLE_NAME)
            if npr:
                db.set_setting("role:news_ping", npr.id)
                found.append(f"@{npr.name} → news_ping")

        # Collector milestone roles (auto-assigned from collections) — optional.
        for spec in config.COLLECTOR_ROLES:
            r = discord.utils.get(guild.roles, name=spec["role"])
            if r:
                db.set_setting(f"role:collector:{spec['role']}", r.id)
                found.append(f"@{r.name} → collector")

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

    # Fixed clock time (18:00 UTC) so it posts once per day at a stable time
    # instead of drifting from process start and double-posting on restarts.
    @tasks.loop(time=dt_time(hour=18, minute=0, tzinfo=timezone.utc))
    async def daily_leaderboard(self):
        for guild in self.bot.guilds:
            try:
                await post_leaderboard(self.bot, guild)
            except Exception as e:
                print(f"[leaderboard] {guild.id}: {e}")

    @daily_leaderboard.before_loop
    async def before_leaderboard(self):
        await self.bot.wait_until_ready()

    # ---- weekly guild sprite digest (opt-in, low-noise) -----------------
    @tasks.loop(hours=config.DIGEST_INTERVAL_HOURS)
    async def weekly_digest(self):
        for guild in self.bot.guilds:
            try:
                if db.get_setting(f"digest_enabled:{guild.id}") != "1":
                    continue
                await post_digest(guild)
            except Exception as e:  # noqa: BLE001 - never kill the loop
                print(f"[digest] {guild.id}: {e}")

    @weekly_digest.before_loop
    async def before_digest(self):
        await self.bot.wait_until_ready()

    # ---- "new sprite released" announcement ----------------------------
    # Sprites have no live API, so the catalog (spritebot/assets/sprites.json)
    # is operator-updated: when you ship a new variant's art and bump the
    # manifest, the bot detects the new released id on next start and announces
    # it once. Deterministic, no scraping. First run just records a baseline.
    @tasks.loop(count=1)
    async def announce_new_releases_once(self):
        current = {s["id"] for s in sprites.released()}
        seen_raw = db.get_setting("seen_released")
        if seen_raw is None:
            db.set_setting("seen_released", ",".join(sorted(current)))
            return
        seen = set(seen_raw.split(",")) if seen_raw else set()
        new_ids = current - seen
        if new_ids:
            for guild in self.bot.guilds:
                try:
                    await post_new_sprites(guild, new_ids)
                except Exception as e:  # noqa: BLE001
                    print(f"[announce] {guild.id}: {e}")
        db.set_setting("seen_released", ",".join(sorted(current)))

    @announce_new_releases_once.before_loop
    async def before_announce(self):
        await self.bot.wait_until_ready()

    @app_commands.command(
        description="(Admin) Re-announce sprites added since the last baseline.")
    async def announcenew(self, interaction: discord.Interaction):
        if not settings.is_admin(interaction.user):
            await interaction.response.send_message("Admins only.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        current = {s["id"] for s in sprites.released()}
        seen_raw = db.get_setting("seen_released") or ""
        new_ids = current - (set(seen_raw.split(",")) if seen_raw else set())
        if not new_ids:
            await interaction.followup.send("No new released sprites to announce.",
                                            ephemeral=True)
            return
        posted = await post_new_sprites(interaction.guild, new_ids)
        db.set_setting("seen_released", ",".join(sorted(current)))
        await interaction.followup.send(
            f"Announced {len(new_ids)} new sprite(s)." if posted else
            "No news/digest channel configured to post in.", ephemeral=True)

    @app_commands.command(description="(Admin) Weekly sprite digest: on / off / now.")
    @app_commands.describe(action="Enable, disable, or post immediately")
    @app_commands.choices(action=[
        app_commands.Choice(name="on", value="on"),
        app_commands.Choice(name="off", value="off"),
        app_commands.Choice(name="now", value="now"),
    ])
    async def digest(self, interaction: discord.Interaction,
                     action: app_commands.Choice[str]):
        if not settings.is_admin(interaction.user):
            await interaction.response.send_message("Admins only.", ephemeral=True)
            return
        gid = interaction.guild.id
        if action.value == "on":
            db.set_setting(f"digest_enabled:{gid}", "1")
            ch = settings.get_channel(interaction.guild, "digest") \
                or settings.get_channel(interaction.guild, "leaderboard")
            where = ch.mention if ch else "the leaderboard channel (set a #sprite-digest channel + /setup)"
            await interaction.response.send_message(
                f"✅ Weekly sprite digest **enabled** → posts to {where}.", ephemeral=True)
        elif action.value == "off":
            db.set_setting(f"digest_enabled:{gid}", "0")
            await interaction.response.send_message(
                "Weekly digest **disabled**.", ephemeral=True)
        else:  # now
            await interaction.response.defer(ephemeral=True)
            posted = await post_digest(interaction.guild)
            await interaction.followup.send(
                "Digest posted." if posted else
                "Nobody's synced a collection yet, or no digest/leaderboard "
                "channel is configured.", ephemeral=True)


async def post_new_sprites(guild, new_ids) -> bool:
    """Announce newly-released sprites to the news (or digest/leaderboard) channel."""
    ch = (settings.get_channel(guild, "news")
          or settings.get_channel(guild, "digest")
          or settings.get_channel(guild, "leaderboard"))
    if not ch:
        return False
    ping = ""
    if config.NEWS_PING_ROLE_NAME:
        rid = db.get_setting("role:news_ping")
        role = guild.get_role(int(rid)) if rid else \
            settings.get_role_by_name(guild, config.NEWS_PING_ROLE_NAME)
        if role:
            ping = role.mention
    items = [sprites.BY_ID[i] for i in new_ids if i in sprites.BY_ID]
    items.sort(key=lambda s: s["name"])
    lines = [f"• **{s['name']}** ({s['rarity']})" for s in items[:25]]
    embed = discord.Embed(
        title=f"🆕 {len(items)} new sprite{'s' if len(items) != 1 else ''} released!",
        description="\n".join(lines) + f"\n\nTrack them on the tracker: {config.TRACKER_URL}",
        color=discord.Color.gold())
    embed.set_footer(text="Update your collection with /synccollection or /spriteset")
    # Show the first new sprite's art if we have it.
    first = items[0]["id"] if items else None
    mentions = discord.AllowedMentions(roles=True) if ping else discord.AllowedMentions.none()
    if first and sprites.image_path(first).exists():
        file = discord.File(sprites.image_path(first), filename=f"{first}.png")
        embed.set_thumbnail(url=f"attachment://{first}.png")
        await ch.send(content=ping or None, embed=embed, file=file, allowed_mentions=mentions)
    else:
        await ch.send(content=ping or None, embed=embed, allowed_mentions=mentions)
    return True


async def post_digest(guild) -> bool:
    """Post the weekly guild sprite digest. Returns True if it actually posted."""
    ch = settings.get_channel(guild, "digest") \
        or settings.get_channel(guild, "leaderboard")
    if not ch:
        return False
    embed = build_progress_embed(guild, title="📰 Weekly Sprite Digest")
    if embed is None:
        return False
    embed.set_footer(text="Sync with /synccollection · turn this off with /digest off")
    await ch.send(embed=embed)
    return True


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
