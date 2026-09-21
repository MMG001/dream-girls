#!/usr/bin/env python3
"""
Dream Girls — Interlinked JSON-LD entity graph generator (spec v3.1).

Builds ONE @graph per page with stable @id cross-references, injects it into
each page's <head> (replacing any prior JSON-LD), then runs two build-time
checks and fails hard on any violation:

  1. @id integrity   — every referenced @id is defined on that same page
  2. property lint   — Rule-11 traps (audience on business, about/inLanguage
                       on Service, extra keys on EntryPoint, *-input on actions)

Run from the repo root:  python3 tools/schema.py
"""
import json, re, sys, html as htmlmod
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://dream-girls.pages.dev"   # <-- swap when the custom domain is attached
LANG = "en-US"

# ─────────────────────────────────────────────────────────────────────────────
# BUSINESS FACTS (single source of truth — every value below is visible on-site)
# ─────────────────────────────────────────────────────────────────────────────
BIZ = {
    "name": "Dream Girls",
    "types": ["NightClub", "AdultEntertainment"],          # v3.1 multi-type: one entity
    "telephone": "+1-612-333-7326",
    "street": "12 N 5th St", "city": "Minneapolis", "region": "MN", "zip": "55403",
    "lat": 44.9799246, "lng": -93.2727167,                 # from the club's Google Maps link (not estimated)
    "map": "https://maps.app.goo.gl/zmz4iUMTAG7ftsHu6",
    "gmp": "https://www.google.com/maps/place/Dream+Girls+Strip+Club/@44.9799246,-93.2727167,17z/data=!3m1!4b1!4m6!3m5!1s0x52b3329069e89623:0xc9499bbe37a1f31c!8m2!3d44.9799246!4d-93.2727167!16s%2Fg%2F1wl4q7hw",
    "sameAs": [
        "https://x.com/dreamgirlsmpls",
        "https://www.instagram.com/dreamgirlsofficial/",
        "https://www.facebook.com/dreamgirlsminneapolis",
    ],
    "hours": [  # mirrors the hours table on specials.html + contact.html
        {"days": ["Wednesday", "Thursday"], "opens": "20:00", "closes": "03:00"},
        {"days": ["Friday", "Saturday"],    "opens": "20:00", "closes": "04:00"},
    ],
    "radius_mi": 30,
    "anchor_city": "Minneapolis", "state": "Minnesota",
    "wiki_city":  "https://en.wikipedia.org/wiki/Minneapolis",
    "wiki_state": "https://en.wikipedia.org/wiki/Minnesota",
    "wiki_metro": "https://en.wikipedia.org/wiki/Minneapolis%E2%80%93Saint_Paul",  # verified title
    "keywords": "strip club, gentlemen's club, adult entertainment, exotic dancers, nude dancers, private dances, VIP room, cabaret, Minneapolis nightlife",
    # visible amenities / policies (this is where the 18+ signal lives — NOT `audience`, Rule 11)
    "amenities": [
        "18+ admission with valid photo ID",
        "Juice bar — no alcohol served",
        "Full-nude stage entertainment",
        "Private dance rooms",
        "VIP room",
        "Free popcorn nightly",
        "Open till 4AM on weekends",
    ],
}

# Concepts the business genuinely covers (Wikipedia sameAs — well-established titles)
KNOWS = [
    ("Strip club",  "https://en.wikipedia.org/wiki/Strip_club"),
    ("Lap dance",   "https://en.wikipedia.org/wiki/Lap_dance"),
    ("Stripper",    "https://en.wikipedia.org/wiki/Stripper"),
    ("Nightlife",   "https://en.wikipedia.org/wiki/Nightlife"),
]

