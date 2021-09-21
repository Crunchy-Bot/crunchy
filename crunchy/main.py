import os
import uvicorn

from roid import SlashCommands
from roid.state import RedisBackend

from crunchy.commands import events_blueprint


app = SlashCommands(
    application_id=int(os.getenv("APPLICATION_ID")),
    application_public_key=os.getenv("PUBLIC_KEY"),
    token=os.getenv("BOT_TOKEN"),
    state_backend=RedisBackend(
        host=os.getenv("REDIS_HOST", "127.0.0.1"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
    ),
)

app.add_blueprint(events_blueprint)


def main():
    app.register_commands_on_start()
    uvicorn.run("crunchy:app")


if __name__ == "__main__":
    main()
