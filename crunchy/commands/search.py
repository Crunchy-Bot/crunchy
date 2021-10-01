import random
import textwrap
from datetime import timedelta
from typing import List, Tuple

from roid import (
    CommandsBlueprint,
    Response,
    Embed,
    InvokeContext,
    Option,
)
from roid.components import SelectOption
from roid.exceptions import AbortInvoke
from roid.objects import CompletedOption, PartialMessage, ResponseFlags, ResponseType
from roid.interactions import OptionData, Interaction, CommandType

from crunchy.app import CommandHandler
from crunchy.config import EMBED_COLOUR, RANDOM_THUMBNAILS

search_blueprint = CommandsBlueprint()


EntityAndEmbed = Tuple[str, Embed]


@search_blueprint.command(
    "anime",
    "Search for information on a given Anime.",
)
async def search_anime(
    app: CommandHandler,
    interaction: Interaction,
    query: str = Option(
        description="Search for the Anime you want here.",
        autocomplete=True,
    ),
):

    data = await app.client.request(
        "GET",
        f"/data/anime/{query}",
    )

    _, embed = make_manga_embed(interaction, data['data'])
    return Response(embed=embed)


@search_anime.autocomplete
async def run_anime_query(app: CommandHandler, query: OptionData = None):
    """Searches our api to fill the autocomplete select boxes."""
    results = await app.client.request(
        "GET",
        "data/anime/search",
        params={"query": query.value, "limit": 5},
    )

    hits = results["data"]["hits"]
    return [
        CompletedOption(name=hit.get("title_english") or hit["title"], value=hit["id"])
        for hit in hits
    ]


@search_blueprint.command(
    "manga",
    "Search for information on a given Manga.",
)
async def search_manga(
    app: CommandHandler,
    interaction: Interaction,
    query: str = Option(
        description="Search for the Manga you want here.",
        autocomplete=True,
    ),
):
    data = await app.client.request(
        "GET",
        f"/data/manga/{query}",
    )

    _, embed = make_manga_embed(interaction, data['data'])
    return Response(embed=embed)


@search_manga.autocomplete
async def run_manga_query(app: CommandHandler, query: OptionData = None):
    """Searches our api to fill the autocomplete select boxes."""
    results = await app.client.request(
        "GET",
        "data/manga/search",
        params={"query": query.value, "limit": 5},
    )

    hits = results["data"]["hits"]
    return [
        CompletedOption(name=hit.get("title_english") or hit["title"], value=hit["id"])
        for hit in hits
    ]


@search_blueprint.command(
    "Search Anime",
    type=CommandType.MESSAGE,
)
async def search_anime_from_message(
    app: CommandHandler,
    interaction: Interaction,
    message: PartialMessage,
):
    embeds = await get_best_anime_results(
        app=app, interaction=interaction, query=message.content
    )

    select_options = [
        SelectOption(label=title, value=str(i), default=i == 0)
        for i, (title, _) in enumerate(embeds)
    ]

    return Response(
        embed=embeds[0][1],
        components=[
            select_other_results.with_options(select_options),
        ],
        component_context={
            "embeds": embeds,
            "select_options": select_options,
            "ttl": timedelta(minutes=2),
        },
    )


@search_blueprint.command(
    "Search Manga",
    type=CommandType.MESSAGE,
)
async def search_anime_from_message(
    app: CommandHandler,
    interaction: Interaction,
    message: PartialMessage,
):
    embeds = await get_best_manga_results(
        app=app, interaction=interaction, query=message.content
    )

    select_options = [
        SelectOption(label=title, value=str(i), default=i == 0)
        for i, (title, _) in enumerate(embeds)
    ]

    return Response(
        embed=embeds[0][1],
        components=[
            select_other_results.with_options(select_options),
        ],
        component_context={
            "embeds": embeds,
            "select_options": select_options,
            "ttl": timedelta(minutes=2),
        },
    )


