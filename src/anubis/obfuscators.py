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
from typing import TypeVar

_FuncNode = TypeVar("_FuncNode", ast.FunctionDef, ast.AsyncFunctionDef)

from anubis.terminal import error, is_ci

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

    _ci = is_ci()
    step = 0
    while True:
        if not _ci:
            print(f"\r        {_PROGRESS_CYCLES[step]}", end="")
        step = (step + 1) % len(_PROGRESS_CYCLES)
        code = _do_rename(pairs, code)
        if not any(re.search(rf"\b{re.escape(k)}\b", code) for k in pairs):
            break

    replace_placeholder = r"('|\")" + placeholder + r"('|\")"
    for original in originals:
        code = re.sub(replace_placeholder, original, code, count=1, flags=re.MULTILINE)

    if not _ci:
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


# ---------------------------------------------------------------------------
# XOR String Encryption — replace string literals with keyed XOR cipher
# ---------------------------------------------------------------------------


def xor_strings(code: str) -> str:
    """Encrypt every plain string constant with a random one-byte XOR key.

    Injects a tiny decoder lambda at the top and replaces each string with
    a ``decoder(b'...', key)`` call.  Unlike ``mix_strings``, the plaintext
    never appears in the source or .pyc.  F-strings, non-ASCII strings, and
    strings longer than 200 chars are skipped.
    """
    key = random.randint(1, 255)
    dec_name = _random_name(8)

    class _XorTransformer(ast.NodeTransformer):
        def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.JoinedStr:  # noqa: N802
            return node  # don't recurse into f-strings

        def visit_Constant(self, node: ast.Constant) -> ast.AST:  # noqa: N802
            if not isinstance(node.value, str) or not node.value or len(node.value) > 200:
                return node
            try:
                encrypted = bytes(ord(c) ^ key for c in node.value)
            except (ValueError, OverflowError):
                return node
            return ast.Call(
                func=ast.Name(id=dec_name, ctx=ast.Load()),
                args=[ast.Constant(value=encrypted), ast.Constant(value=key)],
                keywords=[],
            )

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    new_tree = _XorTransformer().visit(tree)
    ast.fix_missing_locations(new_tree)
    try:
        new_code = ast.unparse(new_tree)
    except Exception:
        return code

    return f"{dec_name}=lambda b,k:''.join(chr(c^k)for c in b)\n" + new_code


# ---------------------------------------------------------------------------
# Constant Blinding — replace integer literals with XOR expressions
# ---------------------------------------------------------------------------


def blind_constants(code: str) -> str:
    """Replace every integer literal ``N`` with ``(N^R)^R`` for a random R.

    Hides magic numbers, port numbers, and sizes from static analysis
    without touching booleans, floats, or values larger than 0xFFFF.
    """

    class _BlindTransformer(ast.NodeTransformer):
        def visit_Constant(self, node: ast.Constant) -> ast.AST:  # noqa: N802
            if isinstance(node.value, bool) or not isinstance(node.value, int):
                return node
            if abs(node.value) > 0xFFFF:
                return node
            r = random.randint(1, 0xFFFF)
            return ast.BinOp(
                left=ast.Constant(value=node.value ^ r),
                op=ast.BitXor(),
                right=ast.Constant(value=r),
            )

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    new_tree = _BlindTransformer().visit(tree)
    ast.fix_missing_locations(new_tree)
    try:
        return ast.unparse(new_tree)
    except Exception:
        return code


# ---------------------------------------------------------------------------
# Opaque Predicates — wrap function bodies in always-true guards
# ---------------------------------------------------------------------------


def _make_opaque_true_expr() -> ast.expr:
    """Return an AST expression that is provably always True at runtime."""
    n = random.randint(0, 999)
    v = random.randint(0, 2)
    arg = ast.arg(arg="_x")
    x = ast.Name(id="_x", ctx=ast.Load())
    no_args = ast.arguments(
        posonlyargs=[],
        args=[arg],
        vararg=None,
        kwonlyargs=[],
        kw_defaults=[],
        kwarg=None,
        defaults=[],
    )
    if v == 0:
        # (lambda _x: _x | 1 != 0)(n)
        body: ast.expr = ast.Compare(
            left=ast.BinOp(left=x, op=ast.BitOr(), right=ast.Constant(value=1)),
            ops=[ast.NotEq()],
            comparators=[ast.Constant(value=0)],
        )
    elif v == 1:
        # (lambda _x: _x * _x >= 0)(n)
        body = ast.Compare(
            left=ast.BinOp(left=x, op=ast.Mult(), right=x),
            ops=[ast.GtE()],
            comparators=[ast.Constant(value=0)],
        )
    else:
        # (lambda _x: (_x ^ _x) == 0)(n)
        body = ast.Compare(
            left=ast.BinOp(left=x, op=ast.BitXor(), right=x),
            ops=[ast.Eq()],
            comparators=[ast.Constant(value=0)],
        )
    return ast.Call(
        func=ast.Lambda(args=no_args, body=body),
        args=[ast.Constant(value=n)],
        keywords=[],
    )


