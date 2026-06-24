"""
Sprite hand-off queues.

A distributor (staff) gives sprites to members one at a time. Members wait in a
fair FIFO line for a specific sprite (e.g. Galaxy Zero Point) or a general
queue. Queues are CLOSED by default — an admin opens only the ones worth
queueing (usually rare sprites), matching how the community already runs it.

Two ways to use it, so it's frictionless in Discord:
  • Buttons:  /queue board <sprite>  posts an embed with Join / Leave buttons
    members just click (works after restarts via persistent dynamic items).
  • Commands: /queue join | leave | mine | list, and for staff
    /queue next | done | skip | open | close.

When a distributor marks /queue done, the bot also flips that sprite to "Have"
in the member's synced collection and nudges them to vouch.
"""

import re

import discord
from discord import app_commands
from discord.ext import commands

from .. import collector, config, db, helpers, settings, sprites


def _label(sprite_id: str) -> str:
    if sprite_id == config.QUEUE_GENERAL_ID:
        return config.QUEUE_GENERAL_LABEL
    sp = sprites.BY_ID.get(sprite_id)
    return sp["name"] if sp else sprite_id


def _resolve(value: str):
    """Map an autocomplete value / typed name to a queue sprite_id, or None."""
    if value == config.QUEUE_GENERAL_ID:
        return config.QUEUE_GENERAL_ID
    if value in sprites.BY_ID:
        return value
    match = next((s for s in sprites.SPRITES if s["name"].lower() == value.lower()), None)
    return match["id"] if match else None


async def _queue_autocomplete(interaction, current: str):
    cur = current.lower()
    out = [app_commands.Choice(name="🌐 " + config.QUEUE_GENERAL_LABEL,
                               value=config.QUEUE_GENERAL_ID)]
    for s in sprites.released():
        if cur in s["name"].lower():
            out.append(app_commands.Choice(name=s["name"], value=s["id"]))
        if len(out) >= 25:
            break
    return out


def queue_embed(guild: discord.Guild, sprite_id: str) -> discord.Embed:
    rows = db.queue_list(sprite_id, limit=15)
    total = db.queue_length(sprite_id)
    is_open = db.is_queue_open(sprite_id)
    lines = []
    for i, r in enumerate(rows):
        m = guild.get_member(r["user_id"])
        name = m.display_name if m else f"User {r['user_id']}"
        lines.append(f"`{i + 1}.` {name}")
    more = f"\n…and {total - 15} more" if total > 15 else ""
    embed = discord.Embed(
        title=f"📋 Queue — {_label(sprite_id)}",
        description=(("\n".join(lines) + more) if lines else "Nobody in line yet — be first!"),
        color=discord.Color.green() if is_open else discord.Color.dark_grey(),
    )
    embed.add_field(name="In line", value=str(total))
    embed.add_field(name="Status", value="🟢 Open" if is_open else "🔴 Closed")
    embed.set_footer(text="Click Join to enter the line · distributors deliver in order")
    return embed


# --- persistent Join/Leave buttons (survive restarts via DynamicItem) -------
class QueueJoinButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"queue:join:(?P<sprite>[a-z0-9_]+)",
):
    def __init__(self, sprite_id: str):
        self.sprite_id = sprite_id
        super().__init__(discord.ui.Button(
            label="Join queue", style=discord.ButtonStyle.success,
            emoji="➕", custom_id=f"queue:join:{sprite_id}"))

    @classmethod
    async def from_custom_id(cls, interaction, item, match: re.Match):
        return cls(match["sprite"])

    async def callback(self, interaction: discord.Interaction):
        await _do_join(interaction, self.sprite_id)


class QueueLeaveButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"queue:leave:(?P<sprite>[a-z0-9_]+)",
):
    def __init__(self, sprite_id: str):
        self.sprite_id = sprite_id
        super().__init__(discord.ui.Button(
            label="Leave", style=discord.ButtonStyle.secondary,
            emoji="➖", custom_id=f"queue:leave:{sprite_id}"))

    @classmethod
    async def from_custom_id(cls, interaction, item, match: re.Match):
        return cls(match["sprite"])

    async def callback(self, interaction: discord.Interaction):
        if db.queue_remove(self.sprite_id, interaction.user.id):
            await interaction.response.send_message(
                f"You left the **{_label(self.sprite_id)}** queue.", ephemeral=True)
            await _refresh_board(interaction, self.sprite_id)
        else:
            await interaction.response.send_message(
                "You weren't in that queue.", ephemeral=True)


def board_view(sprite_id: str) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    view.add_item(QueueJoinButton(sprite_id))
    view.add_item(QueueLeaveButton(sprite_id))
    return view


