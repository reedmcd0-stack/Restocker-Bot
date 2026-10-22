
import discord
from discord import app_commands
from discord.ext import commands

BANNER_URL = (
    "https://cdn.discordapp.com/attachments/"
    "1561171049004146724/1561368448808779826/"
    "IMG_20261018_152036.png"
    "?ex=6ad6192f&is=6ad4c7af"
    "&hm=01337e1cc028d6112dc08b8cabdf7402"
    "de72ba5dda945b8b8d0d3a5be066b7d0"
)

SERVICES = [
    "Paramount+",
    "Disney+",
    "Crunchyroll",
    "Steam",
    "Netflix",
    "Supercell",
    "Eldorado",
    "Epic Games",
    "PlayStation",
    "Roblox",
    "Deezer",
    "Hotmail",
    "Spotify",
    "Prime Video",
    "Cap Cut",
    "Express VPN",
    "Hidive",
    "Dazn",
    "TunnelBear",
    "Hulu",
]

EMBED_COLOR = discord.Color.from_rgb(255, 115, 0)


class Publish(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="publish",
        description="Publish a restock announcement",
    )
    @app_commands.describe(
        service="Choose a service",
        quantity="Restock quantity",
    )
    @app_commands.choices(
        service=[
            app_commands.Choice(name=s, value=s)
            for s in SERVICES
        ]
    )
    async def publish(
        self,
        interaction: discord.Interaction,
        service: app_commands.Choice[str],
        quantity: app_commands.Range[int, 1, 100000],
    ):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "You need the Manage Server permission to use this command.",
                ephemeral=True,
            )
            return

        restock_emoji = discord.utils.get(
            self.bot.emojis, name="restock"
        )
        check_emoji = discord.utils.get(
            self.bot.emojis, name="check"
        )

        restock = str(restock_emoji) if restock_emoji else ":restock:"
        check = str(check_emoji) if check_emoji else ":check"

        embed = discord.Embed(
            title=f"{restock} x{quantity} {service.value} Restocked!",
            description=(
                f"{check} **Service:** {service.value}\n"
                f"{restock} **Quantity:** `x{quantity}`"
            ),
            color=EMBED_COLOR,
        )

        # Banner inside the embed, below the text
        embed.set_image(url=BANNER_URL)

        embed.set_footer(
            text="VantaOperation • Restock System"
        )

        try:
            await interaction.channel.send(
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none(),
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "I cannot send messages or embeds in this channel. "
                "Check my permissions.",
                ephemeral=True,
            )
            return

        except discord.HTTPException:
            await interaction.response.send_message(
                "Discord could not publish the announcement. "
                "Check the banner URL and bot permissions.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"{check} Restock announcement published.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Publish(bot))

