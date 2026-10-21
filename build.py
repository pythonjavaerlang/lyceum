# coding=utf-8
"""Lyceum static site generator.

Extracts the inner content of the existing builder-exported HTML pages, wraps it
in a shared Jinja2 base (SEO + htmx + mobile nav), rewrites asset/page links to
relative/clean URLs, replaces the dynamic gallery with a static grid, and emits:
  dist/<slug>/index.html      full page (extends base)
  dist/<slug>/fragment.html   htmx fragment (content only, for hx-get)
plus sitemap.xml, robots.txt, .nojekyll, CNAME and per-page OG images.
"""
from __future__ import annotations

import datetime
import re
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

import config
from og_image import generate_og_image
from seo import SeoMeta, seo_head, organization_schema, website_schema

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "content" / "pages"          # self-contained source HTML (committed)
DIST = ROOT / "dist"
TEMPLATES = ROOT / "templates"
MEDIA_URL = "/media/"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES)),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True, lstrip_blocks=True,
)
env.globals.update(
    seo_head=seo_head, site_name=config.SITE_NAME, site_short=config.SITE_SHORT,
    media_url=MEDIA_URL,
)

# source file -> (slug, Ukrainian title)
PAGES = {
    "index.html":            ("",                 config.SITE_NAME),
    "about.html":            ("about",            "Про ліцей"),
    "enrolling.html":        ("enrolling",        "Вступ до ліцею"),
    "admission_rules.html":  ("admission-rules",  "Правила прийому"),
    "transparency.html":     ("transparency",     "Прозорість та інформаційна відкритість"),
    "regulations.html":      ("regulations",      "Статут закладу освіти"),
    "structure.html":        ("structure",        "Структура та органи управління"),
    "student_groups.html":   ("student-groups",   "Учнівські гуртки"),
    "camp.html":             ("camp",             "Відпочинково-оздоровчий комплекс (табір)"),
    "edu_prg.html":          ("edu-prg",          "Освітній проєкт"),
    "services.html":         ("services",         "Ми пропонуємо"),
    "rules.html":            ("rules",            "Основні принципи навчання"),
    "board.html":            ("board",            "Керівництво ліцею"),
    "building.html":         ("building",         "Матеріально-технічна база"),
    "ancillary.html":        ("ancillary",        "Інша інформація"),
    "orphans.html":          ("orphans",          "Середня освіта для дітей-переселенців"),
    "helping-orphans.html":  ("helping-orphans",  "Безкоштовна освіта для соціально незахищених"),
    "landing1.html":         ("landing",          "Освітній проєкт"),
}

# Map original page filenames -> clean slugs for inter-page link rewriting.
FILE_TO_SLUG = {src: slug for src, (slug, _) in PAGES.items()}

_sitemap: list[str] = []

# Tally.so enrollment form embed (replace TALLY_ENROLL_ID after creating the form).
TALLY_ENROLL_ID = "PRd01V"
TALLY_EMBED = f"""
<div class="style2 container default"><div class="wrapper"><div class="inner">
  <h2 class="style2">Подати заявку на вступ</h2>
  <iframe data-tally-src="https://tally.so/embed/{TALLY_ENROLL_ID}?alignLeft=1&amp;hideTitle=1&amp;transparentBackground=1&amp;dynamicHeight=1"
          loading="lazy" width="100%" height="600" frameborder="0" title="Заявка на вступ до ліцею"></iframe>
  <noscript><p>Увімкніть JavaScript або перейдіть за
     <a href="https://tally.so/r/{TALLY_ENROLL_ID}">посиланням на форму</a>.</p></noscript>
  <script>(function(){{var d=document,w="https://tally.so/widgets/embed.js",v=function(){{typeof Tally!=="undefined"?Tally.loadEmbeds():d.querySelectorAll("iframe[data-tally-src]:not([src])").forEach(function(e){{e.src=e.dataset.tallySrc;}});}};if(typeof Tally!=="undefined"){{v();}}else if(!d.querySelector('script[src="'+w+'"]')){{var s=d.createElement("script");s.src=w;s.onload=v;s.onerror=v;d.body.appendChild(s);}}}})();</script>
</div></div></div>
"""

INNER_OPEN = re.compile(r'<div id="main">\s*<div class="inner">', re.S)


def extract_inner(src_html: str) -> str:
    m = INNER_OPEN.search(src_html)
    start = m.end()
    tail = src_html.rfind("</body>")
    body = src_html[start:tail]
    # trim the trailing wrapper closes we captured after the content
    body = re.sub(r'(\s*</div>\s*){1,3}\s*$', "", body)
    return body.strip()


def canonical(slug: str) -> str:
    p = "/" + slug.strip("/")
    if p != "/":
        p += "/"
    return f"{config.BASE_URL}{p}"


# ── Link / asset rewriting ────────────────────────────────────────────────────
_PAGE_LINK = re.compile(r'href="([a-z0-9_\-]+)\.html(#[\w-]+)?"', re.I)
_ASSET_IMG = re.compile(r'(src|href)="(assets/images/[^"]+)"')
_LOCAL_ASSET = re.compile(r'(src|href)="([\w\-]+\.(?:png|jpg|jpeg|gif|svg|pdf))"')
_CSS_LINK = re.compile(r'<link[^>]+href="public\.css"[^>]*>', re.I)
_INLINE_STYLE = re.compile(r'\s+style="[^"]*"', re.I)
_CONTACTS_BLOCK = re.compile(
    r'<div id="container07"[^>]*>.*?</div>\s*</div>\s*</div>', re.S)
_GALLERY_BLOCK = re.compile(
    r'<a href="/gallery/[^"]*">\s*<img[^>]*>\s*</a>', re.S)


