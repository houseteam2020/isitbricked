# Is It Bricked? (static site)
Plain HTML/CSS/JS. All data is in `data/mods.json`. To regenerate it, edit `build_data.py` and run `python3 build_data.py`.
Source verification log: `docs/sources/verified_reddit_2026-10-20.md`. All 14 Reddit threads were opened in a browser on 2026-10-20. Reddit returns 403 to bots, but the links open normally in a browser.

Local preview: `python3 -m http.server 8765`, then open http://localhost:8765

## Placeholders to replace before launch
- Newsletter (index.html, #newsletter): beehiiv embed code.
- Report form (index.html, #report): Tally or Google Form link, or a contact email.
- Affiliate (index.html, "Running out of space?"): Amazon Associates link with the owner's tag, plus the disclosure text.

## Publish (GitHub Pages)
1. Create a public repo, e.g. `isitbricked`, and push this folder to `main`.
2. In the repo, go to Settings > Pages > Source: "Deploy from a branch", choose `main` / root.
3. Optional custom domain: add a CNAME file with the domain and set the DNS records shown in GitHub's docs.
