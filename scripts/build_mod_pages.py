#!/usr/bin/env python3
"""Build static, crawlable SEO pages from data/mods.json.

Writes:
  mods/<id>/index.html   one page per mod (https://isitbricked.com/mods/<id>/)
  mods/index.html        list of every mod page
  sitemap.xml            all public pages
  robots.txt             points crawlers to the sitemap
  index.html             refreshes the static mod list between MODLIST markers

Every claim on a page comes from mods.json (status, summary, dated reports).
Run from the repo root after editing data:  python3 scripts/build_mod_pages.py
"""
import html, json, os, re, shutil, sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://isitbricked.com"
# Optional: Google Search Console HTML-tag token (content="..." value only).
GSC_TOKEN_FILE = os.path.join(ROOT, "data", "google_site_verification.txt")

LABEL = {"works": "Works", "crashes": "Crashes", "bricks": "Bricks",
         "fixed": "Fixed", "mixed": "Mixed reports", "unknown": "Unknown"}
# Same wording as the status definitions on about.html.
MEANING = {
    "bricks": "Reports say the game wouldn't start or stayed stuck loading, and fixing it took a reinstall or clearing reserved space.",
    "crashes": "Reports of crashes or freezes during play, with no conflicting \"works for me\" reports found yet.",
    "mixed": "Credible reports point both ways, so we show both sides instead of picking one.",
    "works": "Recent reports of stable use on the current patch, with no unresolved crash reports.",
    "fixed": "Earlier crash reports, followed by a mod update and new reports that it now works.",
    "unknown": "Someone suspected it, but nobody has confirmed it either way.",
}
SHORT = {  # one-line answer to "Is <mod> safe on PS5?"
    "bricks": "Players report that {name} bricks the game on PS5.",
    "crashes": "Players report that {name} crashes or freezes the game on PS5.",
    "mixed": "Player reports on {name} are mixed: some crash, some say it works.",
    "works": "Players report that {name} works on PS5.",
    "fixed": "{name} was reported broken, then fixed by a mod update.",
    "unknown": "Not confirmed either way yet for {name}.",
}
TITLE_WORD = {"bricks": "bricks", "crashes": "crashes", "mixed": "mixed reports",
              "works": "works", "fixed": "fixed", "unknown": "unconfirmed"}
TIP_RE = re.compile(r"load order|master", re.I)

e = lambda s: html.escape(str(s if s is not None else ""), quote=True)


def badge(s):
    return f'<span class="badge b-{e(s)}">{e(LABEL.get(s, s))}</span>'


def plural(n, w):
    return f"{n} {w}{'' if n == 1 else 's'}"


def head(title, desc, url, extra=""):
    gsc = ""  # verification tag only needs to be on the homepage (added in main)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(url)}">
