// Pipelines for the Emend Hugo theme.
//
// Build, test, package and release the theme in one container, so a laptop and
// GitHub Actions execute exactly the same steps. Invoked through the mise tasks
// (`mise run ci`), which GitHub Actions calls in turn.
package main

import (
	"context"
	"fmt"
	"net/url"
	"regexp"
	"strings"
	"time"

	"dagger/emend/internal/dagger"
)

const (
	alpineImage = "alpine:3.22"
	// Hugo finds a theme as <themesDir>/<theme>, so the source is mounted under
	// the theme's name and its parent is the themes directory.
	themesDir = "/src"
	themeName = "emend"
	themeDir  = themesDir + "/" + themeName
	siteURL   = "https://example.org/"
)

// hugoPin finds the Hugo version in .mise.toml, the one place tool versions
// are pinned.
var hugoPin = regexp.MustCompile(`(?m)^hugo\s*=\s*"([^"]+)"`)

// semver is a plain release version: no "v" prefix, no pre-release suffix.
var semver = regexp.MustCompile(`^[0-9]+\.[0-9]+\.[0-9]+$`)

type Emend struct{}

// toolchain returns a container with the standard (non-extended) Hugo release
// pinned in .mise.toml, the tools the checks need, and the theme source.
func (m *Emend) toolchain(ctx context.Context, source *dagger.Directory) (*dagger.Container, error) {
	mise, err := source.File(".mise.toml").Contents(ctx)
	if err != nil {
		return nil, err
	}
	pin := hugoPin.FindStringSubmatch(mise)
	if pin == nil {
		return nil, fmt.Errorf("no hugo version pinned in .mise.toml")
	}
	version := pin[1]

	platform, err := dag.DefaultPlatform(ctx)
	if err != nil {
		return nil, err
	}
	arch := "amd64"
	if strings.Contains(string(platform), "arm64") {
		arch = "arm64"
	}

	// The official release archive is the standard edition; extended builds
	// have "extended" in the file name. The checksum file guards the download.
	base := "https://github.com/gohugoio/hugo/releases/download/v" + version
	archive := fmt.Sprintf("hugo_%s_linux-%s.tar.gz", version, arch)

	return dag.Container().
		From(alpineImage).
		// GNU grep and tar: check-output.sh and the packaging step use options
		// busybox lacks.
		WithExec([]string{"apk", "add", "--no-cache", "bash", "grep", "tar", "python3"}).
		WithFile("/tmp/hugo/"+archive, dag.HTTP(base+"/"+archive)).
		WithFile("/tmp/hugo/checksums.txt", dag.HTTP(fmt.Sprintf("%s/hugo_%s_checksums.txt", base, version))).
		WithWorkdir("/tmp/hugo").
		WithExec([]string{"sh", "-c", fmt.Sprintf(
			"grep ' %s$' checksums.txt | sha256sum -c - && tar -xzf %s -C /usr/local/bin hugo", archive, archive)}).
		WithMountedDirectory(themeDir, source).
		WithWorkdir(themeDir), nil
}

// hugoBuild builds a site against a themes directory. --panicOnWarning keeps
// the theme free of deprecated Hugo APIs on the pinned version. An empty
// baseURL keeps the one in the site's configuration.
func hugoBuild(tools *dagger.Container, site, themes, destination string, minify bool, baseURL string) *dagger.Container {
	args := []string{
		"hugo", "build", "--source", site, "--destination", destination,
		"--panicOnWarning", "--cleanDestinationDir", "--noBuildLock", "--quiet",
	}
	if minify {
		args = append(args, "--minify")
	}
	if baseURL != "" {
		args = append(args, "--baseURL", baseURL)
	}
	return tools.
		WithEnvVariable("HUGO_THEMESDIR", themes).
		WithEnvVariable("HUGO_THEME", themeName).
		WithExec(args)
}

