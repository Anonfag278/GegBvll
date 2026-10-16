"""User-installed slash commands. Python 3.10+, discord.py 2.4+."""
import asyncio
import logging
import os
from dataclasses import dataclass, field

import discord
from discord import app_commands

log = logging.getLogger(__name__)


@dataclass
class Run:
    stop: asyncio.Event = field(default_factory=asyncio.Event)
    sent: int = 0


class App(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.none(),
                         allowed_mentions=discord.AllowedMentions.none())
        self.runs: dict[int, Run] = {}
        self.tree = app_commands.CommandTree(
            self,
            allowed_installs=app_commands.AppInstallationType(user=True, guild=False),
            allowed_contexts=app_commands.AppCommandContext(
                guild=True, dm_channel=True, private_channel=True),
        )
        self.tree.add_command(app_commands.Command(
            name="repeat", description="Send a message 1–5 times in this channel.",
            callback=self.repeat))
        self.tree.add_command(app_commands.Command(
            name="stop", description="Stop your active repetition run in any channel.",
            callback=self.stop))

    async def setup_hook(self):
        await self.tree.sync()  # Global commands are required for user installation.
        log.info("Slash commands synced")

    async def on_ready(self):
        log.info("Connected as %s", self.user)

    @app_commands.describe(message="Text to send (mentions do not ping)", count="Number of messages, 1–5")
    async def repeat(self, interaction: discord.Interaction,
                     message: app_commands.Range[str, 1, 2000],
                     count: app_commands.Range[int, 1, 5]):
        if not message.strip():
            await interaction.response.send_message("Enter a non-empty message.", ephemeral=True)
            return
        user_id = interaction.user.id
        if user_id in self.runs:
            await interaction.response.send_message("A run is active. Use /stop first.", ephemeral=True)
            return
        run = Run()
        self.runs[user_id] = run  # Reserve before awaiting to prevent overlapping runs.
        try:
            # A real initial response keeps all five follow-ups available for messages.
            await interaction.response.send_message(
                "Sending. Use /stop to stop further messages.", ephemeral=True)
            result = "Completed"
            try:
                for _ in range(count):
                    if run.stop.is_set():
                        break
                    # Sequential awaited sends: discord.py respects Discord's rate limits.
                    await interaction.followup.send(
                        message, ephemeral=False, wait=True,
                        allowed_mentions=discord.AllowedMentions.none())
                    run.sent += 1
                if run.stop.is_set():
                    result = "Stopped"
            except discord.HTTPException as exc:
                # Do not retry a possibly delivered message or work around restrictions.
                log.warning("Send failed (HTTP %s, Discord code %s)", exc.status, exc.code)
                result = f"Stopped after a Discord error (HTTP {exc.status}, code {exc.code})"
            await interaction.edit_original_response(content=f"{result}: {run.sent}/{count} messages sent.")
        except discord.HTTPException as exc:
            log.warning("Interaction failed (HTTP %s, Discord code %s)", exc.status, exc.code)
        finally:
            self.runs.pop(user_id, None)

    async def stop(self, interaction: discord.Interaction):
        run = self.runs.get(interaction.user.id)
        if run is None:
            text = "No active run."
        else:
            run.stop.set()
            text = "Stop requested. A message already in flight may still finish."
        await interaction.response.send_message(text, ephemeral=True)


def main():
    token = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Set DISCORD_BOT_TOKEN; see README.md.")
    logging.basicConfig(level=logging.INFO)
    App().run(token, log_handler=None)


if __name__ == "__main__":
    main()
