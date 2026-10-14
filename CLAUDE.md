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
- Header, footer, and the contact form are shared across pages via
  `partials/header.html`, `partials/footer.html`, and
  `partials/contact-form.html`. Each page wraps the matching region in
  `PARTIAL:HEADER` / `PARTIAL:FOOTER` / `PARTIAL:CONTACT_FORM` comment
  markers (see `index.html` or `contact/index.html` for the exact form);
  `scripts/build.py` overwrites everything between matching markers from
  the partial file (`PARTIALS_MAP` in that script maps marker name to
  source file — add a pair there for any future shared block). Edit the
  partial, run the script — never hand-edit a page's copy of a shared
  region, it'll just get overwritten.
- **Adding something to the nav is always a manual edit to
  `partials/header.html`, and always waits for Josh's OK — no exceptions,
  even when a page that would belong there already exists.** Nav v1
  (Phase 1): Weddings, Pricing, About, Contact only — no Corporate &
  Parties, Stories, Reviews, Tools, Mixes, or FAQ until each is approved.
- The contact form posts to Formspree over `fetch` (not a plain HTML POST)
  so GA4's `generate_lead` event fires only on a genuinely successful
  submit, never on click and never on a Formspree-side rejection — see
  the `.booking-form-wrap` handler in `script.js`. Every page using the
  form needs a `.booking-form-wrap` → `.form-success` / `.form-error`
  pair; `scripts/check_seo.py` doesn't check this, so review by eye when
  touching it.
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
- The site is fully multi-page as of Phase 1 — the nav links to real pages
  (`/weddings/`, `/pricing/`, `/about/`, `/contact/`), not homepage
  anchors. The one exception is `/#booking`: that was the old one-page
  site's booking section, and `script.js` redirects it to `/contact/` on
  load (`location.hash === '#booking'` → `location.replace('/contact/')`)
  so any old bookmark or inbound link still lands somewhere useful. Don't
  add new homepage-anchor links — point directly at the real page instead.
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

## Design

Light mode (Phase 1 decision — the Phase 0 build was dark, now retired).
`styles.css` `:root` vars: `--bg`/`--surface`/`--surface2`/`--text`/`--muted`
are the light palette; `--gold` is the text-safe accent (eyebrows, links,
icons — passes against `--bg`/`--surface`); `--gold-btn` + `--gold-lt`
(hover) are for button/phone-bar *backgrounds* only, always paired with
`--text` as the foreground, never `--gold`. Don't mix these up — a button
styled with `--gold` as its own text color was the old dark-mode pairing
and fails contrast in light mode. `scripts/check_contrast.py`'s `PAIRS`
list tests the actual pairs in use; add to it if you introduce a new one.

The homepage hero (`.hero`) is a deliberate exception: full-bleed photo +
dark gradient overlay, so its text colors are hardcoded light values, not
theme variables — it's a fixed dark island regardless of the site's light
theme. Every other page uses `.hero-light` (text-first, photo below, not
behind) specifically so the mobile-first-screen requirement (H1 + one
line + both CTAs visible before any image) is easy to guarantee — don't
give a subpage a full-bleed photo hero like Home's.

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
content type. **Accessibility ≥90 is a hard fail. Performance ≥90 is still
a warning only** in `.lighthouserc.json` — the Phase 1 redesign (light
mode, the 5 core pages) has shipped, but performance hasn't been
re-measured and tuned against it yet (large hero photos, Google Fonts,
etc.). Flip `categories:performance` from `"warn"` to `"error"` once
that's done, not automatically just because Phase 1 shipped. On push to
`main`, a final job submits every sitemap URL to IndexNow.

## Raw photos and unpublished content

Go in `_inbox/` at the repo root. That folder is gitignored — never commit
anything from it directly; process images (resize + WebP) into `assets/`
first.

**Known issue**: `assets/josh.webp` and `assets/event-1.webp` are
byte-identical (confirmed via md5, traces back to the original pre-Claude
upload) — not two different photos despite the filenames and old alt
text. `event-1.webp` is currently unreferenced by any page. Flag this to
Josh during the pending photo-rename pass; don't use both on the same
page assuming they differ.

## Crawlers

`robots.txt` allows all crawlers, with explicit `Allow: /` blocks for
`GPTBot`, `OAI-SearchBot`, `ClaudeBot`, and `PerplexityBot` ahead of the
wildcard rule, plus a `Sitemap:` line. IndexNow key file lives at the repo
root as `<key>.txt` — `scripts/ci_indexnow_submit.py` discovers it by
filename pattern rather than a hardcoded value, so rotating the key only
means swapping that one file.
