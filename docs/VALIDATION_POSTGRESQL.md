# Validation locale PostgreSQL — 28 septembre 2026

## Résultat vérifié

**61 tests réussis, 0 échec, 0 erreur, 4 cas non applicables ignorés.**

Exécution complète sur Python 3.14, psycopg 3.3.6 et PostgreSQL 17.11 local, avec TLS vérifié et un rôle applicatif distinct du compte de migration. Durée pytest : 36,83 secondes. Les 12 cas paramétrés PostgreSQL ont tous réussi. Les quatre cas ignorés sont uniquement les variantes SQLite des tests spécifiques à PostgreSQL (migration, permissions, TLS).

Ruff : `All checks passed!` ; formatage : `31 files already formatted`.

Rapport JUnit local, ignoré par Git : `.postgres-test/results.xml`. Journaux du dernier serveur de test : `.postgres-test/1f0dc9ed-12ce-421d-b7e7-27d151c5b5d2/`. Le serveur a été arrêté normalement après les tests.

Aucune connexion ni modification de Supabase réel, aucune publication, aucun commit et aucun push n'ont été exécutés. Le fichier `local-data/accounts.sqlite3` n'a pas été supprimé ou modifié par cette reprise : son SHA-256 avant/après est identique, `898D663CB2CC585A1C34A54C6BB80D03088BE148C34E393BDF7287F173E0C4A9`.

## État au début de la reprise

- Dernier résultat antérieur confirmé : 49 tests réussis, 8 PostgreSQL ignorés.
- Le premier serveur PostgreSQL temporaire avait démarré ; connexion TLS et création de la base avaient été constatées, mais la suite n'avait pas produit de bilan exploitable.
- Le code de migration ADMIN, de concurrence et de permissions était présent mais pas encore validé sur PostgreSQL.
- Les tentatives intermédiaires ont révélé des problèmes du banc de tests Windows : canaux de sortie hérités, dossier temporaire pytest inaccessible entre contextes d'exécution et encodage de sortie. Une tentative a eu 65 erreurs de préparation des dossiers temporaires, avant les assertions métier.
- Pendant cette reprise, seul le lanceur de vérification `scripts/test_postgres.py` a été corrigé ; le code métier PostgreSQL n'a pas nécessité de correction supplémentaire. Les sorties vont dans des fichiers, les chemins temporaires sont isolés, l'encodage est UTF-8 et la connexion locale conserve `localhost` pour vérifier le certificat tout en utilisant explicitement IPv4.

## Couverture vérifiée

| Fonction | SQLite | PostgreSQL |
|---|---|---|
| Inscription uniquement FREE, Argon2, tokens hachés | Réussi | Réussi |
| Connexion, déconnexion, mauvais identifiants | Réussi | Réussi |
| Authentification ADMIN et refus des actions ADMIN aux FREE | Réussi | Réussi |
| Modification du rôle/quota et désactivation | Réussi | Réussi |
| Protection du dernier ADMIN actif | Réussi | Réussi |
| Récupération de mot de passe à usage unique et révocation des sessions | Réussi | Réussi |
| FREE : cinq succès/jour ; échecs non facturés ; identifiant non réutilisable | Réussi | Réussi |
| ADMIN : quota illimité | Réussi | Réussi |
| Minuit America/Toronto, y compris changement d'heure | Réussi | Réussi |
| Huit demandes simultanées : cinq acceptées, trois refusées | Réussi | Réussi |
| Conservation des comptes lors de la recréation du service | Réussi | Réussi |
| Isolation des quotas et sessions des utilisateurs | Réussi | Réussi |
| Import ADMIN conservant UUID, champs et hachage ; seconde exécution sans doublon | Sans objet | Réussi |
| Aucun transfert des sessions SQLite ; refus des conflits de comptes | Sans objet | Réussi |
| Refus d'écraser un compte sans remplacement explicite | Sans objet | Réussi |
| Migrations réexécutées sans perte de comptes | Sans objet | Réussi |
| Rôle applicatif : DDL, modification de version, suppression de comptes/audit refusés | Sans objet | Réussi |
| TLS actif ; CA invalide et mauvais nom de serveur refusés | Sans objet | Réussi |

Les tests utilisent des comptes fictifs. Le quota concurrent utilise un ETL simulé bloquant pour contrôler l'ordre des réservations ; les tests existants du moteur ETL et du parcours Streamlit restent exécutés séparément dans la même suite. Il ne s'agit pas d'un test de charge ni d'un audit de sécurité exhaustif.

