from __future__ import annotations

import hashlib
from copy import deepcopy
from functools import partial
from html import escape
from uuid import uuid4

import pandas as pd
import streamlit as st

from accounts.errors import DatabaseError
from accounts.service import AccountError
from etl.demo import CSV, demo
from etl.engine import (
    MAX_BYTES,
    SUPPORTED,
    TYPES,
    ETLError,
    bundle,
    default_recipe,
    extract,
    json_bytes,
    load_recipe,
    profile,
    validate_recipe,
)
from ui.accounts import (
    account_database_error,
    account_page,
    admin_page,
    auth_page,
    current_user,
    service,
    sign_out,
)
from ui.i18n import LANGUAGES, display_metadata, display_rejections, translate
from ui.layout import render_contact, render_styles

t = partial(translate, language=st.session_state.get("language", "fr"))

# Brand names live in the entry point so a running server cannot use a stale
# imported catalogue and silently fall back to the French name after a rename.
PLATFORM_NAMES = {
    "fr": "Plateforme de traitement des données",
    "en": "DataFlow Studio",
    "ar": "منصّة معالجة وتحويل البيانات",
}
platform_name = PLATFORM_NAMES.get(st.session_state.get("language", "fr"), PLATFORM_NAMES["fr"])

st.set_page_config(page_title=platform_name, page_icon=":material/hub:", layout="wide")
DEFAULTS = dict(
    datasets=[],
    recipe=None,
    result=None,
    history=[],
    reviewed=set(),
    stage="Vue d’ensemble",
    revision=0,
    import_errors=[],
    demo=False,
    package=None,
    selected_keys=[],
)
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = deepcopy(value)
ss = st.session_state
ss.setdefault("language", "fr")
if "pending_stage" in ss:
    ss.stage = ss.pop("pending_stage")
user = current_user()
# The ETL workspace must remain usable when the optional account backend is
# paused or temporarily unavailable.
account_service = service()
account_db_error = account_database_error()
quota = None
if user and account_service is not None:
    try:
        quota = account_service.quota(ss.auth_token)
    except DatabaseError as exc:
        account_db_error = str(exc)
STAGES = [
    "Vue d’ensemble",
    "1 · Importer",
    "2 · Préparer",
    "3 · Contrôler",
    "4 · Exporter",
    "Journal",
    "Mon compte",
]
if user and user["role"] == "ADMIN":
    STAGES.append("Administration")
if ss.stage not in STAGES:
    ss.stage = "Vue d’ensemble"


def go(stage):
    ss.stage = stage


def reset():
    for key, value in DEFAULTS.items():
        ss[key] = deepcopy(value)
    ss.revision += 1
    for key in list(ss):
        if key.startswith(("upload_", "review_", "selection_", "rules_", "recipe_")):
            del ss[key]


def demo_start():
    ss.datasets, ss.recipe = demo()
    ss.recipe["name"] = t(ss.recipe["name"])
    ss.selected_keys = [d.key for d in ss.datasets]
    ss.result, ss.package, ss.import_errors = (None, None, [])
    ss.reviewed, ss.demo = (set(), True)
    ss.revision += 1
    ss.stage = "2 · Préparer"


def n(value):
    return f"{value:,}".replace(",", " ")


def render_platform_title(language, location="main"):
    # Native st.title cannot set lang/translate. Preserve the exact localized
    # brand and replace the DOM subtree when the selected language changes.
    language = language if language in PLATFORM_NAMES else "fr"
    direction = "rtl" if language == "ar" else "ltr"
    with st.container(key=f"platform_title_{location}_{language}"):
        st.html(
            f'<h1 id="platform-title-{location}-{language}" lang="{language}" '
            f'dir="{direction}" translate="no" class="notranslate">'
            f"{escape(PLATFORM_NAMES[language])}</h1>"
        )


