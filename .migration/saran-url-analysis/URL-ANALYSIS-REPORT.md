# URL Analysis Report — Asahi Kasei "Saran" Site

**Site crawled:** https://www.asahi-kasei.co.jp/saran/
**Date:** 2026-09-01 (structural analysis added 2026-09-02)
**Discovery method:** Full site crawl (no sitemap available) + DOM structural analysis of all 391 live pages

> **Full-site analysis findings** (measured across all 391 live pages, not a sample):
> - External recipe platform (ahp-recipe.jp) is linked from **236 pages (60%)** — incl. 142 preservation pages, far beyond the recipe section (sitewide dependency).
> - **Google Tag Manager on 373 pages (95%)** delivers analytics, cookie-consent and Google Custom Search at runtime (hence they appear in static markup on only ~9 pages).
> - **YouTube embedded 77 times across 24 pages**, concentrated in B2B and product sections.
> - Card grid 257 (65%), breadcrumb 370 (94%), tab-nav 143 (36%), news list 56 (14%), hero slider 44 (11%), data table 41 (10%), accordion 23 (6%).
> - Only **2 real HTML `<form>` tags** sitewide; no enterprise REST/SOAP, payment, CRM or auth integration. Per-page matrix: `page-features.json`.
**Scope:** `/saran/` section of asahi-kasei.co.jp (Asahi Kasei Home Products — サランラップ®/ジップロック®/クックパー® brand site)

---

## 1. Summary

| Metric | Count |
|---|---|
| Total HTML pages discovered | **434** |
| Total documents (PDF) | **32** |
| Total URLs crawled | 466 |
| URL groups (templates) | 43 |
| Language | Japanese (single locale) |

**Status breakdown (HTML pages):**

| Status | Count | Meaning |
|---|---|---|
| 200 OK | 391 | Live pages |
| 404 Not Found | 42 | Broken/removed links |
| 403 Forbidden | 1 | Access restricted |
| Documents (PDF) 200 | 30 | Live PDFs |
| Documents (PDF) 404 | 2 | Broken PDF links |

No sitemap.xml or robots.txt sitemap reference exists on the domain, so the site was fully crawled from the `/saran/` entry point.

---

## 2. Site structure by section

The site divides into a consumer-facing brand site (shared header/footer) and a separately-templated B2B (業務用/business) sub-site.

| Section | Pages | Description |
|---|---:|---|
| `/preservation/` — 保存テクニック | 160 | Food-preservation techniques, organized by food type (vegetables, fruits, fish, meat, grain, dairy, beans, dry food, dishes, baby food) |
| `/products/` — 商品紹介 | 134 | Product pages for each brand + a large `/products/business/` (B2B) sub-site |
| `/recipe/` — レシピライブラリ | 87 | Recipe library, world cuisine, kitchen ideas |
| `/corporate_info/` — 会社情報 | 9 | Company profile, employee interviews, news releases |
| `/sustainability/` — サステナビリティ | 9 | Sustainability / SDGs initiatives |
| `/customer/` — お問い合わせ | 6 | Contact, FAQ, discontinued products |
| `/global/` | 9 | Global/English brand landing pages |
| `/cm/` — CM・動画 | 3 | TV commercials and videos |
| `/bb-form/` | 3 | Contact form entry pages (q142/q143/q144) |
| Misc | ~5 | sitemap, about_us, cookie, recycle |
| External asahi-kasei paths | 9 | `/jp/*` corporate privacy/contact pages (mostly 404 from this section) |

---

## 3. Page templates (URL groups)

The 434 pages fall into ~43 directory-based groups. The largest and most representative templates:

| Group | Pages | Confidence | Template type |
|---|---:|---|---|
| `/saran/recipe/idea_cooking` | 49 | 95% | Kitchen-idea article pages |
| `/saran/preservation/vegetables` | 48 | 95% | Food detail (preservation how-to) |
| `/saran/recipe/world` | 35 | 95% | World-cuisine recipe pages |
| `/saran/products/business/cookper` | 32 | 85% | B2B product/content pages |
| `/saran/preservation/baby` | 21 | 95% | Baby-food freezing pages |
| `/saran/preservation/dish` | 19 | 95% | Prepared-dish preservation |
| `/saran/products/business/lineup` | 16 | 85% | B2B product lineup |
| `/saran/preservation/fruits` | 15 | 95% | Fruit preservation detail |
| `/saran` (top/section indexes) | 15 | 85% | Landing/index pages |
| `/saran/products/ziploc` | 13 | 95% | Ziploc product pages |
| `/saran/products/cookper` | 12 | 95% | Cookper product pages |
| `/saran/preservation` (+ fish, grain, meat, dry_food, dairy, beans, other) | ~50 | 90–95% | Food-category detail pages |
| `/saran/products/business/*` (saranwrap, ziploc, greasetrap, case, images) | ~30 | 85–95% | B2B sub-site |
| `/saran/products/frosch`, `zubizuba`, `gift_novelty`, `saranwrap` | ~16 | 90% | Consumer product pages |
| `/saran/corporate_info/interview` | 6 | 95% | Employee interview pages |
| `/saran/sustainability` | 8 | 95% | Sustainability report pages |

