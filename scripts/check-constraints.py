#!/usr/bin/env python3
"""Check a built Hugo site against a strict Content Security Policy.

Generic: it knows nothing about this theme's fixtures, so a site using the
theme can run it against its own build. It parses the HTML (so minified,
single-line pages and attributes such as srcdoc are handled) and reports:

- resources loaded from a host other than --site-url or an --allow prefix
  (elements, srcset, inline <style>, style attributes, CSS and JS files)
- inline scripts: more than one per page, or a script whose sha256 is not
  one of the --script-hash values
- inline event handlers, javascript: URLs, <base href> and off-site form actions
- <figure> inside <p> and nested <a>, which browsers re-parse unpredictably
- <img> without an alt attribute
- with --base-path, root-relative URLs that escape the site's subpath

It checks author-controlled output for mistakes; it is not a sanitizer for
untrusted HTML.

Standard library only. Usage:
    check-constraints.py PUBLIC_DIR --site-url https://example.org/ \
        [--allow PREFIX]... [--script-hash sha256-...]... [--base-path /blog/]
        [--print-script-hashes]
"""
import argparse
import base64
import hashlib
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

# <link rel> values that make the browser fetch something. canonical,
# alternate, me, prev and next are references, not loads.
LOADING_RELS = {
    "stylesheet", "preload", "modulepreload", "prefetch", "prerender",
    "preconnect", "dns-prefetch", "icon", "apple-touch-icon", "manifest",
}
URL_ATTRS = {
    "script": ("src",), "img": ("src", "srcset"), "source": ("src", "srcset"),
    "video": ("src", "poster"), "audio": ("src",), "track": ("src",),
    "iframe": ("src",), "embed": ("src",), "object": ("data",),
    "input": ("src",), "form": ("action",), "button": ("formaction",),
    # SVG references (href and the older xlink:href).
    "image": ("href", "xlink:href"), "use": ("href", "xlink:href"),
}
JS_URL_ATTRS = ("href", "src", "action", "formaction", "xlink:href")
# <script> types the browser executes (and CSP therefore governs); any other
# type, such as application/ld+json, is an inert data block.
EXECUTABLE_SCRIPT_TYPES = {
    "", "module", "importmap", "text/javascript", "application/javascript",
    "text/ecmascript", "application/ecmascript",
}
# Starting one of these closes an open <p>; only <figure> is reported, since
# it is the one the image render hook can produce.
CLOSES_P = {
    "address", "article", "aside", "blockquote", "details", "div", "dl",
    "fieldset", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5",
    "h6", "header", "hr", "main", "nav", "ol", "p", "pre", "section",
    "table", "ul",
}
# url(...), @import "..." and quoted strings such as image-set("...").
CSS_URL = re.compile(r"""url\(\s*['"]?([^'")\s]+)|@import\s+['"]([^'"]+)|['"]((?:https?:)?//[^'"]+)""", re.I)
JS_URL = re.compile(r"""["'`]((?:https?:)?//[^"'`\s]+)""")
XML_NAMESPACE = "http://www.w3.org/"


class Checker:
    def __init__(self, site_url, allow, script_hashes, base_path=""):
        # A trailing slash stops https://example.org matching example.org.evil.com.
        site_url = site_url.rstrip("/") + "/"
        # The site's own host written protocol-relative (//host/...) is not third-party.
        self.own = [site_url, "//" + site_url.split("://", 1)[-1]] + allow
        # "/blog/" for a site served from https://example.org/blog/; empty when
        # the site is at the root and no such check is wanted.
        self.base_path = base_path.strip("/")
        self.script_hashes = set(script_hashes)
        self.seen_hashes = set()
        self.problems = []

    def report(self, where, message):
        self.problems.append(f"{where}: {message}")

    def is_external(self, url):
        url = url.strip()
        lowered = url.lower()
        if not lowered.startswith(("http://", "https://", "//")):
            return False
        # Scheme and host are case-insensitive; comparing the whole URL that way
        # is close enough for a same-site test.
        return not any(lowered.startswith(prefix.lower()) for prefix in self.own)

    def escapes_base_path(self, url):
        """A root-relative URL that does not start with the site's subpath."""
        if not self.base_path or not url.startswith("/") or url.startswith("//"):
            return False
        return not (url + "/").startswith(f"/{self.base_path}/")

    def check_css(self, where, css):
        for match in CSS_URL.finditer(css):
            url = match.group(1) or match.group(2) or match.group(3)
            if self.is_external(url):
                self.report(where, f"third-party URL in CSS: {url}")

    def check_js(self, where, js):
        for match in JS_URL.finditer(js):
            url = match.group(1)
            if not url.startswith(XML_NAMESPACE) and self.is_external(url):
                self.report(where, f"third-party URL in JS: {url}")

    def check_html(self, where, html):
        parser = PageParser(self, where)
        parser.feed(html)
        parser.close()
        if parser.inline_scripts > 1:
            self.report(where, f"{parser.inline_scripts} inline scripts on one page")


