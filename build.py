#!/usr/bin/env python3
"""Build the static CVCEC website into docs/ (served by GitHub Pages).

Usage:
  python3 build.py                                  # production build (indexable)
  PREVIEW=1 SITE_BASE=/cvcec-website/ python3 build.py  # preview build (noindex)

Content lives in src/pages (one HTML fragment per page) and src/posts (news).
Links inside content are written root-relative ("/about"); the build turns them
into relative links so the same files work at www.cvcec.org/ and at a preview
sub-path such as cvcec.github.io/cvcec-website/.
Images are written as "@/<file>" and are served from docs/images/ (light .webp
versions in docs/images/w/ are used automatically when they exist).
"""
import hashlib
import html
import json
import os
import re
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import quote
import sys

sys.path.insert(0, str(Path(__file__).parent / "tools"))
from i18n import translate  # noqa: E402

ROOT = Path(__file__).parent
SRC = ROOT / "src"
OUT = ROOT / "docs"
SITE = "https://www.cvcec.org"
PREVIEW = os.environ.get("PREVIEW") == "1"
REMOTE_IMAGES = os.environ.get("REMOTE_IMAGES") == "1"
SITE_BASE = os.environ.get("SITE_BASE", "/")  # only used by 404.html
JW = "https://primary.jwwb.nl/public/l/o/m/temp-vrecvbisaxoqyllchcds/"
JW_PEXELS = "https://primary.jwwb.nl/pexels/"
DEFAULT_OG = "@/cvcec-youth-heritage-program-3-high.jpg"
ORG = "Canada Vietnam Cultural & Educational Council"
SCHOOL = "https://vietclass.cvcec.org/"

# (label, href, children) — a child is (label, href) and may point to another site
NAV = [
    ("About", "/about", [("About CVCEC", "/about"), ("Governance & accountability", "/about/governance")]),
    ("Programs", "/programs", [("All programs", "/programs"),
                               ("Vietnamese School · Trường Tiếng Việt Của Em", "/programs/vietnamese-school"),
                               ("Viet Youth Readiness Hub", "/programs/viet-youth-readiness-hub"),
                               ("Readiness & Safety Initiative", "/programs/viet-youth-safety-initiative", "sub"),
                               ("Leading Urban Change (U of T)", "/programs/leading-urban-change", "sub"),
                               ("Study in Canada guide", "https://duhoccanada.cvcec.org/")]),
    ("Branches", "/about#branches", [("PEI Branch", "/programs/pei-branch"),
                                     ("Manitoba Branch", "https://manitoba.cvcec.org/"),
                                     ("CVCEC in Vietnam", "https://vn.cvcec.org/")]),
    ("Our Impact", "/our-impact", []),
    ("News & Media", "/news-media", [("Media coverage", "/news-media"), ("News releases", "/news-media/news"),
                                     ("Photo gallery", "/news-media/gallery")]),
    ("Contact", "/contact", []),
]

CRUMB = {
    "about": "About", "governance": "Governance", "programs": "Programs",
    "viet-youth-readiness-hub": "Viet Youth Readiness Hub", "vietnamese-school": "Vietnamese School", "pei-branch": "PEI Branch", "viet-youth-safety-initiative": "Viet Youth Readiness & Safety Initiative", "leading-urban-change": "Leading Urban Change", "mentoring-program": "Mentoring Program", "our-impact": "Our Impact",
    "news-media": "News & Media", "news": "News releases", "gallery": "Photo gallery",
    "get-involved": "Get Involved", "contact": "Contact", "privacy-policy": "Privacy Policy",
    "accessibility": "Accessibility",
}

# Old addresses that should keep working
REDIRECTS = {
    "/media-coverage/3020163_cvcec-celebrates-vietnamese-lunar-new-year-2025-across-canadian-schools-and-communities":
        "/news-media/3020163_cvcec-celebrates-lunar-new-year-2025-with-toronto-s-vietnamese-community",
    "/viet-youth-readiness-hub": "/programs/viet-youth-readiness-hub",
    # The Mentoring Program now lives on the Vietnam branch site
    "/programs/mentoring-program": "https://vn.cvcec.org/#mentoring",
    "/vi/programs/mentoring-program": "https://vn.cvcec.org/#mentoring",
}

