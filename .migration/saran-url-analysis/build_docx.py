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
            '<w:t>Prepared: 2026-09-01  |  Method: full-site crawl (no sitemap)  |  434 pages, 32 PDFs</w:t></w:r></w:p>')

para("")
heading("Executive Summary", 2)
para("The Saran site is a Japanese-language consumer brand site for Asahi Kasei Home Products "
     "(Saran Wrap®, Ziploc®, Cookper®, Frosch®, etc.). A full crawl discovered 434 HTML pages "
     "and 32 PDF documents across ~13 template types. The site is largely template-driven and "
     "content-heavy: two clusters — Preservation food-detail pages (159) and Recipe/kitchen-idea "
     "pages (86) — account for over half of all pages and are highly standardized, making them "
     "strong candidates for automated migration. A structurally separate B2B (業務用) sub-site "
     "(83 pages) carries its own header, footer and navigation and must be treated as a distinct "
     "template. The recipe library is externalized to a third-party platform (ahp-recipe.jp), and "
     "a Google Custom Search, a cookie-consent manager, an AI FAQ chatbot, YouTube embeds and "
     "multiple retail/store-locator integrations are present.")

pagebreak()
# ================= 1. TEMPLATES INVENTORY =================
heading("1. Templates Inventory", 1)
para("Unique page templates across the site, with complexity and absolute reference URLs.", size=9, color="595959")
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
     "the visual layout differs, these are noted as design variations of one block rather than new blocks.",
     size=9, color="595959")
