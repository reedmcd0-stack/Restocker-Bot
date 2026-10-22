import os
import logging
from pathlib import Path

import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

STATUS_CODE = "/TK7a2RBgZS"
ACCESS_ROLE_ID = 1560363466701676554

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s: %(message)s",
)

log = logging.getLogger("VantaOperation")


class VantaOperation(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents,
        )

    async def setup_hook(self):
        commands_dir = Path(__file__).parent / "commands"

        if not commands_dir.is_dir():
            log.error("La carpeta commands no existe: %s", commands_dir)
            return

        # Cargar todas las extensiones Python de la carpeta commands.
        for file in sorted(commands_dir.glob("*.py")):
            if file.name.startswith("_"):
                continue

            extension = f"commands.{file.stem}"

            try:
                await self.load_extension(extension)
                log.info("Loaded extension: %s", extension)

            except Exception:
                log.exception("Could not load extension: %s", extension)

        # Sincronizar los comandos Slash globales.
        try:
            synced = await self.tree.sync()

            log.info(
                "Synced %s slash commands: %s",
                len(synced),
                [command.name for command in synced],
            )

        except Exception:
            log.exception("Slash command sync failed")

    async def on_ready(self):
        log.info(
            "VantaOperation online: %s (ID: %s)",
            self.user,
            self.user.id if self.user else "unknown",
        )

    async def on_presence_update(
        self,
        before: discord.Member,
        after: discord.Member,
    ):
        role = after.guild.get_role(ACCESS_ROLE_ID)

        if role is None:
            return

        has_code = any(
            isinstance(activity, discord.CustomActivity)
            and STATUS_CODE in (
                (activity.name or "")
                + " "
                + (activity.state or "")
            )
            for activity in after.activities
        )

        has_role = role in after.roles

        try:
            if has_code and not has_role:
                await after.add_roles(
                    role,
                    reason="Estado de Vanta verificado",
                )
                log.info("Access role granted to %s", after.id)

            elif not has_code and has_role:
                await after.remove_roles(
                    role,
                    reason="Código de estado eliminado",
                )
                log.info("Access role removed from %s", after.id)

        except discord.Forbidden:
            log.error(
                "No permission to manage role %s. "
                "Check the bot's role hierarchy.",
                ACCESS_ROLE_ID,
            )

        except discord.HTTPException:
            log.exception(
                "Failed to update role for %s",
                after.id,
            )


bot = VantaOperation()


@bot.tree.command(
    name="ping",
    description="Check bot latency",
)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Pong! {round(bot.latency * 1000)} ms"
    )


if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN is missing. Set it before starting the bot."
    )


bot.run(TOKEN)
