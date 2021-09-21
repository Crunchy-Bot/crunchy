from enum import Enum

from roid import (
    CommandsBlueprint,
    Response,
    ResponseFlags,
    Interaction,
    ButtonStyle,
    InvokeContext,
)
from roid.objects import Channel, ChannelType, MemberPermissions
from roid.helpers import check, require_user_permissions
from roid.exceptions import AbortInvoke, Forbidden, NotFound, DiscordServerError

from crunchy.app import CommandHandler
from crunchy.tools import assetloader
from crunchy.config import DISCORD_API, SUPPORT_SERVER_URL

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
                "this channel. Make sure it's a guild text channel and not a thread or direct message."
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


@require_user_permissions(
    MemberPermissions.MANAGE_GUILD | MemberPermissions.MANAGE_WEBHOOKS
)
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
        components=[[test_button]],
        component_context={"channel_id": channel.id, "webhook_url": url},
    )


@require_user_permissions(
    MemberPermissions.MANAGE_GUILD | MemberPermissions.MANAGE_WEBHOOKS
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
        components=[[test_button]],
        component_context={"channel_id": channel.id, "webhook_url": url},
    )


@events_blueprint.button("🚀 Test", style=ButtonStyle.PRIMARY, oneshot=True)
async def test_button(app: CommandHandler, ctx: InvokeContext):
    """
    A button that sends a test POST request to the webhook with a test message.

    If The request fails the error handler takes care of the responses otherwise
    it responds as a sucess.
    """
    try:
        channel_id = ctx["channel_id"]
        webhook_url = ctx["webook_url"]
    except KeyError:
        return Response(
            content=(
                f"Oops! Something has gone awfully wrong in the (events:test_button:KeyError) handler, "
                f"please contact the developer @ {SUPPORT_SERVER_URL}"
            )
        )

    await app.http.request(
        "POST",
        f"{webhook_url}?wait=true",
        pass_token=False,
        json={"content": "🚀 Testing, testing, I think we're ready!"},
    )

    return Response(
        content=f"I've sent a test message! If it appears in <#{channel_id}>",
        flags=ResponseFlags.EPHEMERAL,
    )


@test_button.error
async def on_button_error(_: Interaction, e: Exception):
    if isinstance(e, NotFound):
        return Response(
            content=(
                "<:HimeSad:676087829557936149> Weird!? This webhook seems to have "
                "been delete between me creating and you clicking the test button!"
            ),
            flags=ResponseFlags.EPHEMERAL,
        )

    if isinstance(e, DiscordServerError):
        return Response(
            content=(
                "<:HimeSad:676087829557936149> Oh no! Discord seem to be having some "
                "issues right now, this doesn't mean your event feed hasn't been "
                "added it just means we aren't able to test it right now."
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
