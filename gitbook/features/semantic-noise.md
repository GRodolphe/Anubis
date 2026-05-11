# Semantic Noise

**Flag:** `--semantic-noise`

Renames every user-defined identifier to a plausible-sounding but semantically wrong English programming term. Unlike `--carbon` (which uses visually confusing `IlIl` strings), semantic noise uses words like `authenticate`, `serialize_data`, and `retry_count` terms that look real but have no relation to what the code actually does.

## Motivation

Research on LLM-based code deobfuscation ([arxiv:2512.16538](https://arxiv.org/abs/2512.16538), [arxiv:2410.05797](https://arxiv.org/abs/2410.05797)) shows that large language models rely heavily on identifier names to understand code semantics. When identifiers carry plausible but wrong meanings, LLMs produce confidently wrong deobfuscation they reconstruct a coherent but incorrect narrative about what the code does.

Random strings (`IlIlIlIl`) are easy for a human to identify as obfuscation and mentally filter out. Misleading English names are harder to dismiss they actively mislead the analyser.

## Example

**Before:**

```python
def send_payload(target, data):
    conn = open_socket(target)
    conn.write(data)
    conn.close()
```

**After:**

```python
def serialize_data(retry_count, buffer_size):
    auth_token = check_permission(retry_count)
    auth_token.validate_user(buffer_size)
    auth_token.terminate_session()
```

The obfuscated version looks like authentication/session management code. The true purpose (network socket write) is completely obscured.

## Vocabulary

The rename pool includes ~80 terms drawn from common programming domains: authentication, networking, serialization, configuration, pipeline processing, and more. When the pool is exhausted, pairs of terms are combined (e.g. `serialize_data_retry_count`).

## What is preserved

- Python keywords and builtins
- Names bound by import statements
- Built-in type method names (`append`, `split`, etc.)
- `__init__` and dunder methods

## Notes

- Use **instead of** `--carbon` for LLM resistance, or combine both: `--carbon` then `--semantic-noise` (carbon first replaces names with `IlIl`, semantic-noise won't find any user identifiers left so run semantic-noise instead of, not after, carbon).
- For maximum effect: `--flatten --opaque --semantic-noise --xor-strings --blind --dynamic-imports`
- Strips comments and docstrings (same as `--carbon`).
