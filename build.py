#!/usr/bin/env python3
"""Build the MERIDIAN symposium website from config.yaml + template.html -> index.html.

Usage:
    python3 build.py

No dependencies beyond the standard library and PyYAML. If PyYAML is missing,
install it with:  pip install pyyaml
"""

from __future__ import annotations

import calendar as _calendar
import datetime as _dt
import html
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit(
        "PyYAML is not installed. Install it with:\n    pip install pyyaml\n"
        "(or: python3 -m pip install pyyaml)"
    )

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config.yaml"
TEMPLATE = HERE / "template.html"
OUTPUT = HERE / "index.html"

# Inline SVG wordmark: a globe with a meridian and an East <-> West axis.
LOGO_SVG = """<svg class="mark" viewBox="0 0 48 48" aria-hidden="true" focusable="false">
  <defs><linearGradient id="ew" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="var(--east)"/><stop offset="1" stop-color="var(--west)"/>
  </linearGradient></defs>
  <circle cx="24" cy="24" r="19" fill="none" stroke="url(#ew)" stroke-width="2.4"/>
  <ellipse cx="24" cy="24" rx="7.5" ry="19" fill="none" stroke="url(#ew)" stroke-width="1.3" opacity=".55"/>
  <line x1="5" y1="24" x2="43" y2="24" stroke="url(#ew)" stroke-width="2.4"/>
  <path d="M11 19 L5 24 L11 29" fill="none" stroke="var(--east)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M37 19 L43 24 L37 29" fill="none" stroke="var(--west)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
</svg>"""


# Verified template links (acmart current).
TEMPLATE_LINKS = [
    ("Download acmart (current, v2.18)", "downloads/acmart-template.zip", True),
    ("ACM Primary Article Template (official)", "https://www.acm.org/publications/proceedings-template", False),
    ("Open in Overleaf — sigconf", "https://www.overleaf.com/latex/templates/association-for-computing-machinery-acm-sig-proceedings-template/bmvfhcdnxfty", False),
    ("Anonymization policy (double-blind)", "https://www.acm.org/publications/policies/anonymization-policy", False),
]
AUTHOR_LINKS = [
    ("ACM ICPS author guidance", "https://www.acm.org/publications/icps/author-guidance", False),
    ("Register / find your ORCID", "https://orcid.org/register", False),
]
TEMPLATE_PREVIEW = "assets/template-preview.jpg"
# acmart formatting facts (current v2.18). The class fixes the typography.
TEMPLATE_SPECS = (
    "The acmart class sets the typography for you, so don't change fonts, font size, "
    "margins or line spacing by hand. The sigconf format is two-column on US-Letter "
    "and uses the Libertine font set, which the class loads automatically. Citations "
    "use the bundled ACM-Reference-Format style. For the review version, add the "
    "anonymous option: \\documentclass[sigconf,anonymous]{acmart}. Stay within the "
    "page limit above (it excludes the reference list)."
)


def esc(value) -> str:
    return html.escape(str(value)) if value is not None else ""


def tbd(value) -> str:
    text = (str(value).strip() if value is not None else "")
    if not text or text.upper().startswith("TBD"):
        return '<span class="tbd">TBD</span>'
    return esc(text)


def link(text: str, url: str, cls: str = "") -> str:
    """External link in a new tab, or plain text if no url."""
    c = f' class="{cls}"' if cls else ""
    if url:
        return f'<a{c} href="{esc(url)}" target="_blank" rel="noopener">{esc(text)}</a>'
    return f'<span{c}>{esc(text)}</span>'


def initials(name: str) -> str:
    words = [w for w in str(name).replace("(", " ").split() if w[:1].isalpha()]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[-1][0]).upper()


def avatar(name: str, photo: str | None = None) -> str:
    if photo:
        return f'<span class="avatar photo"><img src="{esc(photo)}" alt="" loading="lazy"></span>'
    side = "east" if sum(map(ord, str(name))) % 2 == 0 else "west"
    return f'<span class="avatar {side}" aria-hidden="true">{esc(initials(name))}</span>'


