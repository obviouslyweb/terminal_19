import discord
from discord.ext import commands

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Cog 'commands' loaded.")

    @commands.command(name="info", help="Display bot version and details.")
    async def info(self, ctx):
        await ctx.send("`CURRENTLY RUNNING T_19 VER 0.2.0.`")

    @commands.command(name="join", help="Join the voice channel you're in.")
    async def join(self, ctx):
        if ctx.author.voice and ctx.author.voice.channel:
            channel = ctx.author.voice.channel
            if ctx.voice_client is not None:
                await ctx.voice_client.move_to(channel)
                await ctx.send(f"`MOVED TO {channel.name}.`")
            else:
                await channel.connect()
                await ctx.send(f"`JOINED {channel.name}.`")
        else:
            await ctx.send("`YOU MUST BE IN A VOICE CHANNEL THAT THE TERMINAL CAN ACCESS.`")

    @commands.command(name="leave", help="Leave the current voice channel.")
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("`DISCONNECTED FROM VOICE CHANNEL.`")
        else:
            await ctx.send("`NOT CURRENTLY IN A VOICE CHANNEL.`")

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
