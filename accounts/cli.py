"""Run with: python -m accounts.cli create-admin (trusted server operator only)."""

import argparse
from getpass import getpass

from accounts.config import database_config
from accounts.errors import DatabaseError
from accounts.migrate import import_admin, migrate_schema
from accounts.service import AccountError, Accounts


def main():
    parser = argparse.ArgumentParser(description="Administration locale DataFlow Studio")
    parser.add_argument(
        "command", choices=["create-admin", "recover-run", "migrate", "import-admin", "check-db"]
    )
    parser.add_argument("--source", help="Chemin de la base SQLite source (lecture seule)")
    parser.add_argument("--email", help="Adresse du compte ADMIN source")
    parser.add_argument("--replace", action="store_true", help="Demander confirmation du remplacement")
    args = parser.parse_args()
    try:
        if args.command == "migrate":
            applied = migrate_schema(database_config(migration=True))
            print("Migrations appliquées : " + (", ".join(map(str, applied)) or "aucune, schéma à jour"))
            return
        if args.command == "import-admin":
            if not args.source or not args.email:
                parser.error("--source et --email sont requis")
            if args.replace:
                expected = "REMPLACER " + args.email
                if input(f"Le compte cible pourra être écrasé. Saisissez {expected} : ") != expected:
                    print("Opération annulée.")
                    return
            outcome = import_admin(
                database_config(migration=True), args.source, args.email, replace=args.replace
            )
            print("Migration du compte : " + outcome + ". Aucune session source transférée.")
            return
        service = Accounts(database_config())
        if args.command == "check-db":
            with service.connection() as db:
                db.execute("SELECT 1").fetchone()
            print("Connexion et version du schéma vérifiées.")
            return
        if args.command == "create-admin":
            name = input("Nom complet : ").strip()
            email = input("Courriel administrateur : ").strip()
            password = getpass("Mot de passe (12 à 128 caractères, saisie masquée) : ")
            if password != getpass("Confirmez le mot de passe : "):
                raise AccountError("Les mots de passe ne correspondent pas.")
            service.bootstrap_admin(name, email, password)
            print("Compte administrateur créé. Vous pouvez vous connecter dans l’application.")
        else:
            print("Arrêtez le serveur et vérifiez que le traitement ne s’exécute plus avant de continuer.")
            if input("Saisissez SERVEUR ARRETE pour confirmer : ") != "SERVEUR ARRETE":
                return
            service.release_failed_reservation(input("Identifiant d’exécution interrompue : ").strip())
            print("Réservation libérée sans comptabilisation.")
    except (AccountError, DatabaseError) as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
