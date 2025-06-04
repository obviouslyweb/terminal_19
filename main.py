import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

# Obtain envoirnment variables & get token
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# Create logging handler
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# Define necessary intents (permissions)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot setup
bot = commands.Bot(command_prefix='!', intents=intents)

# Load cogs
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}') 
    await bot.load_extension("cogs.commands")
    await bot.load_extension("cogs.events")
    await bot.load_extension("cogs.audio")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)

# TO-DO:
    # + Further format and add details for !help
    # + Update bot description & documentation