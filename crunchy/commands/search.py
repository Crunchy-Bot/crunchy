import random
import textwrap

from roid import (
    CommandsBlueprint,
    Response,
    Embed,
)
from roid.objects import CompletedOption, EmbedImage
from roid.interactions import OptionData, Interaction

from crunchy.app import CommandHandler
from crunchy.config import EMBED_COLOUR, RANDOM_THUMBNAILS

search_blueprint = CommandsBlueprint()


@search_blueprint.command(
    "anime",
    "Search for information on a given Anime.",
    guild_ids=[629317680481959946, 675647130647658527],
)
async def search_anime(
    app: CommandHandler,
    interaction: Interaction,
    query: str,
):
    results = await app.client.request(
        "GET",
        "data/anime/search",
        params={"query": query, "limit": 1},
    )

    first = results["data"]["hits"][0]
    title = first["title_english"] or first["title"]

    if first["title_japanese"] is not None:
        title = f"{title} ({first['title_japanese']})"

    description = first["description"] or "No Description."
    genres = first["genres"]
    rating = int(first["rating"] / 2)
    img_url = first["img_url"]

    stars = "\⭐" * rating
    genres = ", ".join(genres or ["None"])

    embed = Embed(
        color=EMBED_COLOUR, thumbnail=EmbedImage(url=random.choice(RANDOM_THUMBNAILS))
    )
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
        name="About this Anime",
        value=f"Rating - {stars}\nGenres - *{genres}*\n",
        inline=False,
    )
    embed.add_field(
        name="Description", value=textwrap.shorten(description, width=500), inline=False
    )

    return Response(content=query)


@search_anime.autocomplete
async def run_query(app: CommandHandler, query: OptionData = None):
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