def require_data():
    if not ss.datasets:
        st.info(t("Importez vos fichiers ou ouvrez la démonstration pour commencer."))
        st.button(t("Importer des fichiers"), on_click=go, args=("1 · Importer",), type="primary")
        st.stop()


with st.sidebar:
    with st.container(key="sidebar_shell"):
        with st.container():
            title_slot = st.empty()
            selected_language = st.selectbox(
                "Langue / Language / اللغة",
                list(LANGUAGES),
                format_func=LANGUAGES.get,
                key="language",
            )
            platform_name = PLATFORM_NAMES[selected_language]
            t = partial(translate, language=selected_language)
            with title_slot.container():
                render_platform_title(selected_language, location="sidebar")
            st.set_page_config(page_title=platform_name)
            st.caption(t("VOTRE ESPACE DE PRÉPARATION"))
            if user and quota is not None:
                st.radio(t("Parcours"), STAGES, key="stage", label_visibility="collapsed", format_func=t)
                st.caption(user["full_name"] + " · " + user["role"])
                st.caption(
                    t("Accès illimité")
                    if quota["limit"] is None
                    else t("Utilisations restantes") + f" : {quota['remaining']} / {quota['limit']}"
                )
                st.button(t("Se déconnecter"), on_click=sign_out, key="logout")
            st.badge(t("Traitement des données"), icon=":material/settings:", color="green")
            st.caption(
                t(
                    "Les fichiers sont traités sur le serveur de l’application. Téléchargez vos résultats et vos recettes pour les conserver."
                )
            )
            st.caption(t("Version 0.2 · Édition de démonstration"))
            if ss.datasets:
                st.button(t("Vider la session"), on_click=reset, icon=":material/restart_alt:")
        render_contact(ss.language)
render_styles(ss.language)
if not user and not account_db_error:
    render_platform_title(selected_language)
    auth_page(ss.language)
    st.stop()
if not user and account_db_error:
    render_platform_title(selected_language)
    st.info(
        "Mode traitement sans compte : importez et préparez vos fichiers. "
        "La connexion et les quotas seront disponibles dès le retour de la base des comptes."
    )
if ss.stage == "Mon compte":
    account_page(ss.language)
    st.stop()
if ss.stage == "Administration":
    admin_page(ss.language)
    st.stop()
if ss.demo:
    st.caption(t(":material/science: Mode démonstration · données fictives, aucune donnée client"))
if ss.stage == "Vue d’ensemble":
    st.badge(t("DE LA SOURCE À L’ANALYSE"), color="green")
    render_platform_title(selected_language)
    st.subheader(t("Des données prêtes.\nDes traitements reproductibles."))
    st.markdown(
        t(
            "Rassemblez vos fichiers, définissez vos règles et préparez des données traçables pour vos analyses."
        )
    )
    with st.container(horizontal=True):
        st.button(
            t("Importer mes fichiers"),
            type="primary",
            icon=":material/upload_file:",
            on_click=go,
            args=("1 · Importer",),
        )
        st.button(
            t("Explorer la démonstration"),
            icon=":material/play_arrow:",
            on_click=demo_start,
            key="demo_start",
        )
    st.space("medium")
    cols = st.columns(3)
    for col, icon, title, body in zip(
        cols,
        ["folder_open", "tune", "verified"],
        ["01  Rassembler", "02  Standardiser", "03  Livrer"],
        [
            "CSV, Excel, JSON, Parquet et tables PDF dans un seul espace.",
            "Des règles explicites et des recettes que vous pouvez réutiliser.",
            "Des données validées, une quarantaine et un rapport de traçabilité.",
        ],
    ):
        with col.container(border=True):
            st.subheader(f":material/{icon}: {t(title)}")
            st.write(t(body))
    left, right = st.columns([1.5, 1])
    with left.container(border=True):
        st.subheader(t("Une recette, plusieurs traitements"))
        st.write(
            t(
                "Prévisualisez les sources, choisissez les types de colonnes et contrôlez les valeurs obligatoires. Enregistrez ensuite votre recette JSON pour préparer les prochains fichiers de même structure."
            )
        )
        st.caption(t("Import → Préparation → Contrôle → Export"))
    with right.container(border=True):
        st.subheader(t("À savoir avant de commencer"))
        st.write(t("25 Mo par fichier · 20 fichiers par lot · 100 000 lignes par traitement."))
        st.caption(
            t(
                "PDF : tables textuelles avec vérification obligatoire. OCR et surveillance automatique de dossier non inclus."
            )
        )
