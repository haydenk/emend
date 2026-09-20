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
| `mise run tag <version> <sha>` | Dagger: create the tag `v<version>` at a commit through the GitHub API (what the Tag Release workflow runs) |
| `mise run release <tag>` | Dagger: test, package and publish to the GitHub release for an existing tag |
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

Check a version before pinning it, because the newest release can carry its
own advisory:

```sh
gh api -X GET advisories -f ecosystem=go -f "affects=<module>@<version>" --jq 'length'   # 0 = clean
```

The `replace` lines at the bottom of `.dagger/go.mod` (the OpenTelemetry log
packages) belong to Dagger: `dagger develop` rewrites them on every run, so an
advisory against those versions can only be fixed by a Dagger release that
raises its pin.

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
mise task, and Dagger does the work. Actions are pinned by commit SHA, and
runners to `ubuntu-24.04-arm` rather than the floating `ubuntu-latest`.
GitHub-hosted arm64 runners are free for public repositories only. The pipeline
itself is architecture-neutral: it picks Hugo's arm64 or amd64 build to match
the machine it runs on.

| Workflow | Runs on | Does |
| --- | --- | --- |
| `ci.yml` | pull requests, pushes to `master` | `mise run ci` |
| `tag.yml` | a merged `release/*` or `hotfix/*` pull request | tags the merge commit `v<version>`, then calls `release.yml` |
| `release.yml` | called by `tag.yml` (or by hand, to retry an existing tag) | checks the tag is on `master`, then `mise run release` |
| `demo.yml` | after a successful release, or by hand | builds the latest release's demo and deploys it to GitHub Pages |
| `codeql.yml` | pull requests, pushes to `master`, weekly | CodeQL analysis of the workflows, JavaScript, Python and Go (after `dagger develop`, so the pipeline's Go type-checks) |
| `labeler.yml` | pull requests | labels by the paths touched |
| `labels.yml` | a change to `.github/labels.json` | syncs the repository's labels |

To release:

1. Create a `release/1.2.3` branch.
2. In `CHANGELOG.md`, move the `[Unreleased]` entries under a new
   `## [1.2.3] - YYYY-MM-DD` heading.
3. Open a pull request into `master` and merge it.

Merging does the rest. `tag.yml` reads the version from the branch name, checks
that the changelog has a section for it, and tags the merge commit `v1.2.3`.
It then calls `release.yml`, which tests, packages and publishes
`emend-v1.2.3.tar.gz` with that changelog section as the release notes, and
`demo.yml` follows with the GitHub Pages deploy. Hugo Modules resolve the same
tags, so module users and tarball users get identical versions.

Releases only start this way. `tag.yml` calls `release.yml` directly, because
a tag created by a workflow's `GITHUB_TOKEN` does not trigger other workflows,
and `release.yml` has no tag trigger of its own: a tag pushed by hand releases
nothing. If the release step fails after the tag exists, fix the pipeline on
`master` and run the Release workflow by hand for that tag (Actions > Release >
Run workflow). That can only republish an existing tag, never create one.

`master` accepts only signed commits, and cannot be force-pushed or deleted;
`v*` tags cannot be moved or deleted.
