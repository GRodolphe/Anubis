"""Obfuscation passes: identifier renaming, junk code, import aliasing, anti-debug."""

from __future__ import annotations

import ast
import io
import os
import random
import re
import string
import tokenize

import requests

from anubis.terminal import error

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _random_name(length: int | None = None) -> str:
    n = length if length is not None else random.randint(8, 20)
    return "".join(random.choice("Il") for _ in range(n))


def _unique_name(used: set[str]) -> str:
    name = _random_name()
    while name in used:
        name = _random_name()
    used.add(name)
    return name


def _collect_imported_names(parsed: ast.Module) -> set[str]:
    """Return names bound by import statements — these must not be renamed.

    Renames would turn ``import signal`` into ``import IlIlIlIl`` and cause
    ModuleNotFoundError at runtime (issue #31).
    """
    names: set[str] = set()
    for node in ast.walk(parsed):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname if alias.asname else alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname if alias.asname else alias.name)
    return names


# ---------------------------------------------------------------------------
# Strip comments / docstrings
# ---------------------------------------------------------------------------


def remove_docs(source: str) -> str:
    io_obj = io.StringIO(source)
    out = ""
    prev_toktype = tokenize.INDENT
    last_lineno = -1
    last_col = 0
    for tok in tokenize.generate_tokens(io_obj.readline):
        token_type, token_string = tok[0], tok[1]
        start_line, start_col = tok[2]
        _end_line, end_col = tok[3]
        if start_line > last_lineno:
            last_col = 0
        if start_col > last_col:
            out += " " * (start_col - last_col)
        if token_type == tokenize.COMMENT:
            pass
        elif token_type == tokenize.STRING:
            if prev_toktype not in (tokenize.INDENT, tokenize.NEWLINE) and start_col > 0:
                out += token_string
        else:
            out += token_string
        prev_toktype = token_type
        last_col = end_col
        last_lineno = start_line
    return "\n".join(line for line in out.splitlines() if line.strip())


# ---------------------------------------------------------------------------
# Identifier rename (Carbon)
# ---------------------------------------------------------------------------


def _do_rename(pairs: dict[str, str], code: str) -> str:
    for key, val in pairs.items():
        code = re.sub(rf"\b({re.escape(key)})\b", val, code, flags=re.MULTILINE)
    return code


_PROGRESS_CYCLES = ["[   " + "> " * n + "  " * (23 - n) + "]" for n in range(1, 24)]


def carbon(code: str) -> str:
    """Rename identifiers using random I/l strings (offline, no network needed)."""
    code = remove_docs(code)
    parsed = ast.parse(code)
    protected = _collect_imported_names(parsed)

    funcs = {
        node
        for node in ast.walk(parsed)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    classes = {node for node in ast.walk(parsed) if isinstance(node, ast.ClassDef)}

    identifiers: set[str] = set()
    for node in ast.walk(parsed):
        if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Load):
            identifiers.add(node.id)
        elif isinstance(node, ast.Attribute) and not isinstance(node.ctx, ast.Load):
            identifiers.add(node.attr)
    for func in funcs:
        for arg_list in (
            func.args.args,
            func.args.kwonlyargs,
            [func.args.vararg] if func.args.vararg else [],
            [func.args.kwarg] if func.args.kwarg else [],
        ):
            for arg in arg_list:
                identifiers.add(arg.arg)

    pairs: dict[str, str] = {}
    used: set[str] = set()

    for func in funcs:
        if func.name != "__init__" and func.name not in protected:
            pairs[func.name] = _unique_name(used)
    for cls in classes:
        if cls.name not in protected:
            pairs[cls.name] = _unique_name(used)
    for ident in identifiers:
        if ident not in protected:
            pairs[ident] = _unique_name(used)

    # Freeze string literals so their contents aren't mangled
    string_regex = r"('|\")[\x1f-\x7e]{1,}?('|\")"
    originals = [
        m.group().replace("\\", "\\\\") for m in re.finditer(string_regex, code, re.MULTILINE)
    ]
    placeholder = os.urandom(16).hex()
    code = re.sub(string_regex, f"'{placeholder}'", code, flags=re.MULTILINE)

    for i, orig in enumerate(originals):
        for key, val in pairs.items():
            originals[i] = re.sub(
                r"({.*)" + re.escape(key) + r"(.*})",
                r"\g<1>" + val + r"\2",
                orig,
                flags=re.MULTILINE,
            )

    step = 0
    while True:
        print(f"\r        {_PROGRESS_CYCLES[step]}", end="")
        step = (step + 1) % len(_PROGRESS_CYCLES)
        code = _do_rename(pairs, code)
        if not any(re.search(rf"\b{re.escape(k)}\b", code) for k in pairs):
            break

    replace_placeholder = r"('|\")" + placeholder + r"('|\")"
    for original in originals:
        code = re.sub(replace_placeholder, original, code, count=1, flags=re.MULTILINE)

    print(f"\r        {_PROGRESS_CYCLES[-1]}\n\n", end="")
    return code


