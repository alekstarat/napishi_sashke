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

    def message(self, sender: str, text: str, timestamp: int) -> None:
        t = datetime.fromtimestamp(timestamp).strftime("%H:%M")
        print_formatted_text(HTML(
            f"<ansiblue>{t}</ansiblue>  <b>{sender}</b>\n"
            f"         {text}\n"
        ))

    def own_message(self, to: str, text: str) -> None:
        t = datetime.now().strftime("%H:%M")
        print_formatted_text(HTML(
            f"<ansigreen>{t}</ansigreen>  <b>you</b> → {to}\n"
            f"         {text}\n"
        ))



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
      /help
      /quit

    """
        )