ORG_LD = {
    "@context": "https://schema.org",
    "@type": "NGO",
    "@id": SITE + "/#organization",
    "name": ORG,
    "alternateName": "CVCEC",
    "legalName": ORG,
    "url": SITE + "/",
    "logo": SITE + "/assets/favicon.png",
    "email": "contact@cvcec.org",
    "foundingDate": "2024-12",
    "identifier": {"@type": "PropertyValue", "propertyID": "Canada Not-for-profit Corporation Number",
                   "value": "1657486-6"},
    "address": {"@type": "PostalAddress", "streetAddress": "Suite 300, 192 Spadina Avenue",
                "addressLocality": "Toronto", "addressRegion": "ON", "postalCode": "M5T 2C2",
                "addressCountry": "CA"},
    "areaServed": [{"@type": "AdministrativeArea", "name": n} for n in
                   ("Ontario", "Prince Edward Island", "Manitoba")],
    "knowsLanguage": ["en", "vi"],
    "sameAs": ["https://www.wikidata.org/wiki/Q142216633", "https://facebook.com/cvcec.org",
               "https://youtube.com/@CVCEC2024", "https://linkedin.com/company/cvcec/"],
}

images = {}  # local file name -> source URL
LANG = "en"  # "en" while building English pages, "vi" while building /vi/ pages
VI_DIR = SRC / "i18n" / "vi"

