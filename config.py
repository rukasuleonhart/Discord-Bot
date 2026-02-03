from discord.ext import commands
from permissions import INTENTS

# 📽️ yt-dlp
YDL_OPTS = {
    "js_runtimes": {"deno": {}},

    # ✅ playlist estável
    "extract_flat": "in_playlist",
    "noplaylist": False,

    # ✅ áudio
    "format": "bestaudio/best",
    "quiet": True,
    "default_search": "ytsearch",
}

# 📻 FFmpeg
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

bot = commands.Bot(
    command_prefix= "$", 
    intents= INTENTS,
    help_command=None
)