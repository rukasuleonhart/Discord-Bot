from discord.ext import commands
from permissions import INTENTS

# 📽️ yt-dlp
YDL_OPTS = {
    "js_runtimes": {"node": {}},
    "remote_components": ["ejs:github"],
    "noplaylist": True,
    "format": "bestaudio/best",
    "quiet": True,
    "default_search": "ytsearch",
    "extract_flat": False,
}

# 📻 FFmpeg
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

bot = commands.Bot(
    command_prefix= "$", 
    intents= INTENTS,
)