# Words in the shared header, menu and footer (English -> Vietnamese)
UI_VI = [
    ('<html lang="en-CA">', '<html lang="vi">'),
    ('content="en_CA"', 'content="vi_VN"'),
    ('Skip to main content', 'Chuyển đến nội dung chính'),
    ('Canadian federal not-for-profit · Free programs for families', 'Tổ chức phi lợi nhuận liên bang Canada · Chương trình miễn phí cho gia đình'),
    ('aria-label="CVCEC home"', 'aria-label="Trang chủ CVCEC"'),
    ('Canada Vietnam Cultural &amp; Educational Council</span></span>', 'Hội đồng Văn hoá &amp; Giáo dục Canada – Việt Nam</span></span>'),
    ('>About CVCEC<', '>Về CVCEC<'), ('>About<', '>Giới thiệu<'),
    ('>Governance &amp; accountability<', '>Quản trị &amp; trách nhiệm giải trình<'),
    ('>All programs<', '>Tất cả chương trình<'), ('>Programs<', '>Chương trình<'),
    ('>Vietnamese School · Trường Tiếng Việt Của Em<', '>Trường Tiếng Việt Của Em<'),
    ('>PEI Branch<', '>Chi nhánh PEI<'), ('>Branches<', '>Chi nhánh<'), ('aria-label="Show Branches pages"', 'aria-label="Xem các trang Chi nhánh"'),
    ('<p class="footer-head" style="margin-top:1.4rem">Branches</p>', '<p class="footer-head" style="margin-top:1.4rem">Chi nhánh</p>'),
    ('>Manitoba Branch<', '>Chi nhánh Manitoba<'), ('>CVCEC in Vietnam<', '>CVCEC tại Việt Nam<'),
    ('>Viet Youth Readiness &amp; Safety Initiative<', '>Sáng kiến Sẵn sàng &amp; An toàn<'),
    ('>Mentoring Program for Educators<', '>Chương trình Mentoring cho nhà giáo<'),
    ('>Study in Canada guide', '>Cẩm nang Du học Canada'),
    ('>Our Impact<', '>Tác động<'), ('>News &amp; Media<', '>Tin tức &amp; Báo chí<'),
    ('>Media coverage<', '>Báo chí đưa tin<'), ('>News releases<', '>Thông cáo báo chí<'),
    ('>Photo gallery<', '>Thư viện ảnh<'), ('>Contact<', '>Liên hệ<'), ('>Get involved<', '>Tham gia<'),
    ('aria-label="Show About pages"', 'aria-label="Xem các trang Giới thiệu"'),
    ('aria-label="Show Programs pages"', 'aria-label="Xem các trang Chương trình"'),
    ('aria-label="Show News &amp; Media pages"', 'aria-label="Xem các trang Tin tức"'),
    ('aria-label="Main"', 'aria-label="Menu chính"'),
    ('Young people, language and learning: <em>a bridge between Canada and Vietnam.</em>', 'Thế hệ trẻ, ngôn ngữ và giáo dục: <em>nhịp cầu nối Canada và Việt Nam.</em>'),
    ('>Learn Vietnamese free<', '>Học tiếng Việt miễn phí<'),
    ('Hội đồng Văn hoá &amp; Giáo dục Canada – Việt Nam. A Canadian federal not-for-profit corporation (No. 1657486-6) based in Toronto, serving Vietnamese-Canadian children, youth, newcomer families and everyone who wants to know Vietnam.',
     'Canada Vietnam Cultural &amp; Educational Council. Tổ chức phi lợi nhuận liên bang Canada (số đăng ký 1657486-6) có trụ sở tại Toronto, đồng hành cùng trẻ em, thanh niên, gia đình mới nhập cư gốc Việt và tất cả những ai muốn hiểu Việt Nam.'),
    ('<p class="footer-head">Organization</p>', '<p class="footer-head">Tổ chức</p>'),
    ('<p class="footer-head">Accountability</p>', '<p class="footer-head">Trách nhiệm giải trình</p>'),
    ('>Vietnamese School<', '>Trường Tiếng Việt<'),
    ('>Readiness &amp; Safety Initiative<', '>Sáng kiến Sẵn sàng &amp; An toàn<'),
    ('>Mentoring Program<', '>Chương trình Mentoring<'),
    ('>Our journey &amp; impact<', '>Hành trình &amp; tác động<'),
    ('>Governance<', '>Quản trị<'), ('>Privacy Policy<', '>Quyền riêng tư<'), ('>Accessibility<', '>Tiếp cận<'),
    ('<strong>Land acknowledgement.</strong> CVCEC is based in Toronto, on the traditional territory of many nations including the Mississaugas of the Credit, the Anishnabeg, the Chippewa, the Haudenosaunee and the Wendat peoples, and now home to many diverse First Nations, Inuit and Métis peoples. Toronto is covered by Treaty 13 with the Mississaugas of the Credit.',
     '<strong>Lời tri ân vùng đất.</strong> CVCEC có trụ sở tại Toronto, trên lãnh thổ truyền thống của nhiều dân tộc, trong đó có Mississaugas of the Credit, Anishnabeg, Chippewa, Haudenosaunee và Wendat, và ngày nay là quê hương của nhiều cộng đồng First Nations, Inuit và Métis. Toronto thuộc Hiệp ước số 13 với Mississaugas of the Credit.'),
    ('All rights reserved.', 'Bảo lưu mọi quyền.'),
    ('aria-label="Close photo"', 'aria-label="Đóng ảnh"'), ('aria-label="Previous photo"', 'aria-label="Ảnh trước"'),
    ('aria-label="Next photo"', 'aria-label="Ảnh sau"'),
    ('aria-label="Breadcrumb"', 'aria-label="Đường dẫn"'),
    # news cards and news release pages
    ('Read the story<span class="sr-only">', 'Đọc tiếp<span class="sr-only">'),
    ('<span>« Previous</span>', '<span>« Bài trước</span>'), ('<span>Next »</span>', '<span>Bài sau »</span>'),
    ('<p class="eyebrow">News release</p>', '<p class="eyebrow">Thông cáo báo chí</p>'),
    ('</time> · Toronto, Ontario</p>', '</time> · Toronto, Ontario</p>'),
    ('aria-label="Share this story"', 'aria-label="Chia sẻ bài viết"'), ('<span>Share:</span>', '<span>Chia sẻ:</span>'),
    ('aria-label="More news"', 'aria-label="Tin khác"'), ('>Home<', '>Trang chủ<'),
    ('<p><strong>About CVCEC</strong><br>\nThe Canada Vietnam Cultural &amp; Educational Council (CVCEC) is a federally incorporated not-for-profit organization based in Toronto. It offers Vietnamese language and culture classes for children, helps newcomer and international students settle into Canadian schools and connects education communities in Canada and Vietnam. More information is available at',
     '<p><strong>Về CVCEC</strong><br>\nHội đồng Văn hoá &amp; Giáo dục Canada – Việt Nam (CVCEC) là tổ chức phi lợi nhuận đăng ký liên bang, có trụ sở tại Toronto. CVCEC tổ chức lớp tiếng Việt và văn hoá cho trẻ em, giúp học sinh mới nhập cư và du học sinh hoà nhập trường học Canada, và kết nối cộng đồng giáo dục Canada và Việt Nam. Thông tin chi tiết tại'),
    ('<p><strong>About the Viet Youth Readiness Hub</strong><br>\nLaunched in Toronto in April 2026, the Viet Youth Readiness Hub (VYRH) is a CVCEC initiative that helps Vietnamese students and families understand Canadian schools through orientation sessions, mentoring and youth leadership opportunities.',
     '<p><strong>Về Viet Youth Readiness Hub</strong><br>\nRa mắt tại Toronto tháng 4/2026, Viet Youth Readiness Hub (VYRH) là sáng kiến của CVCEC giúp học sinh và gia đình Việt Nam hiểu trường học Canada qua các buổi định hướng, mentoring và cơ hội lãnh đạo cho thanh niên.'),
    ('<p><strong>Media contact</strong><br>\nPhan Thi Quynh Trang, founder and president<br>', '<p><strong>Liên hệ báo chí</strong><br>\nPhan Thị Quỳnh Trang, Nhà sáng lập kiêm Chủ tịch<br>'),
]