# ─────────────────────────────────────────────────────────────────────────────
# SERVICES — per-slug metadata (three-level detail rule applied per page)
# ─────────────────────────────────────────────────────────────────────────────
SERVICES = {
    "svc-parties": {
        "name": "Bachelor, bachelorette & group parties",
        "serviceType": "Group event hosting",
        "url": "/parties.html", "own_page": "parties.html",
        "blurb": "Birthdays, bachelor and bachelorette nights, and big group blowouts. Groups of six or more get free cover.",
        "category": ("Bachelor party", "https://en.wikipedia.org/wiki/Bachelor_party"),
        "output": "A reserved group night with free cover for six or more",
        "related": ["svc-vip-room", "svc-private-dances"],
        "card_on": ["index.html"],
    },
    "svc-private-dances": {
        "name": "Private dances",
        "serviceType": "Private dance entertainment",
        "url": "/specials.html", "own_page": "specials.html",
        "blurb": "Topless and nude lap dances start at $20 on the floor. Private dance rooms are priced at the club.",
        "category": ("Lap dance", "https://en.wikipedia.org/wiki/Lap_dance"),
        "output": "A private dance with an entertainer",
        "related": ["svc-vip-room"],
        "card_on": ["index.html", "roll-call.html"],
    },
    "svc-vip-room": {
        "name": "VIP room",
        "serviceType": "VIP lounge access",
        "url": "/parties.html", "own_page": None,           # described on parties + specials, no dedicated page
        "blurb": "Private dances and the VIP room are priced at the club. Ask your entertainer or the floor host to set it up.",
        "category": ("Strip club", "https://en.wikipedia.org/wiki/Strip_club"),
        "output": "VIP room access",
        "related": ["svc-private-dances", "svc-parties"],
        "card_on": ["parties.html", "specials.html", "roll-call.html"],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# PAGES — (subtype, breadcrumb name, mainEntity service slug or None)
# ─────────────────────────────────────────────────────────────────────────────
PAGES = {
    "index.html":     ("WebPage",        "Home",      None),
    "about.html":     ("AboutPage",      "About",     None),
    "specials.html":  ("WebPage",        "Specials",  "svc-private-dances"),
    "roll-call.html": ("CollectionPage", "Roll Call", None),
    "parties.html":   ("WebPage",        "Parties",   "svc-parties"),
    "gallery.html":   ("CollectionPage", "Gallery",   None),
    "contact.html":   ("ContactPage",    "Contact",   None),
    "faq.html":       ("FAQPage",        "FAQ",       None),
    "terms.html":     ("WebPage",        "Terms & Conditions", None),
    "privacy.html":   ("WebPage",        "Privacy Policy",     None),
}

ID = lambda frag: f"{BASE}/#{frag}"
def page_url(f): return BASE + ("/" if f == "index.html" else "/" + f)

# PHOTOS — the Sept 2026 venue shoot (assets/photos/, all 850x550).
# Ordered exactly like the gallery tabs: outside / interior / booths.
PHOTOS = [
    ("outside-03.jpg", "Dreamgirls marquee at 12 N 5th St — Where your fantasy begins"),
    ("outside-02.jpg", "Dreamgirls and Sneaky Pete's neon rooftop signs at night in downtown Minneapolis"),
    ("outside-01.jpg", "Dreamgirls entrance on N 5th Street next to the light rail platform"),
    ("outside-04.jpg", "Dreamgirls canopy over the sidewalk on 5th Street at night"),
    ("stage-04.jpg", "Main stage under blue lights with stage-side seating at Dream Girls"),
    ("club-01.jpg", "Main showroom with stage, poles and table seating"),
    ("club-02.jpg", "Stage-side view across the main floor toward the bar"),
    ("stage-01.jpg", "Main stage with sparkling floor and overhead stage lights"),
    ("club-03.jpg", "Full club floor with tiered seating and the main stage"),
    ("stage-03.jpg", "Wide view of the main stage, spiral staircase and stage rail"),
    ("club-05.jpg", "Stage and cocktail seating under the show lights"),
    ("stage-02.jpg", "Stage rail seating wrapping the main stage"),
    ("dj-booth.jpg", "The DJ booth that runs the room all night"),
    ("club-04.jpg", "Lounge seating on the club floor"),
    ("booth-04.jpg", "Row of private dance booth seating with cocktail tables"),
    ("booth-01.jpg", "Private dance booth chair and ottoman"),
    ("booth-02.jpg", "Semi-private booth seating area"),
    ("booth-03.jpg", "Private dance booth with mirrored wall"),
]

def node_photo(fn, caption):
    u = BASE + "/assets/photos/" + fn
    return {"@type": "ImageObject", "url": u, "contentUrl": u,
            "width": 850, "height": 550, "caption": caption}

# ─────────────────────────────────────────────────────────────────────────────
# NODE BUILDERS
# ─────────────────────────────────────────────────────────────────────────────
def node_website():
    return {"@type": "WebSite", "@id": ID("website"), "name": BIZ["name"], "url": BASE + "/",
            "publisher": {"@id": ID("business")}, "inLanguage": LANG}

def node_logo():
    return {"@type": "ImageObject", "@id": ID("logo"), "url": BASE + "/assets/dream-girls-logo.png",
            "contentUrl": BASE + "/assets/dream-girls-logo.png", "width": 450, "height": 205, "caption": "Dream Girls logo"}

def node_primary_image():
    return {"@type": "ImageObject", "@id": ID("primaryimage"), "url": BASE + "/assets/og-image.png",
            "contentUrl": BASE + "/assets/og-image.png", "width": 1200, "height": 630,
            "caption": "Dream Girls — 18+ full-nude strip club in downtown Minneapolis"}

def node_service_area():
    return {"@type": "GeoCircle", "@id": ID("service-area"),
            "description": f"{BIZ['radius_mi']}-mile service radius anchored on {BIZ['anchor_city']}, {BIZ['state']}",
            "geoMidpoint": {"@type": "GeoCoordinates", "latitude": BIZ["lat"], "longitude": BIZ["lng"]},
            "geoRadius": str(round(BIZ["radius_mi"] * 1609.34))}   # meters

def entry(url):
    return {"@type": "EntryPoint", "urlTemplate": url,
            "actionPlatform": ["http://schema.org/DesktopWebPlatform", "http://schema.org/MobileWebPlatform"]}

def node_business(page):
    b = BIZ
    n = {
        "@type": b["types"], "@id": ID("business"),
        "name": b["name"], "url": BASE + "/",
        "logo": {"@id": ID("logo")}, "image": {"@id": ID("primaryimage")},
        "telephone": b["telephone"],
        "address": {"@type": "PostalAddress", "streetAddress": b["street"], "addressLocality": b["city"],
                    "addressRegion": b["region"], "postalCode": b["zip"], "addressCountry": "US"},
        "geo": {"@type": "GeoCoordinates", "latitude": b["lat"], "longitude": b["lng"]},
        "hasMap": b["map"],
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": h["days"], "opens": h["opens"], "closes": h["closes"]}
            for h in b["hours"]],
        "sameAs": b["sameAs"] + [b["gmp"]],
        "areaServed": [
            {"@id": ID("service-area")},
            {"@type": "State", "name": b["state"], "sameAs": b["wiki_state"]},
            {"@type": "City",  "name": b["anchor_city"], "sameAs": b["wiki_city"]},
            # Requested by client: single metro region (not a city list). Remove for strict v3 3-node compliance.
            {"@type": "AdministrativeArea", "name": "Minneapolis–Saint Paul (Twin Cities) metropolitan area", "sameAs": b["wiki_metro"]},
        ],
        "knowsAbout": [{"@type": "Thing", "name": n_, "sameAs": u} for n_, u in KNOWS],
        "keywords": b["keywords"],
        "publicAccess": True,
        "isAccessibleForFree": False,                 # cover charge is published
        "tourBookingPage": BASE + "/parties.html",    # party/VIP booking entry (Place scope)
        "amenityFeature": [{"@type": "LocationFeatureSpecification", "name": a, "value": True} for a in b["amenities"]],
        "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Dream Girls services",
            "itemListElement": [{"@type": "Offer", "itemOffered": {"@id": ID(s)}} for s in SERVICES]},
        "potentialAction": [
            {"@type": "ReserveAction", "name": "Book a party", "target": entry(BASE + "/contact.html#party")},
            {"@type": "ApplyAction",   "name": "Apply for employment", "target": entry(BASE + "/contact.html#employment")},
            {"@type": "ApplyAction",   "name": "Request a showgirl audition", "target": entry(BASE + "/contact.html#audition")},
            {"@type": "AskAction",     "name": "Contact Dream Girls", "target": entry(BASE + "/contact.html")},
            {"@type": "CommunicateAction", "name": "Call Dream Girls", "target": entry("tel:+16123337326")},
        ],
    }
    # Cover pricing is printed on specials.html only → makesOffer only there (Rule 3)
    if page == "specials.html":
        n["makesOffer"] = [
            {"@type": "Offer", "name": "Cover before midnight", "price": "10", "priceCurrency": "USD", "availability": "https://schema.org/InStock"},
            {"@type": "Offer", "name": "Cover after midnight",  "price": "15", "priceCurrency": "USD", "availability": "https://schema.org/InStock"},
            {"@type": "Offer", "name": "First beverage (required, after midnight)", "price": "14", "priceCurrency": "USD", "availability": "https://schema.org/InStock"},
            {"@type": "Offer", "name": "Lap dance (from)", "price": "20", "priceCurrency": "USD", "availability": "https://schema.org/InStock"},
        ]
    return n