<meta property="og:type" content="article"><meta property="og:site_name" content="Is It Bricked?">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{e(url)}">
<meta name="twitter:card" content="summary">
{gsc}<link rel="stylesheet" href="/style.css">{extra}</head><body>
<header><a class="brand" href="/">Is It <span>Bricked?</span></a><nav><a href="/">Tracker</a><a href="/mods/">All mods</a><a href="/about.html">Methodology</a><a href="/report.html">Report a mod</a><a href="/#newsletter">Newsletter</a></nav></header>
"""


FOOT = """<footer>Is It Bricked? is a fan-run project, not affiliated with Bethesda, ZeniMax, Microsoft or Sony. Statuses summarize public player reports and are not guarantees. Always test on a new save. <a href="/about.html">Methodology</a> · <a href="/report.html">Report a mod</a><br>Stuck on a quest bug? Try <a href="https://questunstuck.com">QuestUnstuck</a> for console-safe fixes.</footer>
<!-- Cloudflare Web Analytics --><script type='module' src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{"token": "02b1b3e635f841c9919ef199beeeff54"}'></script><!-- End Cloudflare Web Analytics --></body></html>
"""


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def mod_page(m, d):
    name, st, mid = m["name"], m["status"], m["id"]
    patch = d["current_patch"]
    checked = d["generated"]
    url = f"{SITE}/mods/{mid}/"
    reps = sorted(m["reports"], key=lambda r: r["date"], reverse=True)
    latest = reps[0]["date"] if reps else None
    n = len(reps)
    short = SHORT[st].format(name=name)
    title = f"Is {name} safe on PS5? {LABEL[st]} · current patch {patch['label'].replace('PS5 ', '')} | Is It Bricked?"
    desc = (f"{short} {m['summary']}")
    if len(desc) > 300:
        desc = desc[:297].rsplit(" ", 1)[0] + "…"
    counts = {}
    for r in reps:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    count_txt = ", ".join(f"{c} {LABEL.get(v, v).lower()}" for v, c in sorted(counts.items(), key=lambda x: -x[1]))

    items = []
    for r in reps:
        dt = r["date"] if r.get("date_precision") == "exact" else "≈" + r["date"]
        q = f'“{e(r["quote"])}”' if r.get("quote") else ""
        note = f' <span class="muted">{e(r["note"])}</span>' if r.get("note") else ""
        ver = f' <span class="vtag">✓ {e(r["verified"])}</span>' if r.get("verified") else ""
        items.append(f'<li>{badge(r["verdict"])} <b><time datetime="{e(r["date"])}">{e(dt)}</time></b> · '
                     f'<a href="{e(r["url"])}" target="_blank" rel="noopener">{e(r["title"])}</a> '
                     f'<span class="muted">({e(r["source"])})</span><br><span class="small">{q}{note}{ver}</span></li>')

    # Reports from other platforms (e.g. PS4): shown for context, never counted toward the PS5 status.
    side = []
    for r in m.get("side_notes", []):
        q = f'“{e(r["quote"])}”' if r.get("quote") else ""
        note = f' <span class="muted">{e(r["note"])}</span>' if r.get("note") else ""
        ver = f' <span class="vtag">✓ {e(r["verified"])}</span>' if r.get("verified") else ""
        side.append(f'<li>{badge(r["verdict"])} <b>{e(r.get("platform", ""))}</b> · <b><time datetime="{e(r["date"])}">{e(r["date"])}</time></b> · '
                    f'<a href="{e(r["url"])}" target="_blank" rel="noopener">{e(r["title"])}</a> '
                    f'<span class="muted">({e(r["source"])})</span><br><span class="small">{q}{note}{ver}</span></li>')
    side_html = ('<h3 style="font-size:16px">Other platforms (not counted for PS5)</h3>'
                 f'<ul class="reports">{"".join(side)}</ul>') if side else ""

    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", m["summary"]) if s.strip()]
    # Pull load-order / master-file sentences into a callout, unless that would
    # just repeat a one-sentence summary shown right above it.
    tips = [s for s in sents if TIP_RE.search(s)] if len(sents) > 1 else []
    tips += [r["note"] for r in reps if r.get("note") and TIP_RE.search(r["note"])]
    tip_html = ""
    if tips:
        tip_html = ('<div class="patch"><b>Load order / required files:</b> ' +
                    " ".join(e(t) for t in dict.fromkeys(tips)) + "</div>")

    answer_text = (f"{short} Status: {LABEL[st]} ({MEANING[st]}) {m['summary']} "
                   f"Based on {plural(n, 'dated player report')}; last checked {checked}.")
    jsonld = ld({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "FAQPage", "mainEntity": [{
                "@type": "Question", "name": f"Is {name} safe on PS5?",
                "acceptedAnswer": {"@type": "Answer", "text": answer_text}}]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Is It Bricked?", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Mods", "item": SITE + "/mods/"},
                {"@type": "ListItem", "position": 3, "name": name, "item": url}]},
        ]})

    body = f"""<main>
