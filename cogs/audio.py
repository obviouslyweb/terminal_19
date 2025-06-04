import discord
import os
import asyncio
from discord.ext import commands

class AudioCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.audio_queues = {}
        self.audio_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audio")
        print("Cog 'audio' loaded.")

    def get_queue(self, guild_id):
        if guild_id not in self.audio_queues:
            self.audio_queues[guild_id] = asyncio.Queue()
        return self.audio_queues[guild_id]

    def resolve_audio_path(self, filename):
        return os.path.join(self.audio_folder, filename)

    def play_next(self, ctx, guild_id):
        queue = self.get_queue(guild_id)

        async def _play():
            if queue.empty():
                return
            filename = await queue.get()
            file_path = self.resolve_audio_path(filename)
            if not os.path.exists(file_path):
                await ctx.send(f"`[T_19] FILE '{filename}' NOT FOUND.`")
                self.play_next(ctx, guild_id)
                return

            print(f"[DEBUG] Now playing: {filename}")
            source = discord.FFmpegPCMAudio(file_path, executable="ffmpeg")

            def after_playing(error):
                if error:
                    print(f"[ERROR] Playback error: {error}")
                fut = asyncio.run_coroutine_threadsafe(
                    self._safe_play_next(ctx, guild_id), self.bot.loop
                )

            ctx.voice_client.play(source, after=after_playing)

        asyncio.create_task(_play())

    async def _safe_play_next(self, ctx, guild_id):
        await asyncio.sleep(1)
        self.play_next(ctx, guild_id)

    @commands.command()
    async def play(self, ctx, filename: str):
        print(f"[DEBUG] Play command received with filename: {filename!r}")
        file_path = self.resolve_audio_path(filename)
        if not os.path.exists(file_path):
            await ctx.send(f"`[T_19] FILE '{filename}' DOES NOT EXIST.`")
            return

        if not ctx.voice_client:
            await ctx.send("`[T_18] TERMINAL MUST BE IN A VOICE CHANNEL TO PLAY AUDIO.`")
            return

        queue = self.get_queue(ctx.guild.id)
        await queue.put(filename)
        await ctx.send(f"`[T_19] QUEUED: '{filename}'.`")

        if not ctx.voice_client.is_playing():
            self.play_next(ctx, ctx.guild.id)

    @commands.command()
    async def skip(self, ctx):
        if not ctx.voice_client:
            await ctx.send("`[T_19] NOT IN A VOICE CHANNEL.`")
            return

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("`[T_19] SKIPPED TO NEXT TRACK.`")
        else:
            await ctx.send("`[T_19] NO AUDIO TO SKIP.`")

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client:
            ctx.voice_client.stop()
            queue = self.get_queue(ctx.guild.id)
            while not queue.empty():
                queue.get_nowait()
            await ctx.send("`[T_19] AUDIO STOPPED AND QUEUE CLEARED.`")
        else:
            await ctx.send("`[T_19] NOT IN A VOICE CHANNEL.`")

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("`[T_19] AUDIO PAUSED.`")
        else:
            await ctx.send("`[T_19] NO AUDIO TO PAUSE.`")

    @commands.command()
    async def unpause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("`[T_19] AUDIO RESUMED.`")
        else:
            await ctx.send("`[T_19] AUDIO IS NOT PAUSED.`")

async def setup(bot):
    await bot.add_cog(AudioCog(bot))
