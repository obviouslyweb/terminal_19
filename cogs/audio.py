import discord
import os
from discord.ext import commands
from discord import app_commands

class AudioCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Cog 'audio' loaded.")

    @commands.command()
    async def play(self, ctx, filename: str):
        print(f"[DEBUG] Play command received with filename: {filename!r}")
        if not os.path.exists(filename):
            await ctx.send(f"`[T_19] COULD NOT PLAY AUDIO: THE FILE '{filename}' DOES NOT CURRENTLY EXIST IN THE TERMINAL.`")
            return

        if not ctx.voice_client:
            await ctx.send("`[T_18] TERMINAL MUST BE IN A VOICE CHANNEL TO PLAY AUDIO.`")
            return

        if ctx.voice_client.is_playing():
            await ctx.send("`[T_19] AUDIO ALREADY IN PROGRESS.`")
            return

        print(f"[DEBUG] Now attempting to play '{filename}'...")
        source = discord.FFmpegPCMAudio(filename, executable="ffmpeg")
        ctx.voice_client.play(source)
        await ctx.send(f"`[T_19] AUDIO PLAYBACK INITIATED FOR '{filename}'.`")

    @commands.command()
    async def stop(self, ctx):
        if not ctx.voice_client:
            await ctx.send("`[T_19] NOT CURRENTLY IN A VOICE CHANNEL; NO AUDIO TO STOP.`")
            return

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("`[T_19] AUDIO PLAYBACK STOPPED.`")
        else:
            await ctx.send("`[T_19] CANNOT STOP AUDIO THAT IS NOT BEING TRANSMITTED.`")

    @commands.command()
    async def pause(self, ctx):
        if not ctx.voice_client:
            await ctx.send("`[T_19] NOT CONNECTED TO A VOICE CHANNEL.`")
            return
        if not ctx.voice_client.is_playing():
            await ctx.send("`[T_19] NO AUDIO IS CURRENTLY PLAYING.`")
            return
        if ctx.voice_client.is_paused():
            await ctx.send("`[T_19] AUDIO IS ALREADY PAUSED.`")
            return
        ctx.voice_client.pause()
        await ctx.send("`[T_19] AUDIO PLAYBACK PAUSED.`")

    @commands.command()
    async def unpause(self, ctx):
        if not ctx.voice_client:
            await ctx.send("`[T_19] NOT CONNECTED TO A VOICE CHANNEL.`")
            return
        if not ctx.voice_client.is_paused():
            await ctx.send("`[T_19] AUDIO IS NOT PAUSED.`")
            return
        ctx.voice_client.resume()
        await ctx.send("`[T_19] AUDIO PLAYBACK RESUMED.`")

async def setup(bot):
    await bot.add_cog(AudioCog(bot))