// Build exampleSite with the theme, minified, and return the generated site.
// Any Hugo warning or deprecation fails the build.
func (m *Emend) Build(
	ctx context.Context,
	// +defaultPath="/"
	// +ignore=[".git", ".dagger", ".github", "docs", "dist", "exampleSite/public", "exampleSite/resources", "**/.DS_Store"]
	source *dagger.Directory,
) (*dagger.Directory, error) {
	tools, err := m.toolchain(ctx, source)
	if err != nil {
		return nil, err
	}
	return hugoBuild(tools, themeDir+"/exampleSite", themesDir, "/out", true, "").Directory("/out"), nil
}

// constraints runs the CSP and markup checker over a built site. The demo's
// video hook is site code, so its YouTube frame and poster image are the only
// allowed third-party URLs.
func constraints(tools *dagger.Container, site, url, basePath, scriptHash string) *dagger.Container {
	return tools.WithExec([]string{"python3", "scripts/check-constraints.py", site,
		"--site-url", url, "--base-path", basePath, "--script-hash", scriptHash,
		"--allow", "https://www.youtube.com/embed/", "--allow", "https://i.ytimg.com/vi/"})
}

// Demo builds exampleSite for publishing at baseURL, such as a GitHub Pages
// project site served from a subpath, and checks the result: the same CSP
// constraints as the tests, and no URL that escapes the subpath.
func (m *Emend) Demo(
	ctx context.Context,
	// +defaultPath="/"
	// +ignore=[".git", ".dagger", ".github", "docs", "dist", "exampleSite/public", "exampleSite/resources", "**/.DS_Store"]
	source *dagger.Directory,
	// Where the site will be served, for example https://owner.github.io/emend/
	baseURL string,
) (*dagger.Directory, error) {
	tools, err := m.toolchain(ctx, source)
	if err != nil {
		return nil, err
	}
	parsed, err := url.Parse(baseURL)
	if err != nil || parsed.Host == "" {
		return nil, fmt.Errorf("baseURL must be an absolute URL, got %q", baseURL)
	}
	baseURL = strings.TrimSuffix(baseURL, "/") + "/"
	scriptHash, err := source.File("scripts/inline-script.sha256").Contents(ctx)
	if err != nil {
		return nil, err
	}
	built := hugoBuild(tools, themeDir+"/exampleSite", themesDir, "/out", true, baseURL)
	return constraints(built, "/out", baseURL, parsed.Path, strings.TrimSpace(scriptHash)).Directory("/out"), nil
}

// Test runs the theme's test suite: the generated syntax stylesheet is
// current, and exampleSite builds without warnings and passes
// scripts/check-output.sh both minified and unminified (sites are not required
// to minify, and the inline script's CSP hash must not depend on it).
func (m *Emend) Test(
	ctx context.Context,
	// +defaultPath="/"
	// +ignore=[".git", ".dagger", ".github", "docs", "dist", "exampleSite/public", "exampleSite/resources", "**/.DS_Store"]
	source *dagger.Directory,
) error {
	tools, err := m.toolchain(ctx, source)
	if err != nil {
		return err
	}
	tools = tools.WithExec([]string{"python3", "scripts/gen-syntax-css.py", "--check"})
	for _, minify := range []bool{true, false} {
		tools = hugoBuild(tools, themeDir+"/exampleSite", themesDir, "/out", minify, "").
			WithExec([]string{"scripts/check-output.sh", "/out"})
	}
	// Served from a subpath (as the GitHub Pages demo is), no URL may point
	// outside it.
	scriptHash, err := source.File("scripts/inline-script.sha256").Contents(ctx)
	if err != nil {
		return err
	}
	subpath := hugoBuild(tools, themeDir+"/exampleSite", themesDir, "/out", true, "https://example.org/sub/path/")
	_, err = constraints(subpath, "/out", "https://example.org/sub/path/", "/sub/path/", strings.TrimSpace(scriptHash)).Sync(ctx)
	return err
}

