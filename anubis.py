# Made by 0sir1ss @ https://github.com/0sir1ss/Anubis
import ast
import argparse
import base64
import hashlib
import io
import os
import platform
import random
import re
import string
import subprocess
import sys
import tokenize

import requests
from regex import F
from Crypto import Random
from Crypto.Cipher import AES

IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    os.system("title Anubis @ github.com/GRodolphe/Anubis")


# ---------------------------------------------------------------------------
# Terminal helpers
# ---------------------------------------------------------------------------

def _ansi_enable():
    os.system("")


def clear():
    os.system("cls" if IS_WINDOWS else "clear")


def pause():
    if IS_WINDOWS:
        os.system("pause >nul")
    else:
        input()


def leave():
    try:
        sys.exit()
    except SystemExit:
        raise
    except Exception:
        exit()


def error(msg: str):
    print(red(f"        [!] Error : {msg}"), end="")
    pause()
    clear()
    leave()


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
        if green < 255:
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


# ---------------------------------------------------------------------------
# Obfuscation helpers
# ---------------------------------------------------------------------------

def _random_name(length: int | None = None) -> str:
    n = length or random.randint(8, 20)
    return "".join(random.choice("Il") for _ in range(n))


def _unique_name(used: set) -> str:
    name = _random_name()
    while name in used:
        name = _random_name()
    used.add(name)
    return name


def remove_docs(source: str) -> str:
    io_obj = io.StringIO(source)
    out = ""
    prev_toktype = tokenize.INDENT
    last_lineno = -1
    last_col = 0
    for tok in tokenize.generate_tokens(io_obj.readline):
        token_type, token_string = tok[0], tok[1]
        start_line, start_col = tok[2]
        end_line, end_col = tok[3]
        if start_line > last_lineno:
            last_col = 0
        if start_col > last_col:
            out += " " * (start_col - last_col)
        if token_type == tokenize.COMMENT:
            pass
        elif token_type == tokenize.STRING:
            if prev_toktype not in (tokenize.INDENT, tokenize.NEWLINE):
                if start_col > 0:
                    out += token_string
        else:
            out += token_string
        prev_toktype = token_type
        last_col = end_col
        last_lineno = end_line
    return "\n".join(l for l in out.splitlines() if l.strip())


def do_rename(pairs: dict, code: str) -> str:
    for key, val in pairs.items():
        code = re.sub(fr"\b({re.escape(key)})\b", val, code, flags=re.MULTILINE)
    return code


def _collect_imported_names(parsed) -> set:
    """Return all module/alias names introduced by import statements.

    These must NOT be renamed because they correspond to actual module names
    on disk (fixes: github.com/0sir1ss/Anubis/issues/31).
    """
    names = set()
    for node in ast.walk(parsed):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # `import foo` binds 'foo'; `import foo as bar` binds 'bar'
                names.add(alias.asname if alias.asname else alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname if alias.asname else alias.name)
    return names


def carbon(code: str) -> str:
    code = remove_docs(code)
    parsed = ast.parse(code)

    protected = _collect_imported_names(parsed)

    funcs = {
        node for node in ast.walk(parsed)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    classes = {
        node for node in ast.walk(parsed) if isinstance(node, ast.ClassDef)
    }
    args: set[str] = set()
    for node in ast.walk(parsed):
        if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Load):
            args.add(node.id)
        elif isinstance(node, ast.Attribute) and not isinstance(node.ctx, ast.Load):
            args.add(node.attr)
    for func in funcs:
        for arg_list in (
            func.args.args,
            func.args.kwonlyargs,
            [func.args.vararg] if func.args.vararg else [],
            [func.args.kwarg] if func.args.kwarg else [],
        ):
            for arg in arg_list:
                args.add(arg.arg)

    pairs: dict[str, str] = {}
    used: set[str] = set()

    for func in funcs:
        if func.name == "__init__" or func.name in protected:
            continue
        pairs[func.name] = _unique_name(used)

    for cls in classes:
        if cls.name in protected:
            continue
        pairs[cls.name] = _unique_name(used)

    for arg in args:
        if arg in protected:
            continue
        pairs[arg] = _unique_name(used)

    # Protect string literals during rename
    string_regex = r"('|\")[\x1f-\x7e]{1,}?('|\")"
    originals = [
        m.group().replace("\\", "\\\\")
        for m in re.finditer(string_regex, code, re.MULTILINE)
    ]
    placeholder = os.urandom(16).hex()
    code = re.sub(string_regex, f"'{placeholder}'", code, flags=re.MULTILINE)

    for i, orig in enumerate(originals):
        for key, val in pairs.items():
            originals[i] = re.sub(
                r"({.*)" + re.escape(key) + r"(.*})",
                r"\g<1>" + val + r"\2",
                originals[i],
                flags=re.MULTILINE,
            )

    cycles = [
        "[   " + "> " * n + "  " * (23 - n) + "]"
        for n in range(1, 24)
    ]

    i = 0
    while True:
        print("\r" + f"        {cycles[i]}", end="")
        i = (i + 1) % len(cycles)
        code = do_rename(pairs, code)
        if not any(re.findall(fr"\b{re.escape(k)}\b", code) for k in pairs):
            break

    replace_placeholder = r"('|\")" + placeholder + r"('|\")"
    for original in originals:
        code = re.sub(replace_placeholder, original, code, count=1, flags=re.MULTILINE)

    print("\r" + f"        {cycles[-1]}\n\n", end="")
    return code


