import os
import uvicorn

from roid.state import RedisBackend

from crunchy.commands import events_blueprint
from crunchy.app import CommandHandler
from crunchy import config

app = CommandHandler(
    application_id=config.application_id,
    application_public_key=config.application_public_key,
    token=config.token,
    state_backend=config.state_backend,
)

app.add_blueprint(events_blueprint)


def main():
    app.register_commands_on_start()
    uvicorn.run("crunchy:app")


if __name__ == "__main__":
    main()