def render_calendar(cfg: dict) -> str:
    """Google-Calendar-style mini months with highlighted, hoverable event days."""
    conf = cfg.get("calendar", {})
    year = conf.get("year", 2026)
    months = conf.get("months", [])
    daymap: dict[str, list[tuple[str, str]]] = {}
    for e in conf.get("events", []):
        if e.get("date"):
            days = [e["date"]]
        else:
            s, en = _dt.date.fromisoformat(e["start"]), _dt.date.fromisoformat(e["end"])
            days = [(s + _dt.timedelta(d)).isoformat() for d in range((en - s).days + 1)]
        for d in days:
            daymap.setdefault(d, []).append((e.get("kind", "ours"), e.get("label", "")))

    cal = _calendar.Calendar(firstweekday=0)  # Monday first
    dow = "".join(f'<span class="cdow">{x}</span>' for x in ["M", "T", "W", "T", "F", "S", "S"])
    blocks = []
    for m in months:
        cells = ""
        for week in cal.monthdayscalendar(year, m):
            for day in week:
                if day == 0:
                    cells += '<span class="cday pad"></span>'
                    continue
                iso = f"{year}-{m:02d}-{day:02d}"
                evs = daymap.get(iso)
                if evs:
                    kind = "rel" if all(k == "related" for k, _ in evs) else "hot"
                    tip = " · ".join(l for _, l in evs)
                    cells += (f'<span class="cday {kind}" data-tip="{esc(tip)}" '
                              f'aria-label="{esc(tip)}" tabindex="0">{day}</span>')
                else:
                    cells += f'<span class="cday">{day}</span>'
        blocks.append(
            f'<div class="calmonth"><div class="cmname">{esc(_calendar.month_name[m])} {year}</div>'
            f'<div class="cgrid">{dow}{cells}</div></div>'
        )
    legend = '<div class="callegend"><span><i class="lg hot"></i> Deadlines &amp; symposium</span></div>'
    return f'<div class="cal">{"".join(blocks)}</div>{legend}'


def section(id_, kicker, title, inner, extra_class="") -> str:
    cls = f' class="{extra_class}"' if extra_class else ""
    return (
        f'<section id="{id_}"{cls}>\n  <div class="wrap">\n'
        f'    <p class="kicker">{esc(kicker)}</p>\n'
        f'    <h2>{esc(title)}</h2>\n{inner}\n  </div>\n</section>'
    )


