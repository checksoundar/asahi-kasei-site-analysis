#!/usr/bin/env python3
"""Build the Saran URL Analysis Report as a native .docx (OOXML, stdlib only)."""
import os, zipfile, html, struct

BASE = os.path.dirname(os.path.abspath(__file__))
IMGDIR = os.path.join(BASE, "screenshots", "cropped")
EMU_PER_IN = 914400
CONTENT_W_IN = 6.3
DXA = lambda inch: int(inch * 1440)

def esc(s): return html.escape(str(s), quote=True)

def png_size(fn):
    with open(fn, "rb") as f: head = f.read(24)
    w, h = struct.unpack(">II", head[16:24]); return w, h

body = []          # document body XML fragments
rels = []          # document relationships
media = []         # (arcname, filepath)
_img_i = [0]

def para(text="", style=None, bold=False, size=None, color=None, space_after=120):
    ppr = ["<w:spacing w:after=\"%d\"/>" % space_after]
    if style: ppr.append(f'<w:pStyle w:val="{style}"/>')
    rpr = []
    if bold: rpr.append("<w:b/>")
    if size: rpr.append(f'<w:sz w:val="{size*2}"/>')
    if color: rpr.append(f'<w:color w:val="{color}"/>')
    rpr_xml = f"<w:rPr>{''.join(rpr)}</w:rPr>" if rpr else ""
    body.append(f'<w:p><w:pPr>{"".join(ppr)}</w:pPr>'
                f'<w:r>{rpr_xml}<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

def heading(text, lvl=1):
    sz = {1: 30, 2: 24, 3: 18}[lvl]
    col = {1: "1F3864", 2: "2E6C80", 3: "44546A"}[lvl]
    body.append(f'<w:p><w:pPr><w:spacing w:before="240" w:after="120"/>'
                f'<w:outlineLvl w:val="{lvl-1}"/></w:pPr>'
                f'<w:r><w:rPr><w:b/><w:sz w:val="{sz*2}"/><w:color w:val="{col}"/></w:rPr>'
                f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

def table(headers, rows, widths):
    tot = DXA(CONTENT_W_IN)
    cw = [int(tot * w) for w in widths]
    grid = "".join(f'<w:gridCol w:w="{c}"/>' for c in cw)
    def cell(txt, w, hdr=False):
        shd = '<w:shd w:val="clear" w:fill="2E6C80"/>' if hdr else ""
        rpr = "<w:rPr><w:b/><w:color w:val=\"FFFFFF\"/><w:sz w:val=\"18\"/></w:rPr>" if hdr else "<w:rPr><w:sz w:val=\"18\"/></w:rPr>"
        # allow line breaks on "\n"
        parts = str(txt).split("\n")
        runs = ('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, esc(parts[0])))
        for extra in parts[1:]:
            runs += '<w:r>%s<w:br/><w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, esc(extra))
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shd}'
                f'<w:tcMar><w:top w:w="40" w:type="dxa"/><w:bottom w:w="40" w:type="dxa"/>'
                f'<w:left w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tcMar></w:tcPr>'
                f'<w:p><w:pPr><w:spacing w:after="0"/></w:pPr>{runs}</w:p></w:tc>')
    out = [f'<w:tbl><w:tblPr><w:tblW w:w="{tot}" w:type="dxa"/>'
           '<w:tblBorders>'
           + "".join(f'<w:{s} w:val="single" w:sz="4" w:color="BFBFBF"/>' for s in
                     ["top","left","bottom","right","insideH","insideV"])
           + '</w:tblBorders></w:tblPr>'
           f'<w:tblGrid>{grid}</w:tblGrid>']
    out.append("<w:tr><w:trPr><w:tblHeader/></w:trPr>" + "".join(cell(h, cw[i], True) for i, h in enumerate(headers)) + "</w:tr>")
    for row in rows:
        out.append("<w:tr>" + "".join(cell(v, cw[i]) for i, v in enumerate(row)) + "</w:tr>")
    out.append("</w:tbl>")
    body.append("".join(out))
    body.append('<w:p><w:pPr><w:spacing w:after="60"/></w:pPr></w:p>')

def image(fn, caption=None, width_in=CONTENT_W_IN):
    path = os.path.join(IMGDIR, fn)
    w, h = png_size(path)
    ew = int(width_in * EMU_PER_IN)
    eh = int(ew * h / w)
    _img_i[0] += 1
    idx = _img_i[0]
    rid = f"rIdImg{idx}"
    arc = f"media/{fn}"
    rels.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{arc}"/>')
    media.append((f"word/{arc}", path))
    body.append(
        '<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:after="40"/></w:pPr><w:r><w:drawing>'
        f'<wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{ew}" cy="{eh}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="{idx}" name="Picture {idx}"/>'
        '<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:nvPicPr><pic:cNvPr id="{idx}" name="{esc(fn)}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{ew}" cy="{eh}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')
    if caption:
        body.append(f'<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:after="200"/></w:pPr>'
                    f'<w:r><w:rPr><w:i/><w:sz w:val="16"/><w:color w:val="595959"/></w:rPr>'
                    f'<w:t xml:space="preserve">{esc(caption)}</w:t></w:r></w:p>')

def pagebreak():
    body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')

# ============================= CONTENT =============================
BASEURL = "https://www.asahi-kasei.co.jp"

# ---- Title ----
body.append('<w:p><w:pPr><w:spacing w:before="600" w:after="120"/><w:jc w:val="center"/></w:pPr>'
            '<w:r><w:rPr><w:b/><w:sz w:val="56"/><w:color w:val="1F3864"/></w:rPr>'
            '<w:t>URL Analysis Report</w:t></w:r></w:p>')
body.append('<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:after="80"/></w:pPr>'
            '<w:r><w:rPr><w:sz w:val="30"/><w:color w:val="2E6C80"/></w:rPr>'
            '<w:t>Asahi Kasei Home Products — "Saran" Site</w:t></w:r></w:p>')
body.append('<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:after="40"/></w:pPr>'
            '<w:r><w:rPr><w:sz w:val="20"/></w:rPr>'
            '<w:t>https://www.asahi-kasei.co.jp/saran/</w:t></w:r></w:p>')
body.append('<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:after="40"/></w:pPr>'
            '<w:r><w:rPr><w:sz w:val="20"/><w:color w:val="595959"/></w:rPr>'
            '<w:t>Prepared: 2026-09-01  |  Method: full-site crawl + structural analysis of all 391 live pages  |  434 pages, 32 PDFs</w:t></w:r></w:p>')

para("")
heading("Executive Summary", 2)
para("The Saran site is a Japanese-language consumer brand site for Asahi Kasei Home Products "
     "(Saran Wrap®, Ziploc®, Cookper®, Frosch®, etc.). A full crawl discovered 434 HTML pages "
     "and 32 PDF documents across ~13 template types. Every one of the 391 live (HTTP 200) pages "
     "was fetched and its DOM structurally analyzed — block markup, embeds and integration "
     "signatures — so the block, integration and complexity findings below are measured across the "
     "whole site, not inferred from a sample.")
para("The site is largely template-driven and content-heavy: two clusters — Preservation "
     "food-detail pages (159) and Recipe/kitchen-idea pages (86) — account for over half of all "
     "pages and are highly standardized, making them strong candidates for automated migration. A "
     "structurally separate B2B (業務用) sub-site (83 pages) carries its own header, footer and "
     "navigation and must be treated as a distinct template. Full-site analysis revealed three "
     "findings not visible in a sample: (1) the external recipe platform (ahp-recipe.jp) is linked "
     "from 236 pages / 60% — including 142 preservation pages, far beyond the recipe section; "
     "(2) Google Tag Manager loads on 373 pages / 95% and is the runtime delivery mechanism for "
     "analytics, the cookie-consent manager and Google Custom Search (which is why those appear in "
     "static markup on only ~9 pages); and (3) YouTube is embedded 77 times across 24 pages, "
     "concentrated in the B2B and product sections.")

pagebreak()
# ================= 1. TEMPLATES INVENTORY =================
heading("1. Templates Inventory", 1)
para("Unique page templates across the site, with complexity and absolute reference URLs. "
     "Templates and page counts were derived from all 434 crawled URLs; block, integration and "
     "complexity findings (sections 2, 4, 5) were measured by fetching and structurally analyzing "
     "every one of the 391 live pages.", size=9, color="595959")
table(
    ["Template", "Complexity", "Reasoning", "Reference URL(s)"],
    [
        ["Homepage", "Complex",
         "Autoplay hero carousel (9 slides), 7+ distinct content sections, news/information feeds — bespoke one-off layout.",
         f"{BASEURL}/saran/"],
        ["Section landing / index", "Medium",
         "Card-grid landing with left/right nav rails and breadcrumb; a few near-identical instances per section.",
         f"{BASEURL}/saran/products/\n{BASEURL}/saran/preservation/\n{BASEURL}/saran/recipe/"],
        ["Preservation food detail", "Simple",
         "Highly standardized article: intro, cold/freeze how-to, related recipes, product cross-sell, related-food grid. 159 near-identical pages.",
         f"{BASEURL}/saran/preservation/vegetables/food01.html"],
        ["Recipe / kitchen-idea content", "Medium",
         "Editorial content pages; many link out to external recipe platform; filter form on the index.",
         f"{BASEURL}/saran/recipe/idea_cooking/cooking03.html\n{BASEURL}/saran/recipe/world/"],
        ["Product brand page", "Medium",
         "Feature callouts, spec/stat blocks, product lineup with store links, video block. Varies per brand.",
         f"{BASEURL}/saran/products/saranwrap/\n{BASEURL}/saran/products/ziploc/"],
        ["B2B business sub-site", "Complex",
         "Separate template with its own header/footer/nav, product slider, news table and multiple YouTube embeds. 83 pages.",
         f"{BASEURL}/saran/products/business/"],
        ["Editorial / sustainability", "Complex",
         "Full-width editorial with scroll-reveal animations and SDGs icon system; custom layout.",
         f"{BASEURL}/saran/sustainability/"],
        ["Corporate info", "Medium",
         "Mission banner, news-release list (dl/dt/dd) and a company-profile data table.",
         f"{BASEURL}/saran/corporate_info/"],
        ["Contact / FAQ", "Complex",
         "FAQ card grid, multiple contact blocks and an embedded AI chatbot iframe (dynamic/session).",
         f"{BASEURL}/saran/customer/"],
        ["Contact form", "Complex",
         "Multi-step inquiry forms (q142/q143/q144) — form logic and validation.",
         f"{BASEURL}/saran/bb-form/q144/"],
        ["CM / video", "Simple",
         "Grid of YouTube video embeds with minimal surrounding content.",
         f"{BASEURL}/saran/cm/"],
        ["Global landing", "Simple",
         "Small set of English/global brand landing pages.",
         f"{BASEURL}/saran/global/"],
        ["Utility (sitemap/about/cookie)", "Simple",
         "Static single-purpose pages.",
         f"{BASEURL}/saran/sitemap.html\n{BASEURL}/saran/about_us.html"],
    ],
    [0.17, 0.10, 0.40, 0.33],
)

pagebreak()
# ================= 2. BLOCKS / COMPONENTS =================
heading("2. Blocks / Components Catalog", 1)
para("Reusable blocks derived from shared DOM structure. Where the content model is the same but "
     "the visual layout differs, these are noted as design variations of one block rather than new "
     "blocks. The 'Pages' column is the measured count across all 391 live pages (structural DOM "
     "match); percentages are of live pages.", size=9, color="595959")
table(
    ["Block / Component", "Complexity", "Pages", "Behaviour & functionality", "Reference URL(s)"],
    [
        ["Global header + mega-menu nav (consumer)", "Complex", "~330",
         "Sticky header with multi-level dropdown menus (products, preservation, recipe, contact) each exposing sub-lists on hover.",
         "All consumer /saran/* pages"],
        ["Global footer", "Medium", "~330",
         "Brand-logo row, multi-column sitemap, legal links, group link, copyright.",
         "All consumer /saran/* pages"],
        ["Breadcrumb", "Simple", "370 (94%)",
         "Home > Section > Page trail.",
         "Nearly all /saran/* pages"],
        ["Card grid (link cards)", "Medium", "257 (65%)",
         "Responsive grid of image+label link cards. Design variations: product grid, recipe grid, food-thumbnail grid, kitchen-idea grid.",
         f"{BASEURL}/saran/products/\n{BASEURL}/saran/preservation/"],
        ["Food-category / content tab navigation", "Medium", "143 (36%)",
         "Tabbed anchors (野菜/果物/魚介…) switching category panels; also used on product/B2B pages.",
         f"{BASEURL}/saran/preservation/"],
        ["News / information list", "Simple", "56 (14%)",
         "Date-titled definition list (dt/dd), often linking to PDFs. Variations: INFORMATION & NEWS on home; news-release list on corporate.",
         f"{BASEURL}/saran/\n{BASEURL}/saran/corporate_info/"],
        ["Hero carousel / slider", "Complex", "44 (11%)",
         "Autoplay tabbed slider with prev/next and pause. Variations: 9 slides (home), 3 (product), 4 (B2B), global landings.",
         f"{BASEURL}/saran/\n{BASEURL}/saran/products/business/"],
        ["Data table", "Simple", "41 (10%)",
         "Static key/value or spec tables. Variations: company profile, B2B product specs.",
         f"{BASEURL}/saran/corporate_info/"],
        ["Video embed (YouTube)", "Medium", "24 (6%); 77 embeds",
         "Embedded YouTube players in card layouts. Variations: consumer CM grid, B2B how-to grid, product page.",
         f"{BASEURL}/saran/cm/\n{BASEURL}/saran/products/business/"],
        ["Accordion / toggle", "Medium", "23 (6%)",
         "Expand/collapse sections (FAQ-style and content toggles).",
         f"{BASEURL}/saran/customer/\n{BASEURL}/saran/products/business/"],
        ["Product lineup + online-store CTA", "Medium", "~45",
         "Product pack images with Amazon / LOHACO / Rakuten purchase links per SKU (retail links on 18–13 pages).",
         f"{BASEURL}/saran/products/saranwrap/\n{BASEURL}/saran/preservation/vegetables/food01.html"],
        ["Product feature-callout block", "Medium", "~30",
         "Image + heading + copy feature rows (密着性, ハリ・コシ, M字型の刃 …).",
         f"{BASEURL}/saran/products/saranwrap/"],
        ["Stat / metric block", "Medium", "~15",
         "Numeric performance figures with footnotes (透湿度 ~2.0x, 酸素 ~200x …).",
         f"{BASEURL}/saran/products/saranwrap/"],
        ["Retailer / SNS strip", "Simple", "~30",
         "Row of store-locator + Amazon + LOHACO + Rakuten24 banners near the footer.",
         "Product & preservation pages"],
        ["Social-share buttons", "Simple", "10 (3%)",
         "Facebook / X / LINE share on content detail pages.",
         f"{BASEURL}/saran/preservation/vegetables/food01.html"],
        ["Scroll-reveal animation wrapper", "Complex", "10 (3%)",
         "Content revealed on scroll (sustainability editorial + some product pages).",
         f"{BASEURL}/saran/sustainability/"],
        ["FAQ card grid", "Medium", "~6",
         "Per-brand FAQ entry cards linking to the external FAQ system.",
         f"{BASEURL}/saran/customer/"],
        ["Contact-info block", "Simple", "~10",
         "Phone/mail contact panels with hours and mail-form links.",
         f"{BASEURL}/saran/customer/\n{BASEURL}/saran/products/business/"],
        ["Recipe search / filter form", "Complex", "1 (+ index)",
         "Keyword box + 7 filtered dropdowns with reset/search; posts to external recipe platform. Only 2 real <form> tags exist sitewide.",
         f"{BASEURL}/saran/recipe/"],
        ["AI chatbot embed", "Complex", "4",
         "Iframe chat widget with product buttons and free-text search (dynamic/session).",
         f"{BASEURL}/saran/customer/"],
        ["Cookie-consent banner (GTM-injected)", "Complex", "Sitewide (runtime)",
         "Iframe overlay with Accept/Reject/Settings. Injected at runtime via GTM (static markup on ~9 pages).",
         "All pages (first visit)"],
        ["Google Custom Search box (GTM-injected)", "Medium", "Sitewide (runtime)",
         "Site search powered by Google CSE (adds #gsc.tab fragment); loaded via GTM.",
         "All consumer pages (header)"],
        ["B2B header/footer/nav", "Complex", "58 live",
         "Distinct navigation, contact footer with tel links and catalog download — separate design system.",
         f"{BASEURL}/saran/products/business/"],
    ],
    [0.22, 0.09, 0.11, 0.33, 0.25],
)

pagebreak()
para("Representative template screenshots (above-the-fold). Full-length captures are in the "
     "screenshots/ folder.", size=9, color="595959")
shots = [
    ("saran-01-homepage.png", "Homepage — hero carousel + section blocks"),
    ("saran-02-products.png", "Product section index — card grid"),
    ("saran-03-preservation.png", "Preservation index — food-category tabs + grid"),
    ("saran-04-recipe.png", "Recipe library — filter form + card grids"),
    ("saran-06-product-detail-saranwrap.png", "Product detail — feature callouts + lineup"),
    ("saran-07-preservation-detail.png", "Preservation food detail — article + cross-sell"),
    ("saran-08-corporate-info.png", "Corporate info — news list + profile table"),
    ("saran-10-customer.png", "Contact / FAQ — FAQ cards + chatbot + contact blocks"),
    ("saran-05-sustainability.png", "Sustainability — editorial / SDGs"),
    ("saran-09-business.png", "B2B business sub-site — distinct template"),
]
for fn, cap in shots:
    image(fn, cap)

pagebreak()
# ================= 3. PAGE COUNTS BY TEMPLATE =================
heading("3. Page Counts by Template", 1)
para("Page volume per template and migration approach (Auto = standardized/low-logic; "
     "Manual = dynamic/custom/heavy-logic).", size=9, color="595959")
table(
    ["Template", "Pages", "Live (200)", "Migration approach"],
    [
        ["Preservation food detail", "159", "159", "Automatic — uniform structure, standardized data"],
        ["Recipe / kitchen-idea content", "86", "86", "Manual/semi — editorial + external recipe links"],
        ["B2B business sub-site", "83", "58", "Manual — separate template & nav, many 404s"],
        ["Product brand page", "50", "45", "Semi — templated but per-brand variation"],
        ["Corporate info", "9", "9", "Semi — list + table are standardized"],
        ["Editorial / sustainability", "9", "9", "Manual — custom layout + animations"],
        ["Global landing", "9", "9", "Semi — small, simple pages"],
        ["Utility (sitemap/about/cookie/recycle)", "7", "7", "Semi — static one-offs"],
        ["Contact / FAQ", "6", "3", "Manual — chatbot + contact logic"],
        ["CM / video", "3", "3", "Semi — video embeds"],
        ["Contact form", "3", "0*", "Manual — form logic (see note)"],
        ["Homepage", "1", "1", "Manual — bespoke one-off"],
        ["External corporate (/jp)", "9", "2", "Exclude — belongs to parent corporate site"],
        ["TOTAL (in-scope /saran)", "425", "—", "≈159 auto / ≈266 semi-manual"],
    ],
    [0.34, 0.10, 0.14, 0.42],
)
para("* The bb-form pages returned 404 when crawled without a trailing slash; the working URLs use "
     "a trailing slash (/saran/bb-form/q144/). They are live interactive forms.", size=9, color="595959")

pagebreak()
# ================= 4. INTEGRATIONS =================
heading("4. Integrations Analysis", 1)
para("Third-party integrations and embedded services, with page counts measured across all 391 "
     "live pages.", size=9, color="595959")
table(
    ["Integration", "Type", "Complexity", "Pages", "Where used / reference"],
    [
        ["Google Tag Manager", "JS tag container", "Medium", "373 (95%)",
         "Sitewide; runtime loader for analytics, consent & search"],
        ["Web analytics (GA via GTM, _ga linker)", "JS tag", "Medium", "373 (95%)",
         "Sitewide; outbound links carry _ga linker params"],
        ["External recipe platform (ahp-recipe.jp)", "API / external app", "Complex", "236 (60%)",
         "Recipe search & detail links; 142 preservation + 83 recipe pages (content_list.php, sheet.php)"],
        ["YouTube video embeds", "Embed (iframe)", "Simple", "24 (77 embeds)",
         f"{BASEURL}/saran/cm/ ; {BASEURL}/saran/products/business/ ; product pages"],
        ["E-commerce retail links (Amazon/LOHACO/Rakuten24)", "Affiliate / deep-link", "Simple", "~18",
         "Product lineup & retailer strip"],
        ["B2B reseller links (Askul/Kaunet/Monotaro/…)", "Deep-link", "Simple", "18",
         f"{BASEURL}/saran/products/business/"],
        ["Cookie-consent manager (GTM-injected iframe)", "Embed / plugin", "Medium", "Sitewide (runtime)",
         "All pages, first visit (ul-banner-main-window iframe)"],
        ["Google Custom Search Engine (GTM-injected)", "Embed / JS", "Medium", "Sitewide (runtime)",
         "Header search on consumer pages (#gsc.tab fragment)"],
        ["Campaign microsites (ahp-web.jp, yomiuri.co.jp)", "External link", "Simple", "8",
         "Product/topic promo tiles"],
        ["AI FAQ chatbot (faq.asahi-kasei.co.jp)", "Embed (iframe)", "Complex", "4",
         f"{BASEURL}/saran/customer/"],
        ["FAQ knowledge base (faq.asahi-kasei.co.jp)", "External app", "Medium", "4+",
         "Per-brand 'よくあるご質問' links on product & customer pages"],
        ["Store locator (asahi-kasei.storelocator.jp)", "External app", "Simple", "~7",
         "Retailer strip (Frosch store search)"],
        ["Social share / X account", "Social link", "Simple", "10",
         "Content-detail share; preservation follow button"],
        ["PDF news releases / catalogs", "Document downloads", "Simple", "32 files",
         "/corporate_info, /assets, /products/business/download"],
    ],
    [0.25, 0.15, 0.11, 0.13, 0.36],
)
para("Measured finding: the external recipe platform is the single most pervasive integration "
     "(236 pages / 60%), reaching well beyond the recipe section into 142 preservation pages via "
     "'related recipe' links. GTM (95%) is the runtime delivery mechanism for analytics, the "
     "cookie-consent manager and Google Custom Search — which is why those appear in static markup "
     "on only ~9 pages. No enterprise REST/SOAP back-office integration (payment, CRM, auth/login) "
     "was observed, and only two real HTML <form> tags exist sitewide; commerce is entirely "
     "outbound deep-links to third-party retailers.", size=9, color="595959")

pagebreak()
# ================= 5. COMPLEX USE CASES =================
heading("5. Complex Use Cases & Observations", 1)
para("Behaviours and edge cases needing special attention during migration, quantified.",
     size=9, color="595959")
table(
    ["Use case / observation", "Instances", "Where found", "Why it's complex"],
    [
        ["Two separate design systems (consumer vs B2B)", "83 B2B pages",
         "/saran/products/business/*",
         "B2B sub-site has its own header/footer/nav/theme — effectively a second site to template."],
        ["Externalized recipe library (site-wide dependency)", "236 pages (60%)",
         "/saran/recipe/* (83) + /saran/preservation/* (142) + cm, ahp-recipe.jp",
         "Recipe data & search live off-site on a dynamic PHP platform; measured on 236 pages — every preservation detail cross-links it, so it is a sitewide dependency, not a recipe-only one."],
        ["GTM-delivered analytics / consent / search", "373 pages (95%)",
         "Sitewide (GTM container)",
         "Analytics, cookie-consent overlay and Google CSE are injected at runtime via GTM, so they are invisible in static HTML and must be reconstituted, not copied from markup."],
        ["Recipe filter form (7 dependent dropdowns)", "1 (high traffic)",
         "/saran/recipe/",
         "Client-side faceted search posting to external system; not static content."],
        ["AI chatbot widget", "4",
         "/saran/customer/ + linked FAQ pages",
         "Dynamic, session-based iframe app; cannot be statically migrated."],
        ["Autoplay hero carousels", "3 variations",
         "home, product detail, B2B",
         "JS sliders with autoplay/pause/tabs; behaviour + timing must be reproduced."],
        ["Scroll-reveal animations", "1 template (9 pages)",
         "/saran/sustainability/*",
         "Content hidden until scroll; affects rendering, capture and accessibility."],
        ["Cookie-consent gating", "Sitewide",
         "All pages, first visit",
         "Regulatory consent manager overlays content and blocks interaction until dismissed."],
        ["Broken cookper newsletter series", "24 pages",
         "/products/business/cookper/vol01–vol24.html",
         "Entire numbered archive 404s; decide restore vs redirect vs drop."],
        ["Broken parent-corporate links", "7 pages",
         "/jp/privacy, /jp/security, /jp/cookie, /jp/contact-us …",
         "Point to parent site paths that 404 (privacy now at asahi-kasei.com/jp/privacy/)."],
        ["Discontinued-product & old-contact links", "7 pages",
         "/products/ziploc/*, /zubizuba/grill, /customer/contact/*",
         "Stale links to removed pages; content decisions required."],
        ["PDF-based news/catalogs", "32 PDFs (2 broken)",
         "/corporate_info, /assets, /products/business/download",
         "Downloads, not pages; must be re-hosted and re-linked."],
        ["Google CSE search dependency", "Sitewide",
         "Header on all consumer pages",
         "Search is delegated to Google CSE; replacement/equivalent needed post-migration."],
        ["Multi-locale seam (global + external /jp)", "18 pages",
         "/saran/global/*, /jp/*",
         "Mix of in-scope global pages and out-of-scope parent-corporate pages complicates scope."],
    ],
    [0.26, 0.12, 0.30, 0.32],
)

para("")
heading("Appendix — Source Files & Method", 2)
para("Method: all 434 URLs were crawled for status and grouping; all 391 live (HTTP 200) pages "
     "were then fetched and their DOM parsed for block markup, embeds and integration signatures "
     "(27 feature detectors). Percentages in sections 2, 4 and 5 are of the 391 live pages.",
     size=9, color="595959")
para("Files: urls-all.json (all 434 pages + 32 PDFs with HTTP status) · urls-grouped.json (43 "
     "directory templates) · page-features.json (per-page structural feature matrix, 391 pages) · "
     "Saran-URL-Analysis-Report.xlsx (8 sheets, incl. Feature Prevalence) · screenshots/ (10 "
     "full-page + cropped). All under .migration/saran-url-analysis/.", size=9, color="595959")

# ============================= PACKAGE =============================
doc = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
       '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
       'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
       'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
       'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
       'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
       '<w:body>' + "".join(body) +
       '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>'
       '<w:pgMar w:top="1080" w:bottom="1080" w:left="1080" w:right="1080" '
       'w:header="720" w:footer="720" w:gutter="0"/></w:sectPr></w:body></w:document>')

CONTENT_TYPES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Default Extension="png" ContentType="image/png"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    '</Types>')

ROOT_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    '</Relationships>')

DOC_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    + "".join(rels) + '</Relationships>')

STYLES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>'
    '<w:sz w:val="21"/></w:rPr></w:rPrDefault></w:docDefaults>'
    '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
    '</w:styles>')

out_path = os.path.join(BASE, "Saran-URL-Analysis-Report.docx")
with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", CONTENT_TYPES)
    z.writestr("_rels/.rels", ROOT_RELS)
    z.writestr("word/document.xml", doc)
    z.writestr("word/_rels/document.xml.rels", DOC_RELS)
    z.writestr("word/styles.xml", STYLES)
    for arc, path in media:
        z.write(path, arc)

print("Wrote", out_path)
print("Body elements:", len(body), "| images:", len(media))
