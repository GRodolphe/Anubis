"""Load anubis.toml project configuration."""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore[no-redef]  # ty: ignore[unresolved-import]
    except ImportError:
        tomllib = None  # type: ignore[assignment]

_BOOL_KEYS = frozenset(
    {
        "antidebug",
        "junk",
        "mix_strings",
        "big_script",
        "carbon",
        "import_alias",
        "encrypt",
        "rft",
        "bcc",
        "compile",
    }
)
_STR_KEYS = frozenset({"output"})


def load_config(path: Path | None = None) -> dict[str, bool | str]:
    """Return options from [obfuscate] in anubis.toml, or {} if absent."""
    if tomllib is None:
        return {}
    p = path or Path("anubis.toml")
    if not p.exists():
        return {}
    try:
        with p.open("rb") as f:
            data = tomllib.load(f)
    except Exception:
        return {}
    section = data.get("obfuscate", {})
    result: dict[str, bool | str] = {}
    for key, value in section.items():
        if (key in _BOOL_KEYS and isinstance(value, bool)) or (
            key in _STR_KEYS and isinstance(value, str)
        ):
            result[key] = value
    return result