@search_blueprint.select(placeholder="Other Results")
async def select_other_results(ctx: InvokeContext, index: str):
    """
    Allows the user to select a list of embeds and rendering that result.

    Args:
        ctx:
            The invoke context to pass the embeds and select_options from the parent.
        index:
            The index of the embed to render. This comes as a string but is converted
            to a int.
    """
    index = int(index)
    embeds: List[EntityAndEmbed] = ctx["embeds"]
    select_options = ctx["select_options"]

    option = select_options.pop(index)
    select_options.insert(0, option)

    return Response(
        embed=embeds[index][1],
        components=[
            select_other_results.with_options(select_options),
        ],
        component_context={
            "ttl": timedelta(minutes=2),
        },
    )


def make_base_embed(
    interaction: Interaction, data: dict, specific: str
) -> EntityAndEmbed:
    """
    Makes a general result embed with a specific name i.e. Manga or Anime.

    Args:
        interaction:
            The interaction data invoking the command.
        data:
            The data to populate the embed with.
        specific:
            The specific type of result (Anime or Manga).

    Returns:
        A discord embed object. With the original entity title.
    """
    title = data.get("title_english") or data["title"]

    if data["title_japanese"] is not None:
        title = f"{title} ({data['title_japanese']})"

    description = data["description"] or "No Description."
    genres = data["genres"]
    rating = int(data["rating"] / 2)
    img_url = data["img_url"]

    stars = "\⭐" * rating
    genres = ", ".join(genres or ["None"])

    embed = Embed(color=EMBED_COLOUR)
    embed.set_thumbnail(url=random.choice(RANDOM_THUMBNAILS))
    embed.set_author(
        name=f"{textwrap.shorten(title.strip(' '), width=100)}",
        icon_url="https://cdn.discordapp.com/emojis/676087821596885013.png?v=1",
    )

    if img_url is not None:
        embed.set_image(url=img_url)

    if interaction.member is None:
        user = interaction.user
    else:
        user = interaction.member.user

    embed.set_footer(
        text="Part of Crunchy, the Crunchyroll Discord bot. Powered by CF8",
        icon_url=user.avatar_url,
    )

    embed.add_field(
        name=f"About this {specific}",
        value=f"Rating - {stars}\nGenres - *{genres}*\n",
        inline=False,
    )

    embed.add_field(
        name="Description", value=textwrap.shorten(description, width=500), inline=False
    )

    return title, embed


def make_manga_embed(interaction: Interaction, data: dict) -> EntityAndEmbed:
    """Makes a embed with Manga being the targeted sub type."""
    return make_base_embed(interaction, data, "Manga")


def make_anime_embed(interaction: Interaction, data: dict) -> EntityAndEmbed:
    """Makes a embed with Anime being the targeted sub type."""
    return make_base_embed(interaction, data, "Anime")


async def get_best_anime_results(
    app: CommandHandler,
    interaction: Interaction,
    query: str,
) -> List[EntityAndEmbed]:
    """
    Gets the top 5 results from the Manga api and turns it into an Embed result.
    """

    results = await app.client.request(
        "GET",
        "data/anime/search",
        params={"query": query, "limit": 5},
    )

    if len(results["data"]["hits"]) == 0:
        embed = Embed(color=EMBED_COLOUR)
        embed.set_author(
            name="Oops! I cant find anything matching that sentence.",
            icon_url="https://cdn.discordapp.com/emojis/676087829557936149.png?v=1",
        )
        raise AbortInvoke(embed=embed, flags=ResponseFlags.EPHEMERAL)

    embeds = []
    for result in results["data"]["hits"]:
        embed = make_anime_embed(interaction, result)
        embeds.append(embed)

    return embeds


async def get_best_manga_results(
    app: CommandHandler,
    interaction: Interaction,
    query: str,
) -> List[EntityAndEmbed]:
    """
    Gets the top 5results from the Manga api and turns it into an Embed result.
    """

    results = await app.client.request(
        "GET",
        "data/manga/search",
        params={"query": query, "limit": 5},
    )

    if len(results["data"]["hits"]) == 0:
        embed = Embed(color=EMBED_COLOUR)
        embed.set_author(
            name="Oops! I cant find anything matching that sentence.",
            icon_url="https://cdn.discordapp.com/emojis/676087829557936149.png?v=1",
        )
        raise AbortInvoke(embed=embed, flags=ResponseFlags.EPHEMERAL)

    embeds = []
    for result in results["data"]["hits"]:
        embed = make_manga_embed(interaction, result)
        embeds.append(embed)

    return embeds
