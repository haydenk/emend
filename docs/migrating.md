# Migrating an existing site

A checklist for moving a site onto the theme.

1. **Templates that shadow the theme.** A site file with the same path as a
   theme file wins. Remove or re-check leftovers from the previous theme, such
   as `layouts/_default/baseof.html`, `layouts/partials/header.html`,
   `layouts/404.html` or `layouts/_markup/render-image.html`.
2. **Menu.** Rename the site's menu to `main` (`[[menus.main]]`).
3. **Markup settings.** Set `markup.highlight.noClasses = false` and
   `markup.goldmark.parser.wrapStandAloneImageWithinParagraph = false`
   ([why](getting-started.md#required-site-configuration)).
4. **Home page.** Set `params.homeCollection` to the sections to list.
5. **Deprecated Hugo settings.** Replace the `languageCode` key with `locale`,
   and `.Language.LanguageCode` with `.Language.Locale` in site templates (an
   RSS template, for example). Hugo 0.158 and later warn about both.
6. **Hooks.** Name them with hyphens (`head-end.html`), in
   `layouts/_partials/hooks/`.
7. **Dark mode in site stylesheets.** Replace selectors from the old theme
   (for example `.dark-mode`) with `light-dark()` or the theme's colour
   variables ([how](customizing.md#colours-and-dark-mode)).
8. **Icons and share image.** The site's own `favicon.ico`,
   `apple-touch-icon.png` and `params.images` win over the theme's generic
   ones. Replace or remove them deliberately.
9. **Content Security Policy.** Update the `script-src` hash
   ([value](content-security-policy.md)).
10. **Caching.** If the site caches fingerprinted assets by path, add `/js/*`
    for `/js/theme-toggle.min.<hash>.js`, and `/css/*` if `inlineCSS = false`.

Then build with `hugo --panicOnWarning` and run the
[checker](content-security-policy.md#checking-a-site) on the output.