<p class="small muted"><a href="/">Tracker</a> › <a href="/mods/">Mods</a> › {e(name)}</p>
<div class="card">
<h1 style="margin-top:0">Is {e(name)} safe on PS5?</h1>
<p style="font-size:17px"><b>Short answer:</b> {badge(st)} {e(short)}</p>
<p class="small muted">Last checked <time datetime="{e(checked)}">{e(checked)}</time> · Based on {plural(n, 'dated player report')}{f' ({e(count_txt)})' if n else ''}{f', latest {e(latest)}' if latest else ''} · Current game patch: {e(patch['label'])} ({e(patch['date'])}, <a href="{e(patch['url'])}">notes</a>) · Category: {e(m['category'])}</p>
<p>{e(m['summary'])}</p>
<p class="small muted"><b>{e(LABEL[st])}</b> means: {e(MEANING[st])}</p>
{tip_html}
<h2 style="font-size:19px">Player reports ({n})</h2>
<ul class="reports">{''.join(items)}</ul>{side_html}
<p class="small muted">We don't test mods ourselves. Each report links to the original post so you can read it and decide. <a href="/about.html">How statuses work</a>.</p>
<p><a class="btn" href="/report.html?mod={e(_q(name))}">Report this mod</a> <a href="{e(m['creations_url'])}" style="margin-left:12px">Find it on Bethesda Creations (PlayStation)</a></p>
</div>
<div class="card" style="margin-top:16px"><h3 style="margin-top:0">Get the weekly "what broke" email</h3>
<p class="small muted">What broke and what got fixed for PS5 Skyrim mods, once a week. Free, unsubscribe anytime.</p>
<p><a class="btn" href="/#newsletter">Sign up for the newsletter</a></p></div>
<p class="small"><a href="/mods/">All {len(d['mods'])} tracked mods</a> · <a href="/">Back to the tracker</a></p>
</main>
"""
    page = head(title, desc, url, "\n" + jsonld) + body + FOOT
    return page, title


def _q(s):
    from urllib.parse import quote
    return quote(s, safe="")


ORDER = {"bricks": 0, "crashes": 1, "mixed": 2, "unknown": 3, "fixed": 4, "works": 5}


def mod_list_html(d):
    ms = sorted(d["mods"], key=lambda m: (ORDER.get(m["status"], 9), m["name"].lower()))
    return "<ul class=\"modlist\">" + "".join(
        f'<li><a href="/mods/{e(m["id"])}/">Is {e(m["name"])} safe on PS5?</a> {badge(m["status"])}</li>'
        for m in ms) + "</ul>"


def main():
    d = json.load(open(os.path.join(ROOT, "data", "mods.json"), encoding="utf-8"))
    ids = [m["id"] for m in d["mods"]]
    assert len(ids) == len(set(ids)), "duplicate mod ids"
    for i in ids:
        assert re.fullmatch(r"[a-z0-9-]+", i), f"bad id {i}"
    out = os.path.join(ROOT, "mods")
    if os.path.isdir(out):
        shutil.rmtree(out)  # drop pages for mods removed from mods.json
    os.makedirs(out)
    for m in d["mods"]:
        page, _ = mod_page(m, d)
        os.makedirs(os.path.join(out, m["id"]))
        open(os.path.join(out, m["id"], "index.html"), "w", encoding="utf-8").write(page)

    lst_url = SITE + "/mods/"
    lst = head("Which Skyrim mods are safe on PS5? All tracked mods | Is It Bricked?",
               f"Status of {len(d['mods'])} PS5 Skyrim mods after patch {d['current_patch']['label']}: which ones brick, crash, or work, each backed by dated player reports.",
               lst_url) + f"""<main><div class="card"><h1 style="margin-top:0">Which Skyrim mods are safe on PS5?</h1>
<p class="muted">{len(d['mods'])} mods tracked · Current patch {e(d['current_patch']['label'])} · Last checked {e(d['generated'])}. Each page links to the dated player reports behind its status.</p>
{mod_list_html(d)}</div></main>
""" + FOOT
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(lst)

    # Homepage static list (crawlable links even without JS).
    ip = os.path.join(ROOT, "index.html")
    idx = open(ip, encoding="utf-8").read()
    new = re.sub(r"<!--MODLIST:START-->.*?<!--MODLIST:END-->",
                 "<!--MODLIST:START-->" + mod_list_html(d) + "<!--MODLIST:END-->", idx, flags=re.S)
    if new == idx and "<!--MODLIST:START-->" not in idx:
        print("warning: MODLIST markers missing from index.html", file=sys.stderr)
    tok = open(GSC_TOKEN_FILE).read().strip() if os.path.exists(GSC_TOKEN_FILE) else ""
    if tok:  # Search Console checks the homepage for this tag.
        tag = f'<meta name="google-site-verification" content="{e(tok)}">'
        new = re.sub(r'<meta name="google-site-verification"[^>]*>\n?', "", new)
        new = new.replace('<link rel="canonical"', tag + "\n<link rel=\"canonical\"", 1)
    open(ip, "w", encoding="utf-8").write(new)

    lastmod = d["generated"]
    urls = [SITE + "/", SITE + "/mods/", SITE + "/about.html", SITE + "/report.html"] + \
           [f"{SITE}/mods/{i}/" for i in ids]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"  <url><loc>{u}</loc><lastmod>{lastmod}</lastmod></url>" for u in urls]
    sm.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(sm) + "\n")
    open(os.path.join(ROOT, "robots.txt"), "w").write(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    print(f"built {len(ids)} mod pages, sitemap with {len(urls)} URLs")


if __name__ == "__main__":
    main()
