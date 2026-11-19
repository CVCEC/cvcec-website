#!/usr/bin/env python3
"""Build the static CVCEC website into docs/ (served by GitHub Pages).

Usage:
  python3 build.py                 # production build (indexable)
  PREVIEW=1 python3 build.py       # preview build (noindex, robots disallow)
  REMOTE_IMAGES=1 python3 build.py # load images from the old Webador server

Content lives in src/pages (one HTML fragment per page) and src/posts (news).
Links inside content are written root-relative ("/about"); the build turns them
into relative links so the same files work at www.cvcec.org/ and at a preview
sub-path such as cvcec.github.io/cvcec-website/.
Images are written as "@/<file>" (old Webador library) and are served from
docs/images/<file>; images.txt lists where each one is copied from.
"""
import html
import os
import re
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
SRC = ROOT / "src"
OUT = ROOT / "docs"
SITE = "https://www.cvcec.org"
PREVIEW = os.environ.get("PREVIEW") == "1"
REMOTE_IMAGES = os.environ.get("REMOTE_IMAGES") == "1"
SITE_BASE = os.environ.get("SITE_BASE", "/")  # only used by 404.html
JW = "https://primary.jwwb.nl/public/l/o/m/temp-vrecvbisaxoqyllchcds/"
JW_PEXELS = "https://primary.jwwb.nl/pexels/"
DEFAULT_OG = "@/canada-vietnam-cultural-educational-council-education-exchange-high.jpg"
ORG = "Canada Vietnam Cultural & Educational Council"

NAV = [
    ("Home", "/", []),
    ("About", "/about", [("About CVCEC", "/about"), ("Governance", "/about/governance")]),
    ("Programs", "/programs", [("All programs", "/programs"),
                               ("Viet Youth Readiness Hub", "/programs/viet-youth-readiness-hub")]),
    ("Our Impact", "/our-impact", []),
    ("News & Media", "/news-media", [("Media coverage", "/news-media"), ("News", "/news-media/news"),
                                     ("Gallery", "/news-media/gallery")]),
    ("Get Involved", "/get-involved", []),
    ("Contact", "/contact", []),
]

images = {}  # local file name -> source URL


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
    depth = max(0, url_path.strip("/").count("/")) if url_path != "/" else 0
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
    return f"{prefix}images/{name}"


def absolute_image(token):
    name = image_name(token)
    return images[name] if REMOTE_IMAGES else f"{SITE}/images/{name}"


def localize(markup, url_path):
    prefix = prefix_for(url_path)

    def fix_href(m):
        attr, val = m.group(1), m.group(2)
        if val.startswith("@"):
            return f'{attr}="{image_url(val, prefix)}"'
        if val.startswith("/") and not val.startswith("//"):
            rel = val.lstrip("/")
            return f'{attr}="{prefix + rel if (prefix + rel) else "./"}"'
        return m.group(0)

    markup = re.sub(r'\b(href|src)="([^"]*)"', fix_href, markup)
    # lazy-load every image except the first one on the page
    count = 0

    def lazy(m):
        nonlocal count
        count += 1
        tag = m.group(0)
        if "loading=" in tag:
            return tag
        extra = ' decoding="async"' if count == 1 else ' loading="lazy" decoding="async"'
        return tag[:-1] + extra + ">"

    return re.sub(r"<img\b[^>]*>", lazy, markup)


def esc(s):
    return html.escape(s, quote=True)


def nav_html(current):
    items = []
    for label, href, children in NAV:
        active = current == href or (href != "/" and current.startswith(href + "/")) \
            or any(current == c[1] for c in children)
        cls = ' class="is-active"' if active else ""
        if children:
            sub = "".join(
                f'<li><a href="{c[1]}"{" aria-current=\"page\"" if current == c[1] else ""}>{esc(c[0])}</a></li>'
                for c in children)
            items.append(
                f'<li class="has-sub"><a href="{href}"{cls}>{esc(label)}</a>'
                f'<button class="sub-toggle" aria-expanded="false" aria-label="Show {esc(label)} pages">'
                f'<svg viewBox="0 0 12 8" aria-hidden="true"><path d="M1 1l5 5 5-5" fill="none" stroke="currentColor" stroke-width="1.8"/></svg></button>'
                f'<ul class="sub">{sub}</ul></li>')
        else:
            cur = ' aria-current="page"' if current == href else ""
            items.append(f'<li><a href="{href}"{cls}{cur}>{esc(label)}</a></li>')
    items.append('<li class="nav-cta"><a href="https://duhoccanada.cvcec.org/">Study in Canada</a></li>')
    return "".join(items)


