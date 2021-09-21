import uvicorn

from roid.exceptions import DiscordServerError, Forbidden, HTTPException

from crunchy.commands import events_blueprint
from crunchy.app import CommandHandler
from crunchy import config
from crunchy.tools.api import CrunchyApiHTTPException
from crunchy.global_error_handlers import (
    on_crunchy_api_error,
    on_discord_server_error,
    on_http_error,
    on_missing_permissions_error,
)

app = CommandHandler(
    application_id=config.APPLICATION_ID,
    application_public_key=config.APPLICATION_PUBLIC_KEY,
    token=config.TOKEN,
    state_backend=config.STATE_BACKEND,
    crunchy_api_key=config.CRUNCHY_API_KEY,
)

app.register_error(CrunchyApiHTTPException, on_crunchy_api_error)
app.register_error(DiscordServerError, on_discord_server_error)
app.register_error(Forbidden, on_missing_permissions_error)
app.register_error(HTTPException, on_http_error)

app.add_blueprint(events_blueprint)


def main():
    app.register_commands_on_start()
    uvicorn.run("crunchy:app")


if __name__ == "__main__":
    main()