def opaque_predicates(code: str) -> str:
    """Wrap every function body in an always-true opaque predicate.

    The ``else`` branch contains unreachable dead code that confuses static
    analysers and degrades LLM-based deobfuscation attempts.
    """

    class _OpaqueTransformer(ast.NodeTransformer):
        def _wrap(self, node: _FuncNode) -> _FuncNode:
            self.generic_visit(node)
            if not node.body or (len(node.body) == 1 and isinstance(node.body[0], ast.Pass)):
                return node
            dead_var = _random_name(6)
            dead_stmts: list[ast.stmt] = [
                ast.Assign(
                    targets=[ast.Name(id=dead_var, ctx=ast.Store())],
                    value=ast.Constant(value=random.randint(0, 9999)),
                    lineno=0,
                    col_offset=0,
                ),
                ast.Pass(),
            ]
            wrapped = ast.If(
                test=_make_opaque_true_expr(),
                body=node.body,
                orelse=dead_stmts,
            )
            ast.fix_missing_locations(wrapped)
            node.body = [wrapped]
            return node

        def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:  # noqa: N802
            return self._wrap(node)

        def visit_AsyncFunctionDef(  # noqa: N802
            self, node: ast.AsyncFunctionDef
        ) -> ast.AsyncFunctionDef:
            return self._wrap(node)

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    new_tree = _OpaqueTransformer().visit(tree)
    ast.fix_missing_locations(new_tree)
    try:
        return ast.unparse(new_tree)
    except Exception:
        return code


# ---------------------------------------------------------------------------
# Dynamic Imports — replace import statements with __import__() calls
# ---------------------------------------------------------------------------


def dynamic_imports(code: str) -> str:
    """Replace ``import X`` statements with XOR-encoded ``__import__()`` calls.

    The module name is never a plain string in the output.
    ``from X import Y`` forms are left intact.
    """
    key = random.randint(1, 255)
    dec_name = _random_name(8)

    lines = code.splitlines()
    out: list[str] = []
    for line in lines:
        m = re.match(r"^(\s*)import\s+([\w.]+)\s*(?:as\s+(\w+))?\s*$", line)
        if m:
            indent, mod, alias = m.group(1), m.group(2), m.group(3)
            bind_name = alias if alias else mod.split(".")[0]
            encoded = bytes(ord(c) ^ key for c in mod)
            out.append(f"{indent}{bind_name}=__import__({dec_name}({encoded!r},{key}))")
        else:
            out.append(line)

    decoder = f"{dec_name}=lambda b,k:''.join(chr(c^k)for c in b)\n"
    return decoder + "\n".join(out)


# ---------------------------------------------------------------------------
# Control Flow Flattening — rewrite function bodies as state machines
# ---------------------------------------------------------------------------


def _has_yield(node: ast.AST) -> bool:
    return any(isinstance(child, (ast.Yield, ast.YieldFrom)) for child in ast.walk(node))


def _flatten_func_body(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    body = node.body
    if len(body) < 2 or _has_yield(node):
        return node

    state_var = _random_name(6)
    chain: list[ast.stmt] = [ast.Break()]

    for i in reversed(range(len(body))):
        stmt = body[i]
        stmt_body: list[ast.stmt] = [stmt]
        if not isinstance(stmt, (ast.Return, ast.Raise)):
            stmt_body.append(
                ast.Assign(
                    targets=[ast.Name(id=state_var, ctx=ast.Store())],
                    value=ast.Constant(value=i + 1),
                    lineno=0,
                    col_offset=0,
                )
            )
        branch = ast.If(
            test=ast.Compare(
                left=ast.Name(id=state_var, ctx=ast.Load()),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=i)],
            ),
            body=stmt_body,
            orelse=chain,
        )
        ast.fix_missing_locations(branch)
        chain = [branch]

    init = ast.Assign(
        targets=[ast.Name(id=state_var, ctx=ast.Store())],
        value=ast.Constant(value=0),
        lineno=0,
        col_offset=0,
    )
    while_loop = ast.While(test=ast.Constant(value=True), body=chain, orelse=[])
    ast.fix_missing_locations(init)
    ast.fix_missing_locations(while_loop)
    node.body = [init, while_loop]
    return node


