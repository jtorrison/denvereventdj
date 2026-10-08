# CLAUDE.md

Repo rules for `denvereventdj.com` (GitHub Pages). See [docs/site-plan.md](docs/site-plan.md)
for the full site plan — page map, build order, and open decisions.

- Static HTML/CSS, no build step. Header and footer are duplicated on every
  page and must match exactly. The canonical source lives in
  `partials/header.html` and `partials/footer.html` — when you change the
  header or footer, update those files, then copy the change into every
  page's `<body>` by hand.
- Voice: warm, casual, conversational, short paragraphs, no filler. Josh
  pulls copy back when it reads too promotional.
- Service pages stay conversion-focused. Education goes in Guides and links
  back to the relevant service page.
- Every page needs: a unique `<title>` and meta description, exactly one
  `<h1>`, a canonical URL on `https://denvereventdj.com/...` (bare domain,
  no `www`), Open Graph / Twitter link-preview tags, and a listing in
  `sitemap.xml`.
- Client names: until naming is settled with Josh (see Decisions in the site
  plan), name venues and public events, not couples.
- Never publish the military/veteran discount. It applies only when a
  client raises it.
- Legal name for anything formal: NOSIRROT LLC d/b/a DenverEventDJ.
- Keep private material out of the repo (contracts, event history notes,
  client contact details). The repo is public.
- Raw photos and unpublished content go in `_inbox/` at the repo root.
  That folder is gitignored — never commit anything from it directly;
  process images (resize + WebP) into `assets/` first.
