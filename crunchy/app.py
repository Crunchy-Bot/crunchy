from roid import SlashCommands

from crunchy.tools import http, api


class CommandHandler(SlashCommands):
    def __init__(
        self,
        application_id: int,
        application_public_key: str,
        token: str,
        crunchy_api_key: str,
        **extra,
    ):
        super().__init__(application_id, application_public_key, token, **extra)

        self.http = http.HttpHandler(token)
        self.client = api.CrunchyApi(crunchy_api_key)