## Fichiers concernés

Modifiés pour cette migration :

```text
.gitignore
accounts/cli.py
accounts/config.py
accounts/service.py
app.py
scripts/launch.py
scripts/package.py
tests/conftest.py
ui/accounts.py
```

Ajout de `psycopg` effectué avant notre adaptation et conservé :

```text
pyproject.toml
uv.lock
```

Nouveaux fichiers :

```text
accounts/database.py
accounts/errors.py
accounts/migrate.py
accounts/sqlite_schema.py
accounts/migrations/001_accounts.sql
accounts/migrations/002_permissions.sql
scripts/test_postgres.py
tests/test_accounts.py
tests/test_database_config.py
tests/test_postgres_migration.py
docs/MIGRATION_SUPABASE.md
docs/VALIDATION_POSTGRESQL.md
```

`reset_admin_local.py`, préexistant et non suivi, n'a pas été modifié et est volontairement exclu des commandes Git ci-dessous.

## Commandes de vérification

Depuis `D:\MyProject\Projet_Application_vibeCoding`, dans PowerShell :

```powershell
uv sync --locked
.venv/Scripts/python.exe -m ruff check app.py accounts etl ui tests scripts
.venv/Scripts/python.exe -m ruff format --check app.py accounts etl ui tests scripts
.venv/Scripts/python.exe scripts/test_postgres.py --bin-dir .postgres-test/pgsql/bin
```

Résultat attendu du banc complet : **61 passed, 4 skipped**, suivi de `server stopped`, et code de sortie 0. Aucun des douze cas PostgreSQL ne doit être ignoré. Sur un autre poste, fournir le chemin de binaires PostgreSQL installés et lancer sous un utilisateur standard autorisé à créer un serveur local. Aucun droit sur Supabase n'est nécessaire.

Sans PostgreSQL :

```powershell
.venv/Scripts/python.exe -m pytest -q
```

Cette commande seule ignore les cas PostgreSQL lorsque `DATAFLOW_TEST_ADMIN_URL` et `DATAFLOW_TEST_APP_URL` sont absentes. Elle ne remplace pas la validation complète ci-dessus. Les variables de test sont générées automatiquement par `scripts/test_postgres.py` ; ne pas y mettre des identifiants Supabase.

## Prochaines étapes manuelles Supabase

Lire d'abord `docs/MIGRATION_SUPABASE.md`, qui détaille TLS, permissions et retour arrière.

1. Sauvegarder SQLite de façon cohérente et conserver la source. Suspendre les écritures pendant le transfert. Aucune sauvegarde ne doit aller dans GitHub.
2. Depuis le tableau de bord Supabase, récupérer les paramètres de connexion **Session pooler** ou directe. Utiliser `sslmode=verify-full`, le nom DNS du certificat et, si nécessaire, le certificat CA fourni par Supabase.
3. Ajouter les secrets opérateur au fichier local ignoré `.streamlit/secrets.toml` :

```toml
# URI privilégiée : poste opérateur uniquement.
DATAFLOW_MIGRATION_DATABASE_URL = "postgresql://postgres.PROJECT_REF:ENCODED_PASSWORD@POOLER_HOST:5432/postgres?sslmode=verify-full"
DATAFLOW_SSL_ROOT_CERT = "system"
```

4. Créer le schéma et vérifier sa réexécution :

```powershell
.venv/Scripts/python.exe -m accounts.cli migrate
.venv/Scripts/python.exe -m accounts.cli migrate
```

Résultat attendu sur une destination neuve : migrations `1, 2`, puis « aucune, schéma à jour ». La base cible est modifiée uniquement lorsque vous exécutez ces commandes.

5. Dans une session `psql` opérateur TLS, attribuer un mot de passe au rôle via `\password dataflow_app` (saisie masquée), puis :

```sql
ALTER ROLE dataflow_app LOGIN;
GRANT CONNECT ON DATABASE postgres TO dataflow_app;
```

6. Ajouter l'URI du rôle restreint à la configuration locale et aux secrets Streamlit :

```toml
DATAFLOW_DATABASE_URL = "postgresql://dataflow_app.PROJECT_REF:ENCODED_PASSWORD@POOLER_HOST:5432/postgres?sslmode=verify-full"
DATAFLOW_SSL_ROOT_CERT = "system"
```

