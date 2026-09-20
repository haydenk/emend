+++
title = "Extending the theme from a site"
date = 2026-08-08T16:00:00Z
tags = ["guide", "hooks", "shortcodes"]
series = "theme-tour"
youtube = "M7lc1UVf-VE"
description = "Hooks and shortcodes a site can add without editing the theme: a linked banner, flash cards and a click-to-load video."
+++

{{< series-banner src="images/banner.png" href="https://example.org/series" alt="Example series banner" >}}

Everything on this page beyond plain Markdown comes from the example site, not
the theme: two shortcodes and two hook partials. It doubles as a test that such
site code keeps working with the theme.

## Hooks

A hook is a partial the theme calls if the site provides it.

- `head-end` adds the flash card stylesheet, only on pages that use the cards
- `single-after-content` adds the video below this text
  - it reads the `youtube` value from the front matter
  - the player loads only after a click

## Shortcodes

### Series banner

The banner above is a linked, responsive image built from a global asset.

### Flash cards

1. The deck is a native `<details>` element
2. Each card flips with a checkbox, so no JavaScript is involved

{{< flashcards >}}
{{< flashcard q="Which file adds markup to the end of `<head>`?" a="`layouts/_partials/hooks/head-end.html` in the site." >}}
{{< flashcard q="How should a site stylesheet pick its dark colours?" a="With `light-dark()` or the theme's colour variables." >}}
{{< /flashcards >}}