async def _refresh_board(interaction: discord.Interaction, sprite_id: str):
    """Update the board embed the button lives on, if it's a board message."""
    try:
        if interaction.message and interaction.message.embeds:
            await interaction.message.edit(embed=queue_embed(interaction.guild, sprite_id))
    except discord.HTTPException:
        pass


async def _do_join(interaction: discord.Interaction, sprite_id: str):
    member = interaction.user
    ok, reason = helpers.eligible_to_vouch(member)  # reuse blacklist+age+tenure gate
    if not ok:
        await interaction.response.send_message(reason, ephemeral=True)
        return
    if not db.is_queue_open(sprite_id):
        await interaction.response.send_message(
            f"The **{_label(sprite_id)}** queue is closed right now.", ephemeral=True)
        return
    if db.queue_position(sprite_id, member.id) is None \
            and db.queue_user_count(member.id) >= config.MAX_QUEUES_PER_USER:
        await interaction.response.send_message(
            f"You're already in {config.MAX_QUEUES_PER_USER} queues (the max). "
            f"Leave one first.", ephemeral=True)
        return
    state = db.queue_add(sprite_id, member.id)
    pos = db.queue_position(sprite_id, member.id)
    if state == "exists":
        await interaction.response.send_message(
            f"You're already in the **{_label(sprite_id)}** queue at position "
            f"**#{pos}**.", ephemeral=True)
        return
    await interaction.response.send_message(
        f"✅ Joined the **{_label(sprite_id)}** queue — you're **#{pos}**. "
        f"A distributor will ping you when it's your turn.", ephemeral=True)
    await _refresh_board(interaction, sprite_id)


