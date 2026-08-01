from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


class ConsoleUI:
    def __init__(self) -> None:
        self.console = Console(
            force_terminal=True,
            color_system="standard",
            markup=True
        )

    def banner(self) -> None:
        self.console.print()

        self.console.print(
            Panel.fit(
                "[bold cyan]Private Messenger[/bold cyan]",
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

    def message(
            self,
            sender: str,
            text: str,
            timestamp: int,
    ) -> None:
        time = datetime.fromtimestamp(
            timestamp
        ).strftime("%H:%M")

        self.console.print(
            f"[blue]{time}[/blue] "
            f"[bold]{sender}[/bold]"
        )

        self.console.print()

        self.console.print(
            f"  {text}"
        )

        self.console.print()

    def system(
        self,
        message: str,
    ) -> None:
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
      /help
      /quit

    """
        )