def layout(url_path, title, description, body, og_image=None, og_type="website"):
    canonical = SITE + (url_path if url_path != "/" else "/")
    og = absolute_image(og_image or DEFAULT_OG)
    robots = '<meta name="robots" content="noindex, nofollow">\n' if PREVIEW else ""
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
{robots}<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(ORG)} (CVCEC)">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Merriweather:wght@700;900&family=Source+Sans+3:ital,wght@0,400;0,600;0,700;1,400&display=swap">
<link rel="stylesheet" href="/assets/site.css">
</head>
<body>
<a class="skip-link" href="#main-content">Skip to main content</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="/">
      <span class="brand-name">{esc(ORG)}</span>
    </a>
    <button class="menu-toggle" aria-expanded="false" aria-controls="site-nav">
      <span class="menu-bars" aria-hidden="true"></span><span class="menu-label">Menu</span>
    </button>
  </div>
  <nav id="site-nav" class="site-nav" aria-label="Main">
    <ul class="wrap nav-list">{nav_html(url_path)}</ul>
  </nav>
</header>
<main id="main-content">
{body}
</main>
<footer class="site-footer">
  <div class="wrap footer-grid">
    <div>
      <p class="footer-brand">{esc(ORG)} (CVCEC)</p>
      <p>A federal not-for-profit corporation (Corp. No. 1657486-6).<br>
      Suite 300, 192 Spadina Ave, Toronto, ON M5T 2C2<br>
      <a href="mailto:contact@cvcec.org">contact@cvcec.org</a></p>
      <ul class="social">
        <li><a href="https://facebook.com/cvcec.org">Facebook</a></li>
        <li><a href="https://youtube.com/@CVCEC2024">YouTube</a></li>
        <li><a href="https://linkedin.com/company/cvcec/">LinkedIn</a></li>
        <li><a href="https://api.whatsapp.com/send?phone=16478972358">WhatsApp</a></li>
      </ul>
    </div>
    <div>
      <p class="footer-head">Explore</p>
      <ul class="footer-links">
        <li><a href="/about">About CVCEC</a></li>
        <li><a href="/programs">Programs</a></li>
        <li><a href="/our-impact">Our impact</a></li>
        <li><a href="/news-media/news">News</a></li>
        <li><a href="/get-involved">Get involved</a></li>
      </ul>
    </div>
    <div>
      <p class="footer-head">Accountability</p>
      <ul class="footer-links">
        <li><a href="/about/governance">Governance</a></li>
        <li><a href="/privacy-policy">Privacy Policy</a></li>
        <li><a href="/accessibility">Accessibility</a></li>
        <li><a href="/contact">Contact</a></li>
      </ul>
    </div>
  </div>
  <div class="wrap land">
    <p><strong>Land acknowledgement:</strong> CVCEC is based in Toronto, on the traditional territory of many nations including the Mississaugas of the Credit, the Anishnabeg, the Chippewa, the Haudenosaunee and the Wendat peoples, and now home to many diverse First Nations, Inuit and Métis peoples. Toronto is covered by Treaty 13 with the Mississaugas of the Credit.</p>
    <p class="copy">© 2025–{date.today().year} {esc(ORG)} (CVCEC)</p>
  </div>
</footer>
<div class="lightbox" hidden>
  <button class="lb-close" aria-label="Close photo">×</button>
  <button class="lb-prev" aria-label="Previous photo">‹</button>
  <figure><img alt=""><figcaption></figcaption></figure>
  <button class="lb-next" aria-label="Next photo">›</button>
