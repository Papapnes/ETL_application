import ast
from copy import deepcopy
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from tests.support import signed_in_app
from ui.i18n import CATALOG, LANGUAGES, display_rejections, fields, translate
from ui.layout import LINKEDIN_URL, layout_css

APP = Path(__file__).resolve().parents[1] / "app.py"


def assert_platform_heading(app, language, expected):
    headings = [item.proto.body for item in app.get("html") if 'id="platform-title-' in item.proto.body]
    assert len(headings) == 2
    for heading in headings:
        assert f">{expected}</h1>" in heading
        assert f'lang="{language}"' in heading
        assert 'translate="no"' in heading
        assert 'class="notranslate"' in heading
    assert any(f'id="platform-title-main-{language}"' in heading for heading in headings)
    assert any(
        f'id="platform-title-sidebar-{language}"' in item.proto.body for item in app.sidebar.get("html")
    )


def test_public_account_screens_use_only_selected_brand():
    app = AppTest.from_file(APP, default_timeout=30).run()
    for language, expected in [
        ("en", "DataFlow Studio"),
        ("ar", "منصّة معالجة وتحويل البيانات"),
        ("fr", "Plateforme de traitement des données"),
    ]:
        app.selectbox(key="language").set_value(language).run()
        for mode in ["Connexion", "Inscription"]:
            app.selectbox(key="auth_mode").set_value(mode).run()
            assert not app.exception
            assert_platform_heading(app, language, expected)


def click(app, label):
    next(button for button in app.button if button.label == label).click().run()
    assert not app.exception


def test_catalog_is_complete_and_placeholders_match():
    for source, localized in CATALOG.items():
        assert set(localized) == set(LANGUAGES)
        for text in localized.values():
            assert text.strip()
            assert fields(text) == fields(source), source
    allowed = {"{v0} · {v1} UTC · {v2}"}
    for node in ast.walk(ast.parse(APP.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "t":
            if node.args and isinstance(node.args[0], ast.Constant):
                assert node.args[0].value in CATALOG or node.args[0].value in allowed


@pytest.mark.parametrize("language", ["en", "ar"])
def test_localized_workflow_and_language_switch_preserve_results(language):
    app = signed_in_app(APP, default_timeout=30).run()
    app.selectbox(key="language").set_value(language).run()
    assert not app.exception
    assert_platform_heading(app, language, translate("Plateforme de traitement des données", language))
    click(app, translate("Explorer la démonstration", language))
    click(app, translate("Appliquer et contrôler", language))
    assert [m.value for m in app.metric] == ["12", "8", "4", "1"]
    assert app.metric[1].label == translate("Lignes valides", language)
    snapshot = deepcopy(app.session_state["result"])
    app.selectbox(key="language").set_value("fr").run()
    assert not app.exception
    assert app.session_state["result"]["recipe"] == snapshot["recipe"]
    pd.testing.assert_frame_equal(app.session_state["result"]["accepted"], snapshot["accepted"])
    app.selectbox(key="language").set_value(language).run()
    click(app, translate("Passer à l’export", language))
    app.checkbox[0].check().run()
    click(app, translate("Générer le dossier ZIP", language))
    assert app.session_state["package"][1][:2] == b"PK"
    app.radio(key="stage").set_value("Journal").run()
    assert not app.exception
    assert any(item.value == translate("Journal des traitements", language) for item in app.title)
    click(app, translate("Vider la session", language))
    assert app.session_state["language"] == language


@pytest.mark.parametrize("language", ["fr", "en", "ar"])
def test_contact_available_even_on_empty_pages(language):
    app = signed_in_app(APP, default_timeout=30)
    app.session_state["language"] = language
    app.run()
    for stage in ["Vue d’ensemble", "1 · Importer", "2 · Préparer", "4 · Exporter"]:
        app.radio(key="stage").set_value(stage).run()
        assert not app.exception
        assert any("Abdelkader Bouzourine" in item.value for item in app.markdown)
        assert any(item.value == translate("Consultant en BI", language) for item in app.caption)
        links = app.get("link_button")
        assert len(links) == 1
        assert links[0].proto.url == LINKEDIN_URL


def test_diagnostics_translated_without_mutating_source_data():
    original = pd.DataFrame(
        {
            "client": ["Client FR"],
            "_etl_issues": ["montant : conversion décimal impossible ; client : valeur obligatoire"],
        }
    )
    displayed = display_rejections(original, "en")
    assert displayed.iloc[0]["_etl_issues"] == "montant: cannot convert to Decimal ; client: required value"
    assert original.iloc[0]["_etl_issues"].startswith("montant : conversion")
    assert displayed.iloc[0]["client"] == "Client FR"
    assert translate("Enregistrement 4 : 3 champs au lieu de 2.", "en") == "Record 4: 3 fields instead of 2."
    assert translate("Aucune ligne valide à exporter.", "ar") == "لا توجد صفوف صالحة للتصدير."


def test_rtl_does_not_reverse_numeric_data_or_pin_footer_over_controls():
    css = layout_css("ar")
    assert "direction: rtl" in css
    assert "direction: ltr" in css
    assert "100dvh" in css
    assert "position: fixed" not in css
    assert "direction: rtl" not in layout_css("en")


def test_platform_name_switches_even_with_an_older_loaded_catalog(monkeypatch):
    import streamlit as st

    # A live server may still hold the catalogue imported before the rename.
    monkeypatch.delitem(CATALOG, "Plateforme de traitement des données")
    page_titles = []
    original = st.set_page_config

    def capture_page_config(*args, **kwargs):
        page_titles.append(kwargs.get("page_title"))
        return original(*args, **kwargs)

    monkeypatch.setattr(st, "set_page_config", capture_page_config)
    app = signed_in_app(APP, default_timeout=30).run()
    for language, expected in [
        ("en", "DataFlow Studio"),
        ("ar", "منصّة معالجة وتحويل البيانات"),
        ("fr", "Plateforme de traitement des données"),
    ]:
        app.selectbox(key="language").set_value(language).run()
        assert not app.exception
        assert_platform_heading(app, language, expected)
        assert page_titles[-1] == expected
