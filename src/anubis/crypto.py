"""AES-CBC encryption used for the one-liner obfuscation mode."""

from __future__ import annotations

import base64
import hashlib

from Crypto import Random
from Crypto.Cipher import AES


class Encryption:
    """Encrypt source lines with AES-CBC and embed them in a self-decrypting stub."""

    def __init__(self, key: bytes) -> None:
        self.bs: int = AES.block_size
        self.key: bytes = hashlib.sha256(key).digest()

    def encrypt(self, raw: str) -> str:
        padded = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(padded.encode())).decode()

    def _pad(self, s: str) -> str:
        pad_len = self.bs - len(s) % self.bs
        return s + pad_len * chr(pad_len)

    def write(self, key: str, source: str) -> str:
        """Return a self-decrypting one-liner that requires ancrypt at runtime."""
        wall = "__ANUBIS_ENCRYPTED__" * 25
        body = f"{wall}{key}{wall}"
        for line in source.split("\n"):
            body += self.encrypt(line) + wall
        return f"import ancrypt\nancrypt.load(__file__)\n'''\n{body}\n'''"
