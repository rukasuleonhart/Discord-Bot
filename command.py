import discord
import yt_dlp
from discord.ext import commands
from collections import deque
from config import YDL_OPTS, FFMPEG_OPTIONS
from permissions import INTENTS

# 🎶 FILA POR SERVIDOR
queues = {}  # { guild_id: deque([(url, title)]) }

bot = commands.Bot(
    command_prefix= "$", 
    intents= INTENTS,
)

# 🔍 Realizando a busca por texto ou url
def extrair_musica(buscar: str):
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(buscar, download=False)

        if isinstance(info, dict) and "entries" in info and info["entries"]:
            entries = [e for e in info["entries"] if e]
        else:
            entries = [info]
        
        musica = []
        for e in entries:
            url = None
            if "requested_formats" in e and e["requested_formats"]:
                url = e["requested_formats"][0].get("url")
            if not url:
                url = e.get("url")
            
            if (not url) and e.get("formats"):
                audio_formats = [f for f in e["formats"] if f.get("acodec") != "none"]
                if audio_formats:
                    url = audio_formats[-1].get("url")

            title = e.get("title", "Sem título")

            if url:
                musica.append((url, title))

        return musica      

# ▶️ Tocar
async def cmd_tocar(ctx: commands.Context, search: str):
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

    # 🔍 Buscar música : se for texto, forçar pesquisa; se for link, usa direto
    busca = search if search.startswith(("http://", "https://")) else f"ytsearch:{search}"
    try:
        musica = extrair_musica(busca)
        if not musica:
            await ctx.reply("❌ Não encontrei nada, verifica direito isso ai meu patão!")
            return
    except Exception as e:
        await ctx.reply(f"⚠️ Erro ao buscar: {e}")
        return
    
    # ➕ adiciona na fila
    # se for playlist empilhar tudo
    for url, title in musica:
        queues[guild_id].append((url, title))
        
    if len(musica) == 1:
        await ctx.reply(f"➕ **{musica[0][1]}** adicionada a fila")
    else:
        await ctx.reply(f"➕ Foram adicionadas as seguintes músicas a fila: **{len(musica)}**")

    def tocar_na_proxima():
        if voice_client.is_playing() or voice_client.is_paused():
            return
        if not queues[guild_id]:
            return
        
        next_url, next_title = queues[guild_id][0]
        source = discord.FFmpegPCMAudio(next_url, **FFMPEG_OPTIONS)
        voice_client.play(source, after=tocar_depois)

    def tocar_depois(error):
        if error:
            print(f"Error ao tocar música: {error}")
        
        if queues[guild_id]:
            queues[guild_id].popleft()

        bot.loop.call_soon_threadsafe(tocar_na_proxima)
    
    # se não está tocando nada reproduzir 🎶
    tocar_na_proxima()

# 📝 Exibir Fila
async def cmd_fila(ctx: commands.Context):
    guild_id = ctx.guild.id

    if guild_id not in queues or not queues[guild_id]:
        await ctx.reply("📪 A fila está vazia.")
        return
    
    mensagem = "🎶 **Fila atual:**\n"

    for i, (_, title) in enumerate(queues[guild_id], start=1):
        mensagem += f"{i}. {title}\n"
    
    await ctx.reply(mensagem)

# ⏭️ Pular musica
async def cmd_pular(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.send("⚠️ Não estou em canal de voz.")

    if not ctx.voice_client.is_playing():
        return await ctx.send("⚠️ Não tem música tocando.")

    ctx.voice_client.stop()
    await ctx.send("⏭️ Música pulada!")

# ⏸️ Pausar musica
async def cmd_pausar(ctx: commands.Context):
    tocando = ctx.voice_client
    if not tocando or not tocando.is_playing():
        return await ctx.reply("⚠️ Não tem nenhuma música tocando")
    tocando.pause()
    await ctx.reply("⏸️ Fila pausada!")

# ⏯️ Continuar
async def cmd_continuar(ctx: commands.Context):
    tocando = ctx.voice_client
    if not tocando or not tocando.is_paused():
        return await ctx.reply("⚠️ Fila não esta pausado.")
    tocando.resume()
    await ctx.reply("⏯️ Reproduzindo...")
