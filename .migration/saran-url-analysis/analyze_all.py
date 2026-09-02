#!/usr/bin/env python3
"""Fetch all live pages and extract structural/integration features (stdlib only)."""
import json, re, os, urllib.request, ssl, gzip, io
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = os.path.dirname(os.path.abspath(__file__))
urls = [u for u in open(os.path.join(BASE, "live-urls.txt")).read().splitlines() if u.strip()]
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; SiteAnalysis/1.0)",
        "Accept-Encoding": "gzip",
    })
    try:
        with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
            raw = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            return url, raw.decode("utf-8", "replace")
    except Exception as e:
        return url, f"__ERROR__{e}"

# feature detectors: name -> regex (searched in lowercased html)
FEATURES = {
    # blocks / components
    "hero_slider": r'class="[^"]*(slick|swiper|slider|carousel|bx-|mainvisual|keyvisual|kv_)',
    "card_grid": r'class="[^"]*(card|grid|list_|_list|thumb|panel)',
    "tab_nav": r'(#tab-\d|class="[^"]*tab)',
    "breadcrumb": r'(breadcrumb|topicpath|pankuzu|class="[^"]*bread)',
    "side_nav": r'class="[^"]*(sidenav|side_nav|localnav|local_nav|subnav|side-)',
    "accordion": r'(accordion|class="[^"]*acc[_-]|toggle)',
    "news_list": r'(<dl|newslist|news_list|information|newsrelease)',
    "data_table": r'<table',
    "social_share": r'(twitter\.com/intent|facebook\.com/share|line\.me|social[_-]?share|sns)',
    "video_youtube": r'(youtube\.com/embed|youtu\.be|youtube-nocookie)',
    "form_tag": r'<form',
    "retail_amazon": r'amazon\.co\.jp',
    "retail_lohaco": r'lohaco',
    "retail_rakuten": r'rakuten',
    "store_locator": r'storelocator',
    # integrations
    "google_cse": r'(cse\.google|gsc\.tab|customsearch|google.*search)',
    "recipe_platform": r'ahp-recipe\.jp',
    "faq_system": r'faq\.asahi-kasei\.co\.jp',
    "chatbot": r'(chatbot|chat-bot|ai.?chat|sptechbot|karakuri|mob20|obot)',
    "cookie_consent": r'(consent|onetrust|cookie.?consent|usercentrics|ul-banner)',
    "analytics_ga": r'(_ga=|gtag|googletagmanager|analytics\.js|ua-\d|g-[a-z0-9]{6,})',
    "gtm": r'googletagmanager\.com',
    "scroll_animation": r'(aos\b|wow\.js|scrollreveal|inview|data-aos|reveal)',
    "map_embed": r'(google\.com/maps|maps\.google|gmap)',
    "campaign_micro": r'(ahp-web\.jp|yomiuri\.co\.jp)',
    "b2b_reseller": r'(askul|kaunet|monotaro|tanomail|tasucall|packstyle)',
    "iframe": r'<iframe',
}

def analyze(url, htmlsrc):
    if htmlsrc.startswith("__ERROR__"):
        return url, {"__error__": htmlsrc[9:]}
    low = htmlsrc.lower()
    feat = {}
    for name, rx in FEATURES.items():
        if re.search(rx, low):
            feat[name] = len(re.findall(rx, low))
    # structural counts
    feat["_forms"] = low.count("<form")
    feat["_tables"] = low.count("<table")
    feat["_iframes"] = low.count("<iframe")
    feat["_youtube"] = len(re.findall(r"youtube\.com/embed|youtu\.be", low))
    feat["_bytes"] = len(htmlsrc)
    # body class (theme hint)
    m = re.search(r'<body[^>]*class="([^"]*)"', low)
    feat["_bodyclass"] = m.group(1)[:80] if m else ""
    return url, feat

results = {}
with ThreadPoolExecutor(max_workers=12) as ex:
    futs = [ex.submit(fetch, u) for u in urls]
    done = 0
    for f in as_completed(futs):
        url, src = f.result()
        u2, feat = analyze(url, src)
        results[u2] = feat
        done += 1
        if done % 50 == 0:
            print(f"  analyzed {done}/{len(urls)}")

json.dump(results, open(os.path.join(BASE, "page-features.json"), "w"), ensure_ascii=False)
errs = {u: f["__error__"] for u, f in results.items() if "__error__" in f}
print("DONE. pages:", len(results), "errors:", len(errs))
if errs:
    for u, e in list(errs.items())[:10]:
        print("  ERR", u, e)
