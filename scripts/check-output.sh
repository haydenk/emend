#!/usr/bin/env bash
# Checks a built exampleSite: the generic CSP/markup constraints
# (check-constraints.py), then the pages and structure the fixtures must
# produce.
#
# Usage: scripts/check-output.sh <public-dir>
set -euo pipefail

out="${1:?usage: check-output.sh <public-dir>}"
here="$(cd "$(dirname "$0")" && pwd)"
script_hash="$(tr -d '[:space:]' < "$here/inline-script.sha256")"
failures=0

fail() {
  echo "FAIL: $1" >&2
  failures=$((failures + 1))
}

require_file() {
  [ -f "$out/$1" ] || fail "missing page: $1"
}

# Patterns are regular expressions that tolerate minified (unquoted) and
# unminified (quoted) attributes.
require_text() {
  grep -Eq -- "$2" "$out/$1" 2>/dev/null || fail "$1 does not match: $2"
}

# 1. Hard constraints. The fixture video hook is site code, so its YouTube
#    frame and poster image are the only allowed third-party URLs.
python3 "$here/check-constraints.py" "$out" \
  --site-url "https://example.org/" \
  --allow "https://www.youtube.com/embed/" \
  --allow "https://i.ytimg.com/vi/" \
  --script-hash "$script_hash" || fail "constraint violations (listed above)"

# The README quotes the hash for sites that install from a tarball.
grep -qF -- "$script_hash" "$here/../README.md" || fail "README.md does not quote $script_hash"

# 2. Pages and structure the fixtures must produce.
require_file index.html
require_file 404.html
require_file posts/page/2/index.html
require_text index.html 'class="?theme-toggle'
require_text index.html 'href="?/guides/extending-the-theme/'
require_text index.html 'href="?/notes/long-form-outline/'
require_text archive/index.html 'class="?archive-group'
require_text tags/index.html 'class="?term-list'
require_text series/index.html 'class="?term-list'
require_text series/theme-tour/index.html 'class="?post-line'
require_text posts/stress-test/index.html 'aria-label="Table of contents"'
require_text posts/stress-test/index.html 'srcset='
# Performance: no render-blocking theme stylesheet, and the first image is prioritised.
require_text index.html '<style>'
require_text posts/stress-test/index.html 'fetchpriority="?high'
require_text posts/stress-test/index.html 'class="?lntable'
require_text guides/extending-the-theme/index.html 'href="?/series/theme-tour/'
# An image that is not a Hugo resource (static file or external URL) still renders.
require_text posts/stress-test/index.html 'src="?/demo-static-image.png'
# The theme's default icons and share image are published and linked.
for icon in favicon.svg favicon.ico apple-touch-icon.png og-image.png; do require_file "$icon"; done
require_text index.html 'rel="?icon"? href="?/favicon.svg'
require_text index.html 'property="og:image" content="https://example.org/og-image.png"'
# A site's static file wins over the theme's file of the same name: the demo's
# share card must be the one published, not the theme's generic mark.
cmp -s "$out/og-image.png" "$here/../exampleSite/static/og-image.png" || fail "og-image.png is not the demo site's override"
# One fixture hook lives in layouts/_partials/hooks/, the other in legacy layouts/partials/hooks/.
require_text guides/extending-the-theme/index.html '/css/flashcards\.'
require_text guides/extending-the-theme/index.html 'youtube\.com/embed'

# Every hook renders, in its documented place (the page is joined to one line so
# the order checks also work on unminified output).
hook_page="$(tr -d '\n' < "$out/index.html")"
hook_order() {
  echo "$hook_page" | grep -Eq -- "$2" || fail "hook $1 missing or misplaced"
}
hook_order head-start '<head>.*content="?head-start.*</head>'
hook_order footer-start '<footer>[[:space:]]*<span hidden data-hook="?footer-start'
hook_order body-end '</footer>[[:space:]]*<span hidden data-hook="?body-end"?></span>[[:space:]]*</body>'

# 3. Markup regressions found in review.
while IFS= read -r page; do
  count="$(grep -o '<h1' "$page" | wc -l | tr -d ' ')"
  [ "$count" = "1" ] || fail "$page has $count <h1> elements"
done < <(grep -rl --include='*.html' '<main' "$out")
empty_figures="$(grep -rlE --include='*.html' '<figure>[[:space:]]*</figure>' "$out" || true)"
[ -z "$empty_figures" ] || fail "empty <figure> in: $empty_figures"
empty_desc="$(grep -rlE --include='*.html' '<meta name="?description"? content(=""|>)' "$out" || true)"
[ -z "$empty_desc" ] || fail "empty meta description: $empty_desc"

if [ "$failures" -gt 0 ]; then
  echo "$failures check(s) failed" >&2
  exit 1
fi
echo "All output checks passed"
