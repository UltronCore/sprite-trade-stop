"""
Control panel ("hub") — a pinned, persistent message of buttons so members can
do the common things by CLICKING instead of typing slash commands. Posted with
/panel (admin). Buttons use static custom_ids and the view is re-registered on
startup, so they keep working after a restart.

Buttons:
  📇 My Collection  — posts your collection image (ephemeral)
  🔎 Find Trades    — members who have what you're missing (ephemeral)
  📋 My Queues      — the queues you're in + positions (ephemeral)
  ➕ Join a Queue   — a dropdown of open queues to join (ephemeral)
  🔄 Sync           — paste your tracker code in a pop-up form (modal)
  🎮 Open Tracker   — link button to the web tracker
"""

import io

import discord
from discord import app_commands
from discord.ext import commands

from .. import collector, config, db, render, settings, sprites
from .collection_sync import find_matches
from .queue import _do_join, _label


class SyncModal(discord.ui.Modal, title="Sync your collection"):
    code = discord.ui.TextInput(
        label="Paste your sync code",
        placeholder="Open the tracker → Copy sync code → paste it here",
        max_length=200,
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            status = sprites.decode(str(self.code))
        except ValueError:
            await interaction.response.send_message(
                "That code isn't valid. On the tracker, click **Copy sync code** "
                f"and paste it here. {config.TRACKER_URL}", ephemeral=True)
            return
        db.set_collection(interaction.user.id, status)
        await collector.apply_collector_roles(interaction.user)
        s = sprites.summarize(status)
        await interaction.response.send_message(
            f"✅ Synced! You have **{s['have']}/{s['total']}** sprites "
            f"({s['mastered']} mastered). Use the panel to view or find trades.",
            ephemeral=True)


class JoinQueueSelect(discord.ui.Select):
    def __init__(self, open_ids: list):
        options = [
            discord.SelectOption(
                label=_label(sid)[:100],
                value=sid,
                emoji="🌐" if sid == config.QUEUE_GENERAL_ID else "📋")
            for sid in open_ids[:25]
        ]
        super().__init__(placeholder="Pick a queue to join…", options=options)

    async def callback(self, interaction: discord.Interaction):
        await _do_join(interaction, self.values[0])


class HubView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # URL button (no custom_id needed; exempt from persistence rules).
        self.add_item(discord.ui.Button(
            label="Open Tracker", emoji="🎮", style=discord.ButtonStyle.link,
            url=config.TRACKER_URL, row=2))

    @discord.ui.button(label="My Collection", emoji="📇",
                       style=discord.ButtonStyle.primary, custom_id="hub:collection", row=0)
    async def my_collection(self, interaction: discord.Interaction, button):
        if not db.has_collection(interaction.user.id):
            await interaction.response.send_message(
                f"You haven't synced yet — click **🔄 Sync** below, or use the "
                f"tracker: {config.TRACKER_URL}", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        status = db.get_collection(interaction.user.id)
        png = render.render_collection(status, interaction.user.display_name, "collection")
        await interaction.followup.send(
            file=discord.File(io.BytesIO(png), filename="my-sprites.png"), ephemeral=True)

    @discord.ui.button(label="Find Trades", emoji="🔎",
                       style=discord.ButtonStyle.success, custom_id="hub:find", row=0)
    async def find_trades(self, interaction: discord.Interaction, button):
        if not db.has_collection(interaction.user.id):
            await interaction.response.send_message(
                "Sync your collection first (🔄 Sync) so the bot knows what you need.",
                ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        ranked = find_matches(interaction.user.id)
        if not ranked:
            await interaction.followup.send(
                "No matches yet — more members need to sync their collections.",
                ephemeral=True)
            return
        lines = []
        for uid, ov in ranked:
            m = interaction.guild.get_member(uid)
            sample = ", ".join(sprites.BY_ID[s]["name"] for s in ov[:4])
            more = f" +{len(ov) - 4}" if len(ov) > 4 else ""
            lines.append(f"**{m.display_name if m else uid}** — {len(ov)} ({sample}{more})")
        embed = discord.Embed(title="🔁 Members who can help your collection",
                              description="\n".join(lines), color=discord.Color.blurple())
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="My Queues", emoji="📋",
                       style=discord.ButtonStyle.secondary, custom_id="hub:myqueues", row=0)
    async def my_queues(self, interaction: discord.Interaction, button):
        rows = db.queue_user_entries(interaction.user.id)
        if not rows:
            await interaction.response.send_message(
                "You're not in any queues. Use **➕ Join a Queue**.", ephemeral=True)
            return
        lines = [f"• **{_label(r['sprite_id'])}** — #"
                 f"{db.queue_position(r['sprite_id'], interaction.user.id)} of "
                 f"{db.queue_length(r['sprite_id'])}" for r in rows]
        await interaction.response.send_message(
            embed=discord.Embed(title="📋 Your queues", description="\n".join(lines),
                                color=discord.Color.green()), ephemeral=True)

    @discord.ui.button(label="Join a Queue", emoji="➕",
                       style=discord.ButtonStyle.success, custom_id="hub:joinq", row=1)
    async def join_queue(self, interaction: discord.Interaction, button):
        open_ids = db.open_queue_ids()
        if not open_ids:
            await interaction.response.send_message(
                "No queues are open right now. Staff open them for rare sprites.",
                ephemeral=True)
            return
        view = discord.ui.View(timeout=120)
        view.add_item(JoinQueueSelect(open_ids))
        await interaction.response.send_message(
            "Pick a queue to join:", view=view, ephemeral=True)

    @discord.ui.button(label="Sync", emoji="🔄",
                       style=discord.ButtonStyle.secondary, custom_id="hub:sync", row=1)
    async def sync(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(SyncModal())


class Hub(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="(Admin) Post the member control panel.")
    async def panel(self, interaction: discord.Interaction):
        if not settings.is_admin(interaction.user):
            await interaction.response.send_message("Admins only.", ephemeral=True)
            return
        embed = discord.Embed(
            title="🦙 Sprite Trade Stop — Control Panel",
            description=(
                "Everything in one click:\n\n"
                "📇 **My Collection** — your collection image\n"
                "🔎 **Find Trades** — who has what you're missing\n"
                "📋 **My Queues** — your spots in line\n"
                "➕ **Join a Queue** — hop into an open hand-off queue\n"
                "🔄 **Sync** — import your collection from the tracker\n"
                "🎮 **Open Tracker** — mark your sprites on the web\n\n"
                "New here? Mark your sprites on the tracker, hit **Copy sync code**, "
                "then click **🔄 Sync**."),
            color=discord.Color.blurple())
        await interaction.channel.send(embed=embed, view=HubView())
        await interaction.response.send_message(
            "Panel posted — pin it so members always have it. 📌", ephemeral=True)


async def setup(bot):
    bot.add_view(HubView())   # persistent: buttons work after restarts
    await bot.add_cog(Hub(bot))