# ---------------------------------------------------------------------------
# Identifier rename (Oxyry — remote)
# ---------------------------------------------------------------------------


def oxyry(code: str) -> str:
    """Rename identifiers via the oxyry.com API (requires network)."""
    src = "__all__ = []\n" + code.replace('"', '\\"').replace("'", "\\'").replace("\\", "\\\\")
    payload = {
        "append_source": False,
        "remove_docstrings": True,
        "rename_nondefault_parameters": True,
        "rename_default_parameters": True,
        "preserve": "",
        "source": src,
    }
    try:
        r = requests.post("https://pyob.oxyry.com/obfuscate", json=payload, timeout=30)
        data: dict[str, str] = r.json()
    except Exception:
        error("A problem occurred whilst contacting oxyry.com")

    if "dest" not in data:
        error(
            f"{data.get('errorMessage', 'Unknown error')}\n"
            "        [!] Please make sure your code is Python 3.3 - 3.7 compatible"
        )

    result = data["dest"].replace("\\\\", "\\")
    result = re.sub(r"#\w*:[0-9]*", "", result)
    for pat in ("__all__=[]\n", "__all__ =[]\n", "__all__ = []\n", "__all__= []\n"):
        result = result.replace(pat, "")
    return result


# ---------------------------------------------------------------------------
# Import aliasing (issue #26)
# ---------------------------------------------------------------------------


def add_import_aliases(code: str) -> str:
    """Rewrite ``import X`` → ``import X as <obfuscated>`` throughout the source."""
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

    for original, obfname in pairs.items():
        # Rewrite the import statement
        code = re.sub(
            rf"^(import\s+{re.escape(original)})\s*$",
            rf"\1 as {obfname}",
            code,
            flags=re.MULTILINE,
        )
        # Replace all usages
        code = re.sub(rf"\b{re.escape(original)}\b", obfname, code, flags=re.MULTILINE)
        # Restore the module name inside the import statement itself
        code = re.sub(
            rf"^(import\s+){re.escape(obfname)}(\s+as\s+{re.escape(obfname)})",
            rf"\g<1>{original}\2",
            code,
            flags=re.MULTILINE,
        )

    return code


# ---------------------------------------------------------------------------
# Anti-debugger injection
# ---------------------------------------------------------------------------