def oxyry(code: str) -> str:
    try:
        src = "__all__ = []\n" + (
            code.replace('"', '\\"').replace("'", "\\'").replace("\\", "\\\\")
        )
        payload = {
            "append_source": False,
            "remove_docstrings": True,
            "rename_nondefault_parameters": True,
            "rename_default_parameters": True,
            "preserve": "",
            "source": src,
        }
        r = requests.post("https://pyob.oxyry.com/obfuscate", json=payload, timeout=30)
        data = r.json()
        try:
            code = data["dest"].replace("\\\\", "\\")
            code = re.sub(r"#\w*:[0-9]*", "", code)
            for pattern in ("__all__=[]\n", "__all__ =[]\n", "__all__ = []\n", "__all__= []\n"):
                code = code.replace(pattern, "")
            return code
        except KeyError:
            error(f"{data.get('errorMessage', 'Unknown error')}\n        [!] Please make sure your code is Python 3.3 - 3.7 compatible")
    except Exception:
        error("A problem occurred whilst contacting oxyry.com")


def add_import_aliases(code: str) -> str:
    """Obfuscate import names with aliasing (issue #26).

    Transforms `import X` → `import X as <obfuscated>` and updates all
    usages within the code.
    """
    parsed = ast.parse(code)
    pairs: dict[str, str] = {}
    used: set[str] = set()

    for node in ast.walk(parsed):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname is None:
                    original = alias.name.split(".")[0]
                    if original not in pairs:
                        pairs[original] = _unique_name(used)

    if not pairs:
        return code

    # Rewrite `import X` → `import X as obfname`
    for original, obfname in pairs.items():
        code = re.sub(
            rf"^(import\s+{re.escape(original)})\s*$",
            rf"\1 as {obfname}",
            code,
            flags=re.MULTILINE,
        )
        # Replace usages (e.g. `original.something` → `obfname.something`)
        code = re.sub(rf"\b{re.escape(original)}\b", obfname, code, flags=re.MULTILINE)
        # But restore the import line itself
        code = re.sub(
            rf"^(import\s+){re.escape(obfname)}(\s+as\s+{re.escape(obfname)})",
            rf"\g<1>{original}\2",
            code,
            flags=re.MULTILINE,
        )

    return code


