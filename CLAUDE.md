# CLAUDE.md

Repo rules for `denvereventdj.com` (GitHub Pages). Planning context — the
full site plan and content roadmap — lives in `_docs/site-plan.md` and
`_docs/content-roadmap.md` (both local-only, gitignored, read them for
background). Business-sensitive rules (discounts, internal policy) live in
`_docs/internal-notes.md` (also local-only) — read it before writing copy
that touches pricing or offers. None of the three are ever committed.

## Repo structure

- Static HTML/CSS, no build step for the *live* site — GitHub Pages serves
  these files exactly as committed. One local maintenance script,
  `scripts/build.py`, keeps a few generated/derived things in sync (see
  "Before every push" below). Run it, don't hand-edit what it manages.
- Header and footer are shared across every page via `partials/header.html`
  and `partials/footer.html`. Each page wraps its header/footer regions in
  `PARTIAL:HEADER` / `PARTIAL:FOOTER` comment markers (see `index.html` for
  the exact form); `scripts/build.py` overwrites everything between those
  markers from the partial files. Edit the partial, run the script — never
  hand-edit a page's header/footer region, it'll just get overwritten.
- **Adding something to the nav is always a manual edit to
  `partials/header.html`, and always waits for Josh's OK — no exceptions,
  even when a page that would belong there already exists.**
- All CSS, JS, and image paths are root-relative (`/styles.css`,
  `/script.js`, `/assets/...`), never page-relative (`assets/...`,
  `../assets/...`). Pages live in subfolders (`/weddings/index.html`,
  `/stories/boulder-flower-farm/index.html`, etc.) — a page-relative path
  resolves differently depending on folder depth and breaks the moment a
  page isn't at the repo root.
- **Local preview gotcha**: root-relative paths only resolve correctly when
  the thing serving the preview treats the repo folder itself as the web
  root. Serving from a parent folder, or opening a page via `file://`,
  produces an unstyled page with a broken logo — not a site bug, a preview
  setup issue. Always serve from inside the repo folder itself (e.g.
  `cd` into it before `python3 -m http.server`).
- `CLAUDE.md`, `scripts/`, and `partials/` stay in the git repo (visible on
  GitHub) but are excluded from the published site via `_config.yml`'s
  Jekyll `exclude:` list — they should never be fetchable at
  `denvereventdj.com/CLAUDE.md` etc.

## Clean URLs

- Every page except the homepage is a folder with `index.html`
  (`weddings/index.html` is served at `/weddings/`). Never create a loose
  `page.html` file, and never both forms of one page. The checker fails
  the build on any stray `.html` file that isn't `index.html` (root
  `404.html` excepted; `partials/`, `scripts/`, `_inbox/` are exempt since
  they aren't pages).
- Internal `<a>` links always use the trailing-slash folder form — never
  link to `.html` or `index.html`. The checker fails the build on either.
- Canonicals and `sitemap.xml` use `https://denvereventdj.com/<path>/`.
- Subpages link to homepage sections as `/#booking` etc. — this works
  identically to a bare `#booking` when you're already on the homepage
  (same document, same-page scroll) and correctly navigates home-then-scroll
  from anywhere else. This is also why the shared header/footer partials
  use `/#services`, `/#booking`, `/` for the logo, etc. instead of bare
  anchors — one identical partial file works on every page.
- `404.html` exists at the repo root (GitHub Pages serves it automatically
  for any unmatched path) with the same chrome, `noindex`, a link home, and
  a Check My Date button.

## Content types

Three content types beyond the core service pages, each with an index
page and a copy-and-fill template:

- **Stories** (`/stories/<slug>/`, template: `partials/story-template.html`)
  — past events. Sections in order: the event, what changed or went wrong,
  what Josh did, the result, photos, CTA. `Article` schema
  (`datePublished`/`dateModified`) + `BreadcrumbList`.
- **Guides** (`/guides/<slug>/`, template: `partials/guide-template.html`)
  — evergreen how-tos and listicles. Visible "Updated `<Month Year>`" date,
  table of contents for long guides, CTA mid-page and at the end, links
  back to the related service page. No guide about cost — cost lives only
  on `/pricing/`. Same `Article` + `BreadcrumbList` schema.
- **Tools** (`/tools/<slug>/`, template: `partials/tool-template.html`) —
  free interactive tools. The page must make sense with JavaScript off: a
  written explanation, how-to, and FAQ in the HTML, JS only for the
  interactive part. No signup, instant result, one CTA. `WebApplication`
  schema + `BreadcrumbList`.
- All three: `FAQPage` schema only when an FAQ is actually visible on the
  page.
