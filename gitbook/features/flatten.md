# Flatten Control Flow

**Flag:** `--flatten`

Rewrites every function body into a `while True` state-machine dispatcher. Each top-level statement in the function becomes a numbered state; a state variable controls which block executes next. The original linear control flow disappears entirely.

## How it works

1. Each statement in the function body is assigned a state number (0, 1, 2, …).
2. The body is replaced with `state = 0` followed by a `while True` loop.
3. Inside the loop, a nested `if/elif/…/else: break` chain dispatches execution to the current state.
4. At the end of each state block, `state` is incremented to the next value.
5. `return` and `raise` statements exit the loop naturally; no special handling needed.

## Example

**Before:**

```python
def process(data):
    cleaned = data.strip()
    result = cleaned.upper()
    return result
```

**After:**

```python
def process(data):
    _s = 0
    while True:
        if _s == 0:
            cleaned = data.strip()
            _s = 1
        elif _s == 1:
            result = cleaned.upper()
            _s = 2
        elif _s == 2:
            return result
        else:
            break
```

## What it defeats

- **Static control-flow graph analysis** the original CFG is destroyed; tools see an unstructured loop instead of a clean linear flow.
- **Decompilers** bytecode decompilers that reconstruct function structure from control flow are confused by the state-machine pattern.
- **LLM-based deobfuscation** the flat, sequential semantics that LLMs rely on are replaced with non-obvious dispatch logic.

## Notes

- Generator functions (`yield`) are skipped state machines and generators conflict.
- Single-statement functions are skipped (no benefit).
- `break`/`continue` inside nested loops work correctly they apply to the inner loop, not the outer `while True`.
- Pairs well with `--opaque` (which adds always-true guards around function bodies) and `--carbon` (which renames the state variable).
