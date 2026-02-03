from security import TOKEN
from config import bot
from language import en_US, pt_BR

@bot.event
async def on_ready():
    print("☑️ Bot inicializado com sucesso!")

en_US.setup(bot)
pt_BR.setup(bot)

bot.run(TOKEN)