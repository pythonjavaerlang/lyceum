"""Verify the built lyceum site: SEO tags, relative links, fragments, assets."""
from __future__ import annotations

import re
import sys
from pathlib import Path

DIST = Path(__file__).resolve().parent / "dist"
errors = []

full_pages = [p for p in DIST.rglob("index.html")]
fragments = [p for p in DIST.rglob("fragment.html")]
print(f"full pages: {len(full_pages)}   fragments: {len(fragments)}")

# 1. Each full page must have SEO essentials.
required = ['<title>', 'rel="canonical"', 'property="og:image"', 'name="description"', 'htmx.org']
for p in full_pages:
    html = p.read_text(encoding="utf-8")
    for r in required:
        if r not in html:
            errors.append(f"{p.relative_to(DIST)} missing {r}")

# 2. OG images referenced exist.
og_refs = set()
for p in full_pages:
    for m in re.finditer(r'property="og:image" content="https://[^/]+/(og/[^"]+)"', p.read_text(encoding="utf-8")):
        og_refs.add(m.group(1))
missing_og = [r for r in og_refs if not (DIST / r).exists()]
print(f"og images referenced: {len(og_refs)}, missing: {len(missing_og)}")
errors += [f"missing og {r}" for r in missing_og]

# 3. Links/assets resolve (relative), skip external + in-page anchors.
def is_ext(u): return u.startswith(("http://", "https://", "//", "mailto:", "tel:", "data:", "#"))
link_re = re.compile(r'(?:href|src|hx-get)="([^"]+)"')
script_re = re.compile(r"<script\b.*?</script>", re.S | re.I)
broken = {}
for p in full_pages + fragments:
    html = script_re.sub("", p.read_text(encoding="utf-8"))
    for m in link_re.finditer(html):
        u = m.group(1)
        if is_ext(u):
            continue
        clean = u.split("#")[0].split("?")[0]
        if not clean or "{{" in clean:
            continue
        target = (p.parent / clean).resolve()
        if clean.endswith("/"):
            ok = (target / "index.html").exists()
        elif target.suffix:
            ok = target.exists()
        else:
            ok = (target / "index.html").exists() or target.exists()
        if not ok:
            broken.setdefault(u, []).append(str(p.relative_to(DIST)))
print(f"broken internal links/assets: {len(broken)}")
for u, where in list(broken.items())[:30]:
    errors.append(f"broken {u} (e.g. {where[0]})")

# 4. sitemap + robots + pages files.
for f in ("sitemap.xml", "robots.txt", ".nojekyll", "CNAME"):
    if not (DIST / f).exists():
        errors.append(f"missing {f}")
print("sitemap/robots/.nojekyll/CNAME:",
      all((DIST / f).exists() for f in ("sitemap.xml", "robots.txt", ".nojekyll", "CNAME")))

print("\n=== RESULT ===")
if errors:
    print(f"{len(errors)} issue(s):")
    for e in errors[:50]:
        print("  -", e)
    sys.exit(1)
print("ALL CHECKS PASSED")
