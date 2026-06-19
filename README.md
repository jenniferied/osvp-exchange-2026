# OSVP EXCHANGE 2026 — Website

Static site for the ICPS application. One data source (`config.yaml`), one small
Python build script, plain HTML/CSS. No npm, no framework. Dark editorial design
(SIGGRAPH-style) with an inline-SVG logo and an Asia⇄Europe gradient motif.
"OSVP EXCHANGE" is a working title — change `event.brand` in `config.yaml` to rename.

## Build

```bash
python3 build.py
```

This renders `config.yaml` + `template.html` into `index.html`. Open `index.html`
in a browser, or serve locally:

```bash
python3 -m http.server 8000   # then open http://localhost:8000
```

Only dependency beyond the standard library is **PyYAML**. If missing:

```bash
pip install pyyaml
```

## Files

| File | Purpose |
|---|---|
| `config.yaml` | Single source of truth — all content lives here. Edit this. |
| `build.py` | Renders config + template into `index.html`. |
| `template.html` | Page shell (`{{TITLE}}`, `{{DESCRIPTION}}`, `{{BODY}}`). |
| `style.css` | Styling. |
| `index.html` | Generated output — do not edit by hand. |

## Status

Dates, formats, committee, partners (incl. HSHL) and tracks are filled. Real avatars
are intentionally **monogram placeholders** — swap in official headshots (with the
persons' OK) before the site goes public.

## Still to fill in (currently TBD / placeholders)

Edit `config.yaml`, then re-run `python3 build.py`:

- **Final name**: confirm or replace `event.brand` ("OSVP EXCHANGE").
- **Venue**: exact Singapore location (`event.location` currently just "Singapore").
- **Submission system + link**: `submission.system` and `submission.url` (OpenReview / EasyChair / HotCRP). Once `url` is set, the "Submit a paper" button activates automatically.
- **Contact email**: `contact.email` — set a dedicated symposium address.
- **NTU Local Arrangements Chair**: name the actual NTU person.
- **Affiliations to confirm**: Julian Stump.

TBD values render with a highlighted "TBD" marker on the page so gaps are visible.

## Hosting

GitHub Pages or an NTU / TH OWL subdomain. The output is fully static (`index.html` + `style.css`).