class PageParser(HTMLParser):
    def __init__(self, checker, where):
        super().__init__(convert_charrefs=True)
        self.checker = checker
        self.where = where
        self.inline_scripts = 0
        self.capture = None  # "script" or "style" while inside one
        self.buffer = []
        self.anchor_depth = 0
        self.p_open = False

    def handle_starttag(self, tag, attrs):
        attrs = {name: (value or "") for name, value in attrs}
        report = lambda message: self.checker.report(self.where, message)

        if tag == "a":
            if self.anchor_depth:
                report("<a> nested inside <a>")
            self.anchor_depth += 1
        if tag in CLOSES_P:
            if tag == "figure" and self.p_open:
                report("<figure> inside <p>")
            self.p_open = tag == "p"

        for name, value in attrs.items():
            if name.startswith("on"):
                report(f"inline event handler: <{tag} {name}=...>")
            # Browsers ignore tabs and newlines inside a URL scheme.
            scheme = re.sub(r"[\t\n\r ]", "", value).lower()
            if name in JS_URL_ATTRS and scheme.startswith("javascript:"):
                report(f"javascript: URL in <{tag} {name}>")
        for name in ("href", "src", "action", "poster", "data"):
            if self.checker.escapes_base_path(attrs.get(name, "").strip()):
                report(f"URL outside the site's base path: <{tag} {name}={attrs[name]}>")
        for part in attrs.get("srcset", "").split(","):
            if part.split() and self.checker.escapes_base_path(part.split()[0]):
                report(f"URL outside the site's base path: <{tag} srcset={part.split()[0]}>")
        if tag == "base":
            report("<base> changes how every relative URL resolves")
        if tag == "img" and "alt" not in attrs:
            report(f"<img> without alt: {attrs.get('src', '')}")
        if tag == "script" and attrs.get("src", "").strip().lower().startswith(("data:", "blob:")):
            report("script loaded from a data: or blob: URL")
        if "style" in attrs:
            self.checker.check_css(self.where, attrs["style"])
        if "srcdoc" in attrs:
            self.checker.check_html(f"{self.where} (srcdoc)", attrs["srcdoc"])

        names = URL_ATTRS.get(tag, ())
        if tag == "link" and LOADING_RELS & set(attrs.get("rel", "").lower().split()):
            names = ("href",)
        for name in names:
            value = attrs.get(name, "")
            # srcset is a comma-separated list of "url descriptor" pairs.
            urls = [part.split()[0] for part in value.split(",") if part.split()] if name == "srcset" else [value]
            for url in urls:
                if self.checker.is_external(url):
                    report(f"third-party resource: <{tag} {name}={url}>")

        if tag == "script" and "src" not in attrs:
            if attrs.get("type", "").strip().lower() in EXECUTABLE_SCRIPT_TYPES:
                self.capture, self.buffer = "script", []
        elif tag == "style":
            self.capture, self.buffer = "style", []

    def handle_endtag(self, tag):
        if tag == "a" and self.anchor_depth:
            self.anchor_depth -= 1
        elif tag == "p":
            self.p_open = False
        if tag == self.capture:
            text = "".join(self.buffer)
            if tag == "style":
                self.checker.check_css(self.where, text)
            else:
                self.inline_scripts += 1
                digest = base64.b64encode(hashlib.sha256(text.encode()).digest()).decode()
                source = f"sha256-{digest}"
                self.checker.seen_hashes.add(source)
                if source not in self.checker.script_hashes:
                    self.checker.report(self.where, f"inline script not allowed by hash: {source}")
            self.capture = None

    def handle_data(self, data):
        if self.capture:
            self.buffer.append(data)


def main():
    args = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    args.add_argument("public_dir", type=Path)
    args.add_argument("--site-url", required=True, help="the site's own baseURL")
    args.add_argument("--allow", action="append", default=[], help="allowed third-party URL prefix")
    args.add_argument("--script-hash", action="append", default=[], help="allowed inline script, as sha256-<base64>")
    args.add_argument("--base-path", default="", help="the site's subpath, e.g. /blog/: root-relative URLs must stay under it")
    args.add_argument("--print-script-hashes", action="store_true", help="print the inline script hashes found and exit")
    options = args.parse_args()

    checker = Checker(options.site_url, options.allow, options.script_hash, options.base_path)
    for path in sorted(options.public_dir.rglob("*")):
        where = str(path.relative_to(options.public_dir))
        if path.suffix == ".html":
            checker.check_html(where, path.read_text(encoding="utf-8"))
        elif path.suffix == ".css":
            checker.check_css(where, path.read_text(encoding="utf-8"))
        elif path.suffix in (".js", ".mjs"):
            checker.check_js(where, path.read_text(encoding="utf-8"))

    if options.print_script_hashes:
        print("\n".join(sorted(checker.seen_hashes)))
        return 0
    for problem in checker.problems:
        print(f"FAIL: {problem}", file=sys.stderr)
    return 1 if checker.problems else 0


if __name__ == "__main__":
    sys.exit(main())
