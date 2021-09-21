import pprint
from enum import Enum

from roid import CommandsBlueprint, Response, ResponseFlags, Interaction
from roid.objects import Channel, ChannelType
from roid.helpers import check
from roid.exceptions import AbortInvoke, Forbidden

from crunchy.app import CommandHandler
from crunchy.tools import assetloader
from crunchy.config import DISCORD_API


NOT_ENOUGH_DATA = AbortInvoke(
    content="<:HimeSad:676087829557936149> Oops! You've not given me enough information to work with here.",
    flags=ResponseFlags.EPHEMERAL,
)


class EventType(Enum):
    """The type of event to register with the API."""

    News = "news"
    Releases = "releases"


events_blueprint = CommandsBlueprint()


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


async def get_webhook_url(
    app: CommandHandler,
    channel: Channel,
    sub_type: EventType,
) -> str:
    """
    Creates a webhook in the given channel and returns the computed URL
    from the response.

    Any issue with the request is returned with a roid.exception's HTTPException
    subclass.

    Args:
        app:
            The slash commands app which has a http handler.

        channel:
            The channel to target the webhook creation.

        sub_type:
            Which event type the webhook belongs to (news or releases).

    Returns:
        A formatted webhook execution url.
    """

    avatar = assetloader.get_base64_asset("crunchy-128.webp")
    data = await app.http.request(
        "POST",
        f"/channels/{channel.id}/webhooks",
        pass_token=True,
        json={
            "name": f"Crunchy Anime {sub_type.name}",
            "avatar": f"data:image/webp;base64,{avatar}",
        },
    )

    return f"{DISCORD_API}/webhooks/{data['id']}/{data['token']}"


async def submit_webhook(
    app: CommandHandler,
    sub_type: EventType,
    guild_id: int,
    webhook_url: str,
):
    """
    Submits a webhook to the Crunchy API.

    Args:
        app:
            The slash commands app with the client attribute linking to the CrunchyApi
            handler.

        sub_type:
            Which event type the webhook belongs to (news or releases).

        guild_id:
            The id of the guild the webhook belongs to.

        webhook_url:
            The url of the webhook.
    """
    payload = {
        "guild_id": str(guild_id),
        "webhook_url": webhook_url,
    }

    await app.client.request("POST", f"/events/{sub_type.value}/update", json=payload)


@check(check_channel_type)
@events_blueprint.command(
    "add-news-channel",
    description=(
        "Add Crunchy's news webhook to a channel of "
        "your choice to get the latest Anime news."
    ),
    defer_register=False,
)
async def add_news_channel(
    app: CommandHandler,
    interaction: Interaction,
    channel: Channel,
) -> Response:
    url = await get_webhook_url(
        app=app,
        channel=channel,
        sub_type=EventType.News,
    )

    await submit_webhook(
        app=app,
        sub_type=EventType.News,
        guild_id=interaction.guild_id,
        webhook_url=url,
    )

    return Response(
        content=(
            f"<:exitment:717784139641651211> All done! I'll send"
            f" to <#{channel.id}> when I get some news."
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
async def add_release_channel(
    app: CommandHandler,
    interaction: Interaction,
    channel: Channel,
) -> Response:
    url = await get_webhook_url(
        app=app,
        channel=channel,
        sub_type=EventType.Releases,
    )

    await submit_webhook(
        app=app,
        sub_type=EventType.Releases,
        guild_id=interaction.guild_id,
        webhook_url=url,
    )

    return Response(
        content=(
            f"<:exitment:717784139641651211> All done! I'll send to "
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
