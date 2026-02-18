import discord, yt_dlp, asyncio
from discord.ext import commands
from collections import deque
from config import YDL_OPTS, FFMPEG_OPTIONS
from permissions import INTENTS

# 🎶 FILA POR SERVIDOR
# { guild_id: deque([(video_page_url, title)]) }
queues: dict[int, deque[tuple[str, str]]] = {}

# { guild_id: {"title": str, "duration": int, "start": float} }
now_playing: dict[int, dict] = {}

# Formatando tempo
def formatar_tempo(segundos: int) -> str:
    m, s = divmod(int(segundos), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

# 🔍 Buscar (fila guarda URL da PÁGINA)
def extrair_musica_sync(buscar: str) -> list[tuple[str, str]]:
    """Retorna lista de (webpage_url, title)."""
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(buscar, download=False)

        if isinstance(info, dict) and "entries" in info and info["entries"]:
            entries = [e for e in info["entries"] if e]
        else:
            entries = [info]

        musicas: list[tuple[str, str]] = []
        for e in entries:
            title = e.get("title", "Sem título")

            webpage_url = e.get("webpage_url")
            if not webpage_url and e.get("id"):
                webpage_url = f"https://www.youtube.com/watch?v={e['id']}"

            if webpage_url:
                musicas.append((webpage_url, title))

        return musicas

async def extrair_musica(buscar: str) -> list[tuple[str, str]]:
    return await asyncio.to_thread(extrair_musica_sync, buscar)

# ============================================================================================================
# 🎧 Resolver stream (só na hora de tocar)                                                                  
# ============================================================================================================
def extrair_stream_sync(video_url: str) -> tuple[str, str, int]:
    """Dada a URL da página do vídeo, retorna (stream_url_direta, title, duration_in_seconds)."""
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return (
            info["url"], 
            info.get("title", "Sem título"),
            info.get("duration", 0)
        )

async def extrair_stream(video_url: str) -> tuple[str, str]:
    return await asyncio.to_thread(extrair_stream_sync, video_url)

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

    if guild_id not in queues:
        queues[guild_id] = deque()

    # 🔍 Buscar música: texto vira ytsearch; link usa direto
    busca = search if search.startswith(("http://", "https://")) else f"ytsearch:{search}"

    try:
        musicas = await extrair_musica(busca)
        if not musicas:
            await ctx.reply("❌ Não encontrei nada, verifica direito isso ai meu patão!")
            return
    except Exception as e:
        await ctx.reply(f"⚠️ Erro ao buscar: {e}")
        return

    # ➕ adiciona na fila (URL DA PÁGINA)
    for video_url, title in musicas:
        queues[guild_id].append((video_url, title))

    if len(musicas) == 1:
        await ctx.reply(f"➕ **{musicas[0][1]}** adicionada a fila")
    else:
        await ctx.reply(f"➕ Foram adicionadas as seguintes músicas a fila: **{len(musicas)}**")

    # ✅ pega o loop atual (pra usar no after, que roda em thread)
    loop = asyncio.get_running_loop()

    async def tocar_na_proxima():
        if voice_client.is_playing() or voice_client.is_paused():
            return
        if not queues[guild_id]:
            return

        video_url, _ = queues[guild_id][0]

        try:
            stream_url, _title_real, duration = await extrair_stream(video_url)
            now_playing[guild_id] = {
                "title": _title_real,
                "duration": duration,
                "start": asyncio.get_event_loop().time()
            }

            source = discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS)
            voice_client.play(source, after=tocar_depois)
        except Exception as e:
            print(f"Falha ao extrair/tocar: {e}")
            if queues[guild_id]:
                queues[guild_id].popleft()
            await tocar_na_proxima()

    def tocar_depois(error):
        if error:
            print(f"Error ao tocar música: {error}")

        if queues[guild_id]:
            queues[guild_id].popleft()
        if not queues[guild_id]:
            now_playing.pop(guild_id, None)

        # ✅ agenda a próxima música de forma thread-safe
        loop.call_soon_threadsafe(lambda: asyncio.create_task(tocar_na_proxima()))

    # ✅ inicia reprodução se não estiver tocando
    asyncio.create_task(tocar_na_proxima())

# ============================================================================================================
# 🧾 Fila paginada com botões
# ============================================================================================================
POR_PAGINA = 20

