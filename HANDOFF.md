# Running denvereventdj.com: handoff guide

Plain-English guide for Josh, or anyone Josh hands the site to: a
developer, a friend, or another AI tool. It covers where everything
lives, how to make a change safely, and what to do each week.

This repo is **public**. Nothing private goes in this file or anywhere
else in the repo: no passwords, client contact details, contracts or
pricing rules. Those stay in the local-only folders described below.
`HANDOFF.md` is in the repo for reference but, like `CLAUDE.md`, is kept
off the live site by `_config.yml`.

For the detailed technical rules (how pages are built, image sizes,
fonts, video), read [`CLAUDE.md`](CLAUDE.md). This file is the overview.

---

## 1. Where everything lives

| What | Where | Notes |
|---|---|---|
| The website files | GitHub repo `jtorrison/denvereventdj` | Plain HTML and CSS. No database, no CMS. |
| Hosting | GitHub Pages | Free. Publishes automatically when `main` changes. |
| Domain | `denvereventdj.com` | Set by the `CNAME` file in the repo. Renewals are with the domain registrar, not GitHub. |
| Contact form | Formspree | The form on `/` and `/contact/` sends to Formspree, which emails Josh. |
| Analytics | Google Analytics 4 | Lead, call-tap, form-error and tool events. |
| Search | Google Search Console, Bing Webmaster Tools | Request indexing for new pages here. |
| Google listing | Google Business Profile | Weekly posts and reviews. |
| Automatic checks | GitHub Actions (`.github/workflows/checks.yml`) | Runs on every push. Also pings IndexNow (Bing and others) when `main` changes. |

Logins for these accounts belong to Josh and are not stored anywhere in
this repo. Losing access to an AI account does not affect any of them:
the site keeps running and the form keeps sending leads with nobody
touching anything.

## 2. Local-only folders: back these up

These folders are on Josh's Mac only. Git ignores them on purpose, so
they are **not** on GitHub. If the Mac is lost, they are gone.

| Folder | What's in it |
|---|---|
| `_docs/` | The content backlog (every planned page and open question), the site plan, outreach email drafts, the Google Ads plan and internal business notes. |
| `_inbox/` | Raw photos, videos and drafts waiting to be published. |
| `_staging/` | Processed photos and videos not used on a page yet. |
| `assets/.originals/` | Full-quality originals of site photos, for re-cropping. |

Back them up to Google Drive (or any private place) now and after big
changes. From the repo folder:

```bash
zip -r ~/Desktop/denvereventdj-local-backup.zip _docs _inbox _staging assets/.originals
```

Then drag the zip into Google Drive. Never upload these folders anywhere
public.

The single most useful file for whoever picks this up is
`_docs/content-backlog.md`. It lists what's live, what's next, and every
question that still needs Josh's answer.

## 3. How a change goes live

Every change follows the same path. Nothing reaches the live site until
it's merged into `main`.

1. **Make a branch** for the change (`git checkout -b short-name`).
2. **Edit** the files.
3. **Run the build script** (it updates the shared header, footer and
   contact form on every page, the sitemap, `llms.txt`, "Updated" dates
   and image sizes):
   ```bash
   python3 scripts/build.py
   ```
4. **Run the four checks.** All four must say OK:
   ```bash
   python3 scripts/build.py --check
   python3 scripts/check_links.py
   python3 scripts/check_seo.py
   python3 scripts/check_contrast.py
   ```
5. **Preview it** on your own computer. From inside the repo folder:
   ```bash
   python3 -m http.server 8743
   ```
   Then open `http://localhost:8743/` in a browser. If the page shows up
   unstyled, the server was started from the wrong folder.
6. **Josh reviews** the pages and says OK.
7. **Merge and push:**
   ```bash
   git checkout main
   git merge --no-ff short-name
   git push origin main
   ```
8. **Wait for the deploy.** GitHub Pages takes about 2 to 8 minutes.
   Progress shows in the repo's Actions tab ("pages build and
   deployment").
9. **New page?** In Google Search Console, paste its full URL into URL
   Inspection and click Request indexing.

Small text fix with no computer handy? You can edit a file directly on
github.com, but only outside the shared header, footer and contact form
regions (between `PARTIAL:` comments), since the build script owns those.
The automatic checks will flag anything that breaks.

## 4. Rules that matter most

- **The menu stays short:** Weddings, Pricing, Stories, Guides, About,
  Contact. Nothing gets added to it without Josh's OK.