def vi_path(url_path):
    """English address -> Vietnamese address (/about -> /vi/about, / -> /vi/)."""
    return "/vi/" if url_path == "/" else "/vi" + url_path


def en_path(url_path):
    if url_path in ("/vi", "/vi/"):
        return "/"
    return url_path[3:] if url_path.startswith("/vi/") else url_path


VI_PAGES = set()  # English paths that have a Vietnamese version


def link_to_vi(markup):
    """Point internal links at the Vietnamese pages when they exist."""
    def fix(m):
        val = m.group(1)
        path, sep, frag = val.partition("#")
        if path in VI_PAGES:
            return f'href="{vi_path(path)}{sep}{frag}"'
        return m.group(0)
    return re.sub(r'href="(/[^"]*)"', fix, markup)


def vi_file(name):
    """Translation file for a page: flat (programs__x.json) or nested (programs/x.json)."""
    f = VI_DIR / f"{name}.json"
    return f if f.exists() else VI_DIR / (name.replace("__", "/") + ".json")


def vi_table(name):
    f = vi_file(name)
    if not f.exists():
        return {}, {}
    data = json.loads(f.read_text(encoding="utf-8"))
    return data.get("meta", {}), data.get("text", {})



def asset_version(name):
    return hashlib.md5((SRC / "assets" / name).read_bytes()).hexdigest()[:8]



# ---------------------------------------------------------------- helpers
def read_fragment(path):
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    if "\n---\n" in text:
        head, body = text.split("\n---\n", 1)
        for line in head.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    return meta, body


def prefix_for(url_path):
    """'../' prefix from the directory of url_path back to the site root."""
    if url_path == "/":
        depth = 0
    elif url_path.endswith("/"):
        depth = url_path.strip("/").count("/") + 1
    else:
        depth = url_path.strip("/").count("/")
    return "../" * depth


def image_name(token):
    if token.startswith("@pexels/"):
        rest = token[len("@pexels/"):]
        name = "pexels-" + rest.split("/")[-1]
        images[name] = JW_PEXELS + rest
    else:
        name = token[2:]
        images[name] = JW + name
    return name


def image_url(token, prefix):
    name = image_name(token)
    if REMOTE_IMAGES:
        return images[name]
    light = OUT / "images" / "w" / (Path(name).stem + ".webp")
    if light.exists():
        return f"{prefix}images/w/{light.name}"
    return f"{prefix}images/{name}"


def absolute_image(token):
    name = image_name(token)
    return images[name] if REMOTE_IMAGES else f"{SITE}/images/{name}"


def localize(markup, url_path):
    prefix = prefix_for(url_path)

    def fix(m):
        attr, val = m.group(1), m.group(2)
        if val.startswith("@"):
            return f'{attr}="{image_url(val, prefix)}"'
        if val.startswith("/") and not val.startswith("//"):
            rel = val.lstrip("/")
            return f'{attr}="{prefix + rel if (prefix + rel) else "./"}"'
        return m.group(0)

    markup = re.sub(r'\b(href|src)="([^"]*)"', fix, markup)
    count = 0

    def lazy(m):
        nonlocal count
        count += 1
        tag = m.group(0)
        if "loading=" in tag:
            return tag
        extra = ' decoding="async"' if count <= 2 else ' loading="lazy" decoding="async"'
        return tag[:-1] + extra + ">"

    return re.sub(r"<img\b[^>]*>", lazy, markup)


def esc(s):
    return html.escape(s, quote=True)


def is_external(href):
    return href.startswith("http")


def nav_html(current):
    items = []
    for label, href, children in NAV:
        active = current == href or current.startswith(href + "/") or any(current == c[1] for c in children)
        if href == "/programs" and current == "/programs/pei-branch":
            active = False
        cls = ' class="is-active"' if active else ""
        if children:
            sub = []
            for c in children:
                cl, ch = c[0], c[1]
                li = ' class="sub-item"' if len(c) > 2 else ""
                cur = ' aria-current="page"' if current == ch else ""
                ext = '<span class="ext" aria-hidden="true">↗</span>' if is_external(ch) else ""
                sub.append(f'<li{li}><a href="{ch}"{cur}>{esc(cl)}{ext}</a></li>')
            items.append(
                f'<li class="has-sub"><a href="{href}"{cls}>{esc(label)}</a>'
                f'<button class="sub-toggle" aria-expanded="false" aria-label="Show {esc(label)} pages">'
                f'<svg viewBox="0 0 12 8" aria-hidden="true"><path d="M1 1l5 5 5-5" fill="none" stroke="currentColor" stroke-width="1.8"/></svg></button>'
                f'<ul class="sub">{"".join(sub)}</ul></li>')
        else:
            cur = ' aria-current="page"' if current == href else ""
            items.append(f'<li><a href="{href}"{cls}{cur}>{esc(label)}</a></li>')
    if LANG == "vi":
        other = "@@EN@@" + current
    else:
        other = vi_path(current) if current in VI_PAGES else "/vi/"
    label, code = ("English", "en") if LANG == "vi" else ("Tiếng Việt", "vi")
    items.append(f'<li class="lang-switch"><a href="{other}" hreflang="{code}" lang="{code}">{label}</a></li>')
    items.append('<li class="nav-cta"><a href="/get-involved">Get involved</a></li>')
    return "".join(items)


