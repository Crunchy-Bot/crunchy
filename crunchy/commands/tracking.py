from roid import CommandsBlueprint, Option, Response
from roid.interactions import OptionData, Interaction
from roid.objects import CompletedOption, ResponseFlags, Embed

from crunchy.app import CommandHandler
from crunchy.config import EMBED_COLOUR

tracking_blueprint = CommandsBlueprint()


@tracking_blueprint.command(
    "my-list",
    description=(
        "Get all your saved items for the given tracking "
        "list (Watchlist, Favourites, etc...)"
    ),
    guild_id=675647130647658527,
)
async def get_tracking(
    app: CommandHandler,
    interaction: Interaction,
    group: str = Option(
        description="Start typing the name of the list.",
        autocomplete=True,
    ),
):
    if group == "__NO_OP":
        return Response(
            content=(
                "Oops! You dont have any tracking lists, use the "
                "'/create-group' command to get started."
            ),
            flags=ResponseFlags.EPHEMERAL,
        )

    if interaction.member is not None:
        user_id = interaction.member.user.id
    else:
        user_id = interaction.user.id

    response = await app.client.request("GET", f"/tracking/{user_id}/{group}")
    data = response["data"]

    # todo :(


@get_tracking.autocomplete
async def get_tracking_groups(
    app: CommandHandler,
    interaction: Interaction,
    group: OptionData = None,
):
    """Gets all the user's existing groups / tags."""

    if interaction.member is not None:
        user_id = interaction.member.user.id
    else:
        user_id = interaction.user.id

    response = await app.client.request(
        "GET",
        f"/tracking/{user_id}/tags",
    )

    def alter(item):
        return item["tag_name"], item["tag_id"]

    results = map(alter, response["data"])
    items = [CompletedOption(name=name, value=id_) for (name, id_) in results]

    if len(items) == 0:
        items.append(
            CompletedOption(
                name=f"Oops! You dont have any tracking groups.",
                value="__NO_OP",
            )
        )
        items.append(
            CompletedOption(
                name=f"To get started making a tracking group",
                value="__NO_OP",
            )
        )
        items.append(
            CompletedOption(
                name=f"run the '/create-group' command.",
                value="__NO_OP",
            )
        )
    return items