- **Never invent facts.** Every story, review, venue name and number
  comes from Josh or the live site. If something is unknown, ask.
- **Voice:** warm, casual, first person ("I"), short paragraphs, not
  salesy. Sell how the night feels, not gear or low prices.
- **Cost only lives on `/pricing/`.** No guide is about cost.
- **Public email is `josh@denvereventdj.com`.** Never publish a personal
  address.
- **Photos:** WebP, about 2000px wide at most, under 200 KB, with real
  descriptive alt text. Run `python3 scripts/make_image_sizes.py` after
  adding photos.
- **Video:** always through `scripts/process_video.sh`, which keeps the
  audio. See `CLAUDE.md`.

## 5. Weekly and monthly routine

**After every gig**
- Ask the couple or host for a Google review.
- Drop the best photos (and a short voice note about the night) into
  `_inbox/`, for a story or recap page.

**Weekly**
- Publish one new story or recap while the event is fresh.
- Post to Google Business Profile with photos, linking to the newest
  story. Drafts are in `_docs/outreach-drafts.md`.
- Check Formspree for new submissions, including the Spam folder.

**Monthly**
- Search Console: Pages report (anything not indexed, and why) and
  Performance report (which searches bring people in).
- GA4: look at `generate_lead` (form leads), `call_tap` and
  `form_error`. Any `form_error` events mean the form needs a look.
- Run `site:denvereventdj.com` in Google to see what's indexed.

## 6. If something breaks

| Problem | Fix |
|---|---|
| The automatic checks fail on "Verify scripts/build.py was run" | Run `python3 scripts/build.py`, commit, push again. |
| A check fails on a link or SEO issue | The error message names the page and the problem. Fix that line. |
| Preview page has no styling and a broken logo | The preview server was started outside the repo folder. Stop it, `cd` into the repo, start it again. |
| Pushed, but the live site hasn't changed | Wait up to 10 minutes, then hard-refresh. Check the Actions tab for a failed "pages build and deployment". |
| No leads coming in | Submit a test from your phone on `/contact/`. Check Formspree's Submissions and Spam, and that notifications go to an inbox you read. If you see a "verify you're human" page, turn off reCAPTCHA for the form in Formspree (a hidden honeypot field still blocks bots). |
| Lighthouse performance warning in the checks | Only a warning. It doesn't block anything. Big new photos are the usual cause. |

## 7. Setting up on a new computer

1. Install `git` and Python 3. For photos, install `cwebp` (part of
   Google's WebP tools) or the Pillow Python package. For video, install
   `ffmpeg`.
2. Copy the repo:
   ```bash
   git clone https://github.com/jtorrison/denvereventdj.git
   ```
3. Unzip the local-only backup from section 2 into the repo folder.
4. Run the four checks from section 3 to confirm everything works.

## 8. Handing this to an AI tool

Any AI coding tool that can read and edit files works (Claude Code,
Cursor, GitHub Copilot and others). Open the repo folder in it and start
with this:

> This is the repo for denvereventdj.com, a static site on GitHub Pages
> for Josh Torrison, a Denver wedding and event DJ. Before changing
> anything, read `HANDOFF.md`, `CLAUDE.md` and
> `_docs/content-backlog.md` (and `_docs/internal-notes.md` before
> touching pricing). Follow CLAUDE.md's rules exactly. Work on a branch,
> run `scripts/build.py` and the four checks, and show me the pages
> before merging. Never invent facts: ask me. Then tell me what the
> backlog says is next.

## 9. Where things stood at handoff (Oct 31, 2026)

- **Live:** 34 pages in the sitemap. Home, Weddings, Pricing, About,
  Contact, Corporate Events, Parties, Reviews, FAQ, Privacy; 2 wedding
  stories; 12 guides; 4 free planning tools; the Venues hub plus
  Mountain and Outdoor wedding pages; and the Stories, Guides and Tools
  index pages.
- **Contact form:** fixed Oct 30 and confirmed working with a phone test.
- **Speed:** responsive images and self-hosted fonts; Lighthouse
  performance is still a warning, not a hard fail (see `CLAUDE.md`).
- **Next up:** see the Priority queue in `_docs/content-backlog.md`. In
  short: event recaps (Nearly Naked Mile, Halloween), a vendors page, a
  book-a-call link, brand search ads, and the remaining wedding stories
  as Josh talks them through.