class Queue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    queue = app_commands.Group(name="queue",
                               description="Wait in line for a sprite hand-off.")

    # ---- members --------------------------------------------------------
    @queue.command(name="join", description="Join the line for a sprite.")
    @app_commands.describe(sprite="Which sprite (or General)")
    @app_commands.checks.cooldown(4, 20.0)
    async def join(self, interaction: discord.Interaction, sprite: str):
        sid = _resolve(sprite)
        if not sid:
            await interaction.response.send_message("Unknown sprite.", ephemeral=True)
            return
        await _do_join(interaction, sid)

    @queue.command(name="leave", description="Leave a queue you're in.")
    @app_commands.describe(sprite="Which queue to leave")
    async def leave(self, interaction: discord.Interaction, sprite: str):
        sid = _resolve(sprite)
        if sid and db.queue_remove(sid, interaction.user.id):
            await interaction.response.send_message(
                f"You left the **{_label(sid)}** queue.", ephemeral=True)
        else:
            await interaction.response.send_message(
                "You weren't in that queue.", ephemeral=True)

    @queue.command(name="mine", description="Show every queue you're in + positions.")
    async def mine(self, interaction: discord.Interaction):
        rows = db.queue_user_entries(interaction.user.id)
        if not rows:
            await interaction.response.send_message(
                "You're not in any queues. Use `/queue join`.", ephemeral=True)
            return
        lines = [f"• **{_label(r['sprite_id'])}** — position "
                 f"**#{db.queue_position(r['sprite_id'], interaction.user.id)}** "
                 f"of {db.queue_length(r['sprite_id'])}" for r in rows]
        embed = discord.Embed(title="📋 Your queues", description="\n".join(lines),
                              color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @queue.command(name="list", description="Show who's in a queue.")
    @app_commands.describe(sprite="Which queue")
    @app_commands.checks.cooldown(4, 15.0)
    async def list_(self, interaction: discord.Interaction, sprite: str):
        sid = _resolve(sprite)
        if not sid:
            await interaction.response.send_message("Unknown sprite.", ephemeral=True)
            return
        await interaction.response.send_message(
            embed=queue_embed(interaction.guild, sid), view=board_view(sid))

    # ---- distributors / admins -----------------------------------------
    @queue.command(name="open", description="(Staff) Open a queue for joining + post a board.")
    @app_commands.describe(sprite="Which sprite queue to open")
    async def open_(self, interaction: discord.Interaction, sprite: str):
        if not settings.is_distributor(interaction.user):
            await interaction.response.send_message("Distributors only.", ephemeral=True)
            return
        sid = _resolve(sprite)
        if not sid:
            await interaction.response.send_message("Unknown sprite.", ephemeral=True)
            return
        db.queue_open(sid)
        channel = settings.get_channel(interaction.guild, "queue") or interaction.channel
        await channel.send(embed=queue_embed(interaction.guild, sid), view=board_view(sid))
        await interaction.response.send_message(
            f"🟢 Opened the **{_label(sid)}** queue in {channel.mention}.", ephemeral=True)

    @queue.command(name="close", description="(Staff) Close a queue.")
    @app_commands.describe(sprite="Which sprite queue to close",
                           clear="Also remove everyone from the line?")
    async def close_(self, interaction: discord.Interaction, sprite: str,
                     clear: bool = False):
        if not settings.is_distributor(interaction.user):
            await interaction.response.send_message("Distributors only.", ephemeral=True)
            return
        sid = _resolve(sprite)
        if not sid:
            await interaction.response.send_message("Unknown sprite.", ephemeral=True)
            return
        db.queue_close(sid)
        if clear:
            for r in db.queue_list(sid, limit=10000):
                db.queue_remove(sid, r["user_id"])
        await interaction.response.send_message(
            f"🔴 Closed the **{_label(sid)}** queue{' and cleared the line' if clear else ''}.",
            ephemeral=True)

    @queue.command(name="next", description="(Staff) Ping the next member in line.")
    @app_commands.describe(sprite="Which queue")
    async def next_(self, interaction: discord.Interaction, sprite: str):
        if not settings.is_distributor(interaction.user):
            await interaction.response.send_message("Distributors only.", ephemeral=True)
            return
        sid = _resolve(sprite)
        if not sid:
            await interaction.response.send_message("Unknown sprite.", ephemeral=True)
            return
        head = db.queue_head(sid)
        if not head:
            await interaction.response.send_message(
                f"The **{_label(sid)}** queue is empty.", ephemeral=True)
            return
        member = interaction.guild.get_member(head["user_id"])
        mention = member.mention if member else f"<@{head['user_id']}>"
        await interaction.response.send_message(
            f"🔔 {mention} — you're up for **{_label(sid)}**! "
            f"{interaction.user.mention} will deliver it. "
            f"Distributor: mark `/queue done` when finished.",
            allowed_mentions=discord.AllowedMentions(users=True))

    @queue.command(name="done", description="(Staff) Mark a member served (removes them).")
    @app_commands.describe(sprite="Which queue", member="Who you delivered to")
    async def done(self, interaction: discord.Interaction, sprite: str,
                   member: discord.Member):
        if not settings.is_distributor(interaction.user):
            await interaction.response.send_message("Distributors only.", ephemeral=True)
            return
        sid = _resolve(sprite)
        if not sid:
            await interaction.response.send_message("Unknown sprite.", ephemeral=True)
            return
        db.queue_remove(sid, member.id)
        # Bonus: if they have a synced collection and this is a real sprite,
        # flip it to "have" automatically.
        note = ""
        if sid != config.QUEUE_GENERAL_ID and db.has_collection(member.id):
            if db.get_collection(member.id).get(sid, 0) < 1:
                db.set_sprite_status(member.id, sid, sprites.HAVE)
                await collector.apply_collector_roles(member)
                note = " (marked in their collection ✅)"
        await interaction.response.send_message(
            f"✅ Delivered **{_label(sid)}** to {member.mention}{note}. "
            f"{member.mention}, please `/vouch {interaction.user.display_name}`!",
            allowed_mentions=discord.AllowedMentions(users=[member]))

    @queue.command(name="skip", description="(Staff) Remove a no-show from a queue.")
    @app_commands.describe(sprite="Which queue", member="Who to remove")
    async def skip(self, interaction: discord.Interaction, sprite: str,
                   member: discord.Member):
        if not settings.is_distributor(interaction.user):
            await interaction.response.send_message("Distributors only.", ephemeral=True)
            return
        sid = _resolve(sprite)
        if sid and db.queue_remove(sid, member.id):
            await interaction.response.send_message(
                f"Removed {member.mention} from the **{_label(sid)}** queue.",
                ephemeral=True)
        else:
            await interaction.response.send_message(
                "They weren't in that queue.", ephemeral=True)

    @queue.command(name="board", description="Post a live Join/Leave board for a queue.")
    @app_commands.describe(sprite="Which queue")
    async def board(self, interaction: discord.Interaction, sprite: str):
        sid = _resolve(sprite)
        if not sid:
            await interaction.response.send_message("Unknown sprite.", ephemeral=True)
            return
        await interaction.response.send_message(
            embed=queue_embed(interaction.guild, sid), view=board_view(sid))

    # autocomplete wiring
    for _cmd in (join, leave, list_, open_, close_, next_, done, skip, board):
        _cmd.autocomplete("sprite")(_queue_autocomplete)


async def setup(bot):
    # Register the persistent dynamic buttons so boards keep working after restart.
    bot.add_dynamic_items(QueueJoinButton, QueueLeaveButton)
    await bot.add_cog(Queue(bot))
