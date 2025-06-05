import discord
from discord.ext import commands

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Cog 'events' loaded.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.content.strip().lower().startswith("!play"):
            parts = message.content.strip().split(maxsplit=1)
            if len(parts) == 1 or not parts[1].strip():
                await message.channel.send(f"{message.author.mention} `PLEASE SPECIFY A FILENAME (!play <filename.ext>). USE !sounds TO VIEW AVAILABLE TRACKS.`")

async def setup(bot):
    await bot.add_cog(EventsCog(bot))