elif ss.stage == "1 · Importer":
    st.caption(t("ÉTAPE 01 / 04"))
    st.title(t("Rassemblez vos sources"))
    st.write(t("Importez plusieurs fichiers. Vous pourrez sélectionner les feuilles ou tables à préparer."))
    uploads = st.file_uploader(
        t("Déposez vos fichiers"),
        type=SUPPORTED,
        accept_multiple_files=True,
        key=f"upload_files_{ss.revision}",
    )
    with st.expander(t("Paramètres de lecture"), icon=":material/settings:"):
        st.caption(
            t("Ces paramètres s’appliquent au lot importé. UTF-8 et détection du séparateur par défaut.")
        )
        a, b, c = st.columns(3)
        encoding = a.selectbox(
            t("Encodage texte"), ["utf-8-sig", "cp1252", "latin-1"], format_func=t, key="control_158"
        )
        sep = b.selectbox(
            t("Séparateur CSV / TXT"),
            ["Détecter", ";", ",", "Tabulation", "|"],
            format_func=t,
            key="control_159",
        )
        header_row = c.number_input(t("Ligne d’en-tête Excel"), 1, 100, 1, key="control_160")
        json_path = st.text_input(
            t("Chemin JSON vers la liste d’objets"),
            placeholder=t("Exemple : data.records"),
            key="control_161",
        )
    if st.button(t("Analyser les fichiers"), type="primary", disabled=not uploads, icon=":material/search:"):
        if len(uploads) > 20 or sum((u.size for u in uploads)) > 100 * 1024 * 1024:
            st.error(t("Limite du lot : 20 fichiers et 100 Mo au total."))
        else:
            options = dict(encoding=encoding, header_row=header_row, json_path=json_path)
            if sep != "Détecter":
                options["delimiter"] = "\t" if sep == "Tabulation" else sep
            datasets, failures, seen = ([], [], set())
            progress = st.progress(0, text=t("Lecture du lot…"))
            for i, uploaded in enumerate(uploads):
                try:
                    data = uploaded.getvalue()
                    fingerprint = hashlib.sha256(data).hexdigest()
                    if fingerprint in seen:
                        raise ETLError("Fichier identique déjà présent dans ce lot.")
                    if len(data) > MAX_BYTES:
                        raise ETLError("Fichier supérieur à 25 Mo.")
                    datasets.extend(extract(uploaded.name, data, options))
                    seen.add(fingerprint)
                except Exception as exc:
                    message = (
                        str(exc)
                        if isinstance(exc, ETLError)
                        else f"Lecture interrompue ({type(exc).__name__})."
                    )
                    failures.append({"Fichier": uploaded.name, "Motif": message})
                progress.progress(
                    (i + 1) / len(uploads), text=t("{v0} / {v1} fichiers analysés", v0=i + 1, v1=len(uploads))
                )
            ss.datasets, ss.import_errors = (datasets, failures)
            ss.recipe, ss.result, ss.package = (None, None, None)
            ss.reviewed, ss.demo = (set(), False)
            ss.revision += 1
            st.rerun()
    if ss.import_errors:
        st.error(
            t(
                "{v0} fichier(s) non importé(s). Corrigez-les ou poursuivez avec les tables disponibles.",
                v0=len(ss.import_errors),
            )
        )
        failures_view = pd.DataFrame(ss.import_errors)
        failures_view["Motif"] = failures_view["Motif"].map(t)
        st.dataframe(display_metadata(failures_view, ss.language), hide_index=True)
    if ss.datasets:
        st.success(t("{v0} table(s) disponible(s).", v0=len(ss.datasets)))
        st.dataframe(
            display_metadata(
                pd.DataFrame(
                    [
                        {
                            "Fichier": d.name,
                            "Table": d.table,
                            "Lignes": len(d.frame),
                            "Colonnes": len(d.frame.columns),
                            "Vérification": t("PDF à vérifier" if d.review_required else "Prête"),
                        }
                        for d in ss.datasets
                    ]
                ),
                ss.language,
            ),
            hide_index=True,
        )
        st.button(t("Préparer les données"), type="primary", on_click=go, args=("2 · Préparer",))
    else:
        st.download_button(
            t("Télécharger un CSV d’exemple"), CSV.encode("utf-8-sig"), "ventes_demo.csv", "text/csv"
        )
