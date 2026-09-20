# Content Security Policy

The theme is built to run under a strict policy:

```
default-src 'self';
script-src 'self' 'sha256-p0dTuQa+s03teJj7uBSVbGnSrucoYbl82pqs3gwbfBM=';
style-src 'self' 'unsafe-inline';
img-src 'self' data:;
base-uri 'self'; form-action 'self'; frame-ancestors 'self'
```

## What the theme emits

- **No third-party requests.** No fonts, scripts, analytics or CDNs.
- **One inline script**, in `layouts/_partials/head.html`. It applies a stored
  light or dark choice before first paint, so the page never flashes the wrong
  mode. Everything else is in one deferred, fingerprinted file with an
  `integrity` attribute.
- **No inline event handlers and no `javascript:` URLs.**
- **Inline styles.** The stylesheet is inlined by default
  (`params.inlineCSS`), and the table render hook writes `style` attributes for
  column alignment, so `style-src` needs `'unsafe-inline'`.
- JSON-LD in a `<script type="application/ld+json">` is data, not script. A
  policy does not block it, and the checker does not count it.

## The script hash

The inline script is written in exactly the form Hugo's minifier produces, so
the hash is the same whether or not a site builds with `--minify`. It is
recorded in `scripts/inline-script.sha256` and quoted in the README; the tests
fail if the built script, that file and the README disagree. `mise run
csp-hash` prints the current value.

## Checking a site

`scripts/check-constraints.py` ships in the release tarball and needs only
Python 3. Run it on a built site:

```sh
python3 check-constraints.py public \
  --site-url https://example.org/ \
  --script-hash 'sha256-p0dTuQa+s03teJj7uBSVbGnSrucoYbl82pqs3gwbfBM=' \
  --allow https://www.youtube.com/embed/
```

| Option | Purpose |
| --- | --- |
| `--site-url` | The site's own base URL. Anything else is third-party |
| `--allow PREFIX` | A third-party URL prefix the site's policy permits (repeatable) |
| `--script-hash` | An allowed inline script, as `sha256-…` (repeatable) |
| `--base-path /blog/` | For a site under a subpath: report root-relative URLs that escape it |
| `--print-script-hashes` | Print the hashes of the inline scripts found, and exit |

It parses the HTML, so minified pages and attributes such as `srcdoc` are
handled, and it reports: third-party resources (elements, `srcset`, inline
styles, CSS and JS files), more than one inline script on a page or one whose
hash is not allowed, inline event handlers, `javascript:` URLs, `<base>`,
off-site form actions, `<img>` without `alt`, and markup browsers re-parse
unpredictably (`<figure>` inside `<p>`, nested links).

It checks output you authored for mistakes. It is not a sanitizer for
untrusted HTML.
