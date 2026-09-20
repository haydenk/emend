# Customizing

Everything here is done from the site. None of it needs a change to the theme.

## Hooks

A hook is a partial the theme calls if the site provides it. Create
`layouts/_partials/hooks/<name>.html` (the legacy `layouts/partials/hooks/`
also works). Each hook receives the page.

| Hook | Where it renders |
| --- | --- |
| `head-start` | First thing in `<head>`, after the charset and viewport |
| `head-end` | Last thing in `<head>`: extra stylesheets, structured data |
| `single-after-content` | On single pages, inside `<article>`, after the content |
| `footer-start` | First thing in `<footer>` |
| `body-end` | Last thing in `<body>` |

For example, a stylesheet loaded only on pages that use a shortcode:

```go-html-template
{{- if .HasShortcode "flashcards" -}}
  {{- with resources.Get "css/flashcards.css" | minify | fingerprint }}
  <link rel="stylesheet" href="{{ .RelPermalink }}" integrity="{{ .Data.Integrity }}">
  {{- end }}
{{- end -}}
```

`exampleSite/layouts/` has working hooks and shortcodes: flash cards, a linked
banner, and a click-to-load video.

## CSS

Create `assets/css/custom.css`. It is appended to the theme's stylesheet.

Useful variables:

| Variable | Purpose |
| --- | --- |
| `--font-body`, `--font-mono` | Font stacks (system fonts by default) |
| `--main-width` | Page width; the text column is this minus the padding |
| `--background`, `--content-primary`, `--content-secondary` | Page and text colours |
| `--code-background`, `--code-border` | Code blocks, table headers, borders |

### Colours and dark mode

The theme switches colours with `color-scheme` and `light-dark()`. The mode
button sets `data-theme="light"` or `"dark"` on `<html>`, and removes it for
auto. So that your rules follow both the system preference and the button, use
the variables above or `light-dark()`:

```css
.note { background: light-dark(#f4f8f4, #26302a); }
```

Do not use a `prefers-color-scheme` media query on its own: it ignores the
button. For a dark-only rule that is not a colour, cover both cases:

```css
:root[data-theme="dark"] .logo { filter: invert(1); }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .logo { filter: invert(1); }
}
```

### Palettes

A palette is a file in `assets/css/colors/` that sets ten variables, a light
and a dark value for each of `--content-primary`, `--content-secondary`,
`--background`, `--code-background` and `--code-border` (see
`assets/css/colors/default.css`). Add your own file and select it with
`params.colorPalette`. Check that text and syntax colours still reach 4.5:1 on
your backgrounds.

## Favicons and the share image

The theme ships a generic mark in `static/`: `favicon.svg`, `favicon.ico`,
`apple-touch-icon.png` and `og-image.png`. Put a file with the same name in the
site's `static/` to replace one, or override
`layouts/_partials/head/favicon.html` for a different set of links.

## Icons

`params.social` entries name an icon. The theme has `github`, `linkedin`,
`rss`, `stackoverflow` and `youtube`. Add one by creating
`layouts/_partials/icons/<name>.html` containing an inline SVG that uses
`fill="currentColor"`.

## Overriding templates

A file in the site's `layouts/` with the same path as a theme file replaces
it. Prefer a hook where one exists: an override has to be kept in step with
the theme by hand.
