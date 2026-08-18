"""Basic commands cog for info, help, leave, etc."""

import discord
import os
import time
import json
from discord import app_commands
from discord.ext import commands
from checks import check_allowed_roles, interaction_has_allowed_role

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Cog 'commands' loaded.")
        self.__cog_name__ = "Core"

    @app_commands.command(name="info", description="Display bot version and details.")
    async def info(self, interaction: discord.Interaction) -> None:
        if not interaction_has_allowed_role(interaction):
            await interaction.response.send_message(
                "You don't have permission to use this command.",
                ephemeral=True,
            )
            return
        version = getattr(self.bot, "version", "?")
        start = getattr(self.bot, "start_time", None)
        uptime_secs = int(time.time() - start) if start else 0
        tracks = 0
        audio_cog = self.bot.get_cog("Audio")
        if audio_cog and getattr(audio_cog, "audio_folder", None):
            valid = (".mp3", ".wav", ".ogg", ".flac", ".m4a")
            for _root, _dirs, files in os.walk(audio_cog.audio_folder):
                tracks += sum(1 for f in files if f.lower().endswith(valid))
        description = (
            f"**Version:** {version}\n"
            f"**Uptime:** {uptime_secs} seconds\n"
            f"**Currently loaded audio tracks:** {tracks}"
        )
        embed = discord.Embed(
            title="Woolwav Information",
            description=description,
            color=0x5865F2,
        )
        embed.set_footer(text="Created by @thewebcon using Discord.py")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="help", description="Display all commands.")
    async def help(self, interaction: discord.Interaction) -> None:
        if not interaction_has_allowed_role(interaction):
            await interaction.response.send_message(
                "You don't have permission to use this command.",
                ephemeral=True,
            )
            return
        embed = discord.Embed(
            title="Woolwav Commands",
            description=(
                "**Core**\n"
                "/help — Display this message\n"
                "/info — Bot version and details\n"
                "/leave — Leave the voice channel\n\n"
                "**Audio**\n"
                "/play (filename/folder) — Join VC and play; use /sounds to list files\n"
                "/audio [subfolder] — List available audio; optional subfolder to browse\n"
                "/skip — Skip to the next track\n"
                "/skipto (timestamp) — Skip to a specific time in the current track\n"
                "/queue — Show now playing and queue\n"
                "/loop — Toggle looping for the current track\n"
                "/stop — Stop and clear the queue\n"
                "/results (integer) — Edit the default number of returned results per page with /audio\n"
                "/clearqueue — Clear the queue\n"
                "/pause — Pause playback\n"
                "/unpause — Resume playback"
            ),
            color=0x5865F2,
        )
        embed.set_footer(text=f"Woolwav v{getattr(self.bot, 'version', '?')}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="results", description="Edit the default number of returned results per page with /audio.")
    @app_commands.describe(number="Provide an integer for the number of returned results per page.")
    async def results(self, interaction: discord.Interaction, number: int) -> None:
        if not interaction_has_allowed_role(interaction):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
        if number >= 5 and number < 101:
            try:
                with open("./settings.json", "r") as f:
                    settings = json.load(f)
                settings["results_default"] = number
                with open("./settings.json", "w") as f:
                    json.dump(settings, f, indent=4)
                await interaction.response.send_message(
                    f"Number of default results per page changed to {number}."
                )
            except Exception as e:
                print(f"[WARN] Results default setting dump failed: {e}")
                await interaction.response.send_message("Failed to save the setting; please try again later.", ephemeral=True)
            except Exception as e:
                print(f"[WARN] Results default setting dump failed: {e}")
        else:
            await interaction.response.send_message(
                "You can't change the returned results to a number less than 5 or greater than 100!",
                ephemeral=True,
            )

    @app_commands.command(name="leave", description="Leave the current voice channel.")
    async def leave(self, interaction: discord.Interaction) -> None:
        if not interaction_has_allowed_role(interaction):
            await interaction.response.send_message(
                "You don't have permission to use this command.",
                ephemeral=True,
            )
            return
        voice_client = interaction.guild.voice_client if interaction.guild else None
        if voice_client:
            voice_client.stop()
            audio_cog = self.bot.get_cog("Audio")
            if audio_cog:
                audio_cog.cleanup_guild(
                    interaction.guild.id
                )
            await voice_client.disconnect()
            await interaction.response.send_message(
                "Disconnected from voice channel."
            )
        else:
            await interaction.response.send_message("Not currently in a voice channel to leave.")

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