def render(cfg: dict) -> str:
    ev = cfg.get("event", {})
    parts = []
    brand = ev.get("brand", "Symposium")
    year = ev.get("year", "")

    # --- Nav --------------------------------------------------------------
    nav = [("scope", "About"), ("cfp", "Call"), ("dates", "Dates"),
           ("committee", "Committee"), ("submission", "Submit")]
    nav_links = "".join(f'<a href="#{i}">{esc(t)}</a>' for i, t in nav)
    parts.append(
        '<nav class="bar">\n  <div class="wrap">\n'
        f'    <a class="brand" href="#top">{LOGO_SVG}<span>{esc(brand)} <em>{esc(year)}</em></span></a>\n'
        f'    <div class="links">{nav_links}</div>\n'
        '  </div>\n</nav>'
    )

    # --- Hero -------------------------------------------------------------
    cta = '<a class="btn primary" href="#cfp">Call for Papers</a><a class="btn ghost" href="#dates">Important Dates</a>'
    parts.append(
        '<header class="hero" id="top">\n'
        f'  <div class="bgyear" aria-hidden="true">{esc(year)}</div>\n'
        '  <div class="wrap">\n'
        f'    <p class="kicker">{esc(ev.get("edition"))} · {esc(ev.get("location"))} · {esc(ev.get("date"))}</p>\n'
        f'    <h1 class="logo">{LOGO_SVG}<span class="word">{esc(brand)}</span><span class="yr">{esc(year)}</span></h1>\n'
        f'    <p class="subtitle">{esc(ev.get("subtitle"))}</p>\n'
        f'    <p class="tagline">{esc(ev.get("tagline"))}</p>\n'
        f'    <div class="cta">{cta}</div>\n'
        + (f'    <p class="adjacency">{esc(ev.get("adjacency"))}</p>\n' if ev.get("adjacency") else "")
        + '  </div>\n</header>'
    )

    # --- Scope + partners (logos, linked) --------------------------------
    def org_logo(o):
        name, url = o.get("name", ""), o.get("url", "")
        if not o.get("logo"):
            return link(name, url, "chip")
        cls = "plogo inv" if o.get("invert") else "plogo"
        style = f' style="--lh:{esc(o["logo_scale"])}"' if o.get("logo_scale") else ""
        box = (f'<span class="plogobox"{style} title="{esc(name)}">'
               f'<img class="{cls}" src="{esc(o["logo"])}" alt="{esc(name)}" loading="lazy"></span>')
        if url:
            return f'<a href="{esc(url)}" target="_blank" rel="noopener">{box}</a>'
        return box
    partner_logos = "".join(org_logo(o) for o in cfg.get("organizers", []))
    scope_inner = (
        f'    <p class="lead">{esc(cfg.get("scope"))}</p>\n'
        f'    <p class="kicker mt">Organizing institutions</p>\n'
        f'    <div class="plogos">{partner_logos}</div>'
    )
    if cfg.get("note"):
        scope_inner += f'\n    <p class="fineprint">{esc(cfg["note"])}</p>'
    parts.append(section("scope", "About", "Two continents, one volume", scope_inner))

    # --- image band ------------------------------------------------------
    band_imgs = [
        ("assets/band-1.jpg", "On set · HSHL"),
        ("assets/band-2.jpg", "LED volume · TH OWL"),
        ("assets/band-3.jpg", "Pipeline · FilmUni"),
    ]
    band = "".join(
        f'<figure><img src="{esc(s)}" alt="{esc(c)}" loading="lazy"></figure>'
        for s, c in band_imgs
    )
    parts.append(f'<div class="band">{band}</div>')

    # --- Call for Papers --------------------------------------------------
    cfp = cfg.get("cfp", {})
    track_cards = ""
    for t in cfg.get("tracks", []):
        thumb = (f'<div class="thumb" style="background-image:url(\'{esc(t.get("image"))}\')"></div>'
                 if t.get("image") else "")
        track_cards += (
            f'<div class="card trk">{thumb}<div class="cardbody">'
            f'<h3>{esc(t.get("title"))}</h3><p>{esc(t.get("desc"))}</p></div></div>'
        )
    fmt_cards = ""
    for f in cfp.get("formats", []):
        href = f'{esc(f.get("id"))}.html' if f.get("id") else "#"
        fmt_cards += (
            f'<a class="card fmt" href="{href}"><div class="cardbody">'
            f'<span class="tag">Proceedings</span>'
            f'<h3>{esc(f.get("title"))}</h3><p>{esc(f.get("desc"))}</p>'
            f'<span class="more">Details, requirements &amp; template →</span></div></a>'
        )
    cfp_inner = (
        f'    <p class="lead">{esc(cfp.get("intro"))}</p>\n'
        f'    <p class="kicker mt">Tracks</p>\n'
        f'    <div class="cards">{track_cards}</div>\n'
        f'    <p class="kicker mt">Submission categories — all enter the proceedings</p>\n'
        f'    <div class="cards fmts">{fmt_cards}</div>\n'
        f'    <div class="notes">\n'
        f'      <p><strong>Template.</strong> {esc(cfp.get("template"))}</p>\n'
        f'      <p><strong>Language.</strong> {esc(cfp.get("language"))}</p>\n'
        f'      <p><strong>Peer review.</strong> {esc(cfp.get("review"))}</p>\n'
        f'      <p><strong>Proceedings.</strong> {esc(ev.get("proceedings"))}</p>\n'
        f'    </div>'
    )
    parts.append(section("cfp", "Call for Papers", "Contribute", cfp_inner))

    # --- Important Dates + Months grid + Related -------------------------
    rows = "".join(
        f'<tr><td class="dt">{tbd(d.get("date"))}</td><td>{esc(d.get("label"))}</td></tr>'
        for d in cfg.get("dates", [])
    )
    related = "".join(
        f'<li><span class="rdt">{esc(d.get("date"))}</span> {esc(d.get("label"))}</li>'
        for d in cfg.get("related_dates", [])
    )
    related_block = (
        f'<div class="related"><p class="kicker">Also on the radar</p><ul>{related}</ul></div>'
        if related else ""
    )
    dates_inner = (
        '    <div class="datesgrid">\n'
        f'      <div class="dcol"><p class="kicker">Deadlines</p><table class="dates">{rows}</table>{related_block}</div>\n'
        f'      <div class="dcol"><p class="kicker">Calendar</p>{render_calendar(cfg)}</div>\n'
        '    </div>'
    )
    parts.append(section("dates", "Timeline", "Important Dates", dates_inner, "alt"))

    # (Author's Guide lives on each category subpage, not the landing page.)

    # --- Committee (linked names) ----------------------------------------
    def people(items):
        out = []
        for p in items:
            name_html = link(p.get("name"), p.get("url"), "name")
            role = f'<span class="prole">{esc(p.get("role"))}</span>' if p.get("role") else ""
            aff = f'<span class="aff">{esc(p.get("affiliation"))}</span>' if p.get("affiliation") else ""
            out.append(
                f'<div class="person">{avatar(p.get("name", ""), p.get("photo"))}'
                f'<span class="pinfo">{name_html}{role}{aff}</span></div>'
            )
        return "".join(out)

    com = cfg.get("committee", {})
    groups = [
        ("General Chair", com.get("general_chairs", [])),
        ("Program Chair", com.get("program_chairs", [])),
        ("Publications Chair", com.get("publications_chairs", [])),
        ("Local Arrangements", com.get("local_arrangements_chairs", [])),
        ("Technical Program Committee", com.get("tpc", [])),
        ("Showcase & Industry", com.get("showcase_industry_chairs", [])),
    ]
    com_inner = "\n".join(
        f'    <div class="committee-group"><h3>{esc(label)}</h3><div class="people">{people(items)}</div></div>'
        for label, items in groups
        if items
    )
    parts.append(section("committee", "People", "Committee", com_inner, "alt"))

    # --- Submission -------------------------------------------------------
    sub = cfg.get("submission", {})
    if sub.get("url"):
        btn = f'<a class="btn primary" href="{esc(sub["url"])}">Submit a paper</a>'
    else:
        btn = '<a class="btn ghost disabled">Submission link coming soon</a>'
    contact = cfg.get("contact", {})
    email = contact.get("email")
    if email and not str(email).upper().startswith("TBD"):
        email_html = f'<a href="mailto:{esc(email)}">{esc(email)}</a>'
    else:
        email_html = '<span class="tbd">TBD</span>'
    sub_inner = (
        f'    <p class="lead">Submission system: {tbd(sub.get("system"))}</p>\n'
        f'    <div class="cta">{btn}</div>\n'
        f'    <p class="fineprint mt">Contact: {email_html}</p>'
    )
    parts.append(section("submission", "Submit", "Submission", sub_inner))

    # --- Footer -----------------------------------------------------------
    org_line = " · ".join(link(o.get("name"), o.get("url")) for o in cfg.get("organizers", []))
    note_html = (f'    <div class="fineprint">{esc(cfg.get("note"))}</div>\n' if cfg.get("note") else "")
    credits = (
        '    <div class="fineprint">Images: HSHL, TH OWL, FilmUni and NTU (own photos). '
        'Track images: University of Portsmouth CCIXR © Tim Sheerman-Chase (CC BY 2.0); '
        '“Captured” immersive installation by Hanna Haaslahti, 2021 (CC BY-SA 4.0) — via Wikimedia Commons.</div>\n'
    )
    parts.append(
        '<footer>\n  <div class="wrap">\n'
        f'    <div class="flogo">{LOGO_SVG}<span>{esc(brand)} {esc(year)}</span></div>\n'
        f'    <div class="organizers">{org_line}</div>\n'
        + note_html
        + credits
        + '  </div>\n</footer>'
    )

    return "\n".join(parts)


