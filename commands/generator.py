
import asyncio
import json
import logging
import random
import time
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger(__name__)

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

DATA = Path("generator_data")
STOCK = DATA / "stock"
PANEL = DATA / "panel.json"

BANNER_URL = (
    "https://cdn.discordapp.com/attachments/"
    "1456334168677023897/1561151206821204058/"
    "d441444b6f07b00e8f7b92b65c126c11.gif"
)

ACCESS_ROLE_ID = 1560363466701676554
STATUS_CODE = "/TK7a2RBgZS"
COOLDOWN_SECONDS = 60

# Dominios reservados para pruebas
ALLOWED_DOMAINS = {
    "gmail.com",
    "hotmail.com",
    "outlook.com",
    "duck.com",
}

USER_COOLDOWNS = {}
STOCK_LOCKS = {}


def get_lock(service):
    if service not in STOCK_LOCKS:
        STOCK_LOCKS[service] = asyncio.Lock()
    return STOCK_LOCKS[service]


def stock_path(service):
    return STOCK / f"{SERVICES.index(service)}.txt"


def is_demo_record(entry: str) -> bool:
    entry = entry.strip()

    if ":" not in entry:
        return False

    identifier, password = entry.split(":", 1)
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


def read_stock(service):
    path = stock_path(service)

    if not path.exists():
        return []

    try:
        return [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and is_demo_record(line.strip())
        ]
    except OSError:
        log.exception("No se pudo leer el stock de %s", service)
        return []


def save_stock(service, entries):
    path = stock_path(service)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        "\n".join(entries) + ("\n" if entries else ""),
        encoding="utf-8",
    )


def save_panel(channel_id, message_id):
    DATA.mkdir(parents=True, exist_ok=True)

    PANEL.write_text(
        json.dumps({
            "channel_id": channel_id,
            "message_id": message_id,
        }),
        encoding="utf-8",
    )


def make_embed(service, description, color=None):
    embed = discord.Embed(
        title=f"VANTA OPERATION  //  {service.upper()}",
        description=description,
        color=color or discord.Color.dark_grey(),
    )
    embed.set_image(url=BANNER_URL)
    return embed


def has_access(member):
    return any(
        role.id == ACCESS_ROLE_ID
        for role in member.roles
    )


class ServiceButton(discord.ui.Button):
    def __init__(self, service):
        self.service = service

        super().__init__(
            label=f"{service} · {len(read_stock(service))}",
            style=discord.ButtonStyle.secondary,
            custom_id=f"vanta:generate:{SERVICES.index(service)}",
        )

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "Utiliza este botón dentro del servidor.",
                ephemeral=True,
            )
            return

        member = interaction.user

        if not has_access(member):
            await interaction.response.send_message(
                embed=make_embed(
                    self.service,
                    f"Necesitas el rol de acceso.\n"
                    f"Configura tu estado con `{STATUS_CODE}`.",
                ),
                ephemeral=True,
            )
            return

        now = time.monotonic()
        expires = USER_COOLDOWNS.get(member.id, 0)

        if now < expires:
            remaining = int(expires - now) + 1

            await interaction.response.send_message(
                embed=make_embed(
                    self.service,
                    f"Espera **{remaining} segundos** antes de intentarlo.",
                ),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        async with get_lock(self.service):
            entries = read_stock(self.service)

            if not entries:
                await interaction.followup.send(
                    embed=make_embed(
                        self.service,
                        "No hay registros de prueba disponibles.",
                    ),
                    ephemeral=True,
                )
                return

            selected = random.choice(entries)

            remaining_entries = entries.copy()
            remaining_entries.remove(selected)

            try:
                save_stock(self.service, remaining_entries)
            except OSError:
                log.exception("No se pudo guardar el stock")

                await interaction.followup.send(
                    embed=make_embed(
                        self.service,
                        "No se pudo actualizar el inventario.",
                    ),
                    ephemeral=True,
                )
                return

            USER_COOLDOWNS[member.id] = (
                time.monotonic() + COOLDOWN_SECONDS
            )

        try:
            await member.send(
                embed=make_embed(
                    self.service,
                    "Registro de prueba:\n"
                    f"```text\n{selected}\n```",
                )
            )
        except discord.HTTPException:
            # Devolver el registro si no se pudo enviar el mensaje
            async with get_lock(self.service):
                current = read_stock(self.service)
                if selected not in current:
                    current.append(selected)
                    try:
                        save_stock(self.service, current)
                    except OSError:
                        log.exception(
                            "No se pudo restaurar el registro al inventario"
                        )

            await interaction.followup.send(
                embed=make_embed(
                    self.service,
                    "No pude enviarte un MD. Revisa tu configuración "
                    "de mensajes privados.",
                ),
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            embed=make_embed(
                self.service,
                "Registro de prueba enviado por MD. Stock actualizado.",
            ),
            ephemeral=True,
        )

        await refresh_panel(interaction.client)


class GeneratorView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)

        container = discord.ui.Container()

        gallery = discord.ui.MediaGallery()
        gallery.add_item(media=BANNER_URL)
        container.add_item(gallery)

        for start in range(0, len(SERVICES), 5):
            buttons = [
                ServiceButton(service)
                for service in SERVICES[start:start + 5]
            ]
            container.add_item(discord.ui.ActionRow(*buttons))

        self.add_item(container)


async def refresh_panel(bot):
    if not PANEL.exists():
        return

    try:
        data = json.loads(PANEL.read_text(encoding="utf-8"))
        channel = await bot.fetch_channel(int(data["channel_id"]))
        message = await channel.fetch_message(int(data["message_id"]))

        await message.edit(view=GeneratorView())

    except (
        discord.HTTPException,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
    ):
        log.exception("No se pudo actualizar el panel")


class Generator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        STOCK.mkdir(parents=True, exist_ok=True)

    @app_commands.command(
        name="generator",
        description="Publica el panel de Vanta.",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def generator(self, interaction: discord.Interaction):
        if interaction.channel is None:
            await interaction.response.send_message(
                "No se encontró el canal.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            message = await interaction.channel.send(
                view=GeneratorView()
            )
            save_panel(interaction.channel_id, message.id)

        except (discord.HTTPException, OSError):
            log.exception("No se pudo publicar el panel")
            await interaction.followup.send(
                "No se pudo publicar el panel. Revisa los permisos y los logs de Railway.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            "Panel publicado correctamente.",
            ephemeral=True,
        )

    @app_commands.command(
        name="stock",
        description="Consulta las existencias.",
    )
    async def stock(self, interaction: discord.Interaction):
        lines = [
            f"**{service}** · `{len(read_stock(service))}`"
            for service in SERVICES
        ]

        embed = discord.Embed(
            title="VANTA // STOCK",
            description="\n".join(lines),
            color=discord.Color.dark_grey(),
        )
        embed.set_image(url=BANNER_URL)

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Generator(bot))
    bot.add_view(GeneratorView())

      
