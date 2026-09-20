# Development

## Setup

Tool versions live in `.mise.toml` and everything runs through
[mise](https://mise.jdx.dev):

```sh
mise install
mise run serve     # http://localhost:1313, live reload
mise run ci        # what CI runs
```

Build, test, package and release run in a [Dagger](https://dagger.io)
pipeline (`.dagger/main.go`), so a laptop and GitHub Actions execute the same
containerised steps. Those tasks need a Docker-compatible engine. The pipeline
installs the standard Hugo release pinned in `.mise.toml` and verifies its
checksum.

## Tasks

| Task | What it does |
| --- | --- |
| `mise run serve` | Serve `exampleSite/` with live reload (local Hugo) |
| `mise run test` | Dagger: the test suite (below) |
| `mise run ci` | Dagger: the tests, plus a release tarball that must install cleanly |
| `mise run build` | Dagger: build `exampleSite/` into `exampleSite/public` |
| `mise run package [version]` | Dagger: build `dist/emend-<version>.tar.gz` and verify it |
| `mise run demo <base_url>` | Dagger: build the demo for a public URL into `dist/demo` |
| `mise run release <tag>` | Dagger: test, package and publish to the GitHub release for a pushed tag |
| `mise run csp-hash` | Dagger: print the CSP hash; fails if it differs from the recorded one |
| `mise run syntax-css [--light s] [--dark s]` | Regenerate the syntax stylesheet from two Chroma styles |
| `mise run icons` | Regenerate the favicon set and the generic `og-image.png` in `static/` |
| `mise run og-image` | Render the demo's share card (needs Chrome or Chromium; `CHROME` selects one) |
| `mise run labels` | Create or update GitHub labels from `.github/labels.json` |
| `mise run setup` | Check the pinned tools are installed |
| `mise run clean` | Remove build output and `dist/` |

## Updating the Dagger module

`.dagger/go.mod` pins the Dagger Go SDK's dependencies (gRPC, OpenTelemetry,
`golang.org/x/*`). They run only inside the pipeline's container, never in the
theme. Dependabot raises security alerts for them but cannot open the fix: the
module imports Dagger's generated code, which is not committed, so its update
job fails with `dependency_file_not_resolvable`. Bump them by hand:

```sh
cd .dagger
go get <module>@latest    # each module named in the alert
go mod tidy
cd .. && mise run ci      # Dagger regenerates its code and must still pass
```

To move to a new Dagger release, change the version in `.mise.toml` and
`dagger.json`, then run `dagger develop`.

## Tests and fixtures

`exampleSite/` is a generic demo that doubles as the test fixture: three
sections, tags and a series, an archive, a Markdown reference post, and
site-level shortcodes and hooks that must keep working with the theme. Its
configuration names no theme; the pipeline and the `serve` task point Hugo at
the repository root through `HUGO_THEME` and `HUGO_THEMESDIR`.

`mise run test` checks that:

- the generated syntax stylesheet is current
- `exampleSite/` builds with `--panicOnWarning`, so a deprecated Hugo API
  fails the build
- the output passes `scripts/check-output.sh` (the pages and structure the
  fixtures must produce) and `scripts/check-constraints.py` (the
  [CSP constraints](content-security-policy.md)), both minified and unminified
- a build under a subpath has no URL that escapes it

`mise run ci` also builds the release tarball and installs it the documented
way, into a copy of `exampleSite/` with nothing else able to supply the theme.

A change to a template should come with a fixture in `exampleSite/` and a
check in `scripts/check-output.sh`.

## Generated files

Do not edit these by hand.

- `assets/css/syntax-highlighting.css` comes from `scripts/gen-syntax-css.py`,
  which runs `hugo gen chromastyles` for a light and a dark style and merges
  them into `light-dark()` pairs. The code background and line numbers use the
  palette variables; a token colour below 4.5:1 on the default palette is
  corrected with `color-mix()`; bold and italic are kept only where both styles
  agree, because `light-dark()` can only switch colours.
- `static/favicon.*`, `static/apple-touch-icon.png` and `static/og-image.png`
  come from `scripts/gen-icons.py`, all drawn from one set of geometry.
- `exampleSite/static/og-image.png`, the demo's share card and the README
  banner, is rendered from `scripts/og-image.html`. The theme's own fallback
  share image stays a plain mark so a site never inherits an advert.

## Performance

No web fonts; the stylesheet is inlined, so nothing blocks first paint; the
only script is deferred; every image has `width` and `height`; rasters are
WebP with a `srcset`; the first image of a page loads with
`fetchpriority="high"` and the rest lazily. What is left to the site and its
host: build with `hugo --minify`, serve compressed, cache `/js/*` and
processed images for a long time, and keep edge features that inject scripts
switched off.

## Continuous integration and releases

Development is trunk-based on `master`. GitHub Actions only triggers things:
each workflow installs the pinned tools with `jdx/mise-action` and calls one
mise task, and Dagger does the work. Actions are pinned by commit SHA.

| Workflow | Runs on | Does |
| --- | --- | --- |
| `ci.yml` | pull requests, pushes to `master` | `mise run ci` |
| `release.yml` | a `v*.*.*` tag | checks the tag is on `master`, then `mise run release` |
| `demo.yml` | after a successful release, or by hand | builds the latest release's demo and deploys it to GitHub Pages |
| `labeler.yml` | pull requests | labels by the paths touched |
| `labels.yml` | a change to `.github/labels.json` | syncs the repository's labels |

To release:

1. Move the `[Unreleased]` entries in `CHANGELOG.md` under a new
   `## [1.2.3] - YYYY-MM-DD` heading.
2. Tag and push: `git tag -a v1.2.3 -m "v1.2.3" && git push origin v1.2.3`.

The release notes are that changelog section. Hugo Modules resolve the same
tags, so module users and tarball users get identical versions.

`master` accepts only signed commits, and cannot be force-pushed or deleted;
`v*` tags cannot be moved or deleted.
