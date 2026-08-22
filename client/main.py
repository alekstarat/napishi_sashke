import asyncio
from pathlib import Path

import config
from client import MessengerClient
from handlers.dispatcher import PacketDispatcher
from handlers.history import HistoryHandler
from handlers.public_key import PublicKeyHandler
from handlers.message import MessageHandler
from handlers.error import ErrorHandler
from handlers.auth import AuthHandler
from handlers.send_ok import SendOkHandler
from config import (
    SERVER_URL,
    TOKEN
)


async def main():


    if TOKEN is None:
        token = input(
            "Token: "
        )
    else:
        token = TOKEN

    dispatcher = PacketDispatcher(
        handlers={}
    )

    dispatcher.register(MessageHandler())
    dispatcher.register(ErrorHandler())
    dispatcher.register(AuthHandler())
    dispatcher.register(SendOkHandler())
    dispatcher.register(HistoryHandler())
    dispatcher.register(PublicKeyHandler())

    client = MessengerClient(
        url=SERVER_URL,
        token=token,
        dispatcher=dispatcher,
        companion=config.COMPANION
    )

    await client.run()


if __name__ == "__main__":

    asyncio.run(
        main()
    )