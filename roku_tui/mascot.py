from __future__ import annotations

# Plain ASCII — used for speech bubbles and headless output
RAT_PLAIN = (
    r"          ___"
    "\n"
    r"         ( ~ )"
    "\n"
    r"          |||"
    "\n"
    r"        (\,;,/)"
    "\n"
    r"        (o o)\//,     o"
    "\n"
    r"         \ /     \,   |"
    "\n"
    r"         `+'(  (   \  o"
    "\n"
    r"            //  \   |_./"
    "\n"
    r"          '~' '~----'"
)

# Rich-markup version (muted comment colour) — for TUI widgets
RAT_MARKUP = (
    "[#565f89]"
    r"          ___"
    "\n"
    r"         ( ~ )"
    "\n"
    r"          |||"
    "\n"
    r"        (\,;,/)"
    "\n"
    r"        (o o)\//,     o"
    "\n"
    r"         \ /     \,   |"
    "\n"
    r"         `+'(  (   \  o"
    "\n"
    r"            //  \   |_./"
    "\n"
    r"          '~' '~----'"
    "[/#565f89]"
)

MASCOT_NAME = "Ratsmith"
ATTRIBUTION = "mascot based on ASCII art by ikas · ascii.co.uk/art/rat"

# Markup version with attribution line — for About / final placement
RAT_MARKUP_CREDITED = RAT_MARKUP + f"\n[dim]  {ATTRIBUTION}[/dim]"


def ratsay(message: str | None = None) -> str:
    """Return a cowsay-style speech bubble above the rat mascot."""
    text = (message or "Anything good on?").strip()
    max_w = 40

    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    cur_len = 0
    for word in words:
        space = 1 if current else 0
        if cur_len + space + len(word) > max_w and current:
            lines.append(" ".join(current))
            current = [word]
            cur_len = len(word)
        else:
            current.append(word)
            cur_len += space + len(word)
    if current:
        lines.append(" ".join(current))

    w = max(len(line) for line in lines)
    parts = [" " + "_" * (w + 2)]

    if len(lines) == 1:
        parts.append(f"< {lines[0].ljust(w)} >")
    else:
        for i, line in enumerate(lines):
            padded = line.ljust(w)
            if i == 0:
                parts.append(f"/ {padded} \\")
            elif i == len(lines) - 1:
                parts.append(f"\\ {padded} /")
            else:
                parts.append(f"| {padded} |")

    parts.append(" " + "-" * (w + 2))
    parts.append("")
    parts.append(RAT_PLAIN)

    return "\n".join(parts)
