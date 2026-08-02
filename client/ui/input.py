from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout


class ConsoleInput:

    def __init__(self) -> None:
        self._session = PromptSession()

    async def read(
        self,
        prompt: str = "> ",
    ) -> str:


        return await self._session.prompt_async(
            prompt,
        )