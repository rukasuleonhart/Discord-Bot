from security import TOKEN
from language import en_US, pt_BR
from config import bot
import discord

@bot.event
async def on_ready():
    print("☑️ Bot inicializado com sucesso!")

en_US.setup(bot)
pt_BR.setup(bot)

# 🆘 Help
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📖 Ajuda — Comandos do Bot",
        description="Lista de comandos disponíveis",
        color=discord.Color.blurple()
    )
    # br - Portugues 
    embed.add_field(
        name=":flag_br: Portugues (pt_BR)",
        value=(
            "`$tocar <música>` - Tocar uma música\n"
            "`$pausar` - pausar a música atual\n"
            "`$continuar` - despausar\n"
            "`$pular` - pular para a próxima música e tirar a atual de fila\n"
            "`$remover <id>` - remover uma música da fila pelo id\n"
            "`$agora` - mostra a música atual\n"
            "`$fila` - exibir fila de músicas\n\n"
        ),
        inline=True  
    )

    # 🇺🇸 - English
    embed.add_field(
        name="🇺🇸 English (en_US)",
        value=(
            "`$play <music>` – Play a song\n"
            "`$pause` – Pause the current song\n"
            "`$resume` – Resume playback\n"
            "`$skip` – Skip to the next song\n"
            "`$remove <id>` remove music by id\n"
            "`$now` - show the music actualy\n"
            "`$queue` – Show the music queue\n"
        ),
        inline=False
    )
    await ctx.send(embed=embed)
    

bot.run(TOKEN)