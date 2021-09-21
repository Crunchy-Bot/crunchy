from roid.response import ResponsePayload, ResponseFlags, ResponseType, ResponseData
from traceback import print_exc


def on_crunchy_api_error(_) -> ResponsePayload:
    print_exc()

    return ResponsePayload(
        type=ResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        data=ResponseData(
            content=(
                "<:KannaWhat:782719609249333248> Our API seems to be having issues "
                "right now, please try again later."
            ),
            flags=ResponseFlags.EPHEMERAL,
        ),
    )
