"""Terminal color helpers and control utilities."""

from __future__ import annotations

import os
import sys
from typing import NoReturn


def _ansi_enable() -> None:
    os.system("")  # Enables ANSI escape codes on Windows


IS_WINDOWS: bool = sys.platform == "win32"


def clear() -> None:
    os.system("cls" if IS_WINDOWS else "clear")


def pause() -> None:
    if IS_WINDOWS:
        os.system("pause >nul")
    else:
        input()


def leave() -> NoReturn:
    sys.exit(0)


def error(msg: str) -> NoReturn:
    print(red(f"        [!] Error : {msg}"), end="")
    pause()
    clear()
    leave()


# ---------------------------------------------------------------------------
# Gradient colour functions
# ---------------------------------------------------------------------------


def red(text: str) -> str:
    _ansi_enable()
    faded = ""
    for line in text.splitlines():
        green = 250
        for ch in line:
            green = max(0, green - 5)
            faded += f"\033[38;2;255;{green};0m{ch}\033[0m"
        faded += "\n"
    return faded


def blue(text: str) -> str:
    _ansi_enable()
    faded = ""
    for line in text.splitlines():
        green = 0
        for ch in line:
            green = min(255, green + 3)
            faded += f"\033[38;2;0;{green};255m{ch}\033[0m"
        faded += "\n"
    return faded


def water(text: str) -> str:
    _ansi_enable()
    faded = ""
    green = 10
    for line in text.splitlines():
        faded += f"\033[38;2;0;{green};255m{line}\033[0m\n"
        green = min(255, green + 15)
    return faded


def purple(text: str) -> str:
    _ansi_enable()
    faded = ""
    r, going_down = 40, False
    for line in text.splitlines():
        for ch in line:
            if going_down:
                r -= 3
            else:
                r += 3
            if r > 254:
                r, going_down = 255, True
            elif r < 1:
                r, going_down = 30, False
            faded += f"\033[38;2;{r};0;220m{ch}\033[0m"
    return faded
