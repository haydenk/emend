# Getting started

## Requirements

- Hugo 0.158.0 or later. The standard edition is enough: the theme uses plain
  CSS, so the extended edition's Sass support is never needed.

## Install

As a Hugo module:

```toml
[[module.imports]]
path = "github.com/haydenk/emend"
```

Or from a [release](https://github.com/haydenk/emend/releases) tarball:

```sh
tar -xzf emend-<version>.tar.gz -C <site>/themes/   # creates themes/emend
```

and set `theme = "emend"` in the site configuration. The tarball holds the
theme files and the CSP checker (`scripts/check-constraints.py`), nothing else.

## Required site configuration

Hugo does not merge a theme's `[markup]` settings into a site, so set these
two in the site:

```toml
[markup.highlight]
noClasses = false    # the stylesheet styles Chroma classes

[markup.goldmark.parser]
wrapStandAloneImageWithinParagraph = false   # lets a captioned image become a <figure>
```

## A minimal site

```toml
baseURL = "https://example.org/"
locale = "en-US"
title = "My Site"
theme = "emend"

[taxonomies]
tag = "tags"
series = "series"

[pagination]
pagerSize = 10

[params]
description = "What this site is about."
toc = true
readTime = true
showTags = true
homeCollection = ["posts"]
homeCollectionTitle = "Latest"

[[menus.main]]
name = "Posts"
pageRef = "/posts"
weight = 10

[[menus.main]]
name = "Tags"
pageRef = "/tags"
weight = 20

[[menus.main]]
name = "Archive"
pageRef = "/archive"
weight = 30

[markup.highlight]
noClasses = false

[markup.goldmark.parser]
wrapStandAloneImageWithinParagraph = false
```

Add `content/archive.md` with `type = "archive"` for the archive page. The
repository's [`exampleSite/`](../exampleSite) is a complete working site.

The theme works from a subpath (`https://example.org/blog/`). Generated URLs
are relative to the site, and a root-relative URL written by hand, in a
Markdown image or a `social` link, gets the base path added.

Next: [Configuration](configuration.md).
