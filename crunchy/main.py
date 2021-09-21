import os
import uvicorn

from roid import SlashCommands


app = SlashCommands(
    application_id=int(os.getenv("APPLICATION_ID")),
    application_public_key=os.getenv("PUBLIC_KEY"),
    token=os.getenv("BOT_TOKEN"),
)


def main():
    ...


if __name__ == '__main__':
    main()
