from roid import CommandsBlueprint


tracking_blueprint = CommandsBlueprint()


@tracking_blueprint.command(
    ""
)
async def get_tracking():
    ...