def bugs(code: str) -> str:
    """Inject anti-debugger code.

    The ctypes.windll check is Windows-only; on other platforms we fall back
    to a pure-Python process-name scanner (fixes issue #29 / #18).
    """
    dbg = (
        "import binascii, platform as _platform, threading, time\n"
        "try:\n"
        "    from psutil import process_iter\n"
        "except ImportError:\n"
        "    import os as _os\n"
        "    _os.system('pip install psutil')\n"
        "    from psutil import process_iter\n"
        "_is_windows = _platform.system() == 'Windows'\n"
        "if _is_windows:\n"
        "    import ctypes\n"
        "    if not ctypes.windll.shell32.IsUserAnAdmin():\n"
        "        print('Please run this program as administrator.')\n"
        "        __import__('sys').exit(0)\n"
    )

    hex_names = [
        '53757370656e64', '50726f67726573732054656c6572696b20466964646c657220576562204465627567676572',
        '466964646c6572', '57697265736861726b', '64756d70636170', '646e537079',
        '646e5370792d783836', '6368656174656e67696e652d7838365f3634', '4854545044656275676765725549',
        '50726f636d6f6e', '50726f636d6f6e3634', '50726f636d6f6e363461', '50726f636573734861636b6572',
        '783332646267', '783634646267', '446f744e657444617461436f6c6c6563746f723332',
        '446f744e657444617461436f6c6c6563746f723634', '485454504465627567676572537663',
        '48545450204465627567676572', '696461', '6964613634', '69646167', '696461673634',
        '69646177', '696461773634', '69646171', '696461713634', '69646175', '696461753634',
        '7363796c6c61', '7363796c6c615f783634', '7363796c6c615f783836', '70726f74656374696f6e5f6964',
        '77696e646267', '7265736861636b6572', '496d706f7274524543', '494d4d554e4954594445425547474552',
        '4d65676144756d706572', '646973617373656d626c79', '4465627567', '5b435055496d6d756e697479',
        '4d65676144756d70657220312e3020627920436f6465437261636b6572202f20536e44', '436861726c6573',
        '636861726c6573', '4f4c4c59444247', '496d706f72745f7265636f6e7374727563746f72',
        '636f6465637261636b6572', '646534646f74', '696c737079', '67726179776f6c66',
        '73696d706c65617373656d626c79657870 6c6f726572', '7836346e657464756d706572', '687864',
        '7065746f6f6c73', '73696d706c65617373656d626c79', '68747470616e616c797a6572',
        '687474706465627567', '70726f636573736861636b6572', '6d656d6f727965646974', '6d656d6f7279',
        '646534646f746d6f64646564', '70726f63657373206861636b6572', '70726f63657373206d6f6e69746f72',
        '717435636f7265', '696461', '696d6d756e697479', '68747470', '74726166666963',
        '77697265736861726b', '666964646c6572', '7061636b6574', '6861636b6572', '6465627567',
        '646e737079', '646f747065656b', '646f747472616365', '70726f6364756d70', '6d616e61676572',
        '6d656d6f7279', '6e65744c696d6974', '6e65744c696d69746572', '73616e64626f78',
    ]

    dbg += (
        "d = " + repr(hex_names) + "\n"
        "d = [binascii.unhexlify(i.encode()).decode() for i in d if b' ' not in i.encode()]\n"
        "def _debugger_thread():\n"
        "    while True:\n"
        "        try:\n"
        "            for proc in process_iter():\n"
        "                for name in d:\n"
        "                    if name.lower() in proc.name().lower():\n"
        "                        proc.kill()\n"
        "        except Exception:\n"
        "            pass\n"
        "        time.sleep(0.5)\n"
        "threading.Thread(target=_debugger_thread, daemon=True).start()\n\n"
    )
    return dbg + code


def junk_code(code: str) -> str:
    """Wrap code in unreachable junk classes."""
    def _make_junk_block() -> str:
        block = ""
        class_names = [
            "".join(random.choices(string.ascii_letters, k=random.randint(8, 20)))
            for _ in range(random.randint(2, 5))
        ]
        for cls in class_names:
            func_names = [
                "__" + "".join(random.choices(string.ascii_letters, k=random.randint(8, 20)))
                for _ in range(random.randint(5, 15))
            ]
            block += f"class {cls}:\n    def __init__(self):\n"
            for fn in func_names:
                block += f"        self.{fn}()\n"
            for fn in func_names:
                params = ", ".join(
                    "".join(random.choices(string.ascii_letters, k=random.randint(5, 20)))
                    for _ in range(random.randint(1, 7))
                )
                block += f"    def {fn}(self, {params}):\n        return self.{random.choice(func_names)}()\n"
        return block

    return "\n" + _make_junk_block() + "\n" + code + "\n" + _make_junk_block()


# ---------------------------------------------------------------------------
# Encryption
# ---------------------------------------------------------------------------

