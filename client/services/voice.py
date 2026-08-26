from __future__ import annotations

import re
import struct
import subprocess
import sys
import time
from pathlib import Path


_BARS = "▁▂▃▄▅▆▇█"


def _run_ffmpeg_device_probe() -> str:
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-list_devices",
                "true",
                "-f",
                "dshow",
                "-i",
                "dummy",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )

    except FileNotFoundError:
        raise RuntimeError(
            "FFmpeg не найден в PATH."
        )

    except subprocess.TimeoutExpired:
        raise RuntimeError(
            "FFmpeg слишком долго определяет устройства."
        )

    return (
        (result.stderr or "")
        + "\n"
        + (result.stdout or "")
    )


def _find_windows_microphone() -> list[str]:
    """
    Finds an audio DirectShow device using FFmpeg.
    """

    output = _run_ffmpeg_device_probe()

    # New FFmpeg format:
    #
    # "USB 2.0 Webcam Device" (video)
    # "Microphone (Realtek(R) Audio)" (audio)

    devices = re.findall(
        r'"([^"]+)"\s*\(audio\)',
        output,
        flags=re.IGNORECASE,
    )

    if not devices:
        raise RuntimeError(
            "FFmpeg не обнаружил аудиоустройств DirectShow.\n\n"
            "Вывод FFmpeg:\n"
            f"{output}"
        )

    # First audio device.
    device = devices[0]

    return [
        "-f",
        "dshow",
        "-i",
        f"audio={device}",
    ]


def _find_record_input() -> list[str]:
    """
    Return FFmpeg input arguments for the default microphone.
    """

    if sys.platform == "win32":
        return _find_windows_microphone()

    if sys.platform == "darwin":
        return [
            "-f",
            "avfoundation",
            "-i",
            ":0",
        ]

    # Linux.
    #
    # PulseAudio/PipeWire's PulseAudio compatibility layer
    # is the preferred input.
    return [
        "-f",
        "pulse",
        "-i",
        "default",
    ]


