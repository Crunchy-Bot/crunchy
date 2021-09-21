import os
import uvicorn

from roid.state import RedisBackend

from crunchy.commands import events_blueprint
from crunchy.app import CommandHandler
from crunchy import config

app = CommandHandler(
    application_id=config.APPLICATION_ID,
    application_public_key=config.APPLICATION_PUBLIC_KEY,
    token=config.TOKEN,
    state_backend=config.STATE_BACKEND,
    crunchy_api_key=config.CRUNCHY_API_KEY,
)

app.add_blueprint(events_blueprint)


def main():
    app.register_commands_on_start()
    uvicorn.run("crunchy:app")


if __name__ == "__main__":
    main()
