# Plateforme de traitement des données · DataFlow Studio

Application locale en français, anglais et arabe pour importer, préparer, contrôler et exporter des données avec des recettes réutilisables.

**Version 0.2 — démonstrateur fonctionnel pour un pilote client.** Le moteur et le parcours sont testés ; une recette métier doit être validée sur les fichiers représentatifs du client avant sa mise en exploitation. Aucune donnée client n’est incluse.

## Langues et coordonnées professionnelles

Le sélecteur **Langue / Language / اللغة**, en haut de la barre latérale, propose **FR · Français**, **EN · English** et **AR · العربية**. Le choix reste actif pendant la session, même après son vidage. Les titres, menus, actions, aides, règles, contrôles qualité et diagnostics affichés sont traduits. Les textes arabes sont affichés de droite à gauche ; les données et identifiants techniques conservent leur ordre.

Le nom de la plateforme dans la barre latérale, sur l’accueil et dans l’onglet du navigateur suit ce choix : **Plateforme de traitement des données** en français, **DataFlow Studio** en anglais et **منصّة معالجة وتحويل البيانات** en arabe.

Les données métier, noms de colonnes sources, noms de fichiers et recettes existantes ne sont pas traduits. Les fichiers exportés et les clés de recettes gardent leur format stable, indépendant de la langue de l’interface. Certains libellés fournis directement par les composants Streamlit (par exemple les commandes internes d’une grille ou du dépôt de fichiers) peuvent rester en anglais. Les modifications du formulaire doivent être appliquées avant de quitter l’étape.