class Encryption:

    def __init__(self, key: bytes):
        self.bs = AES.block_size
        self.key = hashlib.sha256(key).digest()

    def encrypt(self, raw: str) -> str:
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode())).decode()

    def _pad(self, s: str) -> str:
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    def write(self, key: str, source: str) -> str:
        wall = "__ANUBIS_ENCRYPTED__" * 25
        newcode = f"{wall}{key}{wall}"
        for line in source.split("\n"):
            newcode += self.encrypt(line) + wall
        return f"import ancrypt\nancrypt.load(__file__)\n'''\n{newcode}\n'''"


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

BANNER = f"""



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


# ---------------------------------------------------------------------------
# Interactive prompts
# ---------------------------------------------------------------------------

def _ask_yn(prompt: str, default: bool = False) -> bool:
    while True:
        ans = input(purple(f"        [>] {prompt} [y/n] : ") + "\033[38;2;148;0;230m").strip().lower()
        if ans == "y":
            return True
        if ans == "n":
            return False
        print(red("        [!] Error : Invalid option [y/n]"), end="")


def interactive_mode():
    clear()
    print(water(BANNER), end="")

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
            ans = input(
                purple("        [>] Carbon (Offline) or Oxyry [c/o] : ") + "\033[38;2;148;0;230m"
            ).strip().lower()
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


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anubis",
        description="Anubis — Python obfuscator",
    )
    parser.add_argument("file", nargs="?", help="Python file to obfuscate")
    parser.add_argument("--antidebug", action="store_true", help="Inject anti-debugger code")
    parser.add_argument("--junk", action="store_true", help="Add junk code")
    parser.add_argument("--carbon", action="store_true", help="Rename identifiers (offline)")
    parser.add_argument("--oxyry", action="store_true", help="Rename identifiers via oxyry.com")
    parser.add_argument("--import-alias", action="store_true", dest="import_alias",
                        help="Obfuscate import names with aliasing")
    parser.add_argument("--encrypt", action="store_true", help="One-line custom encryption (disables exe compile)")
    parser.add_argument("--compile", action="store_true", help="Compile output to exe with Nuitka")
    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.file is None:
        # Fall back to interactive mode when no arguments are given
        file, use_antidebug, use_junk, carbonate, oxy, use_import_alias, use_encrypt = interactive_mode()
        do_compile = False
    else:
        file = args.file
        use_antidebug = args.antidebug
        use_junk = args.junk
        carbonate = args.carbon
        oxy = args.oxyry
        use_import_alias = args.import_alias
        use_encrypt = args.encrypt
        do_compile = args.compile

        if not os.path.exists(file):
            parser.error(f"File not found: {file}")

        clear()
        print(water(BANNER), end="")

    key = base64.b64encode(os.urandom(32)).decode()

    with open(file, "r", encoding="utf-8") as f:
        src = f.read()

    if use_junk:
        src = junk_code(src)
    if use_antidebug:
        src = bugs(src)
    if use_junk:
        src = junk_code(src)
    if carbonate:
        src = carbon(src)
    if oxy:
        src = oxyry(src)
    if use_import_alias:
        src = add_import_aliases(src)
    if use_encrypt:
        src = Encryption(key.encode()).write(key, src)

    name = f"{file[:-3]}-obf.py"
    with open(name, "w", encoding="utf-8") as f:
        f.write(src)

    print(blue(f"        [>] Code has been successfully obfuscated @ {name}"), end="")

    if args.file is None and not use_encrypt:
        if _ask_yn("Would you like to compile to an exe"):
            do_compile = True

    if do_compile and not use_encrypt:
        params = [
            "nuitka", "--mingw64", "--onefile",
            "--enable-plugin=numpy", "--include-module=psutil",
            "--remove-output", "--assume-yes-for-downloads",
            name,
        ]
        p = subprocess.Popen(params, stdout=subprocess.DEVNULL, shell=IS_WINDOWS, cwd=os.getcwd())
        print(red("\n        [!] Exe may take a while to compile\n        [!] Nuitka Information:\n\n"), end="")
        p.wait()
        print(blue(f"\n        [>] Code has been successfully compiled @ {name[:-3] + '.exe'}"), end="")
    elif do_compile and use_encrypt:
        print(red("\n        [!] Cannot compile to exe when encryption is enabled"), end="")

    print(blue("\n        [>] Press any key to exit... "), end="")
    if args.file is None:
        pause()
    clear()
    leave()


if __name__ == "__main__":
    main()