class VoiceService:
    def __init__(
        self,
        cache_dir: Path | None = None,
    ) -> None:

        self.cache_dir = (
            cache_dir
            or Path(__file__).parent.parent
            / "cache"
            / "voice"
        )

        self.cache_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._proc: subprocess.Popen | None = None
        self._out_path: Path | None = None
        self._started_at: float | None = None

        self._play_proc: subprocess.Popen | None = None

    @property
    def is_recording(self) -> bool:
        return (
            self._proc is not None
            and self._proc.poll() is None
        )

    def start_recording(self) -> Path:
        """
        Start recording to an OGG/Opus file.

        The function verifies that FFmpeg actually started
        successfully before returning.
        """

        if self.is_recording:
            raise RuntimeError(
                "Already recording"
            )

        self.stop_playback()

        out = (
            self.cache_dir
            / f"rec_{int(time.time() * 1000)}.ogg"
        )

        try:
            inp = _find_record_input()
        except Exception:
            raise

        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",

            "-y",

            *inp,

            "-ac",
            "1",

            "-ar",
            "16000",

            "-c:a",
            "libopus",

            "-b:a",
            "24k",

            "-application",
            "voip",

            str(out),
        ]

        try:
            proc = subprocess.Popen(
                cmd,

                # We need stdin because FFmpeg will be stopped
                # by sending "q".
                stdin=subprocess.PIPE,

                stdout=subprocess.DEVNULL,

                # Keep stderr so we can report the actual FFmpeg
                # error if the process exits immediately.
                stderr=subprocess.PIPE,
            )

        except FileNotFoundError:
            raise RuntimeError(
                "FFmpeg не найден в PATH."
            )

        except OSError as exc:
            raise RuntimeError(
                f"Не удалось запустить FFmpeg: {exc}"
            )

        # Give FFmpeg a short amount of time to initialize
        # the input device.
        time.sleep(0.25)

        # FFmpeg has already exited -> recording failed.
        if proc.poll() is not None:
            error = ""

            try:
                if proc.stderr:
                    error = (
                        proc.stderr.read()
                        .decode(
                            "utf-8",
                            errors="replace",
                        )
                        .strip()
                    )
            except Exception:
                pass

            if not error:
                error = (
                    "FFmpeg завершился без сообщения об ошибке."
                )

            raise RuntimeError(
                "FFmpeg не смог начать запись:\n"
                f"{error}"
            )

        self._proc = proc
        self._out_path = out
        self._started_at = time.time()

        return out

    def stop_recording(self) -> Path | None:
        """
        Stop recording gracefully and return the resulting file.

        FFmpeg is stopped with the `q` command so that it can properly
        finalize the OGG container.
        """

        proc = self._proc
        path = self._out_path
        started = self._started_at

        self._proc = None
        self._out_path = None
        self._started_at = None

        if proc is None:
            return None

        try:
            if proc.poll() is None:

                # Proper FFmpeg shutdown.
                if proc.stdin:
                    try:
                        proc.stdin.write(
                            b"q\n"
                        )
                        proc.stdin.flush()
                    except (
                        BrokenPipeError,
                        OSError,
                    ):
                        pass

                try:
                    proc.wait(
                        timeout=5
                    )

                except subprocess.TimeoutExpired:
                    # Something went wrong. Force terminate.
                    try:
                        proc.kill()
                    except Exception:
                        pass

                    try:
                        proc.wait(
                            timeout=2
                        )
                    except Exception:
                        pass

        finally:
            try:
                if proc.stdin:
                    proc.stdin.close()
            except Exception:
                pass

        if path is None:
            return None

        if not path.exists():
            return None

        # Empty/tiny file.
        try:
            size = path.stat().st_size
        except OSError:
            return None

        if size < 200:
            path.unlink(
                missing_ok=True
            )
            return None

        # Discard recordings shorter than 0.3 sec.
        if (
            started is not None
            and time.time() - started < 0.3
        ):
            path.unlink(
                missing_ok=True
            )
            return None

        return path

    def recording_elapsed(self) -> float:
        if self._started_at is None:
            return 0.0

        return (
            time.time()
            - self._started_at
        )

    def play(
        self,
        path: Path,
    ) -> None:
        """
        Play audio asynchronously.
        """

        self.stop_playback()

        if not path.exists():
            return

        try:
            self._play_proc = subprocess.Popen(
                [
                    "ffplay",
                    "-nodisp",
                    "-autoexit",
                    "-loglevel",
                    "quiet",
                    str(path),
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        except FileNotFoundError:
            raise RuntimeError(
                "ffplay не найден. "
                "Убедись, что FFmpeg полностью установлен "
                "и добавлен в PATH."
            )

    def stop_playback(self) -> None:
        if self._play_proc is None:
            return

        try:
            if self._play_proc.poll() is None:

                self._play_proc.terminate()

                try:
                    self._play_proc.wait(
                        timeout=1
                    )

                except subprocess.TimeoutExpired:
                    self._play_proc.kill()

        except Exception:
            pass

        finally:
            self._play_proc = None

    @staticmethod
    def duration_seconds(
        path: Path,
    ) -> float:

        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(path),
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            return float(
                result.stdout.strip() or 0
            )

        except Exception:
            return 0.0

    @staticmethod
    def format_duration(
        seconds: float,
    ) -> str:

        s = max(
            0,
            int(round(seconds)),
        )

        return (
            f"{s // 60}:"
            f"{s % 60:02d}"
        )

    @classmethod
    def waveform(
        cls,
        path: Path,
        width: int = 28,
    ) -> str:

        try:
            raw = subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-i",
                    str(path),
                    "-ac",
                    "1",
                    "-ar",
                    "8000",
                    "-f",
                    "s16le",
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

        try:
            samples = struct.unpack(
                "<" + "h" * n_samples,
                raw,
            )
        except struct.error:
            return "·" * width

        chunk = max(
            1,
            n_samples // width,
        )

        levels: list[str] = []

        peak = 1.0
        rms_list: list[float] = []

        for i in range(width):

            chunk_s = samples[
                i * chunk:
                (i + 1) * chunk
            ]

            if not chunk_s:
                rms_list.append(0.0)
                continue

            rms = (
                sum(
                    s * s
                    for s in chunk_s
                )
                / len(chunk_s)
            ) ** 0.5

            rms_list.append(rms)

            peak = max(
                peak,
                rms,
            )

        for rms in rms_list:

            norm = min(
                1.0,
                (rms / peak) * 1.15,
            )

            idx = min(
                7,
                int(norm * 7),
            )

            levels.append(
                _BARS[idx]
            )

        return "".join(levels)

    def live_waveform(
        self,
        width: int = 20,
    ) -> str:
        """
        Animated-looking waveform used by the console UI.

        This is visual only; actual audio is recorded by FFmpeg.
        """

        t = time.time()

        bars = []

        for i in range(width):

            v = abs(
                ((t * 7 + i * 1.7) % 2)
                - 1
            )

            v = (
                v
                * (
                    0.4
                    + 0.6
                    * abs(
                        ((t * 3.1 + i) % 2)
                        - 1
                    )
                )
            )

            idx = min(
                7,
                int(v * 7),
            )

            bars.append(
                _BARS[idx]
            )

        return "".join(bars)


def format_voice_line(
    waveform: str,
    duration: str,
    playing: bool = False,
    index: int | None = None,
) -> str:
    """
    Format a voice message line.

    Example:
        ► ▁▂▃▅▇▅▃▂  0:03
    """

    icon = "■" if playing else "►"

    idx = (
        f"{index}."
        if index is not None
        else ""
    )

    return (
        f"{icon}"
        f"{idx} "
        f"{waveform}  "
        f"{duration}"
    )