def node_service(slug, page):
    """Three-level detail rule."""
    s = SERVICES[slug]
    base = {"@type": "Service", "@id": ID(slug), "name": s["name"], "url": BASE + s["url"], "provider": {"@id": ID("business")}}
    if s["own_page"] == page:            # full node
        cn, cu = s["category"]
        base.update({
            "serviceType": s["serviceType"], "description": s["blurb"],
            "areaServed": {"@id": ID("service-area")},
            "category": {"@type": "Thing", "name": cn, "sameAs": cu},
            "serviceOutput": {"@type": "Thing", "name": s["output"]},
            "isRelatedTo": [{"@id": ID(r)} for r in s["related"]],
            "mainEntityOfPage": {"@id": page_url(page) + "#webpage"},
        })
    elif page in s["card_on"]:           # card-level
        cn, cu = s["category"]
        base.update({"serviceType": s["serviceType"], "description": s["blurb"],
                     "areaServed": {"@id": ID("service-area")},
                     "category": {"@type": "Thing", "name": cn, "sameAs": cu}})
    return base                          # nav-level: @id, name, url, provider only

def node_breadcrumb(page):
    _, name, _ = PAGES[page]
    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"}]
    if page != "index.html":
        items.append({"@type": "ListItem", "position": 2, "name": name, "item": page_url(page)})
    return {"@type": "BreadcrumbList", "@id": page_url(page) + "#breadcrumb", "itemListElement": items}

