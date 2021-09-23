from typing import Optional

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

        self.__token = token
        self.__crunchy_api_key = crunchy_api_key

        self.http: Optional[http.HttpHandler] = None
        self.client: Optional[api.CrunchyApi] = None

        self.on_event("startup")(self.startup)

    async def startup(self):
        self.http = http.HttpHandler(self.__token)
        self.client = api.CrunchyApi(self.__crunchy_api_key)

        self.on_event("shutdown")(self.http.shutdown)
        self.on_event("shutdown")(self.client.shutdown)
