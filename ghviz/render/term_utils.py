"""Reads the real, current terminal width — bypassing the COLUMNS env var.

Python's shutil.get_terminal_size() and os.get_terminal_size() both check the
COLUMNS environment variable FIRST, before asking the OS for the real size.
If a shell sets COLUMNS once and doesn't refresh it on window resize (this
varies by shell/terminal), rich ends up wrapping text at a stale, too-narrow
width — which is exactly why native `git log` reflows correctly on resize but
a naive rich-based tool doesn't. This queries the terminal driver (tty) directly
via ioctl, so it always reflects the actual current window size.
"""

from __future__ import annotations

import shutil
import sys


def real_terminal_width(default: int = 100) -> int:
    try:
        import fcntl
        import struct
        import termios

        packed = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, struct.pack("HHHH", 0, 0, 0, 0))
        _, cols, _, _ = struct.unpack("HHHH", packed)
        if cols:
            return cols
    except Exception:
        pass

    # Fallback for non-Unix platforms or when stdout isn't a real tty
    return shutil.get_terminal_size(fallback=(default, 24)).columns