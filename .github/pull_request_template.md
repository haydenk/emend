<!--
Fill in the sections that apply; delete the ones that don't. The "why" matters
more than the "what": the diff shows the "what".
-->

## Summary

<!-- One or two sentences: what does this change, and why? -->

## Related Issues

<!-- "Closes #123", "Refs #456" -->

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor / chore (no behaviour change)
- [ ] Tooling / CI
- [ ] Documentation

## Checklist

- [ ] `mise run ci` passes locally
- [ ] Fixture added or updated in `exampleSite/`, with a check in `scripts/check-output.sh` (or not applicable)
- [ ] `CHANGELOG.md` `[Unreleased]` section updated (if a site owner would notice the change)
- [ ] Generated files regenerated if their inputs changed (`mise run syntax-css`, `mise run icons`, `mise run og-image`)
- [ ] Inline script unchanged, or `scripts/inline-script.sha256` and `README.md` updated (`mise run csp-hash`)
- [ ] No third-party hosts, no build step, no new inline scripts or event handlers

## Testing

<!-- How did you verify this? Commands run, browsers and widths checked, screenshots for visual changes (light and dark). -->