- Each type has a real index page (`/stories/`, `/guides/`, `/tools/`)
  listing entries as cards, newest/most-recently-updated first. **An index
  page stays `noindex` and out of `sitemap.xml` until it has at least one
  entry** — `scripts/build.py` flips both automatically the moment a real
  entry exists (it's just reflecting what's already there). It **never**
  touches the nav — see "Adding something to the nav" above.
- Story/guide "Updated" date: both the visible text and the schema's
  `dateModified` are driven by one `<!-- updated: YYYY-MM-DD -->` marker
  near the top of the page. Edit the marker, run `scripts/build.py`, both
  update together — never hand-edit the visible date or the schema field
  directly, they'll drift.

## Publishing from `_inbox`

Josh drops a markdown file in `_inbox/<type>/<slug>/` with front matter:
`type, title, slug, title_tag, meta_description, primary_keyword,
published, updated, hero_image, related` (list of URLs), plus photos in
the same folder.

"Publish `_inbox/<type>/<slug>`" means:
1. Read the front matter and markdown content.
2. Copy `partials/<type>-template.html` to `<type>/<slug>/index.html`,
   fill in every `{{TOKEN}}`.
3. Convert any photos in that `_inbox` folder to WebP into `assets/`
   (resize to ~2000px wide max, aim under 200KB — see Phase 0 for the
   `cwebp` pattern).
4. Add the entry's card to `<type>/index.html`.
5. Update any `related` links it points at, or that should point back at
   it.
6. Run `python3 scripts/build.py`, then the full checker suite
   (`check_links.py`, `check_seo.py`, `check_contrast.py`), before pushing.

Adding the new page to the nav is a separate, explicit ask — don't do it
as part of "publish."

## Every page needs

- A unique `<title>` (≤60 chars) and meta description (≤155 chars),
  exactly one `<h1>`.
- A canonical URL on `https://denvereventdj.com/<path>/` (bare domain, no
  `www`, trailing slash).
- Open Graph / Twitter link-preview tags, every local asset path
  root-relative, every `<img>` with non-empty `alt`.
- A listing in `sitemap.xml` (unless intentionally `noindex`).

The checker (`scripts/check_seo.py` + `scripts/check_links.py`) enforces
all of this mechanically — see "Checks" below.

## Voice and content rules

- Voice: warm, casual, conversational, short paragraphs, no filler. Josh
  pulls copy back when it reads too promotional.
- Service pages stay conversion-focused. Education goes in Guides and
  links back to the relevant service page.
- **Client names**: couples' full names, including last names, are fine to
  publish — decided, not pending.
- Legal name for anything formal: NOSIRROT LLC d/b/a DenverEventDJ (public
  record).
- Public contact email is `josh@denvereventdj.com`. Never publish Josh's
  personal gmail address.
- Keep private material out of the repo (contracts, event history notes,
  client contact details). The repo is public.
- Business-sensitive rules (pricing specifics, discounts, internal policy)
  never go in this file, in commit messages, or in page copy/schema — they
  live only in `_docs/internal-notes.md` (gitignored, local).

## Before every push

Run `python3 scripts/build.py` (updates partial-injected regions,
`sitemap.xml`, `llms.txt`, and story/guide "Updated" dates/schema), then
the checker suite:

```
python3 scripts/build.py --check   # confirms the build above is current
python3 scripts/check_links.py     # link shape, sitemap completeness, stray files
python3 scripts/check_seo.py       # title/description/canonical/h1/alt/asset-path
python3 scripts/check_contrast.py  # WCAG AA
```

CI (`.github/workflows/checks.yml`) runs all of the above on every push,
plus Lighthouse (mobile) on the homepage and the first entry of each
content type. **Accessibility ≥90 is a hard fail. Performance ≥90 is a
warning only until the Phase 1 redesign ships** — TODO at that point: flip
`categories:performance` from `"warn"` to `"error"` in `.lighthouserc.json`.
On push to `main`, a final job submits every sitemap URL to IndexNow.

## Raw photos and unpublished content

Go in `_inbox/` at the repo root. That folder is gitignored — never commit
anything from it directly; process images (resize + WebP) into `assets/`
first.

## Crawlers

`robots.txt` allows all crawlers, with explicit `Allow: /` blocks for
`GPTBot`, `OAI-SearchBot`, `ClaudeBot`, and `PerplexityBot` ahead of the
wildcard rule, plus a `Sitemap:` line. IndexNow key file lives at the repo
root as `<key>.txt` — `scripts/ci_indexnow_submit.py` discovers it by
filename pattern rather than a hardcoded value, so rotating the key only
means swapping that one file.
