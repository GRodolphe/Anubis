# Anti-Debug

**Flag:** `--antidebug`

The anti-debug pass prepends a background thread to the script that continuously scans running processes and kills any known debugger or analysis tool it finds.

## How it works

At startup, the injected code:

1. Reads a list of known debugger process names (stored as hex-encoded strings to avoid plain-text detection).
2. Starts a daemon thread that loops every 0.5 seconds.
3. On each iteration, it calls `psutil.process_iter()` and kills any process whose name matches a known debugger (case-insensitive substring match).

On **Windows only**, it additionally checks that the process is running as Administrator (some debuggers require elevated privileges to attach).

## Targeted tools

The list includes 80+ tools, among them:

- OllyDbg, x64dbg, x32dbg, WinDbg
- Wireshark, dnSpy, de4dot, IDA Pro / IDA64
- Process Hacker, Procmon, Procmon64
- HTTP Debugger, Fiddler, Charles
- MegaDumper, Import REC, Scylla
- Simple Assembly Explorer, de4dot modified
- And many more

## Requirements

`psutil` must be available in the runtime environment. The injected code auto-installs it via `pip` if it is missing.

## Notes

- The thread is a **daemon thread** — it exits automatically when the main script finishes.
- This is a runtime defence only. It does not affect static analysis of the source file.
- Combine with `--bcc` or `--rft` to hide the injected code from static inspection.
