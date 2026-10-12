from functools import partial

import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from accounts.config import database_config, send_reset_email, smtp_ready
from accounts.errors import DatabaseError
from accounts.service import AccountError, Accounts
from ui.i18n import translate

ACCOUNT_DATABASE_ERROR = "_account_database_error"


@st.cache_resource
def _service(path):
    return Accounts(path)


def service():
    try:
        try:
            runtime_secrets = dict(st.secrets)
        except StreamlitSecretNotFoundError:
            runtime_secrets = {}
        account_service = _service(database_config(runtime_secrets=runtime_secrets))
        st.session_state.pop(ACCOUNT_DATABASE_ERROR, None)
        return account_service
    except DatabaseError as exc:
        # File processing remains available if the optional account backend
        # is paused or temporarily unavailable.
        st.session_state[ACCOUNT_DATABASE_ERROR] = str(exc)
        return None


def account_database_error():
    return st.session_state.get(ACCOUNT_DATABASE_ERROR)


def clear_private_state():
    # Auth transitions must clear uploads, results, widget values and download buffers.
    language = st.session_state.get("language", "fr")
    for key in list(st.session_state):
        del st.session_state[key]
    st.session_state.language = language


def sign_out():
    service().logout(st.session_state.get("auth_token"))
    clear_private_state()


def current_user():
    token = st.session_state.get("auth_token")
    if not token:
        return None
    account_service = service()
    if account_service is None:
        st.session_state.pop("auth_token", None)
        return None
    try:
        return account_service.identity(token)
    except DatabaseError as exc:
        st.error(str(exc))
        st.stop()
    except AccountError:
        clear_private_state()
        st.rerun()


def auth_page(language):
    t = partial(translate, language=language)
    st.subheader(t("Bienvenue dans votre espace sécurisé"))
    st.caption(t("Connectez-vous pour préparer vos données. Un compte FREE inclut 5 traitements par jour."))
    mode = st.selectbox(
        t("Accès au compte"),
        ["Connexion", "Inscription", "Mot de passe oublié", "Réinitialiser le mot de passe"],
        format_func=t,
        key="auth_mode",
    )
    client = st.context.ip_address or "unknown"
    if mode in {"Connexion", "Inscription"}:
        with st.form("identity_form", clear_on_submit=True):
            name = st.text_input(t("Nom complet"), max_chars=120) if mode == "Inscription" else ""
            email = st.text_input(t("Adresse courriel"), max_chars=254)
            password = st.text_input(t("Mot de passe"), type="password", max_chars=128)
            confirmation = (
                st.text_input(t("Confirmer le mot de passe"), type="password", max_chars=128)
                if mode == "Inscription"
                else password
            )
            if mode == "Inscription":
                st.caption(t("Utilisez entre 12 et 128 caractères. Aucun paiement n’est demandé."))
            submitted = st.form_submit_button(
                t("Se connecter" if mode == "Connexion" else "Créer mon compte"), type="primary"
            )
        if submitted:
            try:
                if password != confirmation:
                    raise AccountError("Les mots de passe ne correspondent pas.")
                if mode == "Connexion":
                    token = service().login(email, password, client)
                    clear_private_state()
                    st.session_state.auth_token = token
                    st.rerun()
                else:
                    service().register(name, email, password, client)
                    st.success(
                        t(
                            "Si cette adresse est disponible, votre compte FREE est créé. Vous pouvez vous connecter ou récupérer votre mot de passe."
                        )
                    )
            except AccountError as exc:
                st.error(t(str(exc)))
    elif mode == "Mot de passe oublié":
        if not smtp_ready():
            st.info(
                t("La récupération par courriel n’est pas encore configurée. Contactez l’administrateur.")
            )
            return
        with st.form("forgot_form", clear_on_submit=True):
            email = st.text_input(t("Adresse courriel"), max_chars=254)
            submitted = st.form_submit_button(t("Envoyer un code de récupération"), type="primary")
        if submitted:
            try:
                service().request_password_reset(email, send_reset_email, client)
                st.success(
                    t(
                        "Si un compte actif correspond à cette adresse, un code valable 30 minutes a été envoyé."
                    )
                )
            except AccountError as exc:
                st.error(t(str(exc)))
    else:
        with st.form("reset_password_form", clear_on_submit=True):
            code = st.text_input(t("Code reçu par courriel"), type="password", max_chars=128)
            password = st.text_input(t("Nouveau mot de passe"), type="password", max_chars=128)
            confirmation = st.text_input(t("Confirmer le mot de passe"), type="password", max_chars=128)
            submitted = st.form_submit_button(t("Enregistrer le nouveau mot de passe"), type="primary")
        if submitted:
            try:
                if password != confirmation:
                    raise AccountError("Les mots de passe ne correspondent pas.")
                service().reset_password(code.strip(), password, client)
                st.success(
                    t("Mot de passe modifié. Reconnectez-vous ; les anciennes sessions ont été fermées.")
                )
            except AccountError as exc:
                st.error(t(str(exc)))


