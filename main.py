import discord
from discord.ext import commands

# Modulos internos
from security import TOKEN

intents = discord.Intents.all() # Guardando permissões do bot
bot = commands.Bot(command_prefix="/", intents=intents) # "prefixo do bot: / "

bot.run(TOKEN)