elif ss.stage == "2 · Préparer":
    require_data()
    st.caption(t("ÉTAPE 02 / 04"))
    st.title(t("Composez votre recette"))
    st.write(
        t(
            "Sélectionnez des tables de même structure. Les identifiants restent du texte tant que vous ne changez pas leur type."
        )
    )
    names = [d.key for d in ss.datasets]
    defaults = [key for key in ss.selected_keys if key in names] or names[:1]
    selected = st.multiselect(
        t("Tables à traiter ensemble"), names, default=defaults, key=f"selection_{ss.revision}"
    )
    ss.selected_keys = selected
    datasets = [d for d in ss.datasets if d.key in selected]
    if not datasets:
        st.info(t("Sélectionnez une table pour afficher l’aperçu."))
        st.stop()
    chosen = st.selectbox(t("Aperçu de la source"), selected, key="control_239")
    source = next((d for d in datasets if d.key == chosen))
    st.dataframe(source.frame.head(100), hide_index=True, height=240)
    st.caption(t("100 premières lignes au maximum · {v0} lignes dans cette table", v0=n(len(source.frame))))
    for d in datasets:
        if d.review_required:
            checked = st.checkbox(
                t("J’ai comparé l’extraction avec le PDF : {v0} / {v1}", v0=d.name, v1=d.table),
                key=f"review_{d.key}",
            )
            if checked:
                ss.reviewed.add(d.key)
            else:
                ss.reviewed.discard(d.key)
    columns = list(datasets[0].frame.columns)
    if ss.recipe is None:
        ss.recipe = default_recipe(columns)
        ss.recipe["name"] = t("Ma recette")
    with st.expander(t("Réutiliser une recette enregistrée"), icon=":material/folder_open:"):
        uploaded_recipe = st.file_uploader(
            t("Recette JSON"), type=["json"], key=f"upload_recipe_{ss.revision}"
        )
        if st.button(t("Charger la recette"), disabled=uploaded_recipe is None):
            try:
                candidate = load_recipe(uploaded_recipe.getvalue())
                if set(candidate["expected_columns"]) != set(columns):
                    raise ETLError("Cette recette ne correspond pas aux colonnes de la table sélectionnée.")
                ss.recipe, ss.result, ss.package = (candidate, None, None)
                ss.revision += 1
                st.rerun()
            except ETLError as exc:
                st.error(t(str(exc)))
    if set(ss.recipe["expected_columns"]) != set(columns):
        st.warning(t("La recette actuelle correspond à une autre structure de données."))
        if st.button(t("Créer une recette pour cette structure")):
            ss.recipe, ss.result, ss.package = (default_recipe(columns), None, None)
            ss.recipe["name"] = t("Ma recette")
            ss.revision += 1
            st.rerun()
        st.stop()
    recipe = deepcopy(ss.recipe)
    ss.setdefault("execution_request_id", str(uuid4()))
    with st.form(f"recipe_form_{ss.revision}_{ss.execution_request_id}"):
        st.subheader(t("Règles de préparation"))
        a, b = st.columns([2, 1])
        recipe["name"] = a.text_input(
            t("Nom de la recette"), recipe["name"], key=f"recipe_name_{ss.revision}"
        )
        recipe["trim"] = b.checkbox(
            t("Retirer les espaces en début et fin"), recipe["trim"], key=f"recipe_trim_{ss.revision}"
        )
        markers = st.text_input(
            t("Marqueurs de valeurs manquantes (séparés par |)"),
            "|".join((x for x in recipe["null_markers"] if x)),
            help=t("Les cellules vides sont toujours considérées comme manquantes. Exemple : NULL|N/A"),
            key=f"recipe_markers_{ss.revision}",
        )
        recipe["null_markers"] = [""] + [x.strip() for x in markers.split("|") if x.strip()]
        rules_df = pd.DataFrame(recipe["rules"])
        edited = st.data_editor(
            rules_df,
            hide_index=True,
            disabled=["column"],
            key=f"rules_{ss.revision}",
            column_config={
                "column": t("Colonne source"),
                "target": t("Nom de sortie"),
                "type": st.column_config.SelectboxColumn(
                    t("Type"), options=TYPES, required=True, format_func=t
                ),
                "required": t("Obligatoire"),
                "fill": t("Remplacer les vides par"),
                "case": st.column_config.SelectboxColumn(
                    t("Casse"),
                    options=["Conserver", "Minuscules", "Majuscules"],
                    required=True,
                    format_func=t,
                ),
                "decimal": st.column_config.SelectboxColumn(
                    t("Décimale"), options=[".", ","], required=True, format_func=t
                ),
                "date_format": t("Format date"),
                "minimum": t("Minimum"),
                "maximum": t("Maximum"),
            },
        )
        st.caption(
            t(
                "Dates : %Y-%m-%d = 2026-01-31 ; %d/%m/%Y = 31/01/2026. Bornes numériques : point décimal. Faites défiler le tableau horizontalement pour les paramètres avancés."
            )
        )
        recipe["deduplicate"] = st.checkbox(
            t("Écarter les doublons (conserver la première ligne valide)"),
            recipe["deduplicate"],
            key=f"recipe_deduplicate_{ss.revision}",
        )
        recipe["duplicate_keys"] = st.multiselect(
            t("Colonnes identifiant un doublon"),
            recipe["expected_columns"],
            default=recipe["duplicate_keys"],
            help=t("Sans sélection, toutes les colonnes métier sont comparées."),
            key=f"recipe_duplicates_{ss.revision}",
        )
        submitted = st.form_submit_button(
            t("Appliquer et contrôler"),
            type="primary",
            icon=":material/play_arrow:",
            disabled=quota["remaining"] == 0 or not quota["plan_active"],
        )
    if quota["remaining"] == 0:
        st.warning(t("Quota quotidien atteint ou réservé par des traitements en cours."))
    if not quota["plan_active"]:
        st.warning(t("Votre plan est temporairement suspendu."))
    if submitted:
        try:
            recipe["rules"] = edited.fillna("").to_dict("records")
            validate_recipe(recipe)
            with st.spinner(t("Préparation et contrôle du lot…")):
                result = service().execute_etl(
                    ss.auth_token, ss.execution_request_id, datasets, recipe, ss.reviewed
                )
            result["report"]["import_failures"] = ss.import_errors
            ss.recipe, ss.result, ss.package = (recipe, result, None)
            ss.history = ([result["report"]] + ss.history)[:20]
            ss.pending_stage = "3 · Contrôler"
            ss.execution_request_id = str(uuid4())
            st.rerun()
        except (ETLError, AccountError) as exc:
            ss.execution_request_id = str(uuid4())
            st.error(t(str(exc)))
        except Exception:
            ss.execution_request_id = str(uuid4())
            st.error(t("Le traitement a échoué. Aucune utilisation réussie n’a été comptabilisée."))
