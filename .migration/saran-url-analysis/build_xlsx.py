#!/usr/bin/env python3
"""Build a multi-sheet .xlsx report natively (no third-party libs).
An xlsx is a ZIP of XML parts following the SpreadsheetML (OOXML) spec."""
import json, zipfile, html, datetime, os

BASE = os.path.dirname(os.path.abspath(__file__))
urls_all = json.load(open(os.path.join(BASE, "urls-all.json")))["analysis-urls-all"]
grouped = json.load(open(os.path.join(BASE, "urls-grouped.json")))["analysis-urls-grouped"]

# ---------- helpers ----------
def col_letter(n):
    s = ""
    while n >= 0:
        s = chr(n % 26 + 65) + s
        n = n // 26 - 1
    return s

def cell_xml(r, c, value, style=0):
    ref = f"{col_letter(c)}{r}"
    if value is None:
        value = ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{ref}" s="{style}"><v>{value}</v></c>'
    txt = html.escape(str(value), quote=True)
    return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t xml:space="preserve">{txt}</t></is></c>'

def sheet_xml(rows, colwidths=None, header_rows=1):
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>']
    out.append('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">')
    if colwidths:
        out.append('<cols>')
        for i, w in enumerate(colwidths, start=1):
            out.append(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>')
        out.append('</cols>')
    out.append('<sheetData>')
    for ri, row in enumerate(rows, start=1):
        out.append(f'<row r="{ri}">')
        for ci, val in enumerate(row):
            style = 1 if ri <= header_rows else (2 if isinstance(val, (int, float)) and not isinstance(val, bool) else 0)
            out.append(cell_xml(ri, ci, val, style))
        out.append('</row>')
    out.append('</sheetData>')
    # freeze header
    out.insert(3 if colwidths else 2, f'<sheetViews><sheetView workbookViewId="0"><pane ySplit="{header_rows}" topLeftCell="A{header_rows+1}" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>')
    out.append('</worksheet>')
    return "".join(out)

# ---------- build sheet data ----------
# Sheet 1: Summary
sb = urls_all.get("statusBreakdown", {})
summary_rows = [
    ["Asahi Kasei \"Saran\" — URL Analysis Report", ""],
    ["Site", "https://www.asahi-kasei.co.jp/saran/"],
    ["Captured", urls_all.get("captured", "")],
    ["Discovery method", urls_all.get("method", "")],
    ["Confidence", urls_all.get("confidence", "")],
    ["", ""],
    ["Metric", "Count"],
    ["Total HTML pages", urls_all["totalUrls"]],
    ["Total documents (PDF)", urls_all["totalDocuments"]],
    ["URL groups (templates)", grouped["urlGroupings"]],
    ["", ""],
    ["HTTP status", "Count"],
    ["200 OK (success)", sb.get("success", 0)],
    ["3xx Redirect", sb.get("redirect", 0)],
    ["4xx Client error (404/403)", sb.get("clientError", 0)],
    ["5xx Server error", sb.get("serverError", 0)],
    ["Timeout / error", sb.get("errorTimeout", 0)],
]

# Sheet 2: All pages
pages = urls_all["urls"]
page_rows = [["#", "URL", "Path", "HTTP Status", "OK?"]]
for i, u in enumerate(pages, start=1):
    url = u["url"]
    path = url.replace("https://www.asahi-kasei.co.jp", "")
    st = u.get("status", "")
    page_rows.append([i, url, path, st, "Yes" if st == 200 else "No"])

# Sheet 3: Documents
docs = urls_all["documents"]
doc_rows = [["#", "URL", "Type", "HTTP Status", "OK?"]]
for i, d in enumerate(docs, start=1):
    url = d["url"]
    ext = url.rsplit(".", 1)[-1].upper()
    st = d.get("status", "")
    doc_rows.append([i, url, ext, st, "Yes" if st == 200 else "No"])

# Sheet 4: Templates / groups
groups = grouped["groups"]
grp_rows = [["Template (directory group)", "Pages", "Confidence"]]
for name, g in sorted(groups.items(), key=lambda kv: len(kv[1]["urls"]), reverse=True):
    grp_rows.append([name, len(g["urls"]), g["confidence"]])

# Sheet 5: Section breakdown
def section_of(url):
    p = url.replace("https://www.asahi-kasei.co.jp/saran/", "").replace("https://www.asahi-kasei.co.jp/", "EXT/")
    seg = p.split("/")[0].split(".")[0]
    return seg if seg else "(saran root)"
sec_counts = {}
for u in pages:
    s = section_of(u["url"])
    sec_counts[s] = sec_counts.get(s, 0) + 1
sec_rows = [["Section", "Pages"]]
for s, c in sorted(sec_counts.items(), key=lambda kv: kv[1], reverse=True):
    sec_rows.append([s, c])

# Sheet 6: Broken links (non-200)
broken = [u for u in pages if u.get("status") != 200] + [d for d in docs if d.get("status") != 200]
brk_rows = [["#", "URL", "HTTP Status"]]
for i, u in enumerate(broken, start=1):
    brk_rows.append([i, u["url"], u.get("status", "")])

# Sheet 7: Screenshots index
shot_rows = [["File", "Page", "Template"]]
shots = [
    ("saran-01-homepage.png", "/saran/", "Home"),
    ("saran-02-products.png", "/saran/products/", "Section index (card grid)"),
    ("saran-03-preservation.png", "/saran/preservation/", "Section index (food tabs)"),
    ("saran-04-recipe.png", "/saran/recipe/", "Recipe library + search"),
    ("saran-05-sustainability.png", "/saran/sustainability/", "Editorial / SDGs"),
    ("saran-06-product-detail-saranwrap.png", "/saran/products/saranwrap/", "Product detail"),
    ("saran-07-preservation-detail.png", "/saran/preservation/vegetables/food01.html", "Content detail article"),
    ("saran-08-corporate-info.png", "/saran/corporate_info/", "Company profile + news"),
    ("saran-09-business.png", "/saran/products/business/", "B2B sub-site (distinct template)"),
    ("saran-10-customer.png", "/saran/customer/", "Contact / FAQ"),
]
for f, p, t in shots:
    shot_rows.append([f, p, t])

sheets = [
    ("Summary", sheet_xml(summary_rows, [30, 55], header_rows=1)),
    ("All Pages", sheet_xml(page_rows, [5, 70, 45, 12, 7])),
    ("Documents", sheet_xml(doc_rows, [5, 80, 8, 12, 7])),
    ("Templates", sheet_xml(grp_rows, [45, 8, 12])),
    ("Sections", sheet_xml(sec_rows, [22, 8])),
    ("Broken Links", sheet_xml(brk_rows, [5, 70, 12])),
    ("Screenshots", sheet_xml(shot_rows, [42, 48, 34])),
]

# ---------- package OOXML ----------
CONTENT_TYPES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
    '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
    + "".join(f'<Override PartName="/xl/worksheets/sheet{i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(len(sheets)))
    + '</Types>')

ROOT_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
    '</Relationships>')

