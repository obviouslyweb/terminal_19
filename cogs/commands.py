import discord
from discord.ext import commands

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Cog 'commands' loaded.")

    @commands.command(name="info")
    async def info(self, ctx):
        await ctx.send("`[T_19] CURRENTLY RUNNING T_19 VER 0.1.0.`")

    @commands.command(name="join")
    async def join(self, ctx):
        if ctx.author.voice and ctx.author.voice.channel:
            channel = ctx.author.voice.channel
            print(f"[DEBUG] Attempting to join VC {channel.name}...")

            if ctx.voice_client is not None:
                await ctx.voice_client.move_to(channel)
                await ctx.send(f"`[T_19] MOVED TO {channel.name}.`")
            else:
                await channel.connect()
                await ctx.send(f"`[T_19] JOINED {channel.name}.`")
        else:
            await ctx.send("`[T_19] YOU MUST BE IN A VOICE CHANNEL THAT THE TERMINAL CAN ACCESS.`")

    @commands.command(name="leave")
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("`[T_19] DISCONNECTED FROM VOICE CHANNEL.`")
        else:
            await ctx.send("`[T_19] NOT CURRENTLY IN A VOICE CHANNEL.`")

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))