def flatten_control_flow(code: str) -> str:
    """Convert every function body into a ``while True`` state-machine.

    Each top-level statement becomes a numbered state. ``return``/``raise``
    exit naturally; all other transitions advance the state counter.
    Generators and single-statement functions are skipped.
    """

    class _CFFTransformer(ast.NodeTransformer):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:  # noqa: N802
            self.generic_visit(node)
            return _flatten_func_body(node)

        def visit_AsyncFunctionDef(  # noqa: N802
            self, node: ast.AsyncFunctionDef
        ) -> ast.AsyncFunctionDef:
            self.generic_visit(node)
            return _flatten_func_body(node)

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    new_tree = _CFFTransformer().visit(tree)
    ast.fix_missing_locations(new_tree)
    try:
        return ast.unparse(new_tree)
    except Exception:
        return code


# ---------------------------------------------------------------------------
# Semantic Noise — misleading English identifiers for LLM resistance
# ---------------------------------------------------------------------------

# Research (arxiv:2512.16538, arxiv:2410.05797) shows LLMs rely heavily on
# identifier names for semantic understanding.  Plausible but wrong names
# degrade LLM deobfuscation more effectively than opaque random strings.
_SEMANTIC_VOCAB: list[str] = [
    "authenticate",
    "validate_user",
    "process_request",
    "handle_error",
    "calculate_total",
    "fetch_data",
    "parse_config",
    "update_cache",
    "send_notification",
    "log_event",
    "check_permission",
    "encrypt_token",
    "decode_payload",
    "serialize_data",
    "deserialize_response",
    "initialize_connection",
    "terminate_session",
    "refresh_credentials",
    "verify_signature",
    "compute_hash",
    "generate_token",
    "expire_cache",
    "load_settings",
    "save_progress",
    "restore_state",
    "flush_buffer",
    "compress_output",
    "decompress_input",
    "transform_data",
    "filter_results",
    "sort_records",
    "merge_tables",
    "split_payload",
    "join_segments",
    "user_id",
    "session_key",
    "auth_token",
    "request_body",
    "response_code",
    "database_url",
    "api_endpoint",
    "retry_count",
    "timeout_ms",
    "max_retries",
    "buffer_size",
    "chunk_count",
    "frame_index",
    "packet_length",
    "header_size",
    "total_bytes",
    "error_code",
    "status_flag",
    "event_type",
    "action_id",
    "config_path",
    "output_dir",
    "temp_file",
    "log_level",
    "debug_mode",
    "is_valid",
    "has_permission",
    "is_connected",
    "was_processed",
    "can_retry",
    "handler",
    "manager",
    "factory",
    "builder",
    "loader",
    "validator",
    "converter",
    "processor",
    "dispatcher",
    "scheduler",
    "executor",
    "resolver",
    "formatter",
    "encoder",
    "decoder",
    "parser",
    "serializer",
    "result",
    "payload",
    "response",
    "request",
    "context",
    "state",
    "pipeline",
    "registry",
    "provider",
    "consumer",
    "producer",
    "broker",
]


def _unique_semantic_name(used: set[str]) -> str:
    available = [n for n in _SEMANTIC_VOCAB if n not in used]
    if available:
        name = random.choice(available)
    else:
        a, b = random.choice(_SEMANTIC_VOCAB), random.choice(_SEMANTIC_VOCAB)
        name = f"{a}_{b}"
        while name in used:
            b = random.choice(_SEMANTIC_VOCAB)
            name = f"{a}_{b}"
    used.add(name)
    return name


def semantic_noise(code: str) -> str:
    """Rename identifiers to semantically misleading English names.

    Unlike ``carbon`` (which uses ``IlIl`` strings), this uses plausible
    programming vocabulary that actively misleads LLM-based code analysis.
    Run instead of ``carbon`` or after it for maximum confusion.
    """
    code = remove_docs(code)
    try:
        parsed = ast.parse(code)
    except SyntaxError:
        return code

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
            pairs[func.name] = _unique_semantic_name(used)
    for cls in classes:
        if cls.name not in protected:
            pairs[cls.name] = _unique_semantic_name(used)
    for ident in identifiers:
        if ident not in protected and ident not in _BUILTIN_ATTR_NAMES:
            pairs[ident] = _unique_semantic_name(used)

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
        if not is_ci():
            print(f"\r        {_PROGRESS_CYCLES[step]}", end="")
        step = (step + 1) % len(_PROGRESS_CYCLES)
        code = _do_rename(pairs, code)
        if not any(re.search(rf"\b{re.escape(k)}\b", code) for k in pairs):
            break

    replace_placeholder = r"('|\")" + placeholder + r"('|\")"
    for original in originals:
        code = re.sub(replace_placeholder, original, code, count=1, flags=re.MULTILINE)

    if not is_ci():
        print(f"\r        {_PROGRESS_CYCLES[-1]}\n\n", end="")
    return code
