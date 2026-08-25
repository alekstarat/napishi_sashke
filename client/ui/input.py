from __future__ import annotations

from typing import Callable

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys


class ConsoleInput:
    """
    Play last voice message:
      Ctrl+P
      /play
    """

    def __init__(
        self,
        on_play_last: Callable[[], None] | None = None,
    ) -> None:
        self._on_play_last = on_play_last
        self._session = PromptSession(mouse_support=False)

    def set_play_callback(self, cb: Callable[[], None] | None) -> None:
        self._on_play_last = cb

    async def read(self, prompt: str = "> ") -> str:
        kb = KeyBindings()

        @kb.add(Keys.ControlC)
        def _ctrl_c(event):
            event.app.exit(exception=KeyboardInterrupt)

        @kb.add("c-p")
        def _play(event):
            if self._on_play_last:
                self._on_play_last()

        return await self._session.prompt_async(
            prompt,
            key_bindings=kb,
            mouse_support=False,
        )