def render_category(cfg: dict, fmt: dict) -> str:
    """A standalone page for one submission category."""
    ev = cfg.get("event", {})
    brand = ev.get("brand", "Symposium")
    year = ev.get("year", "")
    sub = cfg.get("submission", {})

    reqs = "".join(f"<li>{esc(r)}</li>" for r in fmt.get("requirements", []))
    tpl = "".join(
        f'<a class="reschip" href="{esc(href)}"'
        + (' download' if dl else ' target="_blank" rel="noopener"')
        + f'>{esc(label)}{" ↓" if dl else " ↗"}</a>'
        for label, href, dl in TEMPLATE_LINKS
    )
    if sub.get("url"):
        cta = f'<a class="btn primary" href="{esc(sub["url"])}">Submit a {esc(fmt.get("title","")).rstrip("s")}</a>'
    else:
        cta = '<a class="btn ghost disabled">Submission opens 1 July 2026</a>'

    nav = (
        '<nav class="bar">\n  <div class="wrap">\n'
        f'    <a class="brand" href="index.html">{LOGO_SVG}<span>{esc(brand)} <em>{esc(year)}</em></span></a>\n'
        '    <div class="links"><a href="index.html#cfp">← All categories</a></div>\n'
        '  </div>\n</nav>'
    )
    banner = (f'  <div class="subbanner" style="background-image:url(\'{esc(fmt.get("image"))}\')"></div>\n'
              if fmt.get("image") else "")
    head = (
        '<header class="subhero">\n  <div class="wrap">\n'
        '    <p class="kicker">Submission category · Proceedings</p>\n'
        f'    <h1>{esc(fmt.get("title"))}</h1>\n'
        f'    <p class="tagline">{esc(fmt.get("desc"))}</p>\n'
        '  </div>\n'
        f'{banner}</header>'
    )
    author = "".join(
        f'<a class="reschip" href="{esc(href)}" target="_blank" rel="noopener">{esc(label)} ↗</a>'
        for label, href, _ in AUTHOR_LINKS
    )
    body_sec = (
        '<section>\n  <div class="wrap narrow">\n'
        f'    <p class="kicker">What it is</p>\n    <p class="lead">{esc(fmt.get("about"))}</p>\n'
        f'    <p class="kicker mt">Requirements</p>\n    <ul class="reqs">{reqs}</ul>\n'
        f'    <p class="kicker mt">What ACM says</p>\n    <p>{esc(fmt.get("acm"))}</p>\n'
        f'    <p class="kicker mt">Template &amp; formatting</p>\n'
        '    <div class="tplrow">\n'
        f'      <a class="tplprev" href="downloads/acmart-template.zip" download><img src="{TEMPLATE_PREVIEW}" alt="acmart sigconf sample — top of the first page" loading="lazy"><span>acmart · sigconf — sample</span></a>\n'
        f'      <div class="tplinfo"><p>{esc(TEMPLATE_SPECS)}</p><div class="reschips">{tpl}</div></div>\n'
        '    </div>\n'
        f'    <p class="kicker mt">More for authors</p>\n    <div class="reschips">{author}</div>\n'
        f'    <div class="cta" style="margin-top:2.4rem;">{cta}<a class="btn ghost" href="index.html#cfp">Back to all categories</a></div>\n'
        '  </div>\n</section>'
    )
    footer = (
        '<footer>\n  <div class="wrap">\n'
        f'    <div class="flogo">{LOGO_SVG}<span>{esc(brand)} {esc(year)}</span></div>\n'
        f'    <div class="fineprint">{esc(cfg.get("note", ""))}</div>\n'
        '  </div>\n</footer>'
    )
    return "\n".join([nav, head, body_sec, footer])


