#!/usr/bin/env python3
"""Generate assets/css/syntax-highlighting.css from two Chroma styles.

Runs `hugo gen chromastyles` for a light and a dark style and merges them into
one stylesheet whose colours are light-dark(<light>, <dark>) pairs, so code
follows the theme's color-scheme (OS preference and the manual toggle).

Merge rules:
- A colour present in only one style falls back to currentColor (or
  transparent for backgrounds) in the other mode.
- light-dark() can only switch colours, so bold/italic/underline are kept
  only where both styles agree.
- The code block background and line numbers use the theme's palette variables
  instead of the styles' own values. A highlighted line is marked with a bar
  at its start rather than a background fill, because a fill would lower the
  contrast of every token on that line.
- A token colour below WCAG AA (4.5:1) on the default palette's code
  background is mixed toward that palette's text colour with color-mix(), by
  the smallest step that reaches 4.5:1. The hue is kept.

Standard library only. Usage (hugo must be on PATH; `mise run syntax-css`):
    gen-syntax-css.py [--light github] [--dark github-dark] [--check]
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "assets/css/syntax-highlighting.css"
PALETTE = ROOT / "assets/css/colors/default.css"
AA = 4.5
RULE = re.compile(r"/\* (\w+) \*/ ([^{]+)\{([^}]*)\}")
# Selectors whose rules are layout, not token colours: emitted by hand below.
# Whitespace has no glyphs, so contrast does not apply; styles often colour it
# to match their background on purpose.
NO_CONTRAST_FIX = {".chroma .w"}
STRUCTURAL = {".bg", ".chroma", ".chroma .lnlinks", ".chroma .lntd", ".chroma .lntable",
              ".chroma .hl", ".chroma .lnt", ".chroma .ln", ".chroma .line"}


def chroma_style(name):
    result = subprocess.run(["hugo", "gen", "chromastyles", "--style", name],
                            capture_output=True, text=True)
    if result.returncode:
        sys.exit(f"hugo gen chromastyles --style {name} failed:\n{result.stderr.strip()}")
    css = result.stdout
    rules = {}
    for token, selector, body in RULE.findall(css):
        declarations = dict(part.split(":", 1) for part in body.split(";") if ":" in part)
        rules[selector.strip()] = (token, {k.strip(): v.strip() for k, v in declarations.items()})
    if ".chroma" not in rules:
        sys.exit(f"hugo produced no CSS for style {name!r}")
    return rules


def rgb(colour):
    """#rgb, #rrggbb or rgb(r, g, b) -> (r, g, b)."""
    if colour.startswith("#"):
        digits = colour[1:]
        if len(digits) == 3:
            digits = "".join(c * 2 for c in digits)
        return tuple(int(digits[i:i + 2], 16) for i in (0, 2, 4))
    return tuple(int(n) for n in re.findall(r"\d+", colour)[:3])


def luminance(colour):
    channel = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(v / 255) for v in colour)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def palette_value(name):
    match = re.search(rf"--{name}:\s*([^;]+);", PALETTE.read_text())
    return rgb(match.group(1))


def accessible(colour, background, text, text_variable):
    """The colour itself, or a color-mix() toward the text colour that reaches AA."""
    if contrast(rgb(colour), background) >= AA:
        return colour
    for percent in range(5, 100, 5):
        # color-mix(in srgb, ...) interpolates the gamma-encoded channels linearly.
        mixed = tuple(round(c * (1 - percent / 100) + t * percent / 100)
                      for c, t in zip(rgb(colour), text))
        if contrast(mixed, background) >= AA:
            return f"color-mix(in srgb, {colour}, var(--{text_variable}) {percent}%)"
    return f"var(--{text_variable})"