Distinct page templates identified for screenshots (see §5):
1. **Home** — carousel hero + section blocks (preservation, recipe, products, topics, CM, news)
2. **Section index** (products / preservation / recipe) — card grids with left/right nav rails
3. **Content detail** (preservation food page) — article body + product cross-sell + related grid
4. **Product detail** (saranwrap) — feature callouts, product lineup, video blocks
5. **Sustainability** — full-width editorial with scroll-reveal animation
6. **Corporate info** — mission statement, news list, company profile table
7. **Customer/contact** — FAQ cards + contact blocks + AI chatbot iframe
8. **Business (B2B)** — completely separate template with its own header/footer/nav

---

## 4. Issues found (broken links)

**42 pages return 404** — the two largest clusters are clearly stale link patterns:

- **`/saran/products/business/cookper/vol01.html` … `vol24.html`** (24 pages) — an entire numbered series of "シェフの目線" (Chef's viewpoint) newsletter volumes is linked but returns 404. These have likely been relocated (the live section is at `/products/business/cookper/getsuyo/`).
- **`/saran/customer/contact/{products,catalog,novelty}.html`** (3) — old contact sub-pages, now replaced by the `/bb-form/` forms.
- **`/saran/products/ziploc/{standing_bag,stock_bag,machi_zipper}.html`** and **`/products/zubizuba/grill.html`** (4) — discontinued-product pages still linked.
- **`/saran/bb-form/q142`, `q143`, `q144`** — reported 404 without trailing slash; the working URLs use a trailing slash (`/bb-form/q144/`).
- **`/jp/privacy`, `/jp/security`, `/jp/cookie`, `/jp/social-media`, `/jp/contact-us*`, `/jp/fragments/*`** (7) — links to the parent corporate site's `/jp/` paths that 404 (the live privacy policy is now at `asahi-kasei.com/jp/privacy/`).
- **1× 403:** `/saran/products/frosch/item/dw_baby` — access restricted.
- **2× PDF 404:** `/content/dam/asahi-kasei/jp/ja/privacy/pdf/affiliates.pdf` and `.../inquiry.pdf`.

**Recommendation:** the `cookper/volXX.html` series (24 links) and the `/jp/*` corporate links are the highest-value fixes — either restore the targets or update the linking pages.

---

## 5. Screenshots captured

Full-page desktop screenshots (1440px wide) of one representative page per template, saved in `screenshots/`:

| File | Page | Template |
|---|---|---|
| `saran-01-homepage.png` | `/saran/` | Home |
| `saran-02-products.png` | `/saran/products/` | Section index (card grid) |
| `saran-03-preservation.png` | `/saran/preservation/` | Section index (food tabs) |
| `saran-04-recipe.png` | `/saran/recipe/` | Recipe library + search |
| `saran-05-sustainability.png` | `/saran/sustainability/` | Editorial / SDGs |
| `saran-06-product-detail-saranwrap.png` | `/saran/products/saranwrap/` | Product detail |
| `saran-07-preservation-detail.png` | `/saran/preservation/vegetables/food01.html` | Content detail article |
| `saran-08-corporate-info.png` | `/saran/corporate_info/` | Company profile + news |
| `saran-09-business.png` | `/saran/products/business/` | B2B sub-site (distinct template) |
| `saran-10-customer.png` | `/saran/customer/` | Contact / FAQ |

*Note: the cookie-consent banner was dismissed before each capture. The sustainability page uses scroll-triggered reveal animations, so some sections appear blank in a static full-page capture.*

---

## 6. Output files

All artifacts are in this folder:

- `urls-all.json` — all 434 pages + 32 documents with HTTP status
- `urls-grouped.json` — pages grouped into 43 directory templates with confidence scores
- `urls-sample.json` — representative sample for downstream analysis
- `screenshots/` — 10 full-page screenshots
- `URL-ANALYSIS-REPORT.md` — this report
