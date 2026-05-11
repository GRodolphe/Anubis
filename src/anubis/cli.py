"""CLI entry point: argparse interface + interactive fallback."""

from __future__ import annotations

import argparse
import base64
import os
import subprocess
import sys

from anubis import __version__
from anubis.crypto import Encryption
from anubis.obfuscators import add_import_aliases, bugs, carbon, junk_code, oxyry
from anubis.terminal import IS_WINDOWS, blue, clear, error, leave, pause, purple, red, water


def _banner() -> str:
    return f"""


                              /$$$$$$  /$$   /$$ /$$   /$$ /$$$$$$$  /$$$$$$  /$$$$$$
                             /$$__  $$| $$$ | $$| $$  | $$| $$__  $$|_  $$_/ /$$__  $$
                            | $$  \\ $$| $$$$| $$| $$  | $$| $$  \\ $$  | $$  | $$  \\__/
                            | $$$$$$$$| $$ $$ $$| $$  | $$| $$$$$$$   | $$  |  $$$$$$
                            | $$__  $$| $$  $$$$| $$  | $$| $$__  $$  | $$   \\____  $$
                            | $$  | $$| $$\\  $$$| $$  | $$| $$  \\ $$  | $$   /$$  \\ $$
                            | $$  | $$| $$ \\  $$|  $$$$$$/| $$$$$$$/ /$$$$$$|  $$$$$$/
                            |__/  |__/|__/  \\__/ \\______/ |_______/ |______/ \\______/



        {purple(f"[>] Running with Python {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}")}

"""


def _ask_yn(prompt: str) -> bool:
    while True:
        ans = (
            input(purple(f"        [>] {prompt} [y/n] : ") + "\033[38;2;148;0;230m").strip().lower()
        )
        if ans == "y":
            return True
        if ans == "n":
            return False
        print(red("        [!] Error : Invalid option [y/n]"), end="")


def _interactive() -> tuple[str, bool, bool, bool, bool, bool, bool]:
    clear()
    print(water(_banner()), end="")

    while True:
        file = input(
            purple("        [>] Enter the python file you wish to obfuscate [script.py] : ")
            + "\033[38;2;148;0;230m"
        )
        if os.path.exists(file):
            break
        print(red("        [!] Error : That file does not exist"), end="")

    use_antidebug = _ask_yn("AntiDebug")
    use_junk = _ask_yn("Junk Code")
    use_rename = _ask_yn("Rename Classes, Functions, Variables & Parameters")
    use_import_alias = _ask_yn("Obfuscate import names (alias)")

    carbonate = oxy = False
    if use_rename:
        while True:
            ans = (
                input(
                    purple("        [>] Carbon (Offline) or Oxyry [c/o] : ")
                    + "\033[38;2;148;0;230m"
                )
                .strip()
                .lower()
            )
            if ans == "c":
                carbonate = True
                break
            if ans == "o":
                oxy = True
                break
            print(red("        [!] Error : Invalid option [c/o]"), end="")

    use_encrypt = _ask_yn("One Line Obfuscation (Can't compile to exe)")
    print(" ")
    return file, use_antidebug, use_junk, carbonate, oxy, use_import_alias, use_encrypt


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anubis",
        description="Anubis — Python obfuscator",
    )
    parser.add_argument(
        "file", nargs="?", help="Python file to obfuscate (omit for interactive mode)"
    )
    parser.add_argument("--antidebug", action="store_true", help="Inject anti-debugger thread")
    parser.add_argument("--junk", action="store_true", help="Add junk class definitions")
    parser.add_argument("--carbon", action="store_true", help="Rename identifiers (offline)")
    parser.add_argument("--oxyry", action="store_true", help="Rename identifiers via oxyry.com")
    parser.add_argument(
        "--import-alias",
        action="store_true",
        dest="import_alias",
        help="Obfuscate imported module names",
    )
    parser.add_argument(
        "--encrypt",
        action="store_true",
        help="One-line AES encryption (requires ancrypt at runtime, disables --compile)",
    )
    parser.add_argument("--compile", action="store_true", help="Compile output to exe with Nuitka")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _run_pipeline(
    src: str,
    *,
    use_junk: bool,
    use_antidebug: bool,
    carbonate: bool,
    use_oxyry: bool,
    use_import_alias: bool,
    use_encrypt: bool,
    key: str,
) -> str:
    if use_junk:
        src = junk_code(src)
    if use_antidebug:
        src = bugs(src)
    if use_junk:
        src = junk_code(src)
    if carbonate:
        src = carbon(src)
    if use_oxyry:
        src = oxyry(src)
    if use_import_alias:
        src = add_import_aliases(src)
    if use_encrypt:
        src = Encryption(key.encode()).write(key, src)
    return src


def _nuitka_compile(output_file: str) -> None:
    params = [
        "nuitka",
        "--onefile",
        "--include-module=psutil",
        "--remove-output",
        "--assume-yes-for-downloads",
        output_file,
    ]
    if IS_WINDOWS:
        params.insert(1, "--mingw64")
    p = subprocess.Popen(params, stdout=subprocess.DEVNULL, shell=IS_WINDOWS, cwd=os.getcwd())
    print(red("\n        [!] Exe may take a while to compile\n"), end="")
    p.wait()
    exe = output_file[:-3] + (".exe" if IS_WINDOWS else ".bin")
    print(blue(f"\n        [>] Compiled @ {exe}"), end="")


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    interactive = args.file is None

    if interactive:
        file, use_antidebug, use_junk, carbonate, oxy, use_import_alias, use_encrypt = (
            _interactive()
        )
        do_compile = False
    else:
        file = args.file
        if not os.path.exists(file):
            error(f"File not found: {file}")
        use_antidebug = args.antidebug
        use_junk = args.junk
        carbonate = args.carbon
        oxy = args.oxyry
        use_import_alias = args.import_alias
        use_encrypt = args.encrypt
        do_compile = args.compile
        clear()
        print(water(_banner()), end="")

    key = base64.b64encode(os.urandom(32)).decode()

    with open(file, encoding="utf-8") as f:
        src = f.read()

    src = _run_pipeline(
        src,
        use_junk=use_junk,
        use_antidebug=use_antidebug,
        carbonate=carbonate,
        use_oxyry=oxy,
        use_import_alias=use_import_alias,
        use_encrypt=use_encrypt,
        key=key,
    )

    output = f"{file[:-3]}-obf.py"
    with open(output, "w", encoding="utf-8") as f:
        f.write(src)

    print(blue(f"        [>] Obfuscated @ {output}"), end="")

    if interactive and not use_encrypt:
        do_compile = _ask_yn("Would you like to compile to an exe")

    if do_compile and use_encrypt:
        print(red("\n        [!] Cannot compile to exe when encryption is enabled"), end="")
    elif do_compile:
        _nuitka_compile(output)

    print(blue("\n        [>] Press any key to exit... "), end="")
    if interactive:
        pause()
    clear()
    leave()
