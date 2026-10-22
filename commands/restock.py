
import asyncio
import json
import logging
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger(__name__)

SERVICES = [
    "Crunchyroll",
    "Steam",
    "Netflix",
    "Deezer",
]

DATA = Path("generator_data")
STOCK = DATA / "stock"
PANEL = DATA / "panel.json"

STOCK.mkdir(parents=True, exist_ok=True)

# Dominios reservados para registros de prueba.
ALLOWED_DOMAINS = {
    "gmail.com",
    "hotmail.com",
    "outlook.com",
    "duck.com",
}

stock_lock = asyncio.Lock()


def stock_path(service: str) -> Path:
    return STOCK / f"{SERVICES.index(service)}.txt"


def valid_test_record(line: str) -> bool:
    line = line.strip()

    if ":" not in line:
        return False

    identifier, password = line.split(":", 1)
    identifier = identifier.strip()
    password = password.strip()

    if not identifier or not password:
        return False

    if "@" not in identifier:
        return True

    if identifier.count("@") != 1:
        return False

    email_name, domain = identifier.rsplit("@", 1)

    return (
        bool(email_name)
        and domain.lower() in ALLOWED_DOMAINS
    )


async def refresh_panel(bot: commands.Bot):
    if not PANEL.exists():
        return

    try:
        data = json.loads(PANEL.read_text(encoding="utf-8"))

        channel = await bot.fetch_channel(int(data["channel_id"]))
        message = await channel.fetch_message(int(data["message_id"]))

        from commands.generator import GeneratorView

        await message.edit(view=GeneratorView())

    except (
        discord.HTTPException,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        ImportError,
        AttributeError,
    ):
        log.exception("No se pudo actualizar el panel")


class Restock(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="restock",
        description="Añadir registros de prueba desde un TXT",
    )
    @app_commands.describe(
        servicio="Servicio cuyo inventario quieres actualizar",
        archivo="Archivo TXT con registros sintéticos",
    )
    @app_commands.choices(
        servicio=[
            app_commands.Choice(name=s, value=s)
            for s in SERVICES
        ]
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def restock(
        self,
        interaction: discord.Interaction,
        servicio: app_commands.Choice[str],
        archivo: discord.Attachment,
    ):
        if not archivo.filename.lower().endswith(".txt"):
            await interaction.response.send_message(
                "Adjunta un archivo .txt.",
                ephemeral=True,
            )
            return

        if archivo.size > 10_000_000:
            await interaction.response.send_message(
                "El archivo supera el límite de 10 MB.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            raw = await archivo.read()
            content = raw.decode("utf-8-sig")
        except (UnicodeDecodeError, discord.HTTPException):
            await interaction.followup.send(
                "No pude leer el archivo. Guárdalo como UTF-8.",
                ephemeral=True,
            )
            return

        lines = [
            line.strip()
            for line in content.splitlines()
            if line.strip()
        ]

        valid = [
            line for line in lines
            if valid_test_record(line)
        ]

        if not valid:
            await interaction.followup.send(
                "No encontré registros de prueba válidos. "
                "Usa dominios de ejemplo como "
                "usuario@example.com:clave_de_prueba.",
                ephemeral=True,
            )
            return

        path = stock_path(servicio.value)
        added = []
        total = 0

        try:
            async with stock_lock:
                path.parent.mkdir(parents=True, exist_ok=True)

                existing = (
                    path.read_text(encoding="utf-8").splitlines()
                    if path.exists()
                    else []
                )

                known = set(existing)

                for line in valid:
                    if line not in known:
                        known.add(line)
                        added.append(line)

                combined = existing + added

                path.write_text(
                    "\n".join(combined)
                    + ("\n" if combined else ""),
                    encoding="utf-8",
                )

                total = sum(
                    1 for line in combined
                    if valid_test_record(line)
                )

        except OSError:
            log.exception("No se pudo guardar el stock")
            await interaction.followup.send(
                "Error al guardar el inventario. "
                "Revisa los logs de Railway.",
                ephemeral=True,
            )
            return

        await refresh_panel(self.bot)

        await interaction.followup.send(
            "**VANTA OPERATION // RESTOCK**\n"
            f"Servicio: **{servicio.value}**\n"
            f"Registros añadidos: **{len(added)}**\n"
            f"Registros inválidos: **{len(lines) - len(valid)}**\n"
            f"Duplicados: **{len(valid) - len(added)}**\n"
            f"Stock total: **{total}**",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Restock(bot))

          
