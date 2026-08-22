import sys
from datetime import datetime
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


class ConsoleUI:
    def __init__(self) -> None:
        self.console = Console(
            file=sys.stdout,
            force_terminal=True,
            color_system="truecolor",
            markup=True,
            highlight=False,
            emoji=False
        )

        self._last_key: str | None = None
        self._last_ts: str | None = None

        self._group_gap = 5 * 60

    def reset_group(self) -> None:
        self._last_key = None
        self._last_ts = None

    def _same_group(self, key: str, timestamp: int) -> bool:
        if self._last_key != key:
            return False
        if self._last_ts is None:
            return False
        return (timestamp - self._last_ts) <= self._group_gap

    def banner(self) -> None:
        self.console.print()

        self.console.print(
            Panel.fit(
                "[bold cyan]napishi_sashke[/bold cyan]",
                border_style="cyan",
            )
        )

        self.console.print()

    def connected(self) -> None:
        self.console.print(
            "[bold green]✓ Connected to server[/bold green]"
        )

    def disconnected(self) -> None:
        self.console.print(
            "[bold red]✗ Disconnected[/bold red]"
        )

    def info(
        self,
        message: str,
    ) -> None:
        self.console.print(
            f"[cyan]{message}[/cyan]"
        )

    def success(
        self,
        message: str,
    ) -> None:
        self.console.print(
            f"[green]✓ {message}[/green]"
        )

    def error(
        self,
        message: str,
    ) -> None:
        self.console.print(
            f"[bold red]✗ {message}[/bold red]"
        )

    def message(self, sender: str, text: str, timestamp: int) -> None:
        key = sender
        t = datetime.fromtimestamp(timestamp).strftime("%H:%M")

        if self._same_group(key, timestamp):
            print_formatted_text(HTML(f"         {text}"))
        else:
            print_formatted_text(HTML(
                f"<ansiblue>{t}</ansiblue>  <b>{sender}</b>\n"
                f"         {text}\n"
            ))
        self._last_key = key
        self._last_ts = timestamp

    def own_message(self, to: str, text: str, timestamp: int | None = None) -> None:
        key = "you"
        ts = timestamp or int(datetime.now().timestamp())
        t = datetime.now().strftime("%H:%M")

        if self._same_group(key, ts):
            print_formatted_text(HTML(f"         {text}"))
        else:
            print_formatted_text(HTML(
                f"\n<ansigreen>{t}</ansigreen>  <b>you</b> → {to}\n"
                f"         {text}"
            ))

        self._last_key = key
        self._last_ts = ts



    def system(
        self,
        message: str,
    ) -> None:
        self.console.print("\n")
        self.console.print(
            Panel(
                message,
                border_style="yellow",
                title="System",
                expand=False,
            )
        )

    def prompt(self) -> str:
        return "you > "

    def help(self):
        self.console.print(
            """
    [cyan]Commands:[/cyan]

      /msg <user> <text>
      /photo <path> [caption]
      /video <path> [caption]
      /audio <path> [caption]
      /chat <user>
      /help
      /quit

    """
        )