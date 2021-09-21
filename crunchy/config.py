import os

from roid.state import RedisBackend

application_id = int(os.getenv("APPLICATION_ID"))
application_public_key = os.getenv("PUBLIC_KEY")
token = os.getenv("BOT_TOKEN")
state_backend = RedisBackend(
    host=os.getenv("REDIS_HOST", "127.0.0.1"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
)

CRUNCHY_API = "https://api.crunchy.gg/v0"
DISCORD_API = "https://discord.com/api/v8"