// Package builds the release tarball and proves it is complete by installing
// it the documented way: extracted into a site's themes/ directory, with
// nothing else able to supply the theme.
func (m *Emend) Package(
	ctx context.Context,
	// +defaultPath="/"
	// +ignore=[".git", ".dagger", ".github", "docs", "dist", "exampleSite/public", "exampleSite/resources", "**/.DS_Store"]
	source *dagger.Directory,
	// Version label for the file name, normally the git tag.
	// +default="dev"
	version string,
) (*dagger.File, error) {
	tools, err := m.toolchain(ctx, source)
	if err != nil {
		return nil, err
	}

	// Only what a site needs: the theme itself, plus the CSP checker the README
	// points sites at.
	theme := dag.Directory()
	for _, dir := range []string{"layouts", "assets", "static", "archetypes"} {
		theme = theme.WithDirectory(dir, source.Directory(dir))
	}
	for _, file := range []string{
		"hugo.toml", "theme.toml", "go.mod", "LICENSE", "NOTICE", "README.md",
		"scripts/check-constraints.py", "scripts/inline-script.sha256",
	} {
		theme = theme.WithFile(file, source.File(file))
	}

	tarball := fmt.Sprintf("/dist/emend-%s.tar.gz", version)
	packed := tools.
		WithDirectory("/stage/"+themeName, theme).
		WithExec([]string{"mkdir", "-p", "/dist", "/verify/themes"}).
		WithExec([]string{"tar", "--sort=name", "--owner=0", "--group=0", "--numeric-owner",
			"-czf", tarball, "-C", "/stage", themeName}).
		WithExec([]string{"tar", "-xzf", tarball, "-C", "/verify/themes"})

	verified := hugoBuild(packed, themeDir+"/exampleSite", "/verify/themes", "/verify/public", true, "").
		WithExec([]string{"scripts/check-output.sh", "/verify/public"})
	return verified.File(tarball), nil
}

// Ci is everything a change must pass: the tests, and a release tarball that
// installs cleanly, so packaging never first breaks on a tag.
func (m *Emend) Ci(
	ctx context.Context,
	// +defaultPath="/"
	// +ignore=[".git", ".dagger", ".github", "docs", "dist", "exampleSite/public", "exampleSite/resources", "**/.DS_Store"]
	source *dagger.Directory,
) error {
	if err := m.Test(ctx, source); err != nil {
		return err
	}
	tarball, err := m.Package(ctx, source, "ci")
	if err != nil {
		return err
	}
	_, err = tarball.Sync(ctx)
	return err
}

// CspHash returns the Content-Security-Policy source for the theme's inline
// script, and fails if it differs from scripts/inline-script.sha256.
func (m *Emend) CspHash(
	ctx context.Context,
	// +defaultPath="/"
	// +ignore=[".git", ".dagger", ".github", "docs", "dist", "exampleSite/public", "exampleSite/resources", "**/.DS_Store"]
	source *dagger.Directory,
) (string, error) {
	tools, err := m.toolchain(ctx, source)
	if err != nil {
		return "", err
	}
	found, err := hugoBuild(tools, themeDir+"/exampleSite", themesDir, "/out", true, "").
		WithExec([]string{"python3", "scripts/check-constraints.py", "/out",
			"--site-url", siteURL, "--print-script-hashes"}).
		Stdout(ctx)
	if err != nil {
		return "", err
	}
	recorded, err := source.File("scripts/inline-script.sha256").Contents(ctx)
	if err != nil {
		return "", err
	}
	found, recorded = strings.TrimSpace(found), strings.TrimSpace(recorded)
	if found != recorded {
		return "", fmt.Errorf("built script is %s but scripts/inline-script.sha256 records %s: update that file and README.md", found, recorded)
	}
	return fmt.Sprintf("script-src 'self' '%s'", found), nil
}

