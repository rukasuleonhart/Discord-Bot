from command import cmd_tocar, cmd_pausar, cmd_continuar, cmd_pular, cmd_fila, cmd_remover, cmd_agora, cmd_parar
from discord.ext import commands

def setup(bot: commands.Bot):

    @bot.command(name="tocar")
    async def play(ctx: commands.Context, * ,search: str):
        await cmd_tocar(ctx, search)

    # ⏸️ Pause
    @bot.command(name="pausar")
    async def pause(ctx: commands.Context):
        await cmd_pausar(ctx)

    # ⏯️ Resume
    @bot.command(name="continuar")
    async def resume(ctx: commands.Context):
        await cmd_continuar(ctx)

    # ⏭️ Skip
    @bot.command(name="pular")
    async def skip(ctx: commands.Context):
        await cmd_pular(ctx)

    # 🔢 Queue
    @bot.command(name="fila")
    async def queue(ctx: commands.Context):
        await cmd_fila(ctx)

    # 🗑️ Remover
    @bot.command(name="remover")
    async def remover(ctx: commands.Context, musica_id: int):
        await cmd_remover(ctx, musica_id)

    # 🎙️ Agora
    @bot.command(name="agora")
    async def agora(ctx: commands.Context):
        await cmd_agora(ctx)

    # ⏹️ Parar
    @bot.command(name="parar")
    async def parar(ctx: commands.Context):
        await cmd_parar(ctx)