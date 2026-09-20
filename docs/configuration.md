# Configuration

## Site parameters

Set these under `[params]`. None is required.

| Parameter | Default | Purpose |
| --- | --- | --- |
| `description` | none | Meta description used when a page has no `description` and no paragraph text |
| `images` | none | Default `og:image` (first entry). See [share images](content.md#share-images) |
| `homeCollection` | none | Section, or list of sections, listed on the home page |
| `homeCollectionTitle` | none | Heading above that list |
| `homeIntroTitle`, `homeIntroContent` | none | Intro block on the home page (the content is Markdown) |
| `social` | none | List of `{ name, title, url, rel }` links on the home page. `name` is an [icon](customizing.md#icons); `rel` is optional, for example `"me"` |
| `toc` | off | Table of contents on single pages |
| `readTime` | off | "N min read" on single pages |
| `showTags` | off | Tag links on single pages |
| `listSummaries` | off | Plain-text summaries in page lists |
| `showListDate` | `true` | Dates in page lists (can also be set on a section) |
| `listDateFormat` | `"2 Jan 2006"` | Date format in page lists |
| `singleDateFormat` | `":date_long"` | Date format on single pages |
| `footerContent` | `© <year> <title>` | Footer text (Markdown) |
| `breadcrumbs.enabled` | `true` | Breadcrumb navigation |
| `breadcrumbs.showCurrentPage` | `false` | Append the current page title |
| `breadcrumbs.home` | `"Home"` | Label for the first crumb |
| `colorPalette` | `"default"` | A [palette](customizing.md#palettes) file in `assets/css/colors/` |
| `inlineCSS` | `true` | Inline the stylesheet so nothing blocks first paint. `false` links a fingerprinted file |

`toc`, `readTime` and `showTags` can also be set in a page's front matter,
which wins over the site value.

## Page parameters

| Front matter | Purpose |
| --- | --- |
| `description` | Meta description and share text for the page |
| `summary` | A line shown under the title |
| `author` | Shown beside the date |
| `images` | Share image for the page (a list, or one string) |
| `autonumber` | Number the page's h2 to h4 headings |
| `hidePagination` | Hide the newer and older links |
| `hideBackToTop` | Hide the "Back to top" link |
| `type = "archive"` | Make the page an [archive](content.md#archive) |

## Menu

The header menu is Hugo's `main` menu. Entries are shown lowercase with a `/`
in front, and the entry for the current page or section is marked.

```toml
[[menus.main]]
name = "Posts"
pageRef = "/posts"
weight = 10
```

A button after the menu cycles the colour mode: auto (follow the system),
light, dark.

## Pagination

Section lists and the home page list use Hugo's own setting:

```toml
[pagination]
pagerSize = 10
```

Lists of terms (`/tags/`, `/series/`) are never paginated.

## Taxonomies

The theme treats `tags` and any other taxonomy differently. Tags are shown as
hashtags (`#lost-sheep`). Other taxonomies, such as `series`, keep their
titles, and a page that belongs to a series links to it. Declare the ones you
use:

```toml
[taxonomies]
tag = "tags"
series = "series"
```
