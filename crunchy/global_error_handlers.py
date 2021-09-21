from traceback import print_exc

from roid.response import ResponsePayload, ResponseFlags, ResponseType, ResponseData

from crunchy.config import SUPPORT_SERVER_URL


def _plain_response(data: ResponseData) -> ResponsePayload:
    return ResponsePayload(type=ResponseType.CHANNEL_MESSAGE_WITH_SOURCE, data=data)


def on_crunchy_api_error(_) -> ResponsePayload:
    print_exc()

    return _plain_response(
        ResponseData(
            content=(
                "<:KannaWhat:782719609249333248> Our API seems to be having issues "
                "right now, please try again later."
            ),
            flags=ResponseFlags.EPHEMERAL,
        )
    )


def on_discord_server_error(_) -> ResponsePayload:
    return _plain_response(
        ResponseData(
            content=(
                "<:KannaWhat:782719609249333248> Discord seems to be having some issues"
                " right now, preventing us from operating normally, please try again later."
            ),
            flags=ResponseFlags.EPHEMERAL,
        )
    )


def on_http_error(_) -> ResponsePayload:
    print_exc()

    return _plain_response(
        ResponseData(
            content=(
                f"<:KannaWhat:782719609249333248> Something's gone wrong while trying "
                f"to process your command. Please try again later or notify the "
                f"dev team @ {SUPPORT_SERVER_URL}"
            ),
            flags=ResponseFlags.EPHEMERAL,
        )
    )