def merge(light, dark):
    modes = {
        "light": (palette_value("code-background-light"), palette_value("content-primary-light"), "content-primary-light"),
        "dark": (palette_value("code-background-dark"), palette_value("content-primary-dark"), "content-primary-dark"),
    }
    groups = {}  # declarations -> [(selector, token)]
    for selector in list(light) + [s for s in dark if s not in light]:
        if selector in STRUCTURAL:
            continue
        token = (light.get(selector) or dark[selector])[0]
        sides = {"light": light.get(selector, ("", {}))[1], "dark": dark.get(selector, ("", {}))[1]}
        declarations = []
        for prop in ("color", "background-color"):
            if not any(prop in side for side in sides.values()):
                continue
            pair = []
            for mode, side in sides.items():
                value = side.get(prop)
                if value is None:
                    value = "currentColor" if prop == "color" else "transparent"
                elif prop == "color" and selector not in NO_CONTRAST_FIX:
                    code_background, text, variable = modes[mode]
                    # A token with its own background is judged against that.
                    own = side.get("background-color")
                    value = accessible(value, rgb(own) if own else code_background, text, variable)
                pair.append(value)
            declarations.append(f"{prop}: light-dark({pair[0]}, {pair[1]});")
        for prop in ("font-weight", "font-style", "text-decoration"):
            if prop in sides["light"] and sides["light"].get(prop) == sides["dark"].get(prop):
                declarations.append(f"{prop}: {sides['light'][prop]};")
        if declarations:
            groups.setdefault(tuple(declarations), []).append((selector, token))
    base = (light[".chroma"][1].get("color", "currentColor"), dark[".chroma"][1].get("color", "currentColor"))
    return base, groups


def render(light_name, dark_name, base, groups):
    lines = [
        f"/* Generated by scripts/gen-syntax-css.py from the Chroma styles \"{light_name}\" (light)",
        f"   and \"{dark_name}\" (dark). Do not edit: run `mise run syntax-css` instead. */",
        "",
        ".bg,",
        ".chroma {",
        "  background-color: var(--code-background);",
        "}",
        "",
        ".chroma {",
        f"  color: light-dark({base[0]}, {base[1]});",
        "  -webkit-text-size-adjust: none;",
        "  text-size-adjust: none;",
        "}",
        "",
        ".chroma .lnlinks {",
        "  outline: none;",
        "  text-decoration: none;",
        "  color: inherit;",
        "}",
        "",
        ".chroma .lntd {",
        "  vertical-align: top;",
        "  padding: 0;",
        "  margin: 0;",
        "  border: 0;",
        "}",
        "",
        ".chroma .lntable {",
        "  border-spacing: 0;",
        "  padding: 0;",
        "  margin: 0;",
        "  border: 0;",
        "}",
        "",
        "/* A bar, not a fill: token contrast on a highlighted line stays as measured. */",
        ".chroma .hl {",
        "  box-shadow: inset 3px 0 0 var(--content-primary);",
        "}",
        "",
        ".chroma .lnt,",
        ".chroma .ln {",
        "  white-space: pre;",
        "  -webkit-user-select: none;",
        "  user-select: none;",
        "  margin-right: 0.4em;",
        "  padding: 0 0.4em;",
        "  color: var(--content-secondary);",
        "}",
        "",
        ".chroma .line {",
        "  display: flex;",
        "}",
    ]
    for declarations, members in groups.items():
        lines += ["", "/* " + ", ".join(token for _, token in members) + " */"]
        lines += [",\n".join(selector for selector, _ in members) + " {"]
        lines += [f"  {declaration}" for declaration in declarations]
        lines += ["}"]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--light", default="github", help="Chroma style for light mode")
    parser.add_argument("--dark", default="github-dark", help="Chroma style for dark mode")
    parser.add_argument("--check", action="store_true",
                        help="write nothing; fail if the stylesheet on disk is out of date")
    options = parser.parse_args()
    base, groups = merge(chroma_style(options.light), chroma_style(options.dark))
    css = render(options.light, options.dark, base, groups)
    if options.check:
        if OUTPUT.read_text() != css:
            sys.exit(f"{OUTPUT.relative_to(ROOT)} is out of date: run `mise run syntax-css`")
        print(f"{OUTPUT.relative_to(ROOT)} is up to date")
        return
    OUTPUT.write_text(css)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {sum(len(m) for m in groups.values())} token rules in {len(groups)} groups")


if __name__ == "__main__":
    main()
