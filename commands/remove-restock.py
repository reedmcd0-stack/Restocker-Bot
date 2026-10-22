
import asyncio
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

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

STOCK_DIR = Path("generator_data") / "stock"
locks = {}
SERVICE_CHOICES = [
    app_commands.Choice(name=service, value=str(index))
    for index, service in enumerate(SERVICES)
]


class RemoveRestock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        STOCK_DIR.mkdir(parents=True, exist_ok=True)

    @app_commands.command(
        name="remove-restock",
        description="Remove entries from a service's stock"
    )
    @app_commands.describe(
        service="Service to remove stock from",
        quantity="Number of entries to remove"
    )
    @app_commands.choices(service=SERVICE_CHOICES)
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_restock(
        self,
        interaction: discord.Interaction,
        service: app_commands.Choice[str],
        quantity: app_commands.Range[int, 1, 1000],
    ):
        index = int(service.value)
        path = STOCK_DIR / f"{index}.txt"
        lock = locks.setdefault(index, asyncio.Lock())

        async with lock:
            if not path.exists():
                await interaction.response.send_message(
                    f"No stock file exists for {SERVICES[index]}.",
                    ephemeral=True,
                )
                return

            lines = [
                line.strip()
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            removed = min(quantity, len(lines))
            remaining = lines[removed:]

            path.write_text(
                "".join(line + "\n" for line in remaining),
                encoding="utf-8",
            )

        await interaction.response.send_message(
            f"Removed {removed} entries from **{SERVICES[index]}**. "
            f"Remaining entries: {len(remaining)}.",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(RemoveRestock(bot))

