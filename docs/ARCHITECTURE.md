# Architecture et décisions

## Séparation des responsabilités

`etl/engine.py` ne dépend pas de Streamlit. Ses entrées sont des octets, des paramètres d’import et une recette JSON ; ses sorties sont des tables, un rapport et une archive en mémoire. L’interface orchestre la sélection des fichiers, les aperçus, la vérification des PDF et les consentements d’export partiel. Un futur traitement planifié pourra appeler le même moteur.

## Pipeline

1. Contrôler le format déclaré et les limites ; calculer SHA-256.
2. Extraire une ou plusieurs tables et valider leurs en-têtes.
3. Préparer les valeurs en texte pour éviter l’inférence implicite sur les identifiants.
4. Vérifier le schéma et l’attestation de revue PDF.
5. Concaténer les sources compatibles et ajouter la provenance.
6. Nettoyer, convertir et contrôler chaque colonne.
7. Détecter les doublons parmi les lignes valides uniquement.
8. Séparer données acceptées et valeurs originales en quarantaine.
9. Produire le rapport et le ZIP complet avant de proposer le téléchargement.

## Règles de fiabilité

- Les erreurs de parsing CSV refusent le fichier entier : aucune ligne mal formée n’est ignorée.
- Les types ou contraintes invalides rejettent la ligne, sans perte de sa valeur d’origine dans la quarantaine.
- Le nombre de lignes sources égale le nombre accepté plus le nombre rejeté.
- Les noms de sortie doivent être uniques ; le préfixe `_etl_` est réservé.
- Les transformations s’appliquent sur une copie des données.
- Les fichiers d’un lot ne sont assemblés que si leurs colonnes correspondent exactement, indépendamment de l’ordre d’en-tête.
- Le ZIP est produit en mémoire ; un échec ne crée pas de dossier de livraison partiellement écrit sur disque.
- L’import de recette valide les valeurs et la structure attendue ; il n’exécute aucun code utilisateur.
- L’état est propre à chaque session. Aucun cache global de données client n’est utilisé ; les extractions sont conservées dans l’état de session pour éviter les relectures à chaque interaction.

## Évolutions prévues

Extraire les importeurs dans un registre d’adaptateurs lorsque de nouveaux formats sont ajoutés. Versionner la recette si les paramètres d’extraction y sont intégrés. Pour la surveillance de dossier, ajouter une file de travaux, un stockage transactionnel, une clé d’idempotence fondée sur source + recette + paramètres, des écritures atomiques et une politique de reprise. Pour un service partagé, isoler les parseurs et ajouter délais d’exécution, quotas mémoire et authentification.