En bas de la barre latérale gauche figurent **Abdelkader Bouzourine**, son titre **Consultant en BI** (traduit selon la langue) et un lien vers [son profil LinkedIn](https://www.linkedin.com/in/abdelkader-bouzourine-data-analyst/). Ce bloc reste dans le flux de la page pour ne pas recouvrir les commandes sur un petit écran.

## Démarrage sur Windows

Sur ce poste, les dépendances sont déjà installées. Double-cliquez sur **Lancer.cmd** : il démarre le code de ce dossier et ouvre le navigateur à la bonne adresse. Si le port 8501 est occupé, il choisit un port disponible et affiche l’adresse dans sa fenêtre, sans interrompre l’ancienne session. Utilisez ce nouvel onglet pour bénéficier des corrections. Gardez la fenêtre du lanceur ouverte pendant l’utilisation ; `Ctrl+C` arrête le serveur.

Sur un autre poste, installez Python 3.12 à 3.14 et [uv](https://docs.astral.sh/uv/getting-started/installation/) puis lancez `Lancer.cmd`. Une connexion est nécessaire pour la première installation. Les versions sont figées dans `uv.lock`.

Lancement manuel depuis le dossier du projet, dans PowerShell :

```powershell
$env:UV_CACHE_DIR = "$PWD/.uv-cache"
uv sync --locked
.venv/Scripts/python.exe -m streamlit run app.py
```

L’application écoute uniquement sur `127.0.0.1`. Elle ne téléverse pas les données vers un service tiers et n’utilise pas de modèle d’IA distant. La télémétrie Streamlit est désactivée. Les fichiers et résultats restent en mémoire pendant la session ; les téléchargements sont enregistrés par votre navigateur. Les sources locales ne sont pas modifiées. Les bibliothèques peuvent utiliser des mécanismes de mémoire temporaire du système ; cette édition n’est pas un environnement d’exécution isolé pour des fichiers hostiles.

## Parcours

1. **Importer** : ajoutez plusieurs fichiers. Réglez si nécessaire l’encodage, le séparateur, la ligne d’en-tête Excel ou le chemin JSON. Les fichiers illisibles apparaissent explicitement dans la liste des erreurs.
2. **Préparer** : sélectionnez des tables de même schéma. Consultez les aperçus, contrôlez les tables PDF et configurez les règles. Le tableau de règles défile horizontalement pour afficher tous les paramètres.
3. **Contrôler** : consultez les données valides, les valeurs originales rejetées, les motifs de rejet, la complétude et les sources. Ajustez la recette si nécessaire.
4. **Exporter** : choisissez CSV, Excel ou Parquet, puis générez et téléchargez le ZIP. Si des lignes sont rejetées ou des fichiers non importés, confirmez explicitement que vous acceptez le résultat partiel.
5. **Réutiliser** : téléchargez `recette.json`. Lors du prochain import, ouvrez « Réutiliser une recette enregistrée » dans Préparer. Les colonnes doivent correspondre ; aucun rapprochement silencieux n’est effectué.

Le résultat contrôlé est un instantané de la dernière recette **appliquée**. Pour prendre en compte des modifications dans le formulaire, cliquez de nouveau sur « Appliquer et contrôler ».

## Formats et limites réelles

| Format | Prise en charge | Limites |
|---|---|---|
| CSV, TSV, TXT | En-têtes, champs entre guillemets, sauts de ligne cités, séparateurs virgule/point-virgule/tabulation/barre | UTF-8 par défaut ; CP1252 et Latin-1 sélectionnables. Tout fichier aux lignes mal formées est refusé. |
| JSON, JSONL | Liste d’objets, chemin pointé vers une liste imbriquée | Les objets et tableaux imbriqués restent des textes JSON ; aucun éclatement implicite. |
| XLS, XLSX | Feuilles multiples, ligne d’en-tête configurable | Pas de recalcul des formules : dépend des valeurs enregistrées. Les zéros uniquement définis par un format d’affichage Excel ne sont pas reconstruits. |
| Parquet | Lecture tabulaire | Les valeurs passent dans une zone de préparation textuelle ; le typage de sortie est défini dans la recette. |
| PDF | Tables détectables dans des PDF textuels | Contrôle humain obligatoire. Sans table détectée, import refusé. OCR absent. |

Limites : **25 Mo/fichier, 20 fichiers et 100 Mo/lot, 100 000 lignes par table et par traitement, 300 colonnes/table, 50 tables/fichier, 100 pages/PDF**. Les limites décompressées des classeurs sont contrôlées à 200 Mo. Ces seuils limitent les usages courants sans garantir une consommation mémoire maximale pour tous les fichiers compressés ou malformés.

## Règles disponibles

- Renommage des colonnes ; suppression des espaces en début et fin.
- Marqueurs explicites de valeurs manquantes ; remplacement configurable.
- Casse : conserver, minuscules ou majuscules.
- Types texte, entier, décimal, date et booléen.
- Champs obligatoires et bornes numériques.
- Dédoublonnage par clé ou toutes les colonnes métier, après validation ; première ligne valide conservée.
- Ajout de plusieurs tables compatibles dans un même résultat, avec ordre de sélection issu de l’ordre d’import.

Les nombres n’acceptent pas de séparateurs de milliers implicites. Les entiers sont limités à ±(2^53−1) pour éviter les pertes de précision lors de la conversion. Les décimaux sont des flottants : cette version n’implémente pas d’arithmétique comptable exacte. Les formats de date doivent être explicites (`%Y-%m-%d`, `%d/%m/%Y`…) ; la gestion de fuseaux horaires n’est pas proposée dans l’interface.

## Dossier exporté

- `donnees.csv`, `donnees.xlsx` ou `donnees.parquet` : lignes valides.
- `quarantaine.csv` : valeurs sources et motifs ; fichier avec en-têtes même sans rejet.
- `rapport.json` : identifiant d’exécution, date UTC, compteurs, empreintes SHA-256, paramètres d’import, validation PDF et éventuels fichiers non importés.
- `recette.json` : règles réutilisables, version 1.
- `LIRE-MOI.txt` : conventions d’export.

Les colonnes `_etl_source`, `_etl_table`, `_etl_record`, `_etl_sha256` retracent les lignes. `_etl_record` désigne la position de l’enregistrement de données dans la table extraite, hors en-tête ; ce n’est pas nécessairement un numéro de ligne physique du fichier. Le préfixe `_etl_` est réservé à l’application : les exports contenant ces colonnes ne sont pas réimportables directement sans retirer ou renommer ces colonnes.

Dans les CSV et Excel, les textes commençant par un signe pouvant être interprété comme une formule reçoivent une apostrophe protectrice. Parquet conserve le texte original. Les nombres négatifs typés restent numériques. Cette protection peut changer la représentation textuelle dans les outils en aval ; elle est indiquée dans le rapport.

## Vérification

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/ruff.exe check app.py etl ui tests scripts
.venv/Scripts/ruff.exe format --check app.py etl ui tests scripts
```

Les tests couvrent les importeurs, la conservation des identifiants, les rejets, les doublons, la dérive de schéma, les exports réouverts, la protection des formules et le parcours de démonstration dans Streamlit AppTest. La vérification visuelle du rendu dans un navigateur réel reste à effectuer sur le poste de présentation ; aucun navigateur automatisable n’était connecté lors du développement.

## Structure

```text
app.py                  Interface et état de session
etl/engine.py           Extraction, recettes, validation, export
etl/demo.py             Données et recette fictives
ui/                     Traductions FR/EN/AR, RTL et coordonnées
tests/                  Tests du moteur et du parcours
examples/               Sources et recette de démonstration
docs/                   Guide de présentation et architecture
.streamlit/config.toml  Thème et écoute locale
uv.lock                 Versions reproductibles
Lancer.cmd              Lancement Windows
```

## Périmètre d’une future livraison de production

Cette édition est locale et mono-utilisateur. Elle n’inclut pas de comptes utilisateurs, base d’historique durable, OCR, surveillance de dossier, tâches planifiées, connecteurs SQL, jointures, pivot/dépivot ou traitements distribués. Le journal conserve 20 traitements en session, puis disparaît à la fermeture/reconnexion. La recette mémorise les transformations et le schéma ; les paramètres de lecture doivent actuellement être réglés à l’import et sont tracés dans le rapport.

Avant la livraison définitive : valider les formats et volumes réels du client, faire sa recette fonctionnelle, confirmer les règles de conservation des fichiers et choisir le mode d’installation. Un hébergement partagé nécessiterait authentification, isolation, quotas, gestion de secrets, stockage durable et tests de charge adaptés.