table(
    ["Block / Component", "Complexity", "Behaviour & functionality", "Reference URL(s)"],
    [
        ["Global header + mega-menu nav (consumer)", "Complex",
         "Sticky header with multi-level dropdown menus (products, preservation, recipe, contact) each exposing sub-lists on hover.",
         "All /saran/* consumer pages"],
        ["Global footer", "Medium",
         "Brand-logo row, multi-column sitemap, legal links, group link, copyright.",
         "All /saran/* consumer pages"],
        ["Hero carousel / slider", "Complex",
         "Autoplay tabbed slider with prev/next and pause control. Design variations: 9 slides (home), 3 slides (product), 4 slides (B2B).",
         f"{BASEURL}/saran/\n{BASEURL}/saran/products/saranwrap/"],
        ["Card grid (link cards)", "Medium",
         "Responsive grid of image+label link cards. Design variations: product grid, recipe grid, food-thumbnail grid, kitchen-idea grid.",
         f"{BASEURL}/saran/products/\n{BASEURL}/saran/preservation/"],
        ["Food-category tab navigation", "Medium",
         "Tabbed anchors (野菜/果物/魚介…) that switch category panels within the preservation index.",
         f"{BASEURL}/saran/preservation/"],
        ["Recipe search / filter form", "Complex",
         "Keyword box + 7 filtered dropdowns (food, theme, genre, keyword, difficulty, time, product) with reset/search; posts to external recipe platform.",
         f"{BASEURL}/saran/recipe/"],
        ["News / information list", "Simple",
         "Date-titled definition list (dt/dd), often linking to PDFs. Design variations: INFORMATION and NEWS on home; news-release list on corporate.",
         f"{BASEURL}/saran/\n{BASEURL}/saran/corporate_info/"],
        ["Company-profile table", "Simple",
         "Static key/value data table (商号, 代表者, 所在地 …).",
         f"{BASEURL}/saran/corporate_info/"],
        ["Product feature-callout block", "Medium",
         "Image + heading + copy feature rows (密着性, ハリ・コシ, M字型の刃 …).",
         f"{BASEURL}/saran/products/saranwrap/"],
        ["Stat / metric block", "Medium",
         "Numeric performance figures with footnotes (透湿度 ~2.0x, 酸素 ~200x …).",
         f"{BASEURL}/saran/products/saranwrap/"],
        ["Product lineup + online-store CTA", "Medium",
         "Product pack images with Amazon / LOHACO / Rakuten purchase links per SKU.",
         f"{BASEURL}/saran/products/saranwrap/\n{BASEURL}/saran/preservation/vegetables/food01.html"],
        ["Retailer / SNS strip", "Simple",
         "Row of store-locator + Amazon + LOHACO + Rakuten24 banners near the footer.",
         "Most consumer pages"],
        ["Breadcrumb", "Simple",
         "Home > Section > Page trail.",
         "Most /saran/* pages"],
        ["Left side-nav rail", "Simple",
         "In-section vertical navigation of sibling pages.",
         f"{BASEURL}/saran/preservation/\n{BASEURL}/saran/products/saranwrap/"],
        ["Video embed (YouTube)", "Medium",
         "Embedded YouTube players in card layouts. Variations: consumer CM grid, B2B how-to grid.",
         f"{BASEURL}/saran/cm/\n{BASEURL}/saran/products/business/"],
        ["FAQ card grid", "Medium",
         "Per-brand FAQ entry cards linking to the external FAQ system.",
         f"{BASEURL}/saran/customer/"],
        ["Contact-info block", "Simple",
         "Phone/mail contact panels with hours and mail-form links.",
         f"{BASEURL}/saran/customer/\n{BASEURL}/saran/products/business/"],
        ["AI chatbot embed", "Complex",
         "Iframe chat widget with product buttons and free-text search (dynamic/session).",
         f"{BASEURL}/saran/customer/"],
        ["Cookie-consent banner", "Complex",
         "Iframe overlay with Accept/Reject/Settings (regulatory consent manager).",
         "All pages (first visit)"],
        ["Google Custom Search box", "Medium",
         "Site search powered by Google CSE (adds #gsc.tab fragment).",
         "All consumer pages (header)"],
        ["Social-share buttons", "Simple",
         "Facebook / X / LINE share on content detail pages.",
         f"{BASEURL}/saran/preservation/vegetables/food01.html"],
        ["B2B header/footer/nav", "Complex",
         "Distinct navigation, contact footer with tel links and catalog download — separate design system.",
         f"{BASEURL}/saran/products/business/"],
    ],
    [0.24, 0.10, 0.40, 0.26],
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
para("Third-party integrations and embedded services detected in page markup and outbound links.",
     size=9, color="595959")
table(
    ["Integration", "Type", "Complexity", "Where used / reference"],
    [
        ["External recipe platform (ahp-recipe.jp)", "API / external app", "Complex",
         "Recipe search & detail links across /saran/recipe/* (content_list.php, sheet.php)"],
        ["Google Custom Search Engine", "Embed / JS", "Medium",
         "Header search on all consumer pages (#gsc.tab fragment)"],
        ["Cookie-consent manager (iframe overlay)", "Embed / plugin", "Medium",
         "All pages, first visit (ul-banner-main-window iframe)"],
        ["AI FAQ chatbot (faq.asahi-kasei.co.jp)", "Embed (iframe)", "Complex",
         f"{BASEURL}/saran/customer/"],
        ["FAQ knowledge base (faq.asahi-kasei.co.jp)", "External app", "Medium",
         "Per-brand 'よくあるご質問' links on product & customer pages"],
        ["YouTube video embeds", "Embed (iframe)", "Simple",
         f"{BASEURL}/saran/cm/ ; {BASEURL}/saran/products/business/"],
        ["Store locator (asahi-kasei.storelocator.jp)", "External app", "Simple",
         "Retailer strip on most consumer pages"],
        ["E-commerce retail links (Amazon/LOHACO/Rakuten24)", "Affiliate / deep-link", "Simple",
         "Product lineup & retailer strip sitewide"],
        ["B2B reseller links (Askul/Kaunet/Monotaro/Tanomail/…)", "Deep-link", "Simple",
         f"{BASEURL}/saran/products/business/"],
        ["X / Twitter official account", "Social link", "Simple",
         "Preservation section follow button"],
        ["Web analytics (GA-style _ga params)", "JS tag", "Medium",
         "Outbound links carry _ga linker params sitewide"],
        ["Campaign microsites (ahp-web.jp, yomiuri.co.jp)", "External link", "Simple",
         "Product/topic promo tiles"],
        ["PDF news releases / catalogs", "Document downloads", "Simple",
         "32 PDFs under /corporate_info, /assets, /products/business/download"],
    ],
    [0.30, 0.16, 0.12, 0.42],
)
para("No enterprise REST/SOAP back-office integration (payment gateway, CRM, auth/login) was "
     "observed. Commerce is handled via outbound deep-links to third-party retailers rather than "
     "an on-site cart/checkout. The recipe platform and FAQ/chatbot are the most integration-heavy "
     "surfaces.", size=9, color="595959")

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
        ["Externalized recipe library", "86 recipe pages + all search",
         "/saran/recipe/*, ahp-recipe.jp",
         "Recipe data & search live off-site on a dynamic PHP platform; on-site pages are thin wrappers/links."],
        ["Recipe filter form (7 dependent dropdowns)", "1 (high traffic)",
         "/saran/recipe/",
         "Client-side faceted search posting to external system; not static content."],
        ["AI chatbot widget", "1",
         "/saran/customer/",
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
heading("Appendix — Source Files", 2)
para("urls-all.json (all 434 pages + 32 PDFs with HTTP status) · urls-grouped.json (43 directory "
     "templates) · urls-sample.json · Saran-URL-Analysis-Report.xlsx (7 sheets) · screenshots/ "
     "(10 full-page + cropped). All under .migration/saran-url-analysis/.", size=9, color="595959")

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