wb_sheets = "".join(f'<sheet name="{html.escape(n)}" sheetId="{i+1}" r:id="rId{i+1}"/>' for i, (n, _) in enumerate(sheets))
WORKBOOK = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
    f'<sheets>{wb_sheets}</sheets></workbook>')

wb_rels = "".join(f'<Relationship Id="rId{i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i+1}.xml"/>' for i in range(len(sheets)))
wb_rels += f'<Relationship Id="rId{len(sheets)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
WORKBOOK_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    + wb_rels + '</Relationships>')

# styles: 0=normal, 1=header(bold, fill), 2=number
STYLES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
    '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts>'
    '<fills count="3"><fill><patternFill patternType="none"/></fill>'
    '<fill><patternFill patternType="gray125"/></fill>'
    '<fill><patternFill patternType="solid"><fgColor rgb="FF2E6C80"/><bgColor indexed="64"/></patternFill></fill></fills>'
    '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
    '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    '<cellXfs count="3">'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
    '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment horizontal="right"/></xf>'
    '</cellXfs>'
    '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
    '</styleSheet>')

out_path = os.path.join(BASE, "Saran-URL-Analysis-Report.xlsx")
with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", CONTENT_TYPES)
    z.writestr("_rels/.rels", ROOT_RELS)
    z.writestr("xl/workbook.xml", WORKBOOK)
    z.writestr("xl/_rels/workbook.xml.rels", WORKBOOK_RELS)
    z.writestr("xl/styles.xml", STYLES)
    for i, (_, xml) in enumerate(sheets):
        z.writestr(f"xl/worksheets/sheet{i+1}.xml", xml)

print("Wrote", out_path)
print("Sheets:", ", ".join(n for n, _ in sheets))
print("Pages:", len(pages), "Docs:", len(docs), "Groups:", len(groups), "Broken:", len(broken))
