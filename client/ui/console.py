import sys
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

try:
    from PIL import Image
    from rich_pixels import Pixels
    _HAS_IMAGE = True
except ImportError:
    _HAS_IMAGE = False

from services.voice import VoiceService, format_voice_line


class ConsoleUI:
    def __init__(self) -> None:
        self.console = Console(
            file=sys.stdout,
            force_terminal=True,
            color_system="truecolor",
            markup=True,
            highlight=False,
            emoji=False,
        )

        self._last_key: str | None = None
        self._last_ts: int | None = None

        self._group_gap = 5 * 60
        # Max terminal columns for media (leave margin for padding)
        self._media_max_width = 60

        # Registered voice messages for click / /play
        # list of (index, path, waveform_line)
        self._voices: list[dict] = []
        self._voice_counter = 0
        self.voice_service = VoiceService()

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

    def _render_image(self, path: Path) -> bool:
        """Render image as half-block pixels. Returns True on success."""
        if not _HAS_IMAGE:
            return False
        try:
            with Image.open(path) as im:
                im = im.convert("RGB")
                max_w = min(self.console.size.width - 12, self._media_max_width)
                if im.width > max_w:
                    ratio = max_w / im.width
                    new_h = int(im.height * ratio)
                    if new_h % 2:
                        new_h -= 1
                    new_h = max(2, new_h)
                    im = im.resize((max_w, new_h), Image.Resampling.LANCZOS)
                elif im.height % 2:
                    # ensure even height for half-blocks
                    im = im.resize((im.width, im.height - 1), Image.Resampling.LANCZOS)

                pixels = Pixels.from_image(im)
                # indent to match message text
                self.console.print(pixels)
            return True
        except Exception:
            return False

    def _extract_video_frame(self, video_path: Path) -> Path | None:
        """Extract first frame of video to a temporary JPEG. Returns path or None."""
        try:
            tmp = tempfile.NamedTemporaryFile(
                suffix=".jpg", delete=False
            )
            tmp.close()
            out = Path(tmp.name)
            # -ss 0 -vframes 1 : first frame, quiet
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i", str(video_path),
                    "-ss", "0",
                    "-vframes", "1",
                    "-q:v", "2",
                    str(out),
                ],
                capture_output=True,
                timeout=15,
            )
            if result.returncode == 0 and out.exists() and out.stat().st_size > 0:
                return out
            out.unlink(missing_ok=True)
            return None
        except Exception:
            return None

    def register_voice(self, path: Path) -> int:
        """Register a voice file and return its play index."""
        self._voice_counter += 1
        idx = self._voice_counter
        wf = VoiceService.waveform(path, width=28)
        dur = VoiceService.format_duration(VoiceService.duration_seconds(path))
        self._voices.append({
            "index": idx,
            "path": path,
            "waveform": wf,
            "duration": dur,
        })
        # keep only last 50
        if len(self._voices) > 50:
            self._voices = self._voices[-50:]
        return idx

    def get_voice(self, index: int | None = None) -> dict | None:
        if not self._voices:
            return None
        if index is None:
            return self._voices[-1]
        for v in self._voices:
            if v["index"] == index:
                return v
        return None

    def play_voice(self, index: int | None = None) -> bool:
        """Play registered voice by index (or last). Returns True if started."""
        v = self.get_voice(index)
        if v is None:
            return False
        self.voice_service.play(v["path"])
        return True

    def render_voice(self, path: Path, caption: str | None = None) -> None:
        """Draw voice message as:  ►3 ▁▂▃▅▇▅▃▂…  0:04"""
        if not path.exists():
            print_formatted_text(HTML("         [voice] (file missing)"))
            return
        idx = self.register_voice(path)
        v = self.get_voice(idx)
        assert v is not None
        line = format_voice_line(v["waveform"], v["duration"], index=idx)
        # cyan play button + dim waveform
        print_formatted_text(HTML(
            f"         <ansigreen>►</ansigreen><ansicyan>{idx}</ansicyan> "
            f"<ansiyellow>{v['waveform']}</ansiyellow>  "
            f"<ansigray>{v['duration']}</ansigray>"
        ))
        if caption:
            print_formatted_text(HTML(f"         {caption}"))
        self.console.print(
            f"[dim]         click / /play {idx} — воспроизвести[/dim]"
        )

    def media(
        self,
        path: Path,
        media_type: str,
        caption: str | None = None,
    ) -> None:
        """
        Display media in the terminal.
        - photo / image: half-block pixel art
        - video: first-frame thumbnail
        - voice / audio: ASCII waveform with play index
        """
        if media_type in ("voice", "audio") and path.exists():
            self.render_voice(path, caption=caption)
            return

        label = f"[{media_type}] {path.name}"
        shown = False

        if media_type in ("photo", "image") and path.exists():
            shown = self._render_image(path)
        elif media_type == "video" and path.exists():
            frame = self._extract_video_frame(path)
            if frame is not None:
                try:
                    shown = self._render_image(frame)
                finally:
                    frame.unlink(missing_ok=True)

        if not shown:
            print_formatted_text(HTML(f"         {label}"))
            if caption:
                print_formatted_text(HTML(f"         {caption}"))
        else:
            if caption:
                print_formatted_text(HTML(f"         {caption}"))

    def recording_status(self, waveform: str, elapsed: float) -> None:
        """Overwrite current line with live recording indicator."""
        dur = VoiceService.format_duration(elapsed)
        # clear line + print
        sys.stdout.write("\r\033[2K")
        sys.stdout.write(
            f"  \033[31m● REC\033[0m  \033[33m{waveform}\033[0m  {dur}  "
            f"\033[2m(Enter / /voice — стоп)\033[0m"
        )
        sys.stdout.flush()

    def clear_recording_status(self) -> None:
        sys.stdout.write("\r\033[2K")
        sys.stdout.flush()

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

    def message_with_media(
        self,
        sender: str,
        text: str,
        timestamp: int,
        media_path: Path | None = None,
        media_type: str | None = None,
    ) -> None:
        """Print message header + optional media + caption/text."""
        key = sender
        t = datetime.fromtimestamp(timestamp).strftime("%H:%M")

        if not self._same_group(key, timestamp):
            print_formatted_text(HTML(
                f"<ansiblue>{t}</ansiblue>  <b>{sender}</b>"
            ))
        self._last_key = key
        self._last_ts = timestamp

        if media_path and media_type:
            self.media(media_path, media_type, caption=text or None)
        elif text:
            print_formatted_text(HTML(f"         {text}"))

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

    def own_message_with_media(
        self,
        to: str,
        text: str,
        media_path: Path | None = None,
        media_type: str | None = None,
        timestamp: int | None = None,
    ) -> None:
        key = "you"
        ts = timestamp or int(datetime.now().timestamp())
        t = datetime.now().strftime("%H:%M")

        if not self._same_group(key, ts):
            print_formatted_text(HTML(
                f"\n<ansigreen>{t}</ansigreen>  <b>you</b> → {to}"
            ))
        self._last_key = key
        self._last_ts = ts

        if media_path and media_type:
            self.media(media_path, media_type, caption=text or None)
        elif text:
            print_formatted_text(HTML(f"         {text}"))

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
      /voice              — запись голосового (повторно — стоп и отправка)
      /play [n]           — воспроизвести голосовое (последнее или №n)
      /chat <user>
      /help
      /quit

    [dim]Мышь: клик в области ввода во время промпта → play последнего голосового[/dim]
    """
        )
