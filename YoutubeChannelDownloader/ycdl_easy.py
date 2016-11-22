import ytapi
import ycdl
import bot

youtube_core = ytapi.Youtube(bot.YOUTUBE_KEY)
youtube = ycdl.YCDL(youtube_core)
