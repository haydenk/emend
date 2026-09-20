# Contributing to Emend

Thanks for helping. This page covers what the theme will and will not take,
how to set up, and what a pull request needs.

## What fits

Emend is deliberately small, and a change has to keep these true:

- plain CSS, with no build step, and a build on standard Hugo
- no third-party hosts of any kind
- exactly one inline script, no inline event handlers, no `javascript:` URLs
- no Hugo warnings or deprecations on the pinned Hugo version
- WCAG 2.2 AA in both light and dark mode

The tests enforce most of this. If a feature can be done from a site with a
[hook](docs/customizing.md#hooks) or `custom.css`, that is usually better than
adding it to the theme. For anything large, open a
[feature request](https://github.com/haydenk/emend/issues/new/choose) first.

## Setup

You need [mise](https://mise.jdx.dev) and a Docker-compatible engine (the
pipeline runs in [Dagger](https://dagger.io)).

```sh
mise install
mise run serve     # http://localhost:1313, live reload
mise run ci        # everything CI runs
```

[docs/development.md](docs/development.md) describes the tasks, the tests and
the generated files.

## Making a change

1. Branch from `master`. Development is trunk-based: keep branches short-lived
   and pull requests small.
2. Make the change. A template or style change should come with a fixture in
   `exampleSite/` and a check in `scripts/check-output.sh`.
3. Regenerate generated files if their inputs changed: `mise run syntax-css`,
   `mise run icons`, `mise run og-image`. Do not edit them by hand.
4. If you change the inline script in `layouts/_partials/head.html`, run
   `mise run csp-hash` and update `scripts/inline-script.sha256` and the hash
   quoted in `README.md` and `docs/content-security-policy.md`.
5. Add a line to the `[Unreleased]` section of `CHANGELOG.md` for anything a
   site owner would notice.
6. Run `mise run ci`, then open a pull request and fill in the template. For a
   visual change, include screenshots in light and dark mode.

Commits on `master` must be signed. GitHub signs a pull request's merge commit
for you; if you push directly, set up
[commit signing](https://docs.github.com/authentication/managing-commit-signature-verification).

## Reporting bugs and security issues

Use the [issue forms](https://github.com/haydenk/emend/issues/new/choose) for
bugs. Report a security problem privately, as the
[security policy](.github/SECURITY.md) describes, not in a public issue.

## Licence

By contributing you agree that your contribution is licensed under
[AGPL-3.0-or-later](LICENSE), the project's licence.
