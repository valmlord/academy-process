"""Make untrusted text safe to place in a line the model or a terminal reads.

Imports nothing from lib/: every module may use it without an import cycle.
"""
import unicodedata

# Not Cc, but each one reorders or breaks what a reader sees: the bidi embeddings, overrides and
# isolates can make a path display as another, and U+2028/U+2029 are line breaks to many readers.
_INVISIBLE_LAYOUT = frozenset(
    "؜‎‏‪‫‬‭‮⁦⁧⁨⁩  "
)


def printable(text: str) -> str:
    """Drop every Unicode Cc character (C0, DEL, C1: tab and newline too) and the layout controls
    above, so an interpolated value can neither start a line of its own nor carry a terminal escape."""
    return "".join(ch for ch in text if unicodedata.category(ch) != "Cc" and ch not in _INVISIBLE_LAYOUT)
