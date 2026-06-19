"""
Web-tracker integration: sync a member's collection from the web app's share
code, then surface it natively in Discord (images + trade matching).

Web grid = editor → /synccollection imports it → bot stores per-member data and
can render images, list holders, and match trades — all inside Discord.

Commands:
  /synccollection <code>   import your collection from the tracker share code/link
  /mycollection [@user]    post your "My Sprites" image
  /missing [@user]         post your "Looking For" image
  /holders <sprite>        who (that synced) has a given sprite — find a trade
  /spritematch             members who have sprites you're missing
"""

import io

import discord
from discord import app_commands
from discord.ext import commands

from .. import config, db, render, sprites


def _released_choices():
    # Discord limits autocomplete choices to 25; use autocomplete instead of a
    # static choice list since there are 41 released sprites.
    return [s for s in sprites.released()]


class CollectionSync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _sprite_autocomplete(self, interaction: discord.Interaction, current: str):
        cur = current.lower()
        out = []
        for s in sprites.released():
            if cur in s["name"].lower():
                out.append(app_commands.Choice(name=s["name"], value=s["id"]))
            if len(out) >= 25:
                break
        return out

    @app_commands.command(
        description="Import your collection from the web tracker (paste the sync code or link).")
    @app_commands.describe(code="Your share code or full tracker link from the 'Copy sync code' button")
    async def synccollection(self, interaction: discord.Interaction, code: str):
        try:
            status = sprites.decode(code)
        except ValueError:
            await interaction.response.send_message(
                "That doesn't look like a valid sync code. On the tracker, click "
                "**Copy sync code** and paste it here.", ephemeral=True)
            return
        db.set_collection(interaction.user.id, status)
        s = sprites.summarize(status)
        await interaction.response.send_message(
            f"✅ Synced! You have **{s['have']}/{s['total']}** sprites "
            f"({s['mastered']} mastered). Try `/mycollection` or `/missing`.",
            ephemeral=True)

    @app_commands.command(description="Post your collection image (synced from the tracker).")
    async def mycollection(self, interaction: discord.Interaction,
                           user: discord.Member = None):
        await self._post_image(interaction, user, "collection")

    @app_commands.command(description="Post the sprites you still need.")
    async def missing(self, interaction: discord.Interaction,
                      user: discord.Member = None):
        await self._post_image(interaction, user, "missing")

    async def _post_image(self, interaction, user, mode):
        target = user or interaction.user
        if not db.has_collection(target.id):
            who = "You haven't" if target == interaction.user else f"{target.display_name} hasn't"
            await interaction.response.send_message(
                f"{who} synced a collection yet. Use `/synccollection` with the "
                f"code from {config.TRACKER_URL}", ephemeral=True)
            return
        await interaction.response.defer()
        status = db.get_collection(target.id)
        png = render.render_collection(status, target.display_name, mode=mode)
        fname = "my-sprites.png" if mode == "collection" else "looking-for.png"
        s = sprites.summarize(status)
        caption = (f"**{target.display_name}** — {s['have']}/{s['total']} collected"
                   if mode == "collection"
                   else f"**{target.display_name}** is looking for "
                        f"{s['total'] - s['have']} sprites")
        await interaction.followup.send(
            content=caption, file=discord.File(fp=io.BytesIO(png), filename=fname))

    @app_commands.command(description="Who (that synced) has a given sprite?")
    @app_commands.describe(sprite="Sprite name")
    async def holders(self, interaction: discord.Interaction, sprite: str):
        sp = sprites.BY_ID.get(sprite)
        if not sp:
            # allow typing a name directly
            match = next((s for s in sprites.SPRITES
                          if s["name"].lower() == sprite.lower()), None)
            sp = match
        if not sp:
            await interaction.response.send_message("Unknown sprite.", ephemeral=True)
            return
        rows = db.sprite_holders(sp["id"])
        if not rows:
            await interaction.response.send_message(
                f"Nobody who's synced has **{sp['name']}** yet.", ephemeral=True)
            return
        lines = []
        for r in rows[:25]:
            m = interaction.guild.get_member(r["user_id"])
            tag = " 👑" if r["status"] == 2 else ""
            lines.append(f"• {m.mention if m else r['user_id']}{tag}")
        embed = discord.Embed(
            title=f"Holders of {sp['name']} ({len(rows)})",
            description="\n".join(lines), color=discord.Color.green())
        embed.set_footer(text="👑 = mastered · DM to arrange a trade")
        await interaction.response.send_message(embed=embed)

    holders.autocomplete("sprite")(_sprite_autocomplete)

    @app_commands.command(description="Look up a sprite: image, rarity, and who has it.")
    @app_commands.describe(sprite="Sprite name")
    async def spriteinfo(self, interaction: discord.Interaction, sprite: str):
        sp = sprites.BY_ID.get(sprite) or next(
            (s for s in sprites.SPRITES if s["name"].lower() == sprite.lower()), None)
        if not sp:
            await interaction.response.send_message("Unknown sprite.", ephemeral=True)
            return
        rows = db.sprite_holders(sp["id"])
        have = len(rows)
        mastered = sum(1 for r in rows if r["status"] == 2)
        synced = len(db.users_with_collections())
        line = sprites.THEME_LABEL.get(sp["theme"], sp["theme"].title())
        embed = discord.Embed(
            title=sp["name"],
            description=(f"**{sp['rarity']}** · {line} line"
                         + ("  ·  *not in game yet*" if sp.get("unreleased") else "")),
            color=discord.Color.green() if not sp.get("unreleased") else discord.Color.greyple(),
        )
        embed.set_thumbnail(url=f"attachment://{sp['id']}.png")
        if synced:
            embed.add_field(name="Server", value=f"{have}/{synced} have · {mastered} mastered")
            top = []
            for r in rows[:8]:
                m = interaction.guild.get_member(r["user_id"])
                top.append((m.display_name if m else str(r["user_id"]))
                           + (" 👑" if r["status"] == 2 else ""))
            if top:
                embed.add_field(name="Holders", value=", ".join(top), inline=False)
        else:
            embed.set_footer(text="Members /synccollection to see who owns this.")
        file = discord.File(sprites.image_path(sp["id"]), filename=f"{sp['id']}.png")
        await interaction.response.send_message(embed=embed, file=file)

    spriteinfo.autocomplete("sprite")(_sprite_autocomplete)

    @app_commands.command(description="Set one sprite's status in your collection.")
    @app_commands.describe(sprite="Sprite name", status="Your status for it")
    @app_commands.choices(status=[
        app_commands.Choice(name="Missing", value=0),
        app_commands.Choice(name="Have", value=1),
        app_commands.Choice(name="Mastered", value=2),
    ])
    async def spriteset(self, interaction: discord.Interaction, sprite: str,
                        status: app_commands.Choice[int]):
        sp = sprites.BY_ID.get(sprite) or next(
            (s for s in sprites.SPRITES if s["name"].lower() == sprite.lower()), None)
        if not sp:
            await interaction.response.send_message("Unknown sprite.", ephemeral=True)
            return
        db.set_sprite_status(interaction.user.id, sp["id"], status.value)
        s = sprites.summarize(db.get_collection(interaction.user.id))
        await interaction.response.send_message(
            f"Set **{sp['name']}** → {status.name}. You're at "
            f"**{s['have']}/{s['total']}** ({s['mastered']} mastered).",
            ephemeral=True)

    spriteset.autocomplete("sprite")(_sprite_autocomplete)

    @app_commands.command(description="Server-wide sprite collection progress.")
    async def guildprogress(self, interaction: discord.Interaction):
        synced = db.users_with_collections()
        if not synced:
            await interaction.response.send_message(
                f"No collections synced yet. Members: `/synccollection` with the "
                f"code from {config.TRACKER_URL}", ephemeral=True)
            return
        rel = sprites.released()
        total = len(rel)
        lb = db.collection_leaderboard(100)
        avg = sum(r["n"] for r in lb) / len(lb)
        completionists = sum(1 for r in lb if r["n"] >= total)
        counts = db.have_counts()
        # most-needed = released sprites the fewest members have
        needed = sorted(rel, key=lambda s: counts.get(s["id"], 0))[:5]
        need_lines = [f"• **{s['name']}** — {len(synced) - counts.get(s['id'], 0)} still need it"
                      for s in needed]
        embed = discord.Embed(
            title="📊 Server Sprite Progress",
            color=discord.Color.blurple(),
            description=(f"**{len(synced)}** members synced · "
                         f"avg **{avg:.0f}/{total}** collected · "
                         f"**{completionists}** completed all {total} 🏆"),
        )
        embed.add_field(name="Most-needed sprites", value="\n".join(need_lines), inline=False)
        top = []
        for i, r in enumerate(lb[:5]):
            m = interaction.guild.get_member(r["user_id"])
            top.append(f"{['🥇','🥈','🥉','🏅','🏅'][i]} {m.display_name if m else r['user_id']} "
                       f"— {r['n']}/{total}")
        embed.add_field(name="Top collectors", value="\n".join(top), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Find members who have sprites you're missing.")
    async def spritematch(self, interaction: discord.Interaction):
        if not db.has_collection(interaction.user.id):
            await interaction.response.send_message(
                "Sync your collection first with `/synccollection`.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        mine = db.get_collection(interaction.user.id)
        my_missing = {s["id"] for s in sprites.released() if mine.get(s["id"], 0) == 0}
        # tally, per other member, how many of my missing sprites they have
        tally = {}
        for uid in db.users_with_collections():
            if uid == interaction.user.id:
                continue
            theirs = db.get_collection(uid)
            overlap = [sid for sid in my_missing if theirs.get(sid, 0) >= 1]
            if overlap:
                tally[uid] = overlap
        if not tally:
            await interaction.followup.send(
                "No matches yet — more members need to `/synccollection`.", ephemeral=True)
            return
        ranked = sorted(tally.items(), key=lambda kv: len(kv[1]), reverse=True)[:10]
        lines = []
        for uid, ov in ranked:
            m = interaction.guild.get_member(uid)
            sample = ", ".join(sprites.BY_ID[s]["name"] for s in ov[:4])
            more = f" +{len(ov) - 4}" if len(ov) > 4 else ""
            lines.append(f"**{m.display_name if m else uid}** — {len(ov)} "
                         f"({sample}{more})")
        embed = discord.Embed(
            title="🔁 Members who can help your collection",
            description="\n".join(lines), color=discord.Color.blurple())
        embed.set_footer(text="Counts how many of YOUR missing sprites each member has.")
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(CollectionSync(bot))
