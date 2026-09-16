#!/usr/bin/env python3
"""Change-rate gate for fluent-korean-review.

Usage: change_rate.py ORIGINAL REVISED

Prints the character-level change rate between the two files and exits
0 (at most 30%), 1 (over 30%, warn) or 2 (over 50%, stop). Borrowed from
im-not-ai's over-editing guard: a rules check that rewrites half the text
has stopped being a rules check.
"""

import difflib
import sys

WARN = 0.30
STOP = 0.50


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 64
    with open(sys.argv[1], encoding="utf-8") as f:
        original = f.read()
    with open(sys.argv[2], encoding="utf-8") as f:
        revised = f.read()

    ratio = difflib.SequenceMatcher(None, original, revised, autojunk=False).ratio()
    rate = 1 - ratio
    if rate > STOP:
        verdict, code = "stop", 2
    elif rate > WARN:
        verdict, code = "warn", 1
    else:
        verdict, code = "ok", 0
    print(f"change_rate={rate:.1%} verdict={verdict}")
    return code


if __name__ == "__main__":
    sys.exit(main())