def read_meta(src):
    t = re.search(r"<title>(.*?)</title>", src, re.S).group(1)
    d = re.search(r'<meta name="description" content="([^"]*)"', src).group(1)
    return htmlmod.unescape(t).strip(), htmlmod.unescape(d).strip()

def node_webpage(page, src):
    subtype, _, main_slug = PAGES[page]
    title, desc = read_meta(src)
    n = {"@type": subtype, "@id": page_url(page) + "#webpage", "url": page_url(page), "name": title,
         "description": desc, "isPartOf": {"@id": ID("website")}, "about": {"@id": ID("business")},
         "breadcrumb": {"@id": page_url(page) + "#breadcrumb"}, "primaryImageOfPage": {"@id": ID("primaryimage")},
         "inLanguage": LANG}
    if main_slug: n["mainEntity"] = {"@id": ID(main_slug)}
    if page == "gallery.html":           # ImageGallery: every photo in the tabbed grid
        n["@type"] = [subtype, "ImageGallery"]
        n["associatedMedia"] = [node_photo(fn, cap) for fn, cap in PHOTOS]
    if page == "faq.html":               # FAQPage: mirror the visible <details> Q&A, HTML stripped
        qa = re.findall(r"<summary>(.*?)</summary>\s*<p>(.*?)</p>", src, re.S)
        strip = lambda x: htmlmod.unescape(re.sub(r"<[^>]+>", "", x)).strip()
        n["mainEntity"] = [{"@type": "Question", "name": strip(q),
                            "acceptedAnswer": {"@type": "Answer", "text": strip(a)}} for q, a in qa]
    return n

