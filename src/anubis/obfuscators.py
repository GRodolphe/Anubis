"""Obfuscation passes: renaming, junk, string mixing, encoding, anti-debug."""

from __future__ import annotations

import ast
import base64
import io
import marshal
import os
import random
import re
import string
import tokenize
import zlib

from anubis.terminal import error

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

# Method names that exist on common Python builtin types.  Renaming these
# is unsafe because the same name may appear as an attribute call on a
# builtin object (e.g. list.pop, str.split) that must not be renamed.
_BUILTIN_ATTR_NAMES: frozenset[str] = frozenset(
    attr
    for typ in (list, dict, set, frozenset, str, bytes, bytearray, tuple, int, float, complex, bool)
    for attr in dir(typ)
    if not attr.startswith("__")
)


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

    Without this guard, ``import signal`` would become ``import IlIlIlIl``,
    causing ModuleNotFoundError at runtime (issue #31).
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
# Carbon — offline identifier renaming
# ---------------------------------------------------------------------------


def _do_rename(pairs: dict[str, str], code: str) -> str:
    for key, val in pairs.items():
        code = re.sub(rf"\b({re.escape(key)})\b", val, code, flags=re.MULTILINE)
    return code


_PROGRESS_CYCLES = ["[   " + "> " * n + "  " * (23 - n) + "]" for n in range(1, 24)]


def carbon(code: str) -> str:
    """Rename identifiers using random I/l strings (offline)."""
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
        if (
            func.name != "__init__"
            and func.name not in protected
            and func.name not in _BUILTIN_ATTR_NAMES
        ):
            pairs[func.name] = _unique_name(used)
    for cls in classes:
        if cls.name not in protected:
            pairs[cls.name] = _unique_name(used)
    for ident in identifiers:
        if ident not in protected and ident not in _BUILTIN_ATTR_NAMES:
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
# Mix Strings — replace string literals with chr() chains
# ---------------------------------------------------------------------------


def _is_simple_string_token(tok_string: str) -> bool:
    """Return True for plain unquoted string literals that can be chr()-encoded."""
    # Skip triple-quoted strings (docstrings / multiline)
    if '"""' in tok_string or "'''" in tok_string:
        return False
    # Skip prefixed strings: f"", b"", r"", rb"", etc.
    prefix = ""
    for ch in tok_string:
        if ch not in "fFbBrRuU":
            break
        prefix += ch
    return not any(c in prefix.lower() for c in "fbr")


def mix_strings(code: str) -> str:
    """Replace simple string literals with ``chr()`` chain expressions.

    ``"hello"`` becomes ``(chr(104)+chr(101)+chr(108)+chr(108)+chr(111))``.
    Triple-quoted strings, f-strings, bytes, and raw strings are skipped.
    Strings longer than 80 characters are skipped to avoid bloat.
    """
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(code).readline))
    except tokenize.TokenError:
        return code

    # Collect (start_row, start_col, end_row, end_col, replacement) for single-line strings
    replacements: list[tuple[int, int, int, int, str]] = []
    for tok in tokens:
        if tok.type != tokenize.STRING:
            continue
        if not _is_simple_string_token(tok.string):
            continue
        try:
            value = ast.literal_eval(tok.string)
        except (ValueError, SyntaxError):
            continue
        if not isinstance(value, str) or not value or len(value) > 80:
            continue
        start_row, start_col = tok.start
        end_row, end_col = tok.end
        if start_row != end_row:
            continue  # Skip multi-line strings
        obf = "(" + "+".join(f"chr({ord(c)})" for c in value) + ")"
        replacements.append((start_row, start_col, end_row, end_col, obf))

    if not replacements:
        return code

    lines = code.splitlines(keepends=True)
    # Process in reverse order so earlier positions stay valid
    replacements.sort(key=lambda r: (r[0], r[1]), reverse=True)
    for start_row, start_col, _end_row, end_col, obf in replacements:
        idx = start_row - 1  # tokenize rows are 1-based
        if idx < 0 or idx >= len(lines):
            continue
        line = lines[idx]
        lines[idx] = line[:start_col] + obf + line[end_col:]

    return "".join(lines)


# ---------------------------------------------------------------------------
# Big Script — inflate with random dead-code blobs
# ---------------------------------------------------------------------------


