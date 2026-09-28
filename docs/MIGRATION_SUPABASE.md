# Migration des comptes vers Supabase PostgreSQL

Cette procédure conserve l'authentification Python/Argon2 existante. Elle n'utilise pas Supabase Auth et ne copie aucun fichier ETL dans Supabase. Aucun déploiement ou transfert distant n'est exécuté automatiquement.

## 1. Architecture et changements

- `accounts/database.py` : accès SQLite/PostgreSQL et transactions.
- `accounts/config.py` : variables d'environnement prioritaires, puis `.streamlit/secrets.toml` ignoré par Git.
- `accounts/service.py` : mêmes rôles, quotas, sessions et règles métier ; SQL portable.
- `accounts/migrations/001_accounts.sql` : schéma privé `dataflow`, neuf tables et contraintes.
- `accounts/migrations/002_permissions.sql` : rôle applicatif restreint et version 2.
- `accounts/migrate.py` et `accounts/cli.py` : opérations explicites de migration.

Le schéma PostgreSQL garde les identifiants et dates ISO textuels pour préserver les données existantes. Les horodatages de session utilisent `DOUBLE PRECISION`, pour conserver la précision des secondes Unix. L'unicité des courriels est insensible à la casse via un index sur `lower(email)`.

Les courtes transactions prennent un verrou consultatif PostgreSQL transactionnel commun. C'est l'équivalent conservateur de la sérialisation `BEGIN IMMEDIATE` de SQLite : réservation des quotas, limitation des tentatives, réinitialisation des mots de passe et protection du dernier ADMIN sont atomiques. Les travaux ETL et le calcul Argon2 restent hors verrou. Cette stratégie privilégie la sûreté pour le pilote ; elle sérialise les écritures de comptes entre utilisateurs et devra être mesurée avant une montée en charge importante. Le délai de verrou est limité à 15 secondes.

## 2. Configuration Supabase et TLS

Créer un projet Supabase. Dans **Connect**, sélectionner une connexion directe ou le **Session pooler** compatible avec le réseau de l'hébergement. Ne pas utiliser le Transaction pooler : l'application initialise aussi des paramètres de session PostgreSQL. Utiliser le nom DNS exact du certificat, pas une adresse IP de substitution.

Le pilote impose `sslmode=verify-full` : chaîne de confiance ET nom du serveur vérifiés. Une URI contenant `sslmode=require`, `prefer` ou `disable` est refusée ; retirer ce paramètre ou le remplacer par `verify-full`.

Par défaut, `DATAFLOW_SSL_ROOT_CERT="system"` utilise les autorités de confiance du système via libpq. Si l'endpoint utilise une autorité non reconnue, télécharger son certificat CA depuis le tableau de bord officiel Supabase et définir `DATAFLOW_SSL_ROOT_CERT` vers ce fichier. Ne jamais désactiver la vérification pour contourner une erreur. Le certificat CA public peut être livré dans `certificates/` ; ne jamais y mettre de clé privée.