Ces valeurs sont des modèles à remplacer. Les noms et suffixes de rôles dépendent du type de connexion. Si le certificat n'est pas reconnu par les autorités système, indiquer le chemin du CA officiel dans `DATAFLOW_SSL_ROOT_CERT`. Ne pas transmettre l'URI de migration à l'application cloud. Ne pas activer `DATAFLOW_DB_BACKEND="sqlite"` dans le cloud.

7. Vérifier avec le compte applicatif :

```powershell
.venv/Scripts/python.exe -m accounts.cli check-db
```

Résultat attendu : « Connexion et version du schéma vérifiées. »

8. Transférer l'ADMIN réel, uniquement à votre initiative :

```powershell
.venv/Scripts/python.exe -m accounts.cli import-admin --source local-data/accounts.sqlite3 --email Abdel.bouzourine.ti@gmail.com
.venv/Scripts/python.exe -m accounts.cli import-admin --source local-data/accounts.sqlite3 --email Abdel.bouzourine.ti@gmail.com
```

Résultat attendu : `imported`, puis `unchanged`. Se reconnecter avec le mot de passe habituel. UUID, nom, courriel, hachage, rôle, statut et date sont conservés ; les sessions ne sont pas transférées. La commande refuse un compte cible différent. N'ajouter `--replace` qu'après revue et sauvegarde ; une confirmation textuelle est obligatoire. Un conflit de courriel entre UUID différents reste refusé.

## Streamlit Cloud et secrets facultatifs

Dans les secrets Streamlit, les clés obligatoires sont `DATAFLOW_DATABASE_URL` et la configuration de confiance TLS adaptée. Le réglage `DATAFLOW_SSL_ROOT_CERT` peut être omis si la valeur par défaut `system` fonctionne.

Pour la récupération par courriel, ajouter au besoin :

```toml
DATAFLOW_SMTP_HOST = "SMTP_HOST"
DATAFLOW_SMTP_PORT = "587"
DATAFLOW_SMTP_USER = "SMTP_USER"
DATAFLOW_SMTP_PASSWORD = "SMTP_PASSWORD"
DATAFLOW_SMTP_FROM = "ADRESSE_VERIFIEE"
```

Ne pas ajouter `DATAFLOW_MIGRATION_DATABASE_URL`, les paramètres `DATAFLOW_TEST_*`, les sauvegardes ou des identifiants administrateur SQL dans les secrets applicatifs cloud.

Le déploiement utilisera `app.py`, `pyproject.toml` et `uv.lock`, avec la version Python validée. `Lancer.cmd` reste local. Avant publication client, retirer le `server.address="127.0.0.1"` de la configuration cloud, adapter les mentions « traitement local » et vérifier les courriels depuis le cloud. Ces préparatifs de publication restent distincts de la migration et n'ont pas été déployés.

## Commandes Git — seulement après validation et préparation cloud

Le dépôt actuel est sur `main` et possède un remote `origin`. Vérifier les changements avant staging :

```powershell
git status --short
git diff --check
git diff --stat
git add .gitignore app.py pyproject.toml uv.lock
git add accounts/cli.py accounts/config.py accounts/service.py accounts/database.py accounts/errors.py accounts/migrate.py accounts/sqlite_schema.py
git add accounts/migrations/001_accounts.sql accounts/migrations/002_permissions.sql
git add ui/accounts.py scripts/launch.py scripts/package.py scripts/test_postgres.py
git add tests/conftest.py tests/test_accounts.py tests/test_database_config.py tests/test_postgres_migration.py
git add docs/MIGRATION_SUPABASE.md docs/VALIDATION_POSTGRESQL.md
git diff --cached --name-only
git diff --cached
```

Contrôler que la sélection ne contient aucun secret, base SQLite, sauvegarde, certificat privé, journal ou `reset_admin_local.py`. Puis seulement :

```powershell
git commit -m "Add verified PostgreSQL account storage and admin migration"
git push origin main
```

**Si Streamlit Cloud suit déjà `main`, le push peut déclencher son redéploiement automatiquement.** Préparer la base, le compte applicatif, l'ADMIN et les secrets Cloud avant ce push. Si la version en ligne est antérieure, les nouvelles clés peuvent être préparées sans remplacer son fichier SQLite ; la bascule définitive doit être planifiée avec suspension des inscriptions et des écritures.

Après la bascule, vérifier à distance la connexion ADMIN, une inscription FREE, les quotas, les trois langues et la persistance après redémarrage. Cette validation Supabase/Cloud reste à faire : les succès locaux ne démontrent pas la configuration réelle de votre projet hébergé.
