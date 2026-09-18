# Dream Girls — Website

Static multi-page website for Dream Girls (18+ topless cabaret & juice bar, Minneapolis).
No build step, no dependencies to install — just HTML, one CSS file, and the logo.

## Structure

```
dream-girls-site/
├── index.html        Home
├── about.html        About + Sneaky Pete's (sister club)
├── specials.html     Cover, nightly + weekly specials, hours
├── roll-call.html    Performer lineup (photo placeholders)
├── parties.html      Bachelor / bachelorette / birthday / VIP
├── gallery.html      Photo grid (placeholders)
├── contact.html      Address, hours, directions + application forms
├── css/
│   └── styles.css    Shared styles (dark "Nocturne" theme)
└── assets/
    └── dream-girls-logo.png
```

## Put it on GitHub (no command line needed)

1. github.com → **New repository** → name it (e.g. `dream-girls-site`) → **Create**.
2. On the empty repo page → **uploading an existing file**.
3. Drag in ALL files, keeping the folders (`css/` and `assets/` must stay as folders).
4. **Commit changes**.

### Make it live for free (GitHub Pages)
Repo → **Settings → Pages** → Source: `main` branch → **Save**.
GitHub gives you a public URL in a minute or two. `index.html` loads as the homepage automatically.

## Adding your photos (after the shoot)

1. Drop image files into `assets/` (e.g. `assets/stage-1.jpg`).
2. In the page, find a placeholder block — it looks like:
   `<div class="ph"> ... </div>`
3. Replace it with:
   `<img src="assets/stage-1.jpg" alt="Description" class="ph"/>`
   (keeping `class="ph"` preserves the rounded frame and sizing)

Placeholders live in: `roll-call.html`, `gallery.html`, `about.html`.

## Forms

The three forms on **contact.html** (Employment, Showgirl Audition, Book a Party)
open the visitor's email app pre-addressed to:
`karinhar12@gmail.com` and `plecou@hotmail.com`.

To receive submissions as clean emails without opening the visitor's mail app,
connect a form service (e.g. Formspree) later — the fields are already in place.

## Details wired in

- Age gate on entry (18+)
- Address: 12 N 5th St, Minneapolis, MN 55403 · Plus Code XPHG+XW
- Phone: (612) 333-7326
- Directions link → Google Maps
- Social: X, Instagram, Facebook
- Hours (Thu/Wed 8PM–3AM, Fri/Sat 8PM–4AM, Sun football season, Mon/Tue closed)
- Footer: Terms · Equal Opportunity Employer · Privacy · FAQ · Sitemap · © 2026 · Webcreativeseo.com

## Placeholder legal pages

Terms, Privacy, FAQ, and Sitemap are linked in the footer but not yet written.
Create `terms.html`, `privacy.html`, etc. when the copy is ready, then point the
footer links to them (currently they're inert `<a>` tags in each page's footer).
