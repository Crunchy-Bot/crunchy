import pprint

from roid import CommandsBlueprint, Response, ResponseFlags, Interaction
from roid.objects import Channel, ChannelType
from roid.helpers import check
from roid.exceptions import AbortInvoke, Forbidden, HTTPException, NotFound

from crunchy.app import CommandHandler
from crunchy.tools import assetloader

events_blueprint = CommandsBlueprint()

NOT_ENOUGH_DATA = AbortInvoke(
    content="<:HimeSad:676087829557936149> Oops! You've not given me enough information to work with here.",
    flags=ResponseFlags.EPHEMERAL,
)


async def check_channel_type(interaction: Interaction):
    """
    Checks if the mentioned channel type is correct or not.

    If it's not then a error message is raised and returned back to the user.
    """
    pprint.pprint(interaction.dict())

    if interaction.data.options is None:
        raise NOT_ENOUGH_DATA

    resolved = interaction.data.resolved
    if resolved is None:
        raise NOT_ENOUGH_DATA

    for option in interaction.data.options:
        try:
            channel = resolved.channels[int(option.value)]
            break
        except (KeyError, ValueError):
            raise AbortInvoke(
                content="<:HimeSad:676087829557936149> Oops! You've given me the wrong data, I need a channel mention.",
                flags=ResponseFlags.EPHEMERAL,
            )
    else:
        raise NOT_ENOUGH_DATA

    if channel.type != ChannelType.GUILD_TEXT:
        raise AbortInvoke(
            content=(
                "<:HimeSad:676087829557936149> Oops! I cant add a webhook to "
                "this channel. Make sure it's a guild text channel and try again!"
            ),
            flags=ResponseFlags.EPHEMERAL,
        )

    return interaction


@check(check_channel_type)
@events_blueprint.command(
    "add-news-channel",
    description=(
        "Add Crunchy's news webhook to a channel of "
        "your choice to get the latest Anime news."
    ),
    defer_register=False,
)
async def add_news_channel(app: CommandHandler, channel: Channel) -> Response:

    avatar = assetloader.get_base64_asset("crunchy-128.webp")
    data = await app.http.request(
        "POST",
        f"/channels/{channel.id}/webhooks",
        pass_token=True,
        json={
            "name": "Crunchy Anime News",
            "avatar": f"data:image/webp;base64,{avatar}",
        },
    )
    print(data)

    return Response(
        content=(
            f"<:exitment:717784139641651211> All done! I'll send"
            f" news to <#{channel.id}> when I get some news."
        ),
        flags=ResponseFlags.EPHEMERAL,
    )


@check(check_channel_type)
@events_blueprint.command(
    "add-release-channel",
    description=(
        "Add Crunchy's release webhook to a channel of "
        "your choice to get the latest Anime release details."
    ),
    defer_register=False,
)
async def add_release_channel(app: CommandHandler, channel: Channel) -> Response:

    avatar = assetloader.get_base64_asset("crunchy-128.webp")
    await app.http.request(
        "POST",
        f"/channels/{channel.id}/webhooks",
        pass_token=True,
        json={
            "name": "Crunchy Anime News",
            "avatar": f"data:image/webp;base64,{avatar}",
        },
    )

    return Response(
        content=(
            f"<:exitment:717784139641651211> All done! I'll send news to "
            f"<#{channel.id}> when a new Anime episode is out!"
        ),
        flags=ResponseFlags.EPHEMERAL,
    )


@add_news_channel.error
@add_release_channel.error
async def on_command_error(_: Interaction, e: Exception):
    if isinstance(e, Forbidden):
        return Response(
            content=(
                "<:HimeSad:676087829557936149> Oops! Looks like I'm missing permissions "
                "to do this. Make sure I have the permission `MANAGE_WEBHOOKS` and try again."
            ),
            flags=ResponseFlags.EPHEMERAL,
        )

    raise e