def account_page(language):
    t = partial(translate, language=language)
    token = st.session_state.auth_token
    user, quota = service().identity(token), service().quota(token)
    st.title(t("Mon compte"))
    st.text(user["full_name"])
    st.text(user["email"])
    st.badge(user["role"])
    if user["role"] == "ADMIN":
        st.success(t("Accès illimité"))
    cols = st.columns(3)
    cols[0].metric(t("Utilisations aujourd’hui"), quota["used"])
    cols[1].metric(
        t("Utilisations restantes"),
        t("Illimité") if quota["remaining"] is None else f"{quota['remaining']} / {quota['limit']}",
    )
    cols[2].metric(t("Traitements en cours"), quota["pending"])
    st.caption(t("Prochain renouvellement") + " : " + quota["next_reset"] + " · America/Toronto")
    st.caption(
        t(
            "Les traitements en cours réservent une utilisation. Seuls les traitements réussis sont comptabilisés."
        )
    )
    if not quota["plan_active"]:
        st.warning(t("Votre plan est temporairement suspendu."))
    if quota["remaining"] == 0:
        st.warning(t("Quota quotidien atteint ou réservé par des traitements en cours."))
    st.info(t("L’offre PRO est attribuée par l’administrateur. Les paiements ne sont pas activés."))


def admin_page(language):
    t = partial(translate, language=language)
    token = st.session_state.auth_token
    try:
        data = service().admin_data(token)
    except AccountError as exc:
        st.error(t(str(exc)))
        return
    st.title(t("Administration"))
    users = data["users"]
    cols = st.columns(3)
    cols[0].metric(t("Utilisateurs inscrits"), len(users))
    cols[1].metric("FREE", sum(u["role"] == "FREE" for u in users))
    cols[2].metric("PRO", sum(u["role"] == "PRO" for u in users))
    cols = st.columns(3)
    cols[0].metric(t("Traitements réussis aujourd’hui"), sum(u["used_today"] for u in users))
    cols[1].metric(t("Total des traitements réussis"), sum(u["total_runs"] for u in users))
    cols[2].metric(t("Utilisateurs au quota atteint"), sum(u["remaining"] == 0 for u in users))
    search = st.text_input(t("Rechercher par nom ou courriel"), key="admin_search").strip().casefold()
    filtered = [u for u in users if search in (u["full_name"] + " " + u["email"]).casefold()]
    if filtered:
        frame = pd.DataFrame(filtered)
        st.dataframe(
            frame,
            hide_index=True,
            column_config={
                "user_id": None,
                "full_name": t("Nom complet"),
                "email": t("Adresse courriel"),
                "role": t("Type de compte"),
                "account_status": t("Statut"),
                "created_at": t("Créé le"),
                "custom_daily_limit": t("Quota personnalisé"),
                "used_today": t("Utilisations aujourd’hui"),
                "pending": t("Traitements en cours"),
                "daily_limit": t("Quota quotidien"),
                "remaining": t("Utilisations restantes"),
                "total_runs": t("Total des traitements réussis"),
            },
        )
        by_id = {u["user_id"]: u for u in filtered}
        selected = st.selectbox(
            t("Compte à modifier"),
            list(by_id),
            format_func=lambda uid: by_id[uid]["full_name"] + " · " + by_id[uid]["email"],
        )
        user = by_id[selected]
        with st.form("edit_user_" + selected):
            role = st.selectbox(
                t("Type de compte"),
                ["FREE", "PRO", "ADMIN"],
                index=["FREE", "PRO", "ADMIN"].index(user["role"]),
            )
            active = st.checkbox(t("Compte actif"), value=user["account_status"] == "ACTIVE")
            custom = st.checkbox(
                t("Utiliser un quota personnalisé"), value=user["custom_daily_limit"] is not None
            )
            limit = st.number_input(
                t("Quota personnalisé"),
                min_value=0,
                max_value=1_000_000,
                value=user["custom_daily_limit"] if user["custom_daily_limit"] is not None else 50,
                step=1,
            )
            st.caption(t("ADMIN dispose toujours d’un quota illimité. Chaque modification est journalisée."))
            save = st.form_submit_button(t("Enregistrer les modifications"), type="primary")
        if save:
            try:
                service().update_user(
                    token, selected, role, "ACTIVE" if active else "DISABLED", int(limit) if custom else None
                )
                st.rerun()
            except AccountError as exc:
                st.error(t(str(exc)))
    else:
        st.info(t("Aucun utilisateur correspondant."))
    with st.expander(t("Configurer les plans FREE et PRO")):
        plan_name = st.selectbox(t("Plan"), ["FREE", "PRO"])
        plan = next(p for p in data["plans"] if p["plan_name"] == plan_name)
        with st.form("plan_" + plan_name):
            limit = st.number_input(t("Limite quotidienne du plan"), 0, 1_000_000, int(plan["daily_limit"]))
            active = st.checkbox(t("Plan actif"), bool(plan["is_active"]))
            st.caption(
                t(
                    "Suspendre un plan bloque ses nouveaux traitements ; suspendre FREE bloque aussi les inscriptions."
                )
            )
            save = st.form_submit_button(t("Enregistrer le plan"))
        if save:
            try:
                service().update_plan(token, plan_name, int(limit), active)
                st.rerun()
            except AccountError as exc:
                st.error(t(str(exc)))