</div>
<script src="/assets/site.js" defer></script>
</body>
</html>
"""
    return localize(page, url_path)


def write(url_path, markup):
    rel = "index.html" if url_path == "/" else url_path.strip("/") + ".html"
    target = OUT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markup, encoding="utf-8")
    return rel


# ---------------------------------------------------------------- news
def fmt_date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return date(y, m, d).strftime("%b %-d, %Y")


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
            f'<p>{p["summary"]}</p>'
            f'<a class="more" href="{p["path"]}">Read more<span class="sr-only"> about {p["title"]}</span> →</a>'
            f'</div></article>')


def build_post(p, prev_p, next_p):
    share_url = quote(SITE + p["path"], safe="")
    share_title = quote(html.unescape(p["title"]), safe="")
    pager = []
    if prev_p:
        pager.append(f'<a class="pager-prev" href="{prev_p["path"]}"><span>« Previous</span>{prev_p["title"]}</a>')
    else:
        pager.append("<span></span>")
    if next_p:
        pager.append(f'<a class="pager-next" href="{next_p["path"]}"><span>Next »</span>{next_p["title"]}</a>')
    body = f"""<article class="wrap narrow post">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="/news-media/news">News</a> / <span>{fmt_date(p["date"])}</span></nav>
  <h1>{p["title"]}</h1>
  <p class="meta"><time datetime="{p["date"]}">{fmt_date(p["date"])}</time></p>
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
    return layout(p["path"], p["seo_title"], p["description"], body, p.get("image"), "article")


# ---------------------------------------------------------------- main
def main():
    if OUT.exists():
        keep_images = OUT / "images"
        for child in OUT.iterdir():
            if child != keep_images:
                shutil.rmtree(child) if child.is_dir() else child.unlink()
    OUT.mkdir(exist_ok=True)
    shutil.copytree(SRC / "assets", OUT / "assets", dirs_exist_ok=True)
    (OUT / ".nojekyll").write_text("")

    posts = load_posts()
    written = []

    # pages
    for f in sorted((SRC / "pages").rglob("*.html")):
        rel = f.relative_to(SRC / "pages").with_suffix("")
        url_path = "/" if str(rel) == "index" else "/" + str(rel)
        meta, body = read_fragment(f)
        body = body.replace("<!--LATEST_NEWS-->",
                            "".join(news_card(p) for p in posts[:6]))
        body = body.replace("<!--ALL_NEWS-->",
                            "".join(news_card(p, "h2") for p in posts))
        written.append((url_path, write(url_path, layout(url_path, meta["title"], meta["description"],
                                                          body, meta.get("image")))))

    # news posts (newest first; "previous" = older story, like the old site)
    for i, p in enumerate(posts):
        older = posts[i + 1] if i + 1 < len(posts) else None
        newer = posts[i - 1] if i > 0 else None
        written.append((p["path"], write(p["path"], build_post(p, older, newer))))

    # 404
    body404 = f"""<section class="wrap narrow page-head"><h1>Page not found</h1>
<p>Sorry, we couldn’t find that page. It may have moved when we updated our website.</p>
<p><a class="btn" href="{SITE_BASE}">Go to the home page</a> <a class="btn btn-ghost" href="{SITE_BASE}news-media/news">See all news</a></p></section>"""
    page404 = layout("/", "Page not found | CVCEC", "This page could not be found.", body404)
    # 404.html is served at any depth, so its links must be absolute
    page404 = page404.replace('href="assets/', f'href="{SITE_BASE}assets/').replace(
        'src="assets/', f'src="{SITE_BASE}assets/')
    page404 = re.sub(r'href="(?!https?:|mailto:|#|/)([^"]*)"', lambda m: f'href="{SITE_BASE}{m.group(1)}"', page404)
    page404 = page404.replace('href="./"', f'href="{SITE_BASE}"')
    (OUT / "404.html").write_text(page404, encoding="utf-8")

    # sitemap + robots
    today = date.today().isoformat()
    urls = "".join(f"<url><loc>{SITE}{p if p != '/' else '/'}</loc><lastmod>{today}</lastmod></url>"
                   for p, _ in written)
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    robots = "User-agent: *\nDisallow: /\n" if PREVIEW else f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n"
    (OUT / "robots.txt").write_text(robots)

    # image manifest for the copy workflow
    manifest = "".join(f"{url} {name}\n" for name, url in sorted(images.items()))
    (ROOT / "images.txt").write_text(manifest)
    print(f"Built {len(written)} pages, {len(images)} images referenced"
          f"{' (preview)' if PREVIEW else ''}{' (remote images)' if REMOTE_IMAGES else ''}.")


if __name__ == "__main__":
    main()
