import discord
from discord.ext import commands

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Cog 'commands' loaded.")
    
    # DEPRECATED; replaced by built-in help feature
    # @commands.command(name="commandlist")
    # async def commandlist(self, ctx):
    #     """Displays bot commands in a more fancy way."""
    #     await ctx.send("`[T_19] CURRENTLY AVAILABLE COMMANDS:`\n\n"
    #     "`------- GENERAL -------`\n"
    #     "`!help - Display command information.`\n"
    #     "`!info - Display bot version`\n\n"
    #     "`------- AUDIO -------`\n"
    #     "`!join - Have the bot join the voice channel you're currently in.`\n"
    #     "`!leave - Force the bot to leave the voice channel it's in.`\n"
    #     "`!play (filename) - Play audio from the bot's sounds list.`\n"
    #     "`!pause - Pause the currently playing track.`\n"
    #     "`!unpause - Resume playing a paused track.`\n"
    #     "`!stop - Stop playing current audio and clear the queue.`\n"
    #     "`!sounds - View all currently available sounds the bot can play.`\n"
    #     "`!skip - Skip to the next queued song.`\n"
    #     "`!queue - View the current queue, as well as currently playing music and the loop status.`\n"
    #     "`!loop - Disable or enable looping.`\n")

    @commands.command(name="info", help="Display bot version and details.")
    async def info(self, ctx):
        await ctx.send("`[T_19] CURRENTLY RUNNING T_19 VER 0.2.0.`")

    @commands.command(name="join")
    async def join(self, ctx):
        """Have the bot join the voice channel you're currently in."""
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
        """Force the bot to leave the voice channel it's in."""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("`[T_19] DISCONNECTED FROM VOICE CHANNEL.`")
        else:
            await ctx.send("`[T_19] NOT CURRENTLY IN A VOICE CHANNEL.`")

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))