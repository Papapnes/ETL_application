"""Run with: python -m accounts.cli create-admin (trusted server operator only)."""

import argparse
from getpass import getpass

from accounts.config import database_path
from accounts.service import AccountError, Accounts


def main():
    parser = argparse.ArgumentParser(description="Administration locale DataFlow Studio")
    parser.add_argument("command", choices=["create-admin", "recover-run"])
    args = parser.parse_args()
    service = Accounts(database_path())
    try:
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
    except AccountError as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
