import discord
import yt_dlp
from discord.ext import commands
from collections import deque
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

# 🎶 FILA POR SERVIDOR
queues = {}  # { guild_id: deque([(url, title)]) }

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
    guild_id = ctx.guild.id

    # cria a fila se não existir
    if guild_id not in queues:
        queues[guild_id] = deque()

    # 🔍 Buscar música
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Verifica se é link direto
            if search.startswith("http://") or search.startswith("https://"):
                info = ydl.extract_info(search, download=False)
            else:
                # Pesquisa por texto
                info = ydl.extract_info(f"ytsearch:{search}", download=False)
                info = info["entries"][0]  # pega o primeiro resultado

            # Pega a URL de áudio do vídeo
            url = info.get("url")
            if not url and "formats" in info:
                url = info["formats"][0]["url"]

            title = info["title"]

        except Exception as e:
            await ctx.reply(f"❌ Não foi possível encontrar ou tocar a música: {e}")
            return

    # ➕ adiciona na fila
    queues[guild_id].append((url, title))
    await ctx.reply(f"➕ **{title}** adicionada à fila")

    # ▶️ toca se não estiver tocando nada
    if not voice_client.is_playing():
        def play_next():
            if queues[guild_id]:
                next_url, next_title = queues[guild_id][0]
                voice_client.play(
                    discord.FFmpegPCMAudio(next_url, **ffmpeg_options),
                    after=lambda e: after_play(e)
                )

        def after_play(error):
            if error:
                print(f"Erro ao tocar música: {error}")
            # remove a música atual da fila
            queues[guild_id].popleft()
            # toca próxima se houver
            play_next()

        # toca a primeira música da fila
        first_url, first_title = queues[guild_id][0]
        source = discord.FFmpegPCMAudio(first_url, **ffmpeg_options)
        voice_client.play(source, after=lambda e: after_play(e))


# 📝 Exibir Fila
@bot.command()
async def fila(ctx: commands.Context):
    guild_id = ctx.guild.id

    if guild_id not in queues or not queues[guild_id]:
        await ctx.reply("📪 A fila está vazia.")
        return
    
    mensagem = "🎶 **Fila atual:**\n"

    for i, (_, title) in enumerate(queues[guild_id], start=1):
        mensagem += f"{i}. {title}\n"
    
    await ctx.reply(mensagem)

# ⏭️ Pular musica @paulinho kk boa
@bot.command()
async def skip(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.send("❌ Não estou em canal de voz.")

    if not ctx.voice_client.is_playing():
        return await ctx.send("❌ Não tem música tocando.")

    ctx.voice_client.stop()
    await ctx.send("⏭️ Música pulada!")

bot.run(TOKEN)