elif ss.stage == "3 · Contrôler":
    st.caption(t("ÉTAPE 03 / 04"))
    st.title(t("Vérifiez le résultat"))
    if ss.result is None:
        require_data()
        st.info(t("Appliquez votre recette pour calculer les résultats."))
        st.button(t("Préparer les données"), on_click=go, args=("2 · Préparer",), type="primary")
        st.stop()
    result, report = (ss.result, ss.result["report"])
    st.caption(t("Recette appliquée : {v0} · résultat figé de ce traitement", v0=report["recipe_name"]))
    cols = st.columns(4)
    for col, label, value in zip(
        cols,
        ["Lignes sources", "Lignes valides", "En quarantaine", "Doublons écartés"],
        [report["input_rows"], report["accepted_rows"], report["rejected_rows"], report["duplicate_rows"]],
    ):
        col.metric(t(label), n(value), border=True)
    if report["rejected_rows"]:
        st.warning(
            t(
                "Certaines lignes nécessitent votre attention. Elles sont conservées avec les valeurs originales et les motifs de rejet."
            )
        )
    else:
        st.success(t("Toutes les lignes respectent les règles configurées."))
    if report.get("import_failures"):
        st.warning(
            t(
                "Le lot est partiel : des fichiers n’ont pas pu être importés. Ils seront signalés dans le rapport."
            )
        )
    view = st.segmented_control(
        t("Vue du résultat"),
        ["Données valides", "Quarantaine", "Qualité", "Traçabilité"],
        default="Données valides",
        format_func=t,
        key="control_364",
    )
    if view == "Quarantaine":
        st.dataframe(
            display_rejections(result["rejected"].head(500), ss.language),
            hide_index=True,
            column_config={"_etl_issues": t("Motifs de rejet")},
        )
        if report["issue_counts"]:
            st.dataframe(
                pd.DataFrame(
                    [(t(reason), count) for reason, count in report["issue_counts"].items()],
                    columns=[t("Motif"), t("Occurrences")],
                ),
                hide_index=True,
            )
    elif view == "Qualité":
        business = result["accepted"].drop(columns=[c for c in result["accepted"] if c.startswith("_etl_")])
        p = profile(business)
        st.metric(t("Complétude des données valides"), f"{p['completeness']} %")
        st.caption(
            t("Part des cellules non vides après traitement ; ce taux ne mesure pas l’exactitude métier.")
        )
        st.dataframe(display_metadata(p["column_profile"], ss.language), hide_index=True)
    elif view == "Traçabilité":
        st.dataframe(
            pd.DataFrame(report["sources"])[["file", "table", "rows", "sha256"]],
            hide_index=True,
            column_config={
                "file": t("Fichier"),
                "table": t("Table"),
                "rows": t("Lignes"),
                "sha256": t("Empreinte SHA-256"),
            },
        )
        st.caption(
            t(
                "Chaque ligne exportée porte sa source, sa table, son numéro d’enregistrement et l’empreinte du fichier."
            )
        )
    else:
        st.dataframe(
            result["accepted"]
            .drop(columns=[c for c in result["accepted"] if c.startswith("_etl_")])
            .head(500),
            hide_index=True,
        )
    st.caption(t("Aperçus limités à 500 lignes. L’export contient toutes les lignes du résultat."))
    with st.container(horizontal=True):
        st.button(t("Ajuster la recette"), on_click=go, args=("2 · Préparer",), icon=":material/tune:")
        st.button(
            t("Passer à l’export"),
            on_click=go,
            args=("4 · Exporter",),
            type="primary",
            disabled=not report["accepted_rows"],
        )
