import random
import textwrap
from datetime import timedelta
from typing import List

from roid import (
    CommandsBlueprint,
    Response,
    Embed,
    InvokeContext,
    Option,
    ButtonStyle,
)
from roid.exceptions import AbortInvoke
from roid.objects import CompletedOption, PartialMessage, ResponseFlags
from roid.interactions import OptionData, Interaction, CommandType
from roid.deferred import DeferredButton

from crunchy.app import CommandHandler
from crunchy.config import EMBED_COLOUR, RANDOM_THUMBNAILS

search_blueprint = CommandsBlueprint()


def make_base_embed(interaction: Interaction, data: dict, specific: str) -> Embed:
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
        A discord embed object.
    """
    title = data["title_english"] or data["title"]

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

    return embed


def make_manga_embed(interaction: Interaction, data: dict) -> Embed:
    return make_base_embed(interaction, data, "Manga")


def make_anime_embed(interaction: Interaction, data: dict) -> Embed:
    return make_base_embed(interaction, data, "Anime")


async def get_best_anime_results(
    app: CommandHandler,
    interaction: Interaction,
    query: str,
) -> List[Embed]:
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
) -> List[Embed]:
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
    embeds = await get_best_anime_results(app=app, interaction=interaction, query=query)
    return Response(embed=embeds[0])


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
async def search_anime(
    app: CommandHandler,
    interaction: Interaction,
    query: str = Option(
        description="Search for the Manga you want here.",
        autocomplete=True,
    ),
):
    embeds = await get_best_manga_results(app=app, interaction=interaction, query=query)
    return Response(embed=embeds[0])


@search_anime.autocomplete
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
    guild_ids=[629317680481959946, 675647130647658527],
    type=CommandType.MESSAGE,
)
async def search_anime(
    app: CommandHandler,
    interaction: Interaction,
    message: PartialMessage,
):
    embeds = await get_best_anime_results(
        app=app, interaction=interaction, query=message.content
    )

    return Response(
        embed=embeds[0],
        components=[
            [
                previous_result,
                close,
                next_result,
            ]
        ],
        component_context={"embeds": embeds, "page": 0, "ttl": timedelta(minutes=2)},
    )


@search_blueprint.button(
    label="Close",
    style=ButtonStyle.DANGER,
    oneshot=True,
)
async def close():
    return Response(delete_parent=True)


@search_blueprint.button(label="Next Result", style=ButtonStyle.PRIMARY)
async def next_result(ctx: InvokeContext):
    embeds = ctx["embeds"]
    page = ctx["page"] + 1

    if page >= len(embeds):
        page = 0

    embed = embeds[page]
    return Response(
        embed=embed,
        components=[
            [
                previous_result,
                close,
                next_result,
            ]
        ],
        component_context={"page": page, "ttl": timedelta(minutes=2)},
    )


@search_blueprint.button(label="Previous Result", style=ButtonStyle.PRIMARY)
async def previous_result(ctx: InvokeContext):
    embeds = ctx["embeds"]
    page = ctx["page"] - 1

    if page < 0:
        page = len(embeds) - 1

    embed = embeds[page]
    return Response(
        embed=embed,
        components=[
            [
                previous_result,
                close,
                next_result,
            ]
        ],
        component_context={"page": page, "ttl": timedelta(minutes=2)},
    )
