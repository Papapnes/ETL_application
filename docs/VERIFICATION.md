# Vérification de la version 0.2

Vérification effectuée le 27 septembre 2026 sur Windows, Python 3.14.6, Streamlit 1.64.0 et pandas 3.0.6. Versions complètes dans `uv.lock`.

## Résultats

- `pytest -q` : **35 tests réussis**.
- `ruff check app.py etl ui tests scripts` : réussi.
- `ruff format --check app.py etl ui tests scripts` : conforme.
- Serveur local : `GET /_stcore/health` retourne HTTP 200 et `ok`.
- Démonstration : 12 lignes sources = 8 acceptées + 4 rejetées, dont 1 doublon.
- Second lot avec la recette sauvegardée : 3 lignes acceptées, aucun rejet ; export généré.

## Périmètre couvert

Import CSV cité/multiligne/CP1252, lignes mal formées, en-têtes dupliqués, identifiants à zéros initiaux, JSON imbriqué, JSONL, XLS, XLSX à plusieurs feuilles, Parquet, tables PDF et absence de tables. Contrôles de schéma, champs obligatoires, dates, bornes, booléens, précision des entiers et priorité donnée à la première ligne valide pour les doublons.

Exports CSV, Excel et Parquet réouverts pour vérifier les lignes et les identifiants ; contrôle de la quarantaine et de la protection des formules Excel. Tests d’interaction Streamlit AppTest : démonstration, passage aux résultats, blocage de l’export partiel avant acceptation, génération de ZIP, invalidation après changement de format, vidage de session, navigation sans données et conservation de la sélection d’un lot.

## Restant à vérifier avec le client

La version multilingue ajoute des tests de complétude du catalogue et de correspondance des paramètres traduits, du parcours en anglais et en arabe, du changement de langue sans mutation des résultats et des recettes, des diagnostics affichés sans modification des données sources, et de la présence des coordonnées et de l’URL LinkedIn sur les écrans vides dans les trois langues. Les règles CSS RTL sont contrôlées structurellement ; leur rendu visuel reste à vérifier dans un navigateur.

- Affichage visuel dans son navigateur et sur son écran : aucun navigateur automatisable connecté lors de cette vérification. AppTest couvre le comportement, pas le rendu final dans un navigateur.
- Import par glisser-déposer et téléchargement réel via son navigateur.
- Ses fichiers PDF, classeurs à formules, particularités de données et volumes réels.
- Ouverture et exploitation des exports dans son environnement Power BI ou autre outil cible.
- Recette métier et conditions d’exploitation acceptées par le client.

Ces contrôles ne constituent ni un test de charge ni un audit de sécurité d’un service partagé.