def breadcrumb_ld(url_path, title):
    if url_path == "/":
        return None
    parts = url_path.strip("/").split("/")
    elems = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"}]
    for i, p in enumerate(parts):
        path = "/" + "/".join(parts[:i + 1])
        name = CRUMB.get(p) or (title.split("|")[0].strip() if i == len(parts) - 1 else p)
        elems.append({"@type": "ListItem", "position": i + 2, "name": name, "item": SITE + path})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": elems}


def faq_ld(body):
    qs = re.findall(r'<details[^>]*data-faq[^>]*>\s*<summary>(.*?)</summary>\s*<div>(.*?)</div>\s*</details>', body, re.S)
    if not qs:
        return None
    strip = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": html.unescape(strip(q)),
         "acceptedAnswer": {"@type": "Answer", "text": html.unescape(strip(a))}} for q, a in qs]}


def ld_tag(obj):
    return f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>\n'


def layout(url_path, title, description, body, og_image=None, og_type="website", extra_ld=()):
    canonical = SITE + url_path
    og = absolute_image(og_image or DEFAULT_OG)
    robots = '<meta name="robots" content="noindex, nofollow">\n' if PREVIEW else ""
    lds = [ORG_LD]
    if url_path == "/":
        lds.append({"@context": "https://schema.org", "@type": "WebSite", "name": ORG + " (CVCEC)",
                    "url": SITE + "/", "inLanguage": "en-CA", "publisher": {"@id": SITE + "/#organization"}})
    for extra in (breadcrumb_ld(url_path, title), faq_ld(body), *extra_ld):
        if extra:
            lds.append(extra)
    ld = "".join(ld_tag(x) for x in lds)
    base_en = en_path(url_path)
    hreflang = ""
    if base_en in VI_PAGES:
        hreflang = (f'<link rel="alternate" hreflang="en-CA" href="{SITE}{base_en}">\n'
                    f'<link rel="alternate" hreflang="vi" href="{SITE}{vi_path(base_en)}">\n'
                    f'<link rel="alternate" hreflang="x-default" href="{SITE}{base_en}">')
    page = f"""<!DOCTYPE html>
<html lang="en-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
{robots}<link rel="canonical" href="{canonical}">
{hreflang}
<meta property="og:type" content="{og_type}">
<meta property="og:locale" content="en_CA">
<meta property="og:site_name" content="{esc(ORG)} (CVCEC)">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#c80000">
<link rel="icon" href="/assets/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="/assets/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&family=Merriweather:ital,wght@0,400;0,700;0,900;1,400&display=swap">
<link rel="stylesheet" href="/assets/site.css?v={asset_version("site.css")}">
{ld}</head>
<body>
<a class="skip-link" href="#main-content">Skip to main content</a>
<div class="topbar"><div class="wrap topbar-inner">
  <span><span class="flags" aria-hidden="true"><i class="flag-ca"></i><i class="flag-vn"></i></span>Canadian federal not-for-profit · Free programs for families</span>
  <span class="topbar-right">Toronto, Ontario · <a href="mailto:contact@cvcec.org">contact@cvcec.org</a></span>
</div></div>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="/" aria-label="CVCEC home">
      <img src="/assets/logo-mark.webp" alt="" width="50" height="53">
      <span class="brand-name"><span class="brand-mark"><b>C</b>VCEC</span>
      <span class="brand-text">Canada Vietnam Cultural &amp; Educational Council</span></span>
    </a>
    <button class="menu-toggle" aria-expanded="false" aria-controls="site-nav">
      <span class="menu-bars" aria-hidden="true"></span><span class="menu-label">Menu</span>
    </button>
    <nav id="site-nav" class="site-nav" aria-label="Main">
      <ul class="nav-list">{nav_html(en_path(url_path))}</ul>
    </nav>
  </div>
</header>
<main id="main-content">
{body}
</main>
<footer class="site-footer">
  <div class="wrap footer-top">
    <p>Young people, language and learning: <em>a bridge between Canada and Vietnam.</em></p>
    <div><a class="btn" href="/get-involved">Get involved</a> <a class="btn btn-ghost-light" href="{SCHOOL}">Learn Vietnamese free</a></div>
  </div>
  <div class="wrap footer-grid">
    <div>
      <div class="footer-brand"><img src="/assets/logo-mark.webp" alt="" width="52" height="55"><span class="brand-mark"><b>C</b>VCEC<small>{esc(ORG)}</small></span></div>
      <p>Hội đồng Văn hoá &amp; Giáo dục Canada – Việt Nam. A Canadian federal not-for-profit corporation (No. 1657486-6) based in Toronto, serving Vietnamese-Canadian children, youth, newcomer families and everyone who wants to know Vietnam.</p>
      <p>Suite 300, 192 Spadina Avenue<br>Toronto, ON M5T 2C2<br><a href="mailto:contact@cvcec.org">contact@cvcec.org</a></p>
      <ul class="social">
        <li><a href="https://facebook.com/cvcec.org">Facebook</a></li>
        <li><a href="https://linkedin.com/company/cvcec/">LinkedIn</a></li>
        <li><a href="https://youtube.com/@CVCEC2024">YouTube</a></li>
        <li><a href="https://api.whatsapp.com/send?phone=16478972358">WhatsApp</a></li>
      </ul>
    </div>
    <div>
      <p class="footer-head">Programs</p>
      <ul class="footer-links">
        <li><a href="/programs/vietnamese-school">Vietnamese School</a></li>
        <li><a href="/programs/viet-youth-readiness-hub">Viet Youth Readiness Hub</a></li>
        <li><a href="/programs/viet-youth-safety-initiative">Readiness &amp; Safety Initiative</a></li>
        <li><a href="/programs/leading-urban-change">Leading Urban Change</a></li>
        <li><a href="https://duhoccanada.cvcec.org/">Study in Canada guide</a></li>
        <li><a href="/programs">All programs</a></li>
      </ul>
    </div>
    <div>
      <p class="footer-head">Organization</p>
      <ul class="footer-links">
        <li><a href="/about">About CVCEC</a></li>
        <li><a href="/our-impact">Our journey &amp; impact</a></li>
        <li><a href="/news-media">Media coverage</a></li>
        <li><a href="/news-media/news">News releases</a></li>
        <li><a href="/news-media/gallery">Photo gallery</a></li>
      </ul>
      <p class="footer-head" style="margin-top:1.4rem">Branches</p>
      <ul class="footer-links">
        <li><a href="/programs/pei-branch">PEI Branch</a></li>
        <li><a href="https://manitoba.cvcec.org/">Manitoba Branch</a></li>
        <li><a href="https://vn.cvcec.org/">CVCEC in Vietnam</a></li>
      </ul>
    </div>
    <div>
      <p class="footer-head">Accountability</p>
      <ul class="footer-links">
        <li><a href="/about/governance">Governance</a></li>
        <li><a href="/privacy-policy">Privacy Policy</a></li>
        <li><a href="/accessibility">Accessibility</a></li>
        <li><a href="/get-involved">Get involved</a></li>
        <li><a href="/contact">Contact</a></li>
      </ul>
    </div>
  </div>
  <div class="wrap land">
    <p><strong>Land acknowledgement.</strong> CVCEC is based in Toronto, on the traditional territory of many nations including the Mississaugas of the Credit, the Anishnabeg, the Chippewa, the Haudenosaunee and the Wendat peoples, and now home to many diverse First Nations, Inuit and Métis peoples. Toronto is covered by Treaty 13 with the Mississaugas of the Credit.</p>
    <p class="copy">© 2025–{date.today().year} {esc(ORG)} (CVCEC). All rights reserved.</p>
  </div>
</footer>
<div class="lightbox" hidden>
  <button class="lb-close" aria-label="Close photo">×</button>
  <button class="lb-prev" aria-label="Previous photo">‹</button>
  <figure><img alt=""><figcaption></figcaption></figure>
  <button class="lb-next" aria-label="Next photo">›</button>
</div>
<script src="/assets/site.js?v={asset_version("site.js")}" defer></script>
</body>
</html>
"""
    if LANG == "vi":
        for a, b in UI_VI:
            page = page.replace(a, b)
        page = link_to_vi(page).replace("@@EN@@", "")
        page = page.replace('"inLanguage": "en-CA"', '"inLanguage": "vi"')
    return localize(page, url_path)


