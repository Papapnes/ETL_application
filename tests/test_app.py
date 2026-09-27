from pathlib import Path

from tests.support import signed_in_app

APP = Path(__file__).resolve().parents[1] / "app.py"


def button(app, text):
    return next(b for b in app.button if b.label == text)


def test_demo_prepare_review_export_and_reset():
    app = signed_in_app(APP, default_timeout=30).run()
    assert not app.exception
    app.button(key="demo_start").click().run()
    assert not app.exception
    button(app, "Appliquer et contrôler").click().run()
    assert not app.exception
    assert [m.value for m in app.metric] == ["12", "8", "4", "1"]
    button(app, "Passer à l’export").click().run()
    assert not app.exception
    assert button(app, "Générer le dossier ZIP").disabled
    app.checkbox[0].check().run()
    button(app, "Générer le dossier ZIP").click().run()
    assert not app.exception
    assert app.session_state["package"][1][:2] == b"PK"
    app.selectbox[0].select("Parquet").run()
    assert app.session_state["package"] is None
    button(app, "Vider la session").click().run()
    assert not app.exception
    assert app.session_state["datasets"] == []


def test_navigation_without_data_does_not_crash():
    app = signed_in_app(APP, default_timeout=30).run()
    for stage in ["1 · Importer", "2 · Préparer", "3 · Contrôler", "4 · Exporter", "Journal"]:
        app.radio(key="stage").set_value(stage).run()
        assert not app.exception


def test_batch_selection_survives_navigation():
    from etl.engine import default_recipe, extract

    app = signed_in_app(APP, default_timeout=30)
    sources = extract("a.csv", b"id,n\n001,2") + extract("b.csv", b"id,n\n002,3")
    app.session_state["datasets"] = sources
    app.session_state["recipe"] = default_recipe(["id", "n"])
    app.session_state["stage"] = "2 · Préparer"
    app.run()
    app.multiselect[0].set_value([d.key for d in sources]).run()
    button(app, "Appliquer et contrôler").click().run()
    assert not app.exception
    assert app.metric[0].value == "2"
    button(app, "Ajuster la recette").click().run()
    assert not app.exception
    assert len(app.multiselect[0].value) == 2
