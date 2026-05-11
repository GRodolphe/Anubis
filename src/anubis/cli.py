"""CLI entry point: argparse interface + interactive fallback."""

from __future__ import annotations

import argparse
import base64
import os
import subprocess
import sys

from anubis import __version__
from anubis.config import load_config
from anubis.crypto import Encryption
from anubis.obfuscators import (
    add_import_aliases,
    bcc_mode,
    big_script,
    blind_constants,
    bugs,
    carbon,
    dynamic_imports,
    flatten_control_flow,
    junk_code,
    mix_strings,
    opaque_predicates,
    rft_mode,
    semantic_noise,
    xor_strings,
)
from anubis.terminal import IS_WINDOWS, blue, clear, error, is_ci, leave, pause, purple, red, water


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


def _interactive() -> tuple[
    str, bool, bool, bool, bool, bool, bool, bool, bool, bool, bool, bool, bool, bool, bool, bool
]:
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
    use_flatten = _ask_yn("Flatten Control Flow (state-machine rewrite)")
    use_opaque = _ask_yn("Opaque Predicates (always-true guards + dead branches)")
    use_mix_strings = _ask_yn("Mix Strings (replace literals with chr() chains)")
    use_xor_strings = _ask_yn("XOR String Encryption (keyed cipher, stronger than Mix Strings)")
    use_blind = _ask_yn("Constant Blinding (hide integer literals)")
    use_big_script = _ask_yn("Big Script (inflate with random junk data)")
    use_carbon = _ask_yn("Carbon — Rename Classes, Functions, Variables & Parameters")
    use_semantic = _ask_yn("Semantic Noise — Rename to misleading English names (LLM resistance)")
    use_import_alias = _ask_yn("Obfuscate import names (alias)")
    use_dynamic_imports = _ask_yn("Dynamic Imports — encode module names with XOR")
    use_encrypt = _ask_yn("AES Encryption — One Line Obfuscation (Can't compile to exe)")
    use_rft = _ask_yn("RFT — Run From Text (base64+zlib exec wrapper)")
    use_bcc = _ask_yn("BCC — Bytecode Compilation (marshal+zlib loader)")

    print(" ")
    return (
        file,
        use_antidebug,
        use_junk,
        use_flatten,
        use_opaque,
        use_mix_strings,
        use_xor_strings,
        use_blind,
        use_big_script,
        use_carbon,
        use_semantic,
        use_import_alias,
        use_dynamic_imports,
        use_encrypt,
        use_rft,
        use_bcc,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anubis",
        description="Anubis — Python obfuscator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
pipeline order (when combined):
  junk → antidebug → junk → flatten → opaque
  → carbon → semantic-noise
  → mix-strings → xor-strings → blind
  → import-alias → dynamic-imports → big-script
  → encrypt → rft → bcc
""",
    )
    parser.add_argument(
        "file", nargs="?", help="Python file to obfuscate (omit for interactive mode)"
    )

    g_transform = parser.add_argument_group("source transforms")
    g_transform.add_argument("--antidebug", action="store_true", help="Inject anti-debugger thread")
    g_transform.add_argument("--junk", action="store_true", help="Add junk class definitions")
    g_transform.add_argument(
        "--flatten",
        action="store_true",
        help="Flatten control flow: rewrite function bodies as while-True state machines",
    )
    g_transform.add_argument(
        "--opaque",
        action="store_true",
        help="Inject opaque predicates: wrap functions in always-true guards with dead branches",
    )
    g_transform.add_argument(
        "--mix-strings",
        action="store_true",
        dest="mix_strings",
        help='Replace string literals with chr() chains: "hi" → (chr(104)+chr(105))',
    )
    g_transform.add_argument(
        "--xor-strings",
        action="store_true",
        dest="xor_strings",
        help="XOR-encrypt string literals with a random key (stronger than --mix-strings)",
    )
    g_transform.add_argument(
        "--blind",
        action="store_true",
        help="Blind integer constants: replace N with (N^R)^R for random R",
    )
    g_transform.add_argument(
        "--big-script",
        action="store_true",
        dest="big_script",
        help="Inflate output with ~256 KB of random dead-code blobs",
    )
    g_transform.add_argument("--carbon", action="store_true", help="Rename identifiers (offline)")
    g_transform.add_argument(
        "--semantic-noise",
        action="store_true",
        dest="semantic_noise",
        help="Rename identifiers to misleading English names (LLM deobfuscation resistance)",
    )
    g_transform.add_argument(
        "--import-alias",
        action="store_true",
        dest="import_alias",
        help="Obfuscate imported module names with random aliases",
    )
    g_transform.add_argument(
        "--dynamic-imports",
        action="store_true",
        dest="dynamic_imports",
        help="Replace import statements with XOR-encoded __import__() calls",
    )

    g_encode = parser.add_argument_group("encoding / compilation")
    g_encode.add_argument(
        "--encrypt",
        action="store_true",
        help="AES-encrypt source into a self-decrypting one-liner (requires ancrypt, disables --compile)",
    )
    g_encode.add_argument(
        "--rft",
        action="store_true",
        help="RFT: encode source as zlib+base64 blob and exec() at runtime",
    )
    g_encode.add_argument(
        "--bcc",
        action="store_true",
        help="BCC: compile to bytecode, marshal+zlib+base64 encode into a loader stub",
    )
    g_encode.add_argument(
        "--compile",
        action="store_true",
        help="Compile final output to a standalone exe with Nuitka",
    )

    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI/CD mode: no interactive prompts, plain stdout, exit 1 on error",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        default=None,
        help="Output file path (default: <input-stem>-obf.py)",
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _run_pipeline(
    src: str,
    *,
    use_junk: bool,
    use_antidebug: bool,
    use_flatten: bool,
    use_opaque: bool,
    use_carbon: bool,
    use_semantic: bool,
    use_mix_strings: bool,
    use_xor_strings: bool,
    use_blind: bool,
    use_import_alias: bool,
    use_dynamic_imports: bool,
    use_big_script: bool,
    use_encrypt: bool,
    use_rft: bool,
    use_bcc: bool,
    key: str,
) -> str:
    # Structural passes first (before renaming)
    if use_junk:
        src = junk_code(src)
    if use_antidebug:
        src = bugs(src)
    if use_junk:
        src = junk_code(src)
    if use_flatten:
        src = flatten_control_flow(src)
    if use_opaque:
        src = opaque_predicates(src)
    # Renaming passes
    if use_carbon:
        src = carbon(src)
    if use_semantic:
        src = semantic_noise(src)
    # Data obfuscation passes
    if use_mix_strings:
        src = mix_strings(src)
    if use_xor_strings:
        src = xor_strings(src)
    if use_blind:
        src = blind_constants(src)
    # Import obfuscation
    if use_import_alias:
        src = add_import_aliases(src)
    if use_dynamic_imports:
        src = dynamic_imports(src)
    # Size inflation
    if use_big_script:
        src = big_script(src)
    # Encoding passes (outermost layer)
    if use_encrypt:
        src = Encryption(key.encode()).write(key, src)
    if use_rft:
        src = rft_mode(src)
    if use_bcc:
        src = bcc_mode(src)
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
    if is_ci():
        print(f"Compiling: {output_file}")
    else:
        print(red("\n        [!] Exe may take a while to compile\n"), end="")
    p.wait()
    exe = output_file[:-3] + (".exe" if IS_WINDOWS else ".bin")
    if is_ci():
        print(f"Compiled: {exe}")
    else:
        print(blue(f"\n        [>] Compiled @ {exe}"), end="")


def main() -> None:
    config = load_config()
    parser = _build_parser()
    if config:
        parser.set_defaults(**config)

    args = parser.parse_args()

    if args.ci:
        os.environ["ANUBIS_CI"] = "1"

    if args.file is None and is_ci():
        error("file argument is required in CI mode")

    interactive = args.file is None

    if interactive:
        (
            file,
            use_antidebug,
            use_junk,
            use_flatten,
            use_opaque,
            use_mix_strings,
            use_xor_strings,
            use_blind,
            use_big_script,
            use_carbon,
            use_semantic,
            use_import_alias,
            use_dynamic_imports,
            use_encrypt,
            use_rft,
            use_bcc,
        ) = _interactive()
        do_compile = False
    else:
        file = args.file
        if not os.path.exists(file):
            error(f"File not found: {file}")
        use_antidebug = args.antidebug
        use_junk = args.junk
        use_flatten = args.flatten
        use_opaque = args.opaque
        use_mix_strings = args.mix_strings
        use_xor_strings = args.xor_strings
        use_blind = args.blind
        use_big_script = args.big_script
        use_carbon = args.carbon
        use_semantic = args.semantic_noise
        use_import_alias = args.import_alias
        use_dynamic_imports = args.dynamic_imports
        use_encrypt = args.encrypt
        use_rft = args.rft
        use_bcc = args.bcc
        do_compile = args.compile
        if not is_ci():
            clear()
            print(water(_banner()), end="")

    key = base64.b64encode(os.urandom(32)).decode()

    with open(file, encoding="utf-8") as f:
        src = f.read()

    src = _run_pipeline(
        src,
        use_junk=use_junk,
        use_antidebug=use_antidebug,
        use_flatten=use_flatten,
        use_opaque=use_opaque,
        use_carbon=use_carbon,
        use_semantic=use_semantic,
        use_mix_strings=use_mix_strings,
        use_xor_strings=use_xor_strings,
        use_blind=use_blind,
        use_import_alias=use_import_alias,
        use_dynamic_imports=use_dynamic_imports,
        use_big_script=use_big_script,
        use_encrypt=use_encrypt,
        use_rft=use_rft,
        use_bcc=use_bcc,
        key=key,
    )

    output = args.output or f"{file[:-3]}-obf.py"
    with open(output, "w", encoding="utf-8") as f:
        f.write(src)

    if is_ci():
        print(f"Obfuscated: {output}")
    else:
        print(blue(f"        [>] Obfuscated @ {output}"), end="")

    if interactive and not use_encrypt and not use_rft and not use_bcc:
        do_compile = _ask_yn("Would you like to compile to an exe")

    if do_compile and use_encrypt:
        if is_ci():
            error("cannot use --compile with --encrypt")
        else:
            print(red("\n        [!] Cannot compile to exe when --encrypt is enabled"), end="")
    elif do_compile:
        _nuitka_compile(output)

    if not is_ci():
        print(blue("\n        [>] Press any key to exit... "), end="")
    if interactive:
        pause()
    if not is_ci():
        clear()
    leave()
