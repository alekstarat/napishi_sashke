import asyncio

from client import MessengerClient
from handlers.dispatcher import PacketDispatcher
from handlers.history import HistoryHandler

from handlers.message import MessageHandler
from handlers.error import ErrorHandler
from handlers.auth import AuthHandler
from handlers.send_ok import SendOkHandler
from config import (
    SERVER_URL,
)


async def main():

    token = input(
        "Token: "
    )


    dispatcher = PacketDispatcher(
        handlers={}
    )

    dispatcher.register(MessageHandler())
    dispatcher.register(ErrorHandler())
    dispatcher.register(AuthHandler())
    dispatcher.register(SendOkHandler())
    dispatcher.register(HistoryHandler())

    client = MessengerClient(
        url=SERVER_URL,
        token=token,
        dispatcher=dispatcher,
    )


    await client.run()


if __name__ == "__main__":

    asyncio.run(
        main()
    )