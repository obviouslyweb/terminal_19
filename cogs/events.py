import discord
from discord.ext import commands

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Cog events loaded.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if "test_swear" in message.content.lower():
            try:
                await message.delete()
                await message.channel.send(f"{message.author.mention} `[T_18] PLEASE FOLLOW PROPER SYSTEM REGULATIONS FOR LANGUAGE.`")
            except discord.Forbidden:
                print("ERROR: Bot lacks permissions to delete messages.")
            except discord.HTTPException as e:
                print(f"ERROR: Failed to delete message: {e}")
        
        print(f"[DEBUG] Processing message: {message.content}")

async def setup(bot):
    await bot.add_cog(EventsCog(bot))