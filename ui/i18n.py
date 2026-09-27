"""Pure translation helpers; no changes to sources or persisted recipe values."""

import re
from string import Formatter

from ui.account_catalog import MESSAGES as ACCOUNT_MESSAGES
from ui.catalog import CATALOG
from ui.errors import MESSAGES

LANGUAGES = {"fr": "FR · Français", "en": "EN · English", "ar": "AR · العربية"}
for row in (MESSAGES.strip() + "\n" + ACCOUNT_MESSAGES.strip()).splitlines():
    fr, en, ar = row.split("|||")
    CATALOG[fr] = {"fr": fr, "en": en, "ar": ar}


def fields(text):
    return {name for _, name, _, _ in Formatter().parse(text) if name is not None}


def _pattern(template):
    parts = []
    for literal, name, _, _ in Formatter().parse(template):
        parts.append(re.escape(literal))
        if name is not None:
            parts.append(f"(?P<{name}>.*?)")
    return re.compile("^" + "".join(parts) + "$", re.DOTALL)


TEMPLATES = [(text, _pattern(text)) for text in CATALOG if fields(text)]


def translate(text, language="fr", **values):
    """Translate UI text or a known engine diagnostic, preserving dynamic values."""
    language = language if language in LANGUAGES else "fr"
    if text in CATALOG:
        translated = CATALOG[text][language]
        return translated.format(**values) if values else translated
    if not values and language != "fr":
        for template, pattern in TEMPLATES:
            match = pattern.fullmatch(text)
            if match:
                params = match.groupdict()
                if template == "{v0} : conversion {v1} impossible":
                    params["v1"] = translate(params["v1"].capitalize(), language)
                elif template == "{v0} : hors borne {v1}":
                    params["v1"] = translate(params["v1"].capitalize(), language)
                return CATALOG[template][language].format(**params)
    return text.format(**values) if values else text


def display_metadata(frame, language):
    """Use only for application-owned metadata tables, never business data headers."""
    return frame.rename(columns=lambda c: translate(str(c), language))


def display_rejections(frame, language):
    """Translate reasons in a display copy. Raw data and exports remain untouched."""
    frame = frame.copy()
    if "_etl_issues" in frame:
        frame["_etl_issues"] = frame["_etl_issues"].map(
            lambda value: " ; ".join(translate(part, language) for part in value.split(" ; "))
        )
    return frame