def write(url_path, markup):
    if url_path == "/":
        rel = "index.html"
    elif url_path.endswith("/"):
        rel = url_path.strip("/") + "/index.html"
    else:
        rel = url_path.strip("/") + ".html"
    target = OUT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markup, encoding="utf-8")
    return rel


# ---------------------------------------------------------------- news
def fmt_date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    if LANG == "vi":
        return f"{d}/{m}/{y}"
    return date(y, m, d).strftime("%B %-d, %Y")


def load_posts():
    posts = []
    for f in sorted((SRC / "posts").glob("*.html")):
        meta, body = read_fragment(f)
        slug = f.stem
        posts.append({**meta, "slug": slug, "path": f"/news-media/{slug}", "body": body,
                      "id": int(slug.split("_")[0])})
    posts.sort(key=lambda p: (p["date"], p["id"]), reverse=True)
    return posts


ABOUT_CVCEC = """<p><strong>About CVCEC</strong><br>
The Canada Vietnam Cultural &amp; Educational Council (CVCEC) is a federally incorporated not-for-profit organization based in Toronto. It offers Vietnamese language and culture classes for children, helps newcomer and international students settle into Canadian schools and connects education communities in Canada and Vietnam. More information is available at <a href="/">cvcec.org</a>.</p>"""
ABOUT_VYRH = """<p><strong>About the Viet Youth Readiness Hub</strong><br>
Launched in Toronto in April 2026, the Viet Youth Readiness Hub (VYRH) is a CVCEC initiative that helps Vietnamese students and families understand Canadian schools through orientation sessions, mentoring and youth leadership opportunities.</p>"""
MEDIA_CONTACT = """<p class="end-mark">-30-</p>
<p><strong>Media contact</strong><br>
Phan Thi Quynh Trang, founder and president<br>
Canada Vietnam Cultural &amp; Educational Council<br>
<a href="mailto:contact@cvcec.org">contact@cvcec.org</a></p>"""


