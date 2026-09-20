# Emend documentation

| Guide | What it covers |
| --- | --- |
| [Getting started](getting-started.md) | Requirements, installing the theme, the site configuration it needs, a minimal site |
| [Configuration](configuration.md) | Every site and page parameter, menus, pagination, taxonomies |
| [Writing content](content.md) | Sections, tags and series, the archive page, images, code, tables, descriptions |
| [Customizing](customizing.md) | Hooks, custom CSS, colours and dark mode, palettes, icons, favicons, overriding templates |
| [Content Security Policy](content-security-policy.md) | The policy the theme is built for, the inline script hash, the checker |
| [Migrating an existing site](migrating.md) | A checklist for moving a site onto the theme |
| [Development](development.md) | mise tasks, the Dagger pipeline, tests and fixtures, generators, CI and releases |

These guides are for people reading the repository. They are not part of the
theme: Hugo ignores `docs/`, the release tarball does not include it, and a
change that only touches `docs/` does not run CI.