def write_page(shell: str, filename: str, title: str, desc: str, body: str) -> None:
    page = shell.replace("{{TITLE}}", esc(title)).replace("{{DESCRIPTION}}", esc(desc)).replace("{{BODY}}", body)
    out = HERE / filename
    out.write_text(page, encoding="utf-8")
    print(f"Wrote {out.name} ({len(page):,} bytes)")


def main() -> None:
    if not CONFIG.exists():
        sys.exit(f"Missing config: {CONFIG}")
    if not TEMPLATE.exists():
        sys.exit(f"Missing template: {TEMPLATE}")

    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    ev = cfg.get("event", {})
    brand, year = ev.get("brand", "Symposium"), ev.get("year", "")
    shell = TEMPLATE.read_text(encoding="utf-8")

    # landing page
    title = f'{brand} {year} — {ev.get("subtitle", "")}'.strip()
    write_page(shell, "index.html", title, (cfg.get("scope") or "").strip()[:160], render(cfg))

    # one page per submission category
    for fmt in cfg.get("cfp", {}).get("formats", []):
        if not fmt.get("id"):
            continue
        ptitle = f'{esc(fmt.get("title"))} — {brand} {year}'
        write_page(shell, f'{fmt["id"]}.html', ptitle, fmt.get("desc", ""), render_category(cfg, fmt))


if __name__ == "__main__":
    main()
