"""SEO <head> block rendering: title, description, canonical, Open Graph,
Twitter Card, robots, and JSON-LD structured data — all Ukrainian-aware."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from html import escape

from markupsafe import Markup

import config


@dataclass
class SeoMeta:
    title: str
    description: str
    canonical_url: str
    og_image: str | None = None
    og_image_alt: str | None = None
    og_type: str = "website"
    keywords: str = config.SEO_DEFAULT_KEYWORDS
    site_name: str = config.SITE_NAME
    robots: str = "index,follow"
    structured_data: list = field(default_factory=list)


def _abs(url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith(("http://", "https://")):
        return url
    return f"{config.BASE_URL}/{url.lstrip('/')}"


def _meta(name: str, content: str | None, *, prop: bool = False) -> str:
    if not content:
        return ""
    attr = "property" if prop else "name"
    return f'<meta {attr}="{escape(name)}" content="{escape(content)}">'


def organization_schema() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "EducationalOrganization",
        "name": config.SITE_NAME,
        "url": config.BASE_URL,
        "sameAs": list(getattr(config, "SOCIAL_LINKS", [])),
    }


def website_schema() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": config.SITE_NAME,
        "url": config.BASE_URL,
        "inLanguage": config.LANG,
    }


def seo_head(meta: SeoMeta) -> str:
    og_image_abs = _abs(meta.og_image)
    parts: list[str] = []
    parts.append(f"<title>{escape(meta.title)}</title>")
    parts.append(_meta("description", meta.description))
    parts.append(_meta("keywords", meta.keywords))
    parts.append(f'<link rel="canonical" href="{escape(meta.canonical_url)}">')
    if meta.robots and meta.robots != "index,follow":
        parts.append(_meta("robots", meta.robots))

    # Open Graph
    parts.append(_meta("og:locale", "uk_UA", prop=True))
    parts.append(_meta("og:type", meta.og_type, prop=True))
    parts.append(_meta("og:title", meta.title, prop=True))
    parts.append(_meta("og:description", meta.description, prop=True))
    parts.append(_meta("og:url", meta.canonical_url, prop=True))
    parts.append(_meta("og:site_name", meta.site_name, prop=True))
    if og_image_abs:
        parts.append(_meta("og:image", og_image_abs, prop=True))
        parts.append(_meta("og:image:secure_url", og_image_abs, prop=True))
        parts.append(_meta("og:image:width", str(config.OG_WIDTH), prop=True))
        parts.append(_meta("og:image:height", str(config.OG_HEIGHT), prop=True))
        parts.append(_meta("og:image:type", "image/jpeg", prop=True))
        parts.append(_meta("og:image:alt", meta.og_image_alt or meta.title, prop=True))

    # Twitter
    parts.append(_meta("twitter:card", "summary_large_image"))
    parts.append(_meta("twitter:title", meta.title))
    parts.append(_meta("twitter:description", meta.description))
    if og_image_abs:
        parts.append(_meta("twitter:image", og_image_abs))
        parts.append(_meta("twitter:image:alt", meta.og_image_alt or meta.title))

    # JSON-LD
    for block in meta.structured_data:
        payload = json.dumps(block, ensure_ascii=False, separators=(",", ":"))
        payload = payload.replace("</", "<\\/")
        parts.append(f'<script type="application/ld+json">{payload}</script>')

    return Markup("\n    ".join(p for p in parts if p))
