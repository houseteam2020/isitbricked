# Is It Bricked? (static site)
Plain HTML/CSS/JS. All data is in `data/mods.json`. To regenerate it, edit `build_data.py` and run `python3 build_data.py`.
Source verification log: `docs/sources/verified_reddit_2026-10-20.md`. All 14 Reddit threads were opened in a browser on 2026-10-20. Reddit returns 403 to bots, but the links open normally in a browser.

Local preview: `python3 -m http.server 8765`, then open http://localhost:8765

## Live integrations
- Newsletter (index.html, #newsletter): native form that posts `email_address` to Kit form 10078153 (`https://app.kit.com/forms/10078153/subscriptions`). `app.js` submits it with fetch and shows a thank-you message, and falls back to a normal POST.
- Report form (`report.html`): FormSubmit form that emails reports to isitbricked@gmail.com. It has a honeypot (`_honey`), `?mod=` prefill, and a mailto fallback for readers whose ad blockers block FormSubmit.
- Affiliate (index.html, "PS5 storage for modders" card): three PS5-compatible heatsink M.2 SSDs (Samsung 990 PRO, WD_BLACK SN850X, Seagate FireCuda 530). Each one links to Amazon with the Associates tag `isitbricked-20` (`rel="sponsored nofollow noopener"`) and to its maker's PS5 compatibility page. The Amazon Associates disclosure is shown under the card and in the footer.

## Publish (GitHub Pages)
1. Create a public repo, e.g. `isitbricked`, and push this folder to `main`.
2. In the repo, go to Settings > Pages > Source: "Deploy from a branch", choose `main` / root.
3. Optional custom domain: add a CNAME file with the domain and set the DNS records shown in GitHub's docs.
