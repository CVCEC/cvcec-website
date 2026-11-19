# cvcec.org — website of the Canada Vietnam Cultural & Educational Council

Static website for **www.cvcec.org**, rebuilt from the earlier Webador site with the same page addresses (so old links, Google results and shared posts keep working). It is hosted free on GitHub Pages from the `docs/` folder.

## How it is organized

| Folder / file | What it holds |
|---|---|
| `src/pages/` | One file per page. The part above `---` is the page title and description; below is the page content. |
| `src/posts/` | One file per news release (the file name is the old Webador address, e.g. `3348082_viet-youth-…`). |
| `src/assets/` | Styles (`site.css`), menu/gallery script (`site.js`), favicon. |
| `build.py` | Turns `src/` into the finished website in `docs/`. |
| `docs/` | The finished website that GitHub Pages serves. Do not edit by hand — run the build. |
| `images.txt` | Where each image was copied from. The **Copy images** workflow downloads them into `docs/images/`. |

## Editing

1. Edit a file in `src/pages/` or `src/posts/` (or add a new post: copy an existing post file, change the number/name, title, date and text).
2. Run `python3 build.py` (no extra software needed).
3. Commit and push. GitHub Pages updates the site within a minute or two.

Preview builds (not indexed by Google): `PREVIEW=1 SITE_BASE=/cvcec-website/ python3 build.py`.

## Moving the domain from Webador

1. In this repository: **Settings → Pages → Custom domain** → `www.cvcec.org` → Save (this creates a `docs/CNAME` file).
2. At Nhân Hòa (DNS for cvcec.org): change only the website records —
   - `@` A records → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `www` → CNAME `cvcec.github.io`
   - **Do not touch** MX (Google Workspace email), TXT verification records, or the `duhoccanada`, `vietnamday`, `truongtiengvietcuaem` subdomains.
3. When the certificate is ready, tick **Enforce HTTPS**.
4. Rebuild without the preview flag (`python3 build.py`) so search engines can index the site, and submit `https://www.cvcec.org/sitemap.xml` in Google Search Console.
5. Keep Webador for a week, check everything, then cancel it.