def big_script(code: str, junk_kb: int = 256) -> str:
    """Prepend random byte-blob variable assignments to inflate script size.

    The blobs are never referenced and are optimised away if the bytecode is
    compiled — they only obscure static analysis of the source file.
    """
    chunks: list[str] = []
    total = 0
    target = junk_kb * 1024

    while total < target:
        name = "_" + "".join(
            random.choices(string.ascii_lowercase + string.digits, k=random.randint(12, 20))
        )
        blob = random.randbytes(random.randint(120, 400))
        chunk = f"{name} = {blob!r}\n"
        chunks.append(chunk)
        total += len(chunk)

    return "".join(chunks) + "\n" + code


# ---------------------------------------------------------------------------
# RFT — Run From Text (source → zlib → base64 → exec)
# ---------------------------------------------------------------------------


def rft_mode(code: str) -> str:
    """Encode the entire source as a compressed base64 blob and exec it.

    The source can be recovered by decoding the blob, so combine with other
    passes for stronger protection.
    """
    compressed = zlib.compress(code.encode("utf-8"), level=9)
    encoded = base64.b64encode(compressed)
    return (
        f"import zlib as _z,base64 as _b\nexec(_z.decompress(_b.b64decode({encoded!r})).decode())\n"
    )


# ---------------------------------------------------------------------------
# BCC — Bytecode Compilation (source → compile → marshal → zlib → base64)
# ---------------------------------------------------------------------------


def bcc_mode(code: str) -> str:
    """Compile source to a code object, marshal it, and embed a loader stub.

    The output cannot be trivially decompiled with ``uncompyle6`` / ``decompile3``.
    Note: the bytecode is Python-version–specific — the loader must run on
    the same interpreter version that produced it.
    """
    try:
        code_obj = compile(code, "<anubis>", "exec")
    except SyntaxError as exc:
        error(f"BCC compilation failed: {exc}")

    marshaled = marshal.dumps(code_obj)
    compressed = zlib.compress(marshaled, level=9)
    encoded = base64.b64encode(compressed)
    return (
        "import marshal as _m,zlib as _z,base64 as _b\n"
        f"exec(_m.loads(_z.decompress(_b.b64decode({encoded!r}))))\n"
    )


# ---------------------------------------------------------------------------
# Anti-debugger injection
# ---------------------------------------------------------------------------

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
    "73696d706c65617373656d626c796578706c6f726572",
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
    """Prepend anti-debugger bootstrap code.

    Uses ``ctypes.windll`` only on Windows; falls back to a cross-platform
    psutil process scanner everywhere else (fixes issues #29, #18).
    """
    header = (
        "import binascii as _bi,platform as _pl,threading as _th,time as _ti\n"
        "try:\n"
        "    from psutil import process_iter as _pi\n"
        "except ImportError:\n"
        "    import os as _os;_os.system('pip install psutil')\n"
        "    from psutil import process_iter as _pi\n"
        "if _pl.system()=='Windows':\n"
        "    import ctypes as _ct\n"
        "    if not _ct.windll.shell32.IsUserAnAdmin():\n"
        "        print('Please run this program as administrator.')\n"
        "        __import__('sys').exit(0)\n"
        f"_d=[_bi.unhexlify(i).decode() for i in {_DEBUGGER_HEX_NAMES!r}]\n"
        "def _dbg():\n"
        "    while True:\n"
        "        try:\n"
        "            for _p in _pi():\n"
        "                for _n in _d:\n"
        "                    if _n.lower() in _p.name().lower():_p.kill()\n"
        "        except Exception:pass\n"
        "        _ti.sleep(0.5)\n"
        "_th.Thread(target=_dbg,daemon=True).start()\n\n"
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
        code = re.sub(
            rf"^(import\s+{re.escape(original)})\s*$",
            rf"\1 as {obfname}",
            code,
            flags=re.MULTILINE,
        )
        code = re.sub(rf"\b{re.escape(original)}\b", obfname, code, flags=re.MULTILINE)
        code = re.sub(
            rf"^(import\s+){re.escape(obfname)}(\s+as\s+{re.escape(obfname)})",
            rf"\g<1>{original}\2",
            code,
            flags=re.MULTILINE,
        )

    return code