# Known debugger process names, hex-encoded so they don't appear as plaintext.
_DEBUGGER_HEX_NAMES: list[str] = [
    "53757370656e64",
    "50726f67726573732054656c6572696b20466964646c657220576562204465627567676572",
    "466964646c6572",
    "57697265736861726b",
    "64756d70636170",
    "646e537079",
    "646e5370792d783836",
    "6368656174656e67696e652d7838365f3634",
    "4854545044656275676765725549",
    "50726f636d6f6e",
    "50726f636d6f6e3634",
    "50726f636d6f6e363461",
    "50726f636573734861636b6572",
    "783332646267",
    "783634646267",
    "446f744e657444617461436f6c6c6563746f723332",
    "446f744e657444617461436f6c6c6563746f723634",
    "485454504465627567676572537663",
    "48545450204465627567676572",
    "696461",
    "6964613634",
    "69646167",
    "696461673634",
    "69646177",
    "696461773634",
    "69646171",
    "696461713634",
    "69646175",
    "696461753634",
    "7363796c6c61",
    "7363796c6c615f783634",
    "7363796c6c615f783836",
    "70726f74656374696f6e5f6964",
    "77696e646267",
    "7265736861636b6572",
    "496d706f7274524543",
    "494d4d554e4954594445425547474552",
    "4d65676144756d706572",
    "646973617373656d626c79",
    "4465627567",
    "5b435055496d6d756e697479",
    "4d65676144756d70657220312e3020627920436f6465437261636b6572202f20536e44",
    "436861726c6573",
    "636861726c6573",
    "4f4c4c59444247",
    "496d706f72745f7265636f6e7374727563746f72",
    "636f6465637261636b6572",
    "646534646f74",
    "696c737079",
    "67726179776f6c66",
    "73696d706c65617373656d626c796578706c6f726572",  # simpleassemblyexplorer
    "7836346e657464756d706572",
    "687864",
    "7065746f6f6c73",
    "73696d706c65617373656d626c79",
    "68747470616e616c797a6572",
    "687474706465627567",
    "70726f636573736861636b6572",
    "6d656d6f727965646974",
    "6d656d6f7279",
    "646534646f746d6f64646564",
    "70726f63657373206861636b6572",
    "70726f63657373206d6f6e69746f72",
    "717435636f7265",
    "696461",
    "696d6d756e697479",
    "68747470",
    "74726166666963",
    "77697265736861726b",
    "666964646c6572",
    "7061636b6574",
    "6861636b6572",
    "6465627567",
    "646e737079",
    "646f747065656b",
    "646f747472616365",
    "70726f6364756d70",
    "6d616e61676572",
    "6d656d6f7279",
    "6e65744c696d6974",
    "6e65744c696d69746572",
    "73616e64626f78",
]


def bugs(code: str) -> str:
    """Prepend anti-debugger bootstrap code to *code*.

    Uses ``ctypes.windll`` only on Windows; falls back to a cross-platform
    psutil process scanner everywhere else (fixes issues #29, #18).
    """
    header = (
        "import binascii as _bi, platform as _pl, threading as _th, time as _ti\n"
        "try:\n"
        "    from psutil import process_iter as _pi\n"
        "except ImportError:\n"
        "    import os as _os; _os.system('pip install psutil')\n"
        "    from psutil import process_iter as _pi\n"
        "if _pl.system() == 'Windows':\n"
        "    import ctypes as _ct\n"
        "    if not _ct.windll.shell32.IsUserAnAdmin():\n"
        "        print('Please run this program as administrator.')\n"
        "        __import__('sys').exit(0)\n"
        f"_d = {_DEBUGGER_HEX_NAMES!r}\n"
        "_d = [_bi.unhexlify(i).decode() for i in _d]\n"
        "def _dbg():\n"
        "    while True:\n"
        "        try:\n"
        "            for _p in _pi():\n"
        "                for _n in _d:\n"
        "                    if _n.lower() in _p.name().lower(): _p.kill()\n"
        "        except Exception: pass\n"
        "        _ti.sleep(0.5)\n"
        "_th.Thread(target=_dbg, daemon=True).start()\n\n"
    )
    return header + code


# ---------------------------------------------------------------------------
# Junk code injection
# ---------------------------------------------------------------------------


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


def junk_code(code: str) -> str:
    """Wrap *code* with unreachable junk class definitions."""
    return "\n" + _make_junk_block() + "\n" + code + "\n" + _make_junk_block()
