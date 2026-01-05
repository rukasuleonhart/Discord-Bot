import discord
import yt_dlp
from discord.ext import commands
from security import TOKEN

# 📽️ yt-dlp
ydl_opts = {
    "format": "bestaudio/best",
    "quiet": True,
}

# 📻 FFmpeg                 
ffmpeg_options = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

# ⛔ Permissões
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="$", intents=intents)

@bot.event
async def on_ready():
    print("☑️ Bot inicializado com sucesso!")

# ▶️ PLAY           
@bot.command()
async def play(ctx: commands.Context, *, search: str):
    if not ctx.author.voice:
        await ctx.reply("✋ Você precisa estar em um canal de voz.")
        return

    channel = ctx.author.voice.channel

    if not ctx.voice_client:
        await channel.connect()

    voice_client = ctx.voice_client

    if voice_client.is_playing():
        voice_client.stop()

    # 🔍 Buscar música
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{search}", download=False)
        video = info["entries"][0]
        url = video["url"]
        title = video["title"]

    source = discord.FFmpegPCMAudio(
        url,
        **ffmpeg_options
    )

    voice_client.play(source)

    await ctx.reply(f"▶️ Tocando **{title}**")

bot.run(TOKEN)