def _render_fila_pagina(fila: deque[tuple[str, str]], pagina: int) -> tuple[str, int, int]:
    total = len(fila)
    total_paginas = max(1, (total + POR_PAGINA - 1) // POR_PAGINA)

    pagina = max(1, min(pagina, total_paginas))
    inicio = (pagina - 1) * POR_PAGINA
    fim = min(inicio + POR_PAGINA, total)

    itens = list(fila)[inicio:fim]

    linhas = []
    for idx, (_url, title) in enumerate(itens, start=inicio + 1):
        if len(title) > 80:
            title = title[:77] + "..."
        linhas.append(f"{idx}. {title}")

    corpo = "\n".join(linhas) if linhas else "📪 A fila está vazia."

    msg = (
        f"🎶 **Fila atual — Página {pagina}/{total_paginas}**\n"
        f"{corpo}\n\n"
        f"**Total:** {total} | **Mostrando:** {inicio+1}-{fim}"
    )
    return msg, pagina, total_paginas


class FilaPaginadaView(discord.ui.View):
    def __init__(self, ctx: commands.Context, pagina: int = 1):
        super().__init__(timeout=90)
        self.ctx = ctx
        self.pagina = pagina
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "Só quem executou o comando pode usar esses botões.",
                ephemeral=True
            )
            return False
        return True

    async def _atualizar(self, interaction: discord.Interaction):
        guild_id = self.ctx.guild.id
        fila = queues.get(guild_id)

        if not fila:
            await interaction.response.edit_message(content="📪 A fila está vazia.", view=None)
            return

        content, self.pagina, total_paginas = _render_fila_pagina(fila, self.pagina)

        self.prev_btn.disabled = (self.pagina <= 1)
        self.next_btn.disabled = (self.pagina >= total_paginas)

        await interaction.response.edit_message(content=content, view=self)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina -= 1
        await self._atualizar(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina += 1
        await self._atualizar(interaction)

    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.danger)
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="✅ Fechado.", view=None)

    async def on_timeout(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass


async def cmd_fila(ctx: commands.Context):
    guild_id = ctx.guild.id

    if guild_id not in queues or not queues[guild_id]:
        await ctx.reply("📪 A fila está vazia.")
        return

    view = FilaPaginadaView(ctx, pagina=1)
    content, view.pagina, total_paginas = _render_fila_pagina(queues[guild_id], view.pagina)

    view.prev_btn.disabled = True
    view.next_btn.disabled = (total_paginas <= 1)

    msg = await ctx.reply(content, view=view)
    view.message = msg

# ============================================================================================================
# ⏭️ Pular musica
# ============================================================================================================
async def cmd_pular(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.send("⚠️ Não estou em canal de voz.")

    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        return await ctx.send("⚠️ Não tem música tocando.")

    ctx.voice_client.stop()
    await ctx.send("⏭️ Música pulada!")

# ============================================================================================================
# ⏸️ Pausar musica
# ============================================================================================================
async def cmd_pausar(ctx: commands.Context):
    tocando = ctx.voice_client
    if not tocando or not tocando.is_playing():
        return await ctx.reply("⚠️ Não tem nenhuma música tocando")
    tocando.pause()
    await ctx.reply("⏸️ Fila pausada!")

# ============================================================================================================
# ⏯️ Continuar
# ============================================================================================================
async def cmd_continuar(ctx: commands.Context):
    tocando = ctx.voice_client
    if not tocando or not tocando.is_paused():
        return await ctx.reply("⚠️ Fila não esta pausado.")
    tocando.resume()
    await ctx.reply("⏯️ Reproduzindo...")

# ============================================================================================================
# 🗑️ Remover música da fila pelo id (posição global)
# ============================================================================================================
async def cmd_remover(ctx: commands.Context, musica_id: int):
    guild_id = ctx.guild.id

    if guild_id not in queues or not queues[guild_id]:
        return await ctx.reply("📪 A fila está vazia.")

    fila = queues[guild_id]

    if musica_id < 1 or musica_id > len(fila):
        return await ctx.reply(f"⚠️ ID inválido. Use um número entre 1 e {len(fila)}.")

    if musica_id == 1 and ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
        return await ctx.reply("⚠️ Essa é a música atual. Use `$pular` para pular.")

    fila_lista = list(fila)
    _url, title = fila_lista.pop(musica_id - 1)
    queues[guild_id] = deque(fila_lista)

    await ctx.reply(f"🗑️ Removida da fila: **{title}** (ID {musica_id})")

# ============================================================================================================
# 🎙️ Tocando agora
# ============================================================================================================
async def cmd_agora(ctx: commands.Context):
    guild_id = ctx.guild.id

    if guild_id not in now_playing:
        return await ctx.reply("⚠️ Nenhuma música tocando agora.")

    data = now_playing[guild_id]

    elapsed = asyncio.get_event_loop().time() - data["start"]
    elapsed_fmt = formatar_tempo(elapsed)
    total_fmt = formatar_tempo(data["duration"])

    await ctx.reply(
        f"🎵 **Tocando agora:** {data['title']}\n"
        f"⏱️ {elapsed_fmt} / {total_fmt}"
    )

# ============================================================================================================
# ⏹️ Parar reprodução
# ============================================================================================================

# Interface para desconectar o bot
class ConfirmarDesconectarView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=30)
        self.ctx = ctx

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "Apenas quem executou o comando pode usar.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="✅ Sim", style=discord.ButtonStyle.danger)
    async def sim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.voice_client:
            await self.ctx.voice_client.disconnect()

        await interaction.response.edit_message(
            content="👋 Desconectado do canal de voz.",
            view=None
        )

    @discord.ui.button(label="❌ Não", style=discord.ButtonStyle.secondary)
    async def nao(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="⏹️ Reprodução parada. Permanecendo no canal.",
            view=None
        )

# Parar

async def cmd_parar(ctx: commands.Context):
    vc = ctx.voice_client
    guild_id = ctx.guild.id

    if not vc:
        return await ctx.reply("⚠️ Não estou conectado em um canal de voz.")

    if not vc.is_playing() and not vc.is_paused():
        return await ctx.reply("⚠️ Não tem música tocando.")

    # Para áudio
    vc.stop()

    # Limpa fila
    if guild_id in queues:
        queues[guild_id].clear()

    now_playing.pop(guild_id, None)

    view = ConfirmarDesconectarView(ctx)

    await ctx.reply(
        "⏹️ Música parada e fila limpa.\n"
        "Deseja que eu desconecte do canal de voz?",
        view=view
    )


