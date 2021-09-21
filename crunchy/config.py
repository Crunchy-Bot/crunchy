import os

from roid.state import RedisBackend

APPLICATION_ID = int(os.getenv("APPLICATION_ID"))
APPLICATION_PUBLIC_KEY = os.getenv("PUBLIC_KEY")
TOKEN = os.getenv("BOT_TOKEN")
STATE_BACKEND = RedisBackend(
    host=os.getenv("REDIS_HOST", "127.0.0.1"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
)

CRUNCHY_API_KEY = os.getenv("CRUNCHY_API_KEY")

CRUNCHY_API = "https://api.crunchy.gg/v0"
DISCORD_API = "https://discord.com/api/v8"

SUPPORT_SERVER_URL = "https://discord.gg/MtETshQ"
