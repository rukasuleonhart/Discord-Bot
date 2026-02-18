# ▶️ Play
from command import cmd_tocar, cmd_pausar, cmd_continuar, cmd_pular, cmd_fila, cmd_remover, cmd_agora, cmd_parar, cmd_embaralhar
from discord.ext import commands

def setup(bot: commands.Bot):

    @bot.command(name="play")
    async def play(ctx: commands.Context, * ,search: str):
        await cmd_tocar(ctx, search)

    # ⏸️ Pause
    @bot.command(name="pause")
    async def pause(ctx: commands.Context):
        await cmd_pausar(ctx)

    # ⏯️ Resume
    @bot.command(name="resume")
    async def resume(ctx: commands.Context):
        await cmd_continuar(ctx)

    # ⏭️ Skip
    @bot.command(name="skip")
    async def skip(ctx: commands.Context):
        await cmd_pular(ctx)

    # 🔢 Queue
    @bot.command(name="queue")
    async def queue(ctx: commands.Context):
        await cmd_fila(ctx)
    
    # 🗑️ Remover
    @bot.command(name="remove")
    async def remover(ctx: commands.Context, musica_id: int):
        await cmd_remover(ctx, musica_id)
    
    # 🎙️ Now
    @bot.command(name="now")
    async def now(ctx: commands.Context):
        await cmd_agora(ctx)

    # ⏹️ Stop
    @bot.command(name="stop")
    async def stop(ctx: commands.Context):
        await cmd_parar(ctx)

    # 🃏 Random
    @bot.command(name="random")
    async def random(ctx: commands.Context):
        await cmd_embaralhar(ctx)