def nodes_events(page):
    """Recurring weekly nights published on specials.html (v3.1)."""
    if page != "specials.html": return []
    def ev(frag, name, day, desc):
        return {"@type": "Event", "@id": page_url(page) + "#" + frag, "name": name, "description": desc,
                "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
                "eventStatus": "https://schema.org/EventScheduled",
                "eventSchedule": {"@type": "Schedule", "byDay": "https://schema.org/" + day,
                                  "repeatFrequency": "P1W", "startTime": "20:00", "endTime": "03:00"},
                "location": {"@id": ID("business")}, "organizer": {"@id": ID("business")},
                "offers": {"@type": "Offer", "name": "Free cover with valid ID", "price": "0", "priceCurrency": "USD",
                           "availability": "https://schema.org/InStock", "url": page_url(page)}}
    return [
        ev("college-night", "College Night Thursdays", "Thursday", "Free cover with college ID. Beverage purchase required."),
        ev("military-night", "Military Wednesdays", "Wednesday", "Free cover with military ID."),
    ]

def build_graph(page, src):
    g = [node_website(), node_business(page), node_logo(), node_primary_image(), node_service_area(),
         node_breadcrumb(page), node_webpage(page, src)]
    g += [node_service(s, page) for s in SERVICES]
    g += nodes_events(page)
    return {"@context": "https://schema.org", "@graph": g}

# ─────────────────────────────────────────────────────────────────────────────
# CHECKS
# ─────────────────────────────────────────────────────────────────────────────
def walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o, list):
        for v in o: yield from walk(v)

def check_ids(graph, page):
    defined, referenced = set(), set()
    for o in walk(graph):
        if "@id" in o:
            (defined if len(o) > 1 else referenced).add(o["@id"])
    dangling = referenced - defined
    assert not dangling, f"[{page}] dangling @id: {sorted(dangling)}"

def check_props(graph, page):
    for o in walk(graph):
        t = o.get("@type"); types = t if isinstance(t, list) else [t]
        if o.get("@id") == ID("business"):
            for bad in ("audience", "inLanguage"):
                assert bad not in o, f"[{page}] `{bad}` on business node (Rule 11)"
        if "Service" in types:
            for bad in ("about", "inLanguage"):
                assert bad not in o, f"[{page}] `{bad}` on Service (Rule 11)"
        if "EntryPoint" in types:
            extra = set(o) - {"@type", "urlTemplate", "actionPlatform"}
            assert not extra, f"[{page}] extra keys on EntryPoint {extra}"
        if any(str(x).endswith("Action") for x in types):
            bad = [k for k in o if k.endswith("-input")]
            assert not bad, f"[{page}] `-input` on {types}: {bad}"

# ─────────────────────────────────────────────────────────────────────────────
# INJECT
# ─────────────────────────────────────────────────────────────────────────────
def inject(page):
    p = ROOT / page
    src = p.read_text()
    src = re.sub(r'\s*<script type="application/ld\+json">.*?</script>', "", src, flags=re.S)   # remove old JSON-LD
    graph = build_graph(page, src)
    check_ids(graph, page); check_props(graph, page)
    js = json.dumps(graph, ensure_ascii=False, separators=(",", ":"))
    json.loads(js)  # parses
    tag = f'<script type="application/ld+json">{js}</script>\n</head>'
    assert src.count("</head>") == 1
    src = src.replace("</head>", tag, 1)
    p.write_text(src)
    return len(graph["@graph"])

if __name__ == "__main__":
    for page in PAGES:
        n = inject(page)
        print(f"  {page:16} {n:2} nodes  ✓ ids  ✓ props")
    print("schema build OK — 0 dangling @ids, 0 Rule-11 violations")
