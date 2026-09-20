# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Emend is a hard fork of [Typo](https://github.com/tomfran/typo) 3. The 1.0.0
entry describes what changed from it.

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [1.0.0] - 2026-09-20

### Added

- A header button that cycles auto, light and dark, with the choice applied before first paint.
- An archive page (`type = "archive"`), a `series` link on single pages, and unpaginated lists of terms with counts.
- Hooks for site code: `head-start`, `head-end`, `single-after-content`, `footer-start` and `body-end`.
- An image render hook that sets `width` and `height`, serves rasters as WebP with a `srcset`, sizes SVGs from their `viewBox`, and loads the first image of a page first.
- Syntax highlighting generated from Chroma's `github` and `github-dark` styles as `light-dark()` pairs.
- A generic favicon set and share image, and a `social` list with inline SVG icons.
- Support for sites served from a subpath.
- `scripts/check-constraints.py`, a Content Security Policy checker a site can run on its own build.
- Documentation in `docs/`, a demo site on GitHub Pages, and release tarballs for manual install.
- A contributing guide, code of conduct, security policy, and issue and pull request templates.
- Automated releases: merging a `release/<version>` pull request tags the commit, publishes the tarball with that version's changelog section as the notes, and deploys the demo site.

### Changed

- The theme requires Hugo 0.158.0 or later and uses Hugo's current template layout.
- System fonts replaced the bundled web fonts, and the stylesheet is inlined by default (`inlineCSS`).
- The header menu is Hugo's `main` menu, shown lowercase with a `/` prefix, and list page size is Hugo's `pagerSize`.
- Tags are shown as lowercase, hyphenated hashtags.
- Meta descriptions and list summaries use a page's description, then its first paragraphs of prose.
- Headings, nested lists, tables, code blocks and dates were restyled for reading on a phone.
- The licence is AGPL-3.0-or-later. Typo's MIT notice is kept in `NOTICE`.

### Removed

- KaTeX, Mermaid, giscus comments, Umami and Google Analytics, and the copy-code button: everything that loaded a third-party host or needed an extra inline script.
- The bundled Literata and Monaspace fonts, the 3,280-icon `svg.html`, all but the default colour palette, the heading anchor links, and the `rawhtml` shortcode.

### Fixed

- Images kept their aspect ratio on narrow screens, and images from `assets/` or an external URL no longer rendered as an empty figure.
- Code blocks with line numbers no longer widened the page.
- Pages have one `<h1>`, labelled navigation landmarks and a skip link.
- Secondary text and syntax colours meet WCAG AA contrast in both modes.

### Security

- The theme makes no third-party requests and has exactly one inline script, so it works under a strict Content Security Policy.

[Unreleased]: https://github.com/haydenk/emend/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/haydenk/emend/releases/tag/v1.0.0
