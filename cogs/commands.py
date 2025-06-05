import discord
from discord.ext import commands

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Cog 'commands' loaded.")
        self.__cog_name__ = "Core"

    @commands.command(name="info", help="Display bot version and details.")
    async def info(self, ctx):
        await ctx.send("`CURRENTLY RUNNING TERMINAL_19 BOT VERSION 1.0.0.`")

    @commands.command()
    async def help(self, ctx):
        await ctx.send("```"
            "TERMINAL_19 COMMANDS\n\n"
            "[ CORE COMMANDS ]\n"
            "!help - Display all commands\n"
            "!info - Display bot version\n"
            "\n"
            "[ AUDIO COMMANDS ]\n"
            "!join - Have the bot join the voice channel you're currently in.\n"
            "!leave - Have the bot leave the voice channel it's in.\n"
            "!play (filename.ext) - Play audio from the bot's sounds list. Filename & extension required.\n"
            "!sounds - Display the bot's sound list in full.\n"
            "!skip - Skips to the next song in the queue.\n"
            "!queue - Show the currently playing track and queued songs, as well as looping status.\n"
            "!loop - Toggles looping, where the currently playing song will replay indefinitely.\n"
            "!stop - Force the bot to stop playing audio entirely, AND clear the queue.\n"
            "!clearqueue - Clear all tracks in the queue.\n"
            "!pause - Pauses the currently playing track.\n"
            "!unpause - Resume playing a paused track.\n"
            "```"
        )

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
