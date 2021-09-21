from traceback import print_exc

from roid.response import ResponsePayload, ResponseFlags, ResponseType, ResponseData

from crunchy.config import SUPPORT_SERVER_URL, REQUIRED_PERMISSIONS


SAD = "<:HimeSad:676087829557936149>"


def _plain_response(data: ResponseData) -> ResponsePayload:
    return ResponsePayload(type=ResponseType.CHANNEL_MESSAGE_WITH_SOURCE, data=data)


def on_crunchy_api_error(_) -> ResponsePayload:
    print_exc()

    return _plain_response(
        ResponseData(
            content=(
                f"{SAD} Our API seems to be having issues "
                "right now, please try again later."
            ),
            flags=ResponseFlags.EPHEMERAL,
        )
    )


def on_discord_server_error(_) -> ResponsePayload:
    return _plain_response(
        ResponseData(
            content=(
                f"{SAD} Discord seems to be having some issues"
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
                f"{SAD} Something's gone wrong while trying "
                f"to process your command. Please try again later or notify the "
                f"dev team @ {SUPPORT_SERVER_URL}"
            ),
            flags=ResponseFlags.EPHEMERAL,
        )
    )


def on_missing_permissions_error(_) -> ResponsePayload:
    return _plain_response(
        ResponseData(
            content=(
                f"{SAD} Oops! Looks like im missing permissions to carry"
                f" out this command. Make sure I have all the permissions {','.join(REQUIRED_PERMISSIONS)}"
            ),
            flags=ResponseFlags.EPHEMERAL,
        )
    )
