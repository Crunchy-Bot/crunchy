import pprint

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


async def get_webhook_url(app: CommandHandler, channel: Channel, sub_type: str) -> str:
    avatar = assetloader.get_base64_asset("crunchy-128.webp")
    data = await app.http.request(
        "POST",
        f"/channels/{channel.id}/webhooks",
        pass_token=True,
        json={
            "name": f"Crunchy Anime {sub_type}",
            "avatar": f"data:image/webp;base64,{avatar}",
        },
    )

    return f"{DISCORD_API}/webhooks/{data['id']}/{data['token']}"


async def submit_webhook(
    app: CommandHandler, target: str, guild_id: int, webhook_url: str
):
    payload = {
        "guild_id": str(guild_id),
        "webhook_url": webhook_url,
    }

    await app.client.request("POST", f"/events/{target}/update", json=payload)


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
    app: CommandHandler, interaction: Interaction, channel: Channel
) -> Response:
    url = await get_webhook_url(app, channel, "News")

    await submit_webhook(
        app=app,
        target="news",
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
    app: CommandHandler, interaction: Interaction, channel: Channel
) -> Response:
    url = await get_webhook_url(app, channel, "Releases")

    await submit_webhook(
        app=app,
        target="releases",
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