// Tag creates the git tag v<version> at a commit, through the GitHub API. It
// refuses a version that is not plain semver or that has no "## [<version>]"
// section in CHANGELOG.md, because that section becomes the release notes.
// Re-running it is safe: a tag that already points at the commit is accepted,
// and one that points elsewhere is an error (release tags are immutable).
func (m *Emend) Tag(
	ctx context.Context,
	// +defaultPath="/"
	// +ignore=[".git", ".dagger", ".github", "docs", "dist", "exampleSite/public", "exampleSite/resources", "**/.DS_Store"]
	source *dagger.Directory,
	// The version to tag, for example 1.2.3 (a leading "v" is accepted).
	version string,
	// The commit to tag: the merge commit on master.
	sha string,
	// The GitHub repository, as owner/name.
	repo string,
	// A token that may create refs (contents: write).
	token *dagger.Secret,
) (string, error) {
	version = strings.TrimPrefix(version, "v")
	if !semver.MatchString(version) {
		return "", fmt.Errorf("version %q is not MAJOR.MINOR.PATCH", version)
	}
	changelog, err := source.File("CHANGELOG.md").Contents(ctx)
	if err != nil {
		return "", err
	}
	if !strings.Contains(changelog, "\n## ["+version+"]") {
		return "", fmt.Errorf("CHANGELOG.md has no \"## [%s]\" section: cut the release in the changelog first", version)
	}

	return dag.Container().
		From(alpineImage).
		WithExec([]string{"apk", "add", "--no-cache", "github-cli"}).
		WithSecretVariable("GH_TOKEN", token).
		WithEnvVariable("GH_REPO", repo).
		WithEnvVariable("TAG", "v"+version).
		WithEnvVariable("SHA", sha).
		// Creating a ref is a side effect: never let Dagger serve it from cache.
		WithEnvVariable("RUN_AT", time.Now().UTC().Format(time.RFC3339Nano)).
		WithExec([]string{"sh", "-euc", `
existing="$(gh api "repos/$GH_REPO/git/ref/tags/$TAG" --jq .object.sha 2>/dev/null || true)"
if [ -n "$existing" ] && [ "$existing" != "$SHA" ]; then
  echo "$TAG already exists at $existing, not $SHA" >&2
  exit 1
fi
[ -n "$existing" ] || gh api -X POST "repos/$GH_REPO/git/refs" -f ref="refs/tags/$TAG" -f sha="$SHA" >/dev/null
printf '%s' "$TAG"`}).
		Stdout(ctx)
}

// Release tests and packages the theme, then publishes the tarball on the
// GitHub release for the tag. The release notes are the tag's section of
// CHANGELOG.md ("## [1.2.3]" for tag v1.2.3), or GitHub's generated notes if
// there is none. Re-running it for the same tag is safe: the release is created
// once and the asset is replaced.
func (m *Emend) Release(
	ctx context.Context,
	// +defaultPath="/"
	// +ignore=[".git", ".dagger", ".github", "docs", "dist", "exampleSite/public", "exampleSite/resources", "**/.DS_Store"]
	source *dagger.Directory,
	// The git tag being released, for example v1.2.3. It must already exist.
	tag string,
	// The GitHub repository, as owner/name.
	repo string,
	// A token that may write releases (contents: write).
	token *dagger.Secret,
) (string, error) {
	if err := m.Test(ctx, source); err != nil {
		return "", err
	}
	tarball, err := m.Package(ctx, source, tag)
	if err != nil {
		return "", err
	}
	asset := fmt.Sprintf("/release/emend-%s.tar.gz", tag)

	return dag.Container().
		From(alpineImage).
		WithExec([]string{"apk", "add", "--no-cache", "github-cli"}).
		WithMountedFile(asset, tarball).
		WithMountedFile("/release/CHANGELOG.md", source.File("CHANGELOG.md")).
		WithSecretVariable("GH_TOKEN", token).
		WithEnvVariable("GH_REPO", repo).
		WithEnvVariable("TAG", tag).
		WithEnvVariable("ASSET", asset).
		// Publishing is a side effect: never let Dagger serve it from cache.
		WithEnvVariable("RUN_AT", time.Now().UTC().Format(time.RFC3339Nano)).
		WithExec([]string{"sh", "-euc", `
version="${TAG#v}"
awk -v ver="$version" '/^## \[/ { if (found) exit; if (index($0, "[" ver "]")) found = 1; next } /^\[[^]]+\]: / { if (found) exit } found { print }' /release/CHANGELOG.md > /release/notes.md
if grep -q '[^[:space:]]' /release/notes.md; then notes="--notes-file /release/notes.md"; else notes="--generate-notes"; fi
gh release view "$TAG" >/dev/null 2>&1 || gh release create "$TAG" --title "$TAG" $notes --verify-tag
gh release upload "$TAG" "$ASSET" --clobber
gh release view "$TAG" --json url --jq .url`}).
		Stdout(ctx)
}