def rewrite(body: str, gallery_imgs: list[str]) -> str:
    # 1. Drop any builder stylesheet link + all builder inline style attributes.
    body = _CSS_LINK.sub("", body)
    body = _INLINE_STYLE.sub("", body)
    # 1b. Contacts live in the shared footer now — remove the duplicate block,
    #     and point any "#container07" buttons at the footer contacts instead.
    body = _CONTACTS_BLOCK.sub("", body)
    body = body.replace('href="#container07"', 'href="#site-contacts"')
    # 2. assets/images/x -> /media/images/x
    body = _ASSET_IMG.sub(lambda m: f'{m.group(1)}="{MEDIA_URL}' + m.group(2)[len("assets/"):] + '"', body)
    # 3. bare local asset files (img068.png, statute.pdf, ...) -> /media/x
    body = _LOCAL_ASSET.sub(lambda m: f'{m.group(1)}="{MEDIA_URL}{m.group(2)}"', body)
    # 4. inter-page .html links -> clean slug + htmx attributes
    def page_link(m):
        fname = m.group(1) + ".html"
        anchor = m.group(2) or ""
        slug = FILE_TO_SLUG.get(fname)
        if slug is None:
            return m.group(0)  # unknown; leave as-is
        href = "/" + (slug + "/" if slug else "")
        frag = f"/{slug}/fragment.html" if slug else "/fragment.html"
        return (f'href="{href}{anchor}" hx-get="{frag}" hx-target="#content" '
                f'hx-swap="innerHTML" hx-push-url="{href}"')
    body = _PAGE_LINK.sub(page_link, body)
    # 5. populate the gallery container with a static grid of bundled images
    if gallery_imgs:
        cards = "".join(
            f'<a href="{MEDIA_URL}images/{img}"><img src="{MEDIA_URL}images/{img}" '
            f'alt="Фото ліцею" loading="lazy" width="153" height="100"></a>'
            for img in gallery_imgs)
        # strip any leftover old gallery anchors, then fill the gallery container
        body = _GALLERY_BLOCK.sub("", body)
        if re.search(r'<div[^>]*class="[^"]*gallery-link[^"]*"[^>]*>', body):
            body = re.sub(r'(<div[^>]*class="[^"]*gallery-link[^"]*"[^>]*>)',
                          r"\1" + cards, body, count=1)
    return body


def strip_text(html: str, limit: int = 160) -> str:
    t = re.sub(r"<[^>]+>", " ", html)
    t = re.sub(r"&[a-z]+;", " ", t)
    t = " ".join(t.split())
    return (t[: limit - 1] + "\u2026") if len(t) > limit else t


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    gallery_imgs = sorted(
        p.name for p in (ROOT / "assets" / "media" / "images").glob("*")
        if p.suffix.lower() in {".jpg", ".jpeg", ".png"} and p.name != "logo.jpg"
    )

    for src_file, (slug, title) in PAGES.items():
        src_path = SRC / src_file
        if not src_path.exists():
            print(f"  skip missing {src_file}")
            continue
        raw = src_path.read_text(encoding="utf-8", errors="replace")
        body = rewrite(extract_inner(raw), gallery_imgs)

        # Enrolling page: append a Tally.so application form embed.
        if slug == "enrolling":
            body += TALLY_EMBED

        desc = strip_text(body) or config.SEO_DEFAULT_DESCRIPTION
        og_rel = generate_og_image(slug or "index", title, DIST,
                                   subtitle=config.SITE_SHORT)
        structured = [organization_schema(), website_schema()] if not slug else []
        meta = SeoMeta(
            title=title if not slug else f"{title} — {config.SITE_SHORT}",
            description=desc,
            canonical_url=canonical(slug),
            og_image="/" + og_rel,
            og_image_alt=title,
            og_type="website" if not slug else "article",
            structured_data=structured,
        )

        full = env.get_template("base.html").render(meta=meta, page_content=body)
        frag = env.get_template("fragment.html").render(meta=meta, page_content=body)
        write(slug, "index.html", full, sitemap=True)
        write(slug, "fragment.html", frag, sitemap=False)

    copy_media()
    write_pages_files()
    write_sitemap()
    write_robots()
    print(f"Built {len(_sitemap)} pages into {DIST}")


def _relativise(html: str, depth: int) -> str:
    prefix = "../" * depth if depth > 0 else "./"
    return re.sub(r'((?:href|src|hx-get|hx-push-url)=")(/(?!/)[^"]*)(")',
                  lambda m: f"{m.group(1)}{prefix}{m.group(2)[1:]}{m.group(3)}", html)


def write(slug: str, filename: str, html: str, *, sitemap: bool):
    rel = slug.strip("/")
    depth = len([p for p in rel.split("/") if p]) if rel else 0
    html = _relativise(html, depth)
    target = DIST / rel / filename if rel else DIST / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
    if sitemap:
        _sitemap.append(canonical(slug))


def copy_media():
    bundled = ROOT / "assets" / "media"
    if bundled.exists():
        shutil.copytree(bundled, DIST / "media", dirs_exist_ok=True)
    # The builder stylesheet is fully replaced by site.css — don't ship it.
    stale = DIST / "media" / "public.css"
    if stale.exists():
        stale.unlink()


def write_pages_files():
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    (DIST / "CNAME").write_text(config.SITE_DOMAIN + "\n", encoding="utf-8")


def write_sitemap():
    today = datetime.date.today().isoformat()
    urls = "\n".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>"
                     for u in sorted(set(_sitemap)))
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n</urlset>\n", encoding="utf-8")


def write_robots():
    (DIST / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {config.BASE_URL}/sitemap.xml\n",
        encoding="utf-8")


if __name__ == "__main__":
    build()
