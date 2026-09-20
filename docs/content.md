# Writing content

## Sections and the home page

Any top-level content directory is a section with its own list page. The home
page lists the sections named in `params.homeCollection`, newest first.

## Tags and series

Tags are written however you like in front matter and shown as one lowercase,
hyphenated hashtag: `tags = ["Lost Sheep"]` is displayed as `#lost-sheep`.

A series is a taxonomy for ordered sets of pages. Give a series a display name
with `content/series/<slug>/_index.md`:

```toml
+++
title = "Theme tour"
+++
```

A page with `series = "theme-tour"` shows a "Series:" link under its title.

## Archive

A page with `type = "archive"` lists every regular page, grouped by month,
newest first:

```toml
+++
title = "Archive"
type = "archive"
+++
```

## Descriptions and summaries

The meta description, the share text and (with `listSummaries`) list summaries
use the page's `description`. Without one they use the page's first paragraphs
of prose. Headings, lists, tables and code are skipped, so an outline-style
page does not produce a run of fragments. A page with no paragraphs falls back
to the site `description`.

## Images

Write images in Markdown. The theme looks the destination up as a page
resource (a file beside `index.md`) and then as a global resource
(`assets/`), and if it finds one:

- it sets `width` and `height`, so the page does not shift while loading
- it serves rasters as WebP, and an image wider than the text column also gets
  a smaller and a 2x version in a `srcset`
- an SVG takes its `width` and `height` from its `viewBox`
- the first image on a page loads first (`fetchpriority="high"`); the rest
  load lazily

An image that is not a Hugo resource, a file in `static/` or an external URL,
is passed through as written.

A standalone image with a title becomes a figure with a caption:

```markdown
![Alt text](photo.jpg "This is the caption")
```

Do not give a title to an image that is itself a link
(`[![alt](img)](url)`); a caption cannot go inside a link.

### Share images

`og:image` is, in order: the page's `images` front matter, a page-bundle image
whose name contains `feature`, `cover` or `thumbnail`, the site's
`params.images`, and finally the theme's generic `static/og-image.png`.

## Code

Fenced code is highlighted with Chroma classes, coloured for light and dark
mode. Line numbers work inline or as a table, and a highlighted line is marked
with a bar:

````markdown
```python {linenos=inline,hl_lines=[3]}
...
```
````

Long lines scroll inside the block. They never widen the page.

## Tables, lists and the rest

- A table wider than the column scrolls inside a focusable region.
- Nested lists indent less at each level, so deep outlines stay readable on a
  phone.
- `autonumber = true` numbers a page's h2 to h4 headings.
- The table of contents is a `<details>` element, open by default.
- Footnotes and task lists are styled.