def news_card(p, heading="h3"):
    img = p.get("image")
    pic = (f'<a class="card-media" href="{p["path"]}" tabindex="-1" aria-hidden="true">'
           f'<img src="{img}" alt=""></a>') if img else ""
    return (f'<article class="news-card">{pic}<div class="card-body">'
            f'<p class="meta"><time datetime="{p["date"]}">{fmt_date(p["date"])}</time></p>'
            f'<{heading}><a href="{p["path"]}">{p["title"]}</a></{heading}>'
            f'<p>{p.get("teaser") or re.sub(r"^[A-Z]+, [^—]+— ", "", p["summary"])}</p>'
            f'<a class="link-arrow" href="{p["path"]}">Read the story<span class="sr-only">: {p["title"]}</span></a>'
            f'</div></article>')


def build_post(p, prev_p, next_p):
    share_url = quote(SITE + p["path"], safe="")
    share_title = quote(html.unescape(p["title"]), safe="")
    pager = []
    pager.append(f'<a class="pager-prev" href="{prev_p["path"]}"><span>« Previous</span>{prev_p["title"]}</a>'
                 if prev_p else "<span></span>")
    if next_p:
        pager.append(f'<a class="pager-next" href="{next_p["path"]}"><span>Next »</span>{next_p["title"]}</a>')
    body = f"""<div class="post-head"><div class="narrow">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span aria-hidden="true">/</span><a href="/news-media/news">News releases</a></nav>
  <p class="eyebrow">News release</p>
  <h1>{p["title"]}</h1>
  <p class="meta"><time datetime="{p["date"]}">{fmt_date(p["date"])}</time> · Toronto, Ontario</p>
</div></div>
<article class="narrow post-body">
  <div class="prose">
{p["body"]}
{ABOUT_CVCEC}
{ABOUT_VYRH if p.get("vyrh") == "yes" else ""}
{MEDIA_CONTACT}
  </div>
  <div class="share" aria-label="Share this story">
    <span>Share:</span>
    <a href="https://www.facebook.com/sharer/sharer.php?u={share_url}">Facebook</a>
    <a href="https://www.linkedin.com/sharing/share-offsite/?url={share_url}">LinkedIn</a>
    <a href="https://x.com/intent/post?url={share_url}&amp;text={share_title}">X</a>
    <a href="mailto:?subject={share_title}&amp;body={share_url}">Email</a>
  </div>
  <nav class="pager" aria-label="More news">{"".join(pager)}</nav>
</article>"""
    article_ld = {"@context": "https://schema.org", "@type": "NewsArticle",
                  "headline": html.unescape(p["title"]), "datePublished": p["date"],
                  "description": html.unescape(p["description"]),
                  "image": [absolute_image(p["image"])] if p.get("image") else [],
                  "author": {"@id": SITE + "/#organization"}, "publisher": {"@id": SITE + "/#organization"},
                  "mainEntityOfPage": SITE + p["path"], "inLanguage": "en-CA"}
    return layout(p["path"], p["seo_title"], p["description"], body, p.get("image"), "article", [article_ld])


