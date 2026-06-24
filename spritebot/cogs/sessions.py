"""
Sessions — host a custom game / sprite hunt / dust farm that members join.

Reuses the slot-limited "session" pattern from the earlier sprite-help bot, with
the queue cog's persistent button UX: a host opens a session, members click Join
(up to an optional slot limit), and the host can split everyone into teams (for
Sprite Royale customs) and close it.

  /session open <kind> [title] [slots]   open one (posts a Join/Leave board)
  /session list                          open sessions
  /session teams <id> <count>            randomly split the roster into teams
  /session close <id>                    host/admin closes it

Buttons are persistent dynamic items, so they keep working after a restart.
"""

import re

import discord
from discord import app_commands
from discord.ext import commands

from .. import db, settings

KINDS = ["Custom Game", "Sprite Hunting", "Dust Farming", "Bot Lobby", "Other"]


def _name(guild: discord.Guild, user_id: int) -> str:
    m = guild.get_member(user_id)
    return m.display_name if m else f"User {user_id}"


def session_embed(guild: discord.Guild, sess) -> discord.Embed:
    members = db.session_members(sess["id"])
    n = len(members)
    cap = f"/{sess['slots']}" if sess["slots"] else ""
    host = guild.get_member(sess["host_id"])
    roster = "\n".join(
        f"`{i + 1}.` {_name(guild, m['user_id'])}" for i, m in enumerate(members)
    ) or "Nobody yet — click Join!"
    color = discord.Color.purple() if sess["status"] == "open" else discord.Color.dark_grey()
    embed = discord.Embed(
        title=f"🎮 {sess['title'] or sess['kind']} (#{sess['id']})",
        description=roster, color=color)
    embed.add_field(name="Type", value=sess["kind"])
    embed.add_field(name="Players", value=f"{n}{cap}")
    embed.add_field(name="Host", value=host.mention if host else "—")
    embed.add_field(name="Status",
                    value="🟢 Open" if sess["status"] == "open" else "🔴 Closed",
                    inline=False)
    embed.set_footer(text="Click Join to get in · host runs /session teams or close")
    return embed


async def _refresh(interaction, sid):
    sess = db.get_session(sid)
    try:
        if interaction.message and sess:
            await interaction.message.edit(embed=session_embed(interaction.guild, sess))
    except discord.HTTPException:
        pass


class SessionJoinButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"sess:join:(?P<sid>[0-9]+)",
):
    def __init__(self, sid: int):
        self.sid = sid
        super().__init__(discord.ui.Button(
            label="Join", style=discord.ButtonStyle.success, emoji="➕",
            custom_id=f"sess:join:{sid}"))

    @classmethod
    async def from_custom_id(cls, interaction, item, match: re.Match):
        return cls(int(match["sid"]))

    async def callback(self, interaction: discord.Interaction):
        result = db.session_join(self.sid, interaction.user.id)
        msg = {"joined": "✅ You're in!", "exists": "You already joined.",
               "full": "That session is full.", "closed": "That session is closed."}[result]
        await interaction.response.send_message(msg, ephemeral=True)
        if result == "joined":
            await _refresh(interaction, self.sid)


class SessionLeaveButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"sess:leave:(?P<sid>[0-9]+)",
):
    def __init__(self, sid: int):
        self.sid = sid
        super().__init__(discord.ui.Button(
            label="Leave", style=discord.ButtonStyle.secondary, emoji="➖",
            custom_id=f"sess:leave:{sid}"))

    @classmethod
    async def from_custom_id(cls, interaction, item, match: re.Match):
        return cls(int(match["sid"]))

    async def callback(self, interaction: discord.Interaction):
        left = db.session_leave(self.sid, interaction.user.id)
        await interaction.response.send_message(
            "You left." if left else "You weren't in it.", ephemeral=True)
        if left:
            await _refresh(interaction, self.sid)


def session_view(sid: int) -> discord.ui.View:
    v = discord.ui.View(timeout=None)
    v.add_item(SessionJoinButton(sid))
    v.add_item(SessionLeaveButton(sid))
    return v