Documentation : [TLS PostgreSQL](https://www.postgresql.org/docs/current/libpq-ssl.html), [connexions Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres).

## 3. Variables et secrets

Créer localement `.streamlit/secrets.toml` (ne jamais le committer). Le CLI le lit également, sans démarrer Streamlit. Les variables d'environnement `DATAFLOW_*` ont priorité sur ce fichier. Les fichiers `.env` ne sont pas chargés automatiquement.

```toml
# Compte restreint : seul cet identifiant doit être fourni à l'application cloud.
DATAFLOW_DATABASE_URL = "postgresql://dataflow_app.PROJECT_REF:ENCODED_PASSWORD@POOLER_HOST:5432/postgres"
DATAFLOW_SSL_ROOT_CERT = "system"

# Uniquement sur le poste de l'opérateur, jamais dans les secrets de l'application cloud.
DATAFLOW_MIGRATION_DATABASE_URL = "postgresql://postgres.PROJECT_REF:ENCODED_PASSWORD@POOLER_HOST:5432/postgres"
```

Ce sont des modèles : reprendre les hôtes, ports et suffixes de rôle fournis pour le projet. Avec une connexion directe, les noms d'utilisateurs n'ont généralement pas le suffixe du pooler. Encoder les caractères spéciaux du mot de passe dans l'URI. Ne pas coller les URI réelles dans un terminal partagé, une conversation, un ticket ou GitHub.

Sur Community Cloud, saisir les clés applicatives dans **Settings → Secrets**, à la racine TOML. [Documentation Streamlit](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

Sans URL valide, le démarrage échoue. Il ne crée jamais une base SQLite de secours. Pour utiliser volontairement SQLite en local uniquement :

```toml
DATAFLOW_DB_BACKEND = "sqlite"
DATAFLOW_DB_PATH = "local-data/accounts.sqlite3"
```

Ne pas combiner cette option avec une URL PostgreSQL : une URL présente reste prioritaire, même si elle est invalide. `Lancer.cmd` garde le démarrage SQLite local si aucune URL ni aucun fichier de secrets n'est fourni ; cette logique n'est pas utilisée dans le cloud.

## 4. Sauvegarder avant toute migration

Arrêter les écritures pendant la sauvegarde et le transfert. Conserver une sauvegarde cohérente de SQLite avec son API de sauvegarde (ne pas copier seulement le fichier principal pendant des écritures WAL). Pour la destination existante, réaliser aussi une sauvegarde PostgreSQL avant un éventuel remplacement. Les sauvegardes contiennent des données sensibles et restent hors GitHub.

La commande `import-admin` transfère uniquement l'ADMIN nommé. Elle ne migre ni les autres utilisateurs, ni l'historique des quotas, ni les sessions, ni les jetons de récupération. Si d'autres comptes doivent être conservés, préparer une migration complète supplémentaire avant d'ouvrir le service au public. Ne pas supprimer la base SQLite source.

## 5. Créer les tables avec le compte de migration

Depuis la racine du projet, dans PowerShell :

```powershell
uv sync --locked
.venv/Scripts/python.exe -m accounts.cli migrate
```

Cette commande exige `DATAFLOW_MIGRATION_DATABASE_URL`. Elle exécute les fichiers SQL versionnés dans une transaction et note leurs versions. Une seconde exécution ne modifie pas les comptes ni les plans existants. Aucune table n'est supprimée. Une version inconnue est refusée. Les futurs changements doivent être ajoutés dans de nouveaux fichiers numérotés, sans réécrire les migrations déjà appliquées.

Ne pas exposer le schéma `dataflow` dans la configuration Data API/PostgREST de Supabase. Les rôles `PUBLIC`, `anon` et `authenticated` n'y reçoivent aucun accès. L'isolation utilisateur est assurée par le service Python : aucun navigateur ne reçoit les identifiants SQL.

## 6. Activer le compte applicatif restreint

La migration crée `dataflow_app` sans droit de connexion et sans mot de passe. Avec une session `psql` opérateur configurée en TLS vérifié :

```text
\password dataflow_app
```

Cette commande demande le nouveau mot de passe en saisie masquée. Ensuite :

```sql
ALTER ROLE dataflow_app LOGIN;
GRANT CONNECT ON DATABASE postgres TO dataflow_app;
```

Adapter le nom de la base si nécessaire. Conserver l'identifiant privilégié uniquement pour l'opérateur. Ne jamais faire de `dataflow_app` le propriétaire du schéma et ne pas lui donner `CREATE`, `SUPERUSER`, `CREATEROLE` ou un rôle privilégié parent.

Le rôle applicatif dispose de SELECT sur les versions, SELECT/UPDATE sur les plans, SELECT/INSERT/UPDATE sur les comptes et usages, des opérations nécessaires sur sessions/récupération/rate_limits, et SELECT/INSERT sur l'audit. Il ne peut ni modifier le schéma, ni supprimer des utilisateurs ou l'audit.

## 7. Transférer le compte ADMIN

```powershell
.venv/Scripts/python.exe -m accounts.cli import-admin --source local-data/accounts.sqlite3 --email Abdel.bouzourine.ti@gmail.com
```

Le compte source doit déjà être ADMIN. La source est ouverte en lecture seule. Les identifiants, nom, courriel, hachage Argon2, rôle, statut, quota personnalisé et date de création sont conservés. Aucun mot de passe ou hachage n'est affiché. Aucune session source n'est importée : se reconnecter avec le mot de passe habituel après le transfert.

- Un compte cible strictement identique donne `unchanged`, sans doublon.
- Un compte cible différent est refusé.
- Un conflit de courriel avec un autre identifiant est toujours refusé : résolution manuelle nécessaire.
- Pour remplacer les champs du même identifiant, ajouter `--replace`. Le CLI impose de saisir `REMPLACER adresse@exemple.com`. Cela invalide aussi les sessions et codes de récupération de ce compte cible. Ne le faire qu'après sauvegarde.

L'import ajoute un événement d'audit sans identifiants de connexion ni hachage. Il est destiné à un opérateur de confiance, jamais à une route publique.

## 8. Vérifier et déployer seulement après validation

```powershell
.venv/Scripts/python.exe -m accounts.cli check-db
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check app.py accounts etl ui tests scripts
```

`check-db` utilise le compte applicatif et vérifie la connexion et la version du schéma. Les tests ordinaires utilisent SQLite ; les tests PostgreSQL sont explicitement ignorés si le serveur de test n'est pas configuré.

Pour exécuter les mêmes contrats sur un vrai serveur local PostgreSQL, avec certificat TLS de test et rôle applicatif restreint :

```powershell
.venv/Scripts/python.exe scripts/test_postgres.py --bin-dir CHEMIN_VERS_POSTGRESQL/bin
```

Le script crée une base isolée nommée `dataflow_test`, génère ses propres certificats, démarre le serveur uniquement sur 127.0.0.1, lance les tests, puis arrête le serveur. Il ne lit aucune URI Supabase. Les fichiers et journaux restent dans `.postgres-test/`, ignoré par Git. Ne pas exécuter les tests de remise à zéro sur une base client.

Les vérifications couvrent FREE, connexion/déconnexion, ADMIN, mauvais identifiants, récupération, quotas et échecs ETL, ADMIN illimité, rôles, désactivation, persistance, concurrence, isolation, import idempotent, permissions SQL et refus des certificats invalides.

Après validation, publier le code sans `.streamlit/secrets.toml`, `.env`, `local-data/`, `.postgres-test/`, sauvegardes ou journaux. Sur Streamlit Cloud, conserver `app.py`, `pyproject.toml` et `uv.lock`, renseigner uniquement les secrets applicatifs, puis vérifier inscription, connexion ADMIN, changement de langue et conservation des comptes après redémarrage.

Avant une ouverture client, adapter également les mentions « traitement local » au traitement sur le serveur cloud et tester le service de courriel.

## 9. Retour arrière

1. Suspendre les nouvelles écritures et noter l'heure de coupure.
2. Sauvegarder PostgreSQL et conserver les deux bases. Ne supprimer aucune table.
3. Revenir à la version applicative précédente si elle reste compatible avec le stockage choisi.
4. Pour une reprise locale SQLite, enlever les URL PostgreSQL de l'environnement ET du fichier de secrets, puis activer explicitement `DATAFLOW_DB_BACKEND="sqlite"` avec le chemin de la sauvegarde vérifiée.
5. Tester la connexion et les comptes avant la réouverture locale. Ne pas utiliser SQLite comme retour arrière persistant dans Community Cloud.
6. Les comptes et changements apparus dans PostgreSQL depuis la coupure ne sont pas automatiquement dans l'ancienne SQLite. Les réconcilier avant toute reprise ; aucune synchronisation inverse automatique n'est fournie.

L'ancienne base demeure intacte, mais revenir à une sauvegarde antérieure sans cette réconciliation ferait perdre les mises à jour récentes. Prévoir une restauration PostgreSQL pour un retour arrière cloud.
