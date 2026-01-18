import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

print("Discord.py Version:", discord.__version__)
print("Loaded from:", discord.__file__)

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

script_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(script_dir, "logs")
os.makedirs(log_dir, exist_ok=True)  # create if missing
log_path = os.path.join(log_dir, "discord.log")

handler = logging.FileHandler(filename=log_path, encoding="utf-8", mode="w")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

@bot.event
async def setup_hook():
    await bot.load_extension("cogs.commands")
    await bot.load_extension("cogs.events")
    await bot.load_extension("cogs.audio")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