def redirect_page(old, new):
    external = new.startswith("http")
    target = new if external else SITE + new
    rel = new if external else prefix_for(old) + new.lstrip("/")
    return f"""<!DOCTYPE html>
<html lang="en-CA"><head><meta charset="utf-8"><title>Page moved | CVCEC</title>
<link rel="canonical" href="{target}"><meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={rel}"></head>
<body><p>This page has moved to <a href="{rel}">{target}</a>.</p></body></html>
"""


# ---------------------------------------------------------------- main
def main():
    if OUT.exists():
        keep = OUT / "images"
        for child in OUT.iterdir():
            if child != keep:
                shutil.rmtree(child) if child.is_dir() else child.unlink()
    OUT.mkdir(exist_ok=True)
    shutil.copytree(SRC / "assets", OUT / "assets", dirs_exist_ok=True)
    (OUT / ".nojekyll").write_text("")

    global LANG
    posts = load_posts()
    written = []
    page_files = []
    for f in sorted((SRC / "pages").rglob("*.html")):
        rel = f.relative_to(SRC / "pages").with_suffix("")
        url_path = "/" if str(rel) == "index" else "/" + str(rel)
        page_files.append((f, url_path, str(rel).replace("/", "__")))
    for f, url_path, name in page_files:
        if vi_file(name).exists():
            VI_PAGES.add(url_path)
    for p in posts:
        if vi_file(f"post__{p['id']}").exists():
            VI_PAGES.add(p["path"])

    def build_pages(posts_here, to_url, tables):
        for f, url_path, name in page_files:
            if LANG == "vi" and url_path not in VI_PAGES:
                continue
            meta, body = read_fragment(f)
            title, desc = meta["title"], meta["description"]
            if LANG == "vi":
                vmeta, table = tables(name)
                body = translate(body, table)
                title, desc = vmeta.get("title", title), vmeta.get("description", desc)
            body = body.replace("<!--LATEST_NEWS-->", "".join(news_card(p) for p in posts_here[:3]))
            body = body.replace("<!--ALL_NEWS-->", "".join(news_card(p, "h2") for p in posts_here))
            out_path = to_url(url_path)
            written.append((out_path, write(out_path, layout(out_path, title, desc, body, meta.get("image")))))
        for i, p in enumerate(posts_here):
            older = posts_here[i + 1] if i + 1 < len(posts_here) else None
            newer = posts_here[i - 1] if i > 0 else None
            written.append((p["path"], write(p["path"], build_post(p, older, newer))))

    # English site
    LANG = "en"
    build_pages(posts, lambda u: u, None)

    # Vietnamese site under /vi/
    LANG = "vi"
    posts_vi = []
    for p in posts:
        vmeta, table = vi_table(f"post__{p['id']}")
        if not table and not vmeta:
            continue
        q = dict(p)
        q.update({k: v for k, v in vmeta.items() if v})
        q["body"] = translate(p["body"], table)
        q["path"] = vi_path(p["path"])
        posts_vi.append(q)
    build_pages(posts_vi, vi_path, vi_table)
    LANG = "en"

    for old, new in REDIRECTS.items():
        write(old, redirect_page(old, new))

    body404 = f"""<section class="section"><div class="narrow">
<p class="eyebrow">Error 404</p><h1>Page not found</h1>
<p class="lead">Sorry, we couldn’t find that page. It may have moved when we updated our website.</p>
<p><a class="btn" href="{SITE_BASE}">Go to the home page</a> <a class="btn btn-outline" href="{SITE_BASE}news-media/news">See all news</a></p></div></section>"""
    page404 = layout("/", "Page not found | CVCEC", "This page could not be found.", body404)
    page404 = re.sub(r'(href|src)="(?!https?:|mailto:|#|/)([^"]*)"',
                     lambda m: f'{m.group(1)}="{SITE_BASE}{m.group(2)}"', page404)
    page404 = page404.replace(f'href="{SITE_BASE}./"', f'href="{SITE_BASE}"')
    (OUT / "404.html").write_text(page404, encoding="utf-8")

    today = date.today().isoformat()
    urls = "".join(f"<url><loc>{SITE}{p}</loc><lastmod>{today}</lastmod></url>" for p, _ in written)
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    robots = "User-agent: *\nDisallow: /\n" if PREVIEW else f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n"
    (OUT / "robots.txt").write_text(robots)

    manifest = "".join(f"{url} {name}\n" for name, url in sorted(images.items()))
    (ROOT / "images.txt").write_text(manifest)
    print(f"Built {len(written)} pages, {len(images)} images referenced"
          f"{' (preview)' if PREVIEW else ''}{' (remote images)' if REMOTE_IMAGES else ''}.")


if __name__ == "__main__":
    main()
