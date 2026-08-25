from __future__ import annotations

import asyncio
import struct
import subprocess
import tempfile
import threading
import time
from pathlib import Path

_BARS = "▁▂▃▄▅▆▇█"

def _find_record_input() -> list[str]:
    """Return ffmpeg input args for default microphone"""
    # Prefer PulseAudio, then ALSA default
    for args in (
        ["-f", "pulse", "-i", "default"],
        ["-f", "alsa", "-i", "default"],
        ["-f", "avfoundation", "-i", ":0"], #macOS
    ):
        pass
    import sys
    if sys.platform == "darwin":
        return ["-f", "avfoundation", "-i", ":0"]
    if sys.platform == "win32":
        return ["-f", "dshow", "-i", "audio=virtual-audio-capturer"]
    return ["-f", "pulse", "-i", "default"]


class VoiceService:
    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or Path(__file__).parent.parent / "cache" / "voice"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._proc: subprocess.Popen | None = None
        self._out_path: Path | None = None
        self._started_at: float | None = None
        self._play_proc: subprocess.Popen | None = None

    @property
    def is_recording(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def start_recording(self) -> Path:
        """Start recording to a temporary ogg file. Returns destination path."""
        if self.is_recording:
            raise RuntimeError("Already recording")

        self.stop_playback()

        out = self.cache_dir / f"rec_{int(time.time() * 1000)}.ogg"
        inp = _find_record_input()

        cmd = [
            "ffmpeg",
            "-y",
            *inp,
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "libopus",
            "-b:a", "24k",
            "-application", "voip",
            str(out),
        ]

        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._out_path = out
        self._started_at = time.time()
        return out

    def stop_recording(self) -> Path | None:
        """Stop recording and return the file path (or None if failed/empty)."""
        if self._proc is None:
            return None

        proc = self._proc
        path = self._out_path
        self._proc = None
        self._out_path = None
        started = self._started_at
        self._started_at = None

        # Graceful stop: send 'q' to ffmpeg
        try:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=1)
        except Exception:
            pass

        if path is None or not path.exists():
            return None
        if path.stat().st_size < 200:
            path.unlink(missing_ok=True)
            return None
        # Too short (< 0.3s) — discard
        if started and (time.time() - started) < 0.3:
            path.unlink(missing_ok=True)
            return None
        return path

    def recording_elapsed(self) -> float:
        if self._started_at is None:
            return 0.0
        return time.time() - self._started_at

    def play(self, path: Path) -> None:
        """Play audio file asynchronously (non-blocking)."""
        self.stop_playback()
        if not path.exists():
            return
        self._play_proc = subprocess.Popen(
            [
                "ffplay",
                "-nodisp",
                "-autoexit",
                "-loglevel", "quiet",
                str(path),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop_playback(self) -> None:
        if self._play_proc is not None:
            try:
                if self._play_proc.poll() is None:
                    self._play_proc.terminate()
                    try:
                        self._play_proc.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        self._play_proc.kill()
            except Exception:
                pass
            self._play_proc = None

    @staticmethod
    def duration_seconds(path: Path) -> float:
        try:
            r = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(path),
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return float(r.stdout.strip() or 0)
        except Exception:
            return 0.0

    @staticmethod
    def format_duration(seconds: float) -> str:
        s = max(0, int(round(seconds)))
        return f"{s // 60}:{s % 60:02d}"

    @classmethod
    def waveform(
            cls,
            path: Path,
            width: int = 28,
    ) -> str:
        """
        Build an ASCII waveform string like:
        ▁▂▃▅▇▅▃▂▁▃▅▇█▇▅▃
        """
        try:
            raw = subprocess.run(
                [
                    "ffmpeg",
                    "-v", "error",
                    "-i", str(path),
                    "-ac", "1",
                    "-ar", "8000",
                    "-f", "s16le",
                    "-",
                ],
                capture_output=True,
                timeout=15,
            ).stdout
        except Exception:
            return "·" * width

        if len(raw) < 4:
            return "·" * width

        n_samples = len(raw) // 2
        samples = struct.unpack("<" + "h" * n_samples, raw)

        chunk = max(1, n_samples // width)
        levels: list[str] = []
        peak = 1.0
        rms_list: list[float] = []

        for i in range(width):
            chunk_s = samples[i * chunk: (i + 1) * chunk]
            if not chunk_s:
                rms_list.append(0.0)
                continue
            rms = (sum(s * s for s in chunk_s) / len(chunk_s)) ** 0.5
            rms_list.append(rms)
            peak = max(peak, rms)

        for rms in rms_list:
            # normalize, bias a bit so quiet speech still shows
            norm = min(1.0, (rms / peak) * 1.15)
            idx = min(7, int(norm * 7))
            levels.append(_BARS[idx])

        return "".join(levels)

    def live_waveform(self, width: int = 20) -> str:
        """Fake animated waveform while recording (no live PCM access via ffmpeg easily)."""
        t = time.time()
        bars = []
        for i in range(width):
            # pseudo-random based on time + position
            v = abs(((t * 7 + i * 1.7) % 2) - 1)  # triangle
            v = v * (0.4 + 0.6 * abs(((t * 3.1 + i) % 2) - 1))
            idx = min(7, int(v * 7))
            bars.append(_BARS[idx])
        return "".join(bars)

def format_voice_line(
        waveform: str,
        duration: str,
        playing: bool = False,
        index: int | None = None,
) -> str:
    """Format display line:  ►  ▁▂▃▅…  0:03   or  ■ when playing."""
    icon = "■" if playing else "►"
    idx = f"{index}." if index is not None else ""
    return f"{icon}{idx} {waveform}  {duration}"