class Sessions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    session = app_commands.Group(name="session",
                                 description="Host or join a custom game / hunt.")

    @session.command(name="open", description="Open a session others can join.")
    @app_commands.describe(kind="What kind of session",
                           title="Optional title (e.g. 'Trios bot lobby')",
                           slots="Max players (0 = unlimited)")
    @app_commands.choices(kind=[app_commands.Choice(name=k, value=k) for k in KINDS])
    @app_commands.checks.cooldown(3, 30.0)
    async def open_(self, interaction: discord.Interaction,
                    kind: app_commands.Choice[str], title: str = "", slots: int = 0):
        slots = max(0, min(slots, 100))
        sid = db.create_session(interaction.user.id, kind.value, title.strip(), slots)
        db.session_join(sid, interaction.user.id)  # host is auto-joined
        embed = session_embed(interaction.guild, db.get_session(sid))
        msg = await interaction.channel.send(embed=embed, view=session_view(sid))
        db.set_session_message(sid, msg.id)
        await interaction.response.send_message(
            f"Opened session **#{sid}**. Members can click Join above.", ephemeral=True)

    @session.command(name="list", description="Show open sessions.")
    async def list_(self, interaction: discord.Interaction):
        rows = db.open_sessions()
        if not rows:
            await interaction.response.send_message(
                "No open sessions. Start one with `/session open`.", ephemeral=True)
            return
        lines = [f"**#{s['id']}** {s['title'] or s['kind']} — "
                 f"{db.session_member_count(s['id'])}"
                 f"{('/' + str(s['slots'])) if s['slots'] else ''} players "
                 f"(host {_name(interaction.guild, s['host_id'])})"
                 for s in rows]
        await interaction.response.send_message(
            embed=discord.Embed(title="🎮 Open sessions", description="\n".join(lines),
                                color=discord.Color.purple()), ephemeral=True)

    @session.command(name="teams", description="(Host) Split the roster into teams.")
    @app_commands.describe(session_id="Session number", count="How many teams")
    @app_commands.checks.cooldown(3, 15.0)
    async def teams(self, interaction: discord.Interaction, session_id: int, count: int):
        sess = db.get_session(session_id)
        if not sess:
            await interaction.response.send_message("No such session.", ephemeral=True)
            return
        if interaction.user.id != sess["host_id"] and not settings.is_admin(interaction.user):
            await interaction.response.send_message(
                "Only the host or an admin can make teams.", ephemeral=True)
            return
        count = max(2, min(count, 10))
        ids = [m["user_id"] for m in db.session_members(session_id)]
        if len(ids) < count:
            await interaction.response.send_message(
                f"Need at least {count} players (have {len(ids)}).", ephemeral=True)
            return
        # Deterministic shuffle (no Math.random equivalent needed): rotate by id sum.
        ids.sort(key=lambda u: (u * 2654435761) & 0xFFFFFFFF)
        teams = [ids[i::count] for i in range(count)]
        lines = []
        for i, t in enumerate(teams):
            names = ", ".join(
                (interaction.guild.get_member(u).display_name
                 if interaction.guild.get_member(u) else f"<@{u}>") for u in t)
            lines.append(f"**Team {i + 1}** ({len(t)}): {names}")
        embed = discord.Embed(
            title=f"🎲 Teams for {sess['title'] or sess['kind']} (#{session_id})",
            description="\n".join(lines), color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)

    @session.command(name="close", description="(Host) Close a session.")
    async def close_(self, interaction: discord.Interaction, session_id: int):
        sess = db.get_session(session_id)
        if not sess:
            await interaction.response.send_message("No such session.", ephemeral=True)
            return
        if interaction.user.id != sess["host_id"] and not settings.is_admin(interaction.user):
            await interaction.response.send_message(
                "Only the host or an admin can close it.", ephemeral=True)
            return
        db.close_session(session_id)
        try:
            ch = interaction.guild.get_channel_or_thread(interaction.channel_id)
            if sess["message_id"] and ch:
                m = await ch.fetch_message(sess["message_id"])
                await m.edit(embed=session_embed(interaction.guild, db.get_session(session_id)),
                             view=None)
        except discord.HTTPException:
            pass
        await interaction.response.send_message(
            f"Closed session #{session_id}.", ephemeral=True)


async def setup(bot):
    bot.add_dynamic_items(SessionJoinButton, SessionLeaveButton)
    await bot.add_cog(Sessions(bot))
