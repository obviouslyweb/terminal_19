from discord.ext import commands

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Cog commands loaded.")

    # ALL COMMANDS GO BELOW
    
    @commands.command()
    async def hello(self, ctx):
        await ctx.send(f"`[T_18] GREETINGS, {ctx.author.name}.`")

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))