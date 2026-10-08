# DenverEventDJ.com — Site Plan

Repo: `jtorrison/denvereventdj` (GitHub Pages, domain `denvereventdj.com`).
Pushing to `main` publishes the site in about a minute.

Goal: turn the one-page site into a full multi-page site that books more
weddings, corporate events and parties. A visitor should know within
seconds that they can check a date, book a call, or call/text Josh now.

---

## 1. What every page must do (conversion first)

Speed of response is the edge: couples contact several DJs at once, and
the first one who answers usually wins. Every page puts these in reach:

- **Check My Date** form (Formspree, short: name, email or phone, date,
  venue, event type). Full details come later on the call.
- **Book a 15-minute call** (scheduling link, e.g. Calendly or a Google
  Calendar booking page).
- **Call or text (720) 445-5369**, sticky on mobile.
- A response-time promise ("I reply within 24 hours, usually same day").
- Proof near the top: Google rating, years DJing (since 2011), events
  played, one short review.

Operations, not code: make sure Formspree submissions hit Josh's phone
instantly (email notification on the phone), so the promise holds.

---

## 2. Page map

Clean folder URLs (`/weddings/` = `weddings/index.html`). One page per
search intent, so pages never compete with each other.

### Core pages (conversion)

| URL | Page | Owns the search | Notes |
|---|---|---|---|
| `/` | Home | Denver Event DJ, wedding & event DJ Denver | Hero with form + call + book-a-call, proof bar, services, featured stories, reviews, final CTA |
| `/weddings/` | Weddings | wedding DJ Denver | Ceremony, cocktail hour, reception, MC; ceremony audio (vow and officiant mics, power for outdoor sites) |
| `/corporate-events/` | Corporate | corporate event DJ Denver | Holiday parties, company events, launches; campus proof (CU Boulder) |
| `/parties/` | Parties & Campus | party DJ Denver, Halloween / private event DJ | Birthdays, Halloween, campus and private events |
| `/pricing/` | Pricing | wedding DJ cost Denver | Packages (from $1,500), what changes the price, market context, book a call. The only page that talks about cost in depth |
| `/about/` | About Josh | Josh Torrison DJ | The story (first gig 2011 at 18), Denver native, "you always get Josh", gear |
| `/mixes/` | Mixes | (supporting) | SoundCloud/Spotify embeds, NOSIRROT world, Ibiza residency; links to the NOSIRROT site rather than duplicating it |
| `/reviews/` | Reviews | Denver Event DJ reviews | All testimonials, Google review link, photos |
| `/faq/` | FAQ | (supporting) | Short answers, linking to guides for depth. Includes the preprogrammed-mix question |
| `/contact/` | Contact | (supporting) | Form, book a call, phone, response promise |

### Stories (past events: "something happened, and we handled it")

`/stories/` index plus one page per event, e.g. `/stories/boulder-flower-farm/`.
Each story follows one shape: the event, what went wrong or changed, what
Josh did, the result, a photo or two, then a CTA.

First set: Boulder Flower Farm (ceremony added two weeks out: outdoor power,
handheld mic for vows, lavalier for the officiant) plus the five approved
case studies: Crestview Ranch, Moss Denver, Chautauqua, Lakewood,
Coeur d'Alene.

### Venue pages (the three venue buckets)

- `/venues/denver/`: downtown and urban indoor venues
- `/venues/mountain-weddings/`: Aspen, Vail, Breckenridge, Estes Park, Evergreen
- `/venues/outdoor-weddings/`: outdoor, farm and backyard (links to Boulder Flower Farm)

### Guides (free information that earns the booking)

`/guides/` index plus articles. Each targets a question the core pages don't:

- `/guides/choosing-a-wedding-dj/`: 5 things to think about when picking a wedding DJ
- `/guides/playlist-vs-live-dj/`: preprogrammed mix vs a live DJ (the FAQ links here)
- Later: ceremony audio for outdoor venues, wedding timeline and music, etc.

Rule: no guide about cost. Cost lives only on `/pricing/`.

### Legal

`/privacy/`: the form collects personal details, so add a short privacy page.

---

## 3. Build order

Work on a branch (`rebuild`) and merge to `main` at the end of each phase,
so the current site stays live until the new one is ready.

**Phase 0: Setup**
1. `CLAUDE.md` with the repo rules in section 4.
2. Shared header (nav + call button) and footer, identical on every page.
3. Fix the domain mismatch: canonical tags and sitemap use `www`, but the
   site runs on `denvereventdj.com`. Use the bare domain everywhere.
4. Resize and convert images to WebP (about 2000 px wide max, aim under
   200 KB). Today one photo is 8192 px / 1.7 MB and the hero is 938 KB.
5. Add analytics (GA4) with events for form submits, call taps and
   book-a-call clicks, so we can see what converts.
6. Checks: link checker and color-contrast checker (same idea as the
   Steady Brand repo), plus sitemap, robots.txt, canonical and
   link-preview tags on every page.

**Phase 1: Conversion core (launch)**: Home, Weddings, Pricing, Contact.

**Phase 2: Proof**: Stories index + Boulder Flower Farm + the five approved
stories, Reviews, About, Mixes.

**Phase 3: Reach**: Corporate, Parties & Campus, the three venue pages,
FAQ, Guides (start with the 5-things guide and playlist vs live DJ).

Each phase is shippable on its own.

---

## 4. Repo rules (copy into CLAUDE.md)

- Static HTML/CSS, no build step. Header and footer are duplicated and must
  match on every page.
- Voice: warm, casual, conversational, short paragraphs, no filler. Josh
  pulls copy back when it reads too promotional.
- Service pages stay conversion-focused. Education goes in Guides and links
  back.
- Every page: unique title and meta description, one H1, canonical URL on
  `https://denvereventdj.com/...`, link-preview tags, listed in the sitemap.
- Client names: see decision 1 below. Until it's settled, name venues and
  public events, not couples.
- Never publish the military/veteran discount. It applies only when a
  client raises it.
- Legal name for anything formal: NOSIRROT LLC d/b/a DenverEventDJ.
- Keep private material out of the repo (contracts, event history notes,
  client contact details). The repo is public.

---

## 5. Decisions for Josh

1. **Naming in stories and reviews.** The current site names couples
   ("Vallejos Wedding", "Delpiccolo Wedding"), which conflicts with the rule
   of keeping client names out of public materials. Suggested: name venues
   and events freely; name couples only with their OK (first names are
   enough).
2. **Pricing on the site.** Publish "packages from $1,500" and the two
   packages ($1,500 and $2,250, to confirm)? Today Josh quotes by proposal
   after a call; the page can show starting prices and still steer to a call.
3. **Pricing message.** The homepage says "Better pricing — guaranteed".
   The pricing page wants "you get what you pay for". Pick one story.
4. **Scheduling tool** for book-a-call (Calendly, Google Calendar booking
   page, or other).

---

## 6. What Josh provides

- [ ] Package contents for each package (what's included, hours, add-ons)
- [ ] For each story: event, date (month/year), what happened, what you did,
      result, 1–3 photos, permission status
- [ ] Reviews to feature (Google export or copy) and which photos go with them
- [ ] Mix links (SoundCloud/Spotify) and the NOSIRROT site URL
- [ ] Corporate and campus proof (e.g. Ralphie's Spirit Rodeo at CU Boulder,
      Halloween events), with any photos
- [ ] Scheduling link once the tool is chosen
- [ ] Answers for the FAQ (start with the preprogrammed-mix answer)