elif ss.stage == "4 · Exporter":
    st.caption(t("ÉTAPE 04 / 04"))
    st.title(t("Livrez des données traçables"))
    if ss.result is None:
        st.info(t("Préparez et contrôlez les données avant de les exporter."))
        st.stop()
    result = ss.result
    st.write(
        t(
            "**{v0} lignes valides** · recette « {v1} »",
            v0=n(len(result["accepted"])),
            v1=result["recipe"]["name"],
        )
    )
    left, right = st.columns([1.5, 1])
    with left.container(border=True):
        st.subheader(t("Préparer le dossier de livraison"))
        output_format = st.selectbox(
            t("Format des données"), ["CSV", "Excel", "Parquet"], format_func=t, key="control_418"
        )
        st.caption(
            t(
                "CSV : UTF-8, séparateur point-virgule. Parquet : conserve les types pour vos outils d’analyse."
            )
        )
        allow = not len(result["rejected"])
        if not allow:
            allow = st.checkbox(
                t("J’accepte d’exporter les lignes valides et de joindre les autres en quarantaine."),
                key="control_424",
            )
        import_ack = True
        if result["report"].get("import_failures"):
            import_ack = st.checkbox(
                t("J’ai pris connaissance des fichiers non importés ; je souhaite exporter ce lot partiel."),
                key="control_429",
            )
        fingerprint = (result["report"]["run_id"], output_format, allow, import_ack)
        if ss.package and ss.package[0] != fingerprint:
            ss.package = None
        if st.button(
            t("Générer le dossier ZIP"),
            type="primary",
            disabled=not allow or not import_ack,
            icon=":material/inventory_2:",
        ):
            try:
                result["report"]["import_failures_acknowledged"] = bool(
                    result["report"].get("import_failures") and import_ack
                )
                ss.package = (fingerprint, bundle(result, output_format, allow))
            except Exception as exc:
                st.error(
                    t(
                        str(exc)
                        if isinstance(exc, ETLError)
                        else f"Export impossible ({type(exc).__name__}). Essayez CSV."
                    )
                )
        if ss.package:
            st.download_button(
                t("Télécharger le dossier de livraison"),
                ss.package[1],
                f"dataflow-studio-{result['report']['run_id'][:8]}.zip",
                "application/zip",
                type="primary",
            )
            st.success(t("Dossier généré. Téléchargez-le pour le conserver."))
    with right.container(border=True):
        st.subheader(t("Dans votre dossier"))
        st.markdown(
            t(
                "- Données validées et traçables\n- Lignes en quarantaine et motifs\n- Rapport d’exécution JSON\n- Recette réutilisable\n- Instructions de lecture"
            )
        )
        st.download_button(
            t("Enregistrer la recette seule"),
            json_bytes(result["recipe"]),
            "recette.json",
            "application/json",
        )
        st.caption(
            t("CSV et Excel : les textes pouvant devenir des formules sont préfixés par une apostrophe.")
        )
elif ss.stage == "Journal":
    st.title(t("Journal des traitements"))
    st.caption(
        t("Les 20 derniers traitements de cette session. Téléchargez les rapports pour un suivi durable.")
    )
    if not ss.history:
        st.info(t("Votre premier traitement apparaîtra ici après l’application d’une recette."))
    else:
        for item in ss.history:
            with st.expander(
                t(
                    "{v0} · {v1} UTC · {v2}",
                    v0=item["recipe_name"],
                    v1=item["created_at"][:19].replace("T", " "),
                    v2=item["run_id"][:8],
                )
            ):
                st.write(
                    t(
                        "{v0} lignes sources → {v1} valides · {v2} en quarantaine",
                        v0=item["input_rows"],
                        v1=item["accepted_rows"],
                        v2=item["rejected_rows"],
                    )
                )
                st.download_button(
                    t("Télécharger le rapport"),
                    json_bytes(item),
                    f"rapport-{item['run_id'][:8]}.json",
                    "application/json",
                    key=f"report_{item['run_id']}",
                )
