# coding=utf-8
"""Static site configuration for the Lyceum site."""
from __future__ import annotations

SITE_DOMAIN = "lyceum.cpbi.info"
BASE_URL = "https://lyceum.cpbi.info"
SITE_NAME = "Чернівецький ліцей іноземних мов, комп’ютерних наук та інформаційних технологій"
SITE_SHORT = "Чернівецький ліцей"
LANG = "uk"

SEO_DEFAULT_DESCRIPTION = (
    "Чернівецький ліцей іноземних мов, комп’ютерних наук та інформаційних "
    "технологій — приватний заклад освіти І–ІІІ ступенів з дошкільним "
    "підрозділом. Вступ, освітні програми, інформаційна відкритість, табір."
)
SEO_DEFAULT_KEYWORDS = (
    "ліцей, Чернівці, іноземні мови, комп’ютерні науки, інформаційні технології, "
    "приватна школа, вступ, дошкільний підрозділ, освітній проект"
)

OG_WIDTH = 1200
OG_HEIGHT = 630

SOCIAL_LINKS = [
    "https://www.facebook.com/privatelyceum/",
    "https://www.instagram.com/chernivtsilyceum/",
]

GA_MEASUREMENT_ID = ""  # none for lyceum
