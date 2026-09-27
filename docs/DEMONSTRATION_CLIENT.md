# Démonstration client — environ 5 minutes

## Préparer la présentation

Lancer l’application avec `Lancer.cmd`, ouvrir http://127.0.0.1:8501 et vérifier l’affichage avant la réunion. Utiliser une fenêtre suffisamment large pour les règles de colonnes. Le jeu présenté est fictif et clairement identifié.

## Déroulé

Choisir la langue du client dans **Langue / Language / اللغة** (FR, EN ou AR). Le nom Abdelkader Bouzourine, le titre professionnel traduit et le lien LinkedIn se trouvent en bas de la barre latérale gauche. Les étapes ci-dessous emploient les libellés français ; le parcours est identique dans les trois langues.

1. Depuis l’accueil, cliquer sur **Explorer la démonstration**.
2. Montrer les identifiants `0001`, les espaces autour de certains noms, les montants à virgule et la recette préconfigurée.
3. Cliquer sur **Appliquer et contrôler**.
4. Résultat attendu : **12 lignes sources, 8 valides, 4 en quarantaine dont 1 doublon**.
5. Dans Quarantaine, montrer les quatre causes : commande répétée, client manquant, montant non numérique et date impossible.
6. Dans Données valides, montrer les identifiants préservés, noms nettoyés et statuts en minuscules. Dans Traçabilité, montrer l’empreinte de source.
7. Passer à l’export. Choisir Excel ou CSV, accepter l’export partiel et générer le ZIP.
8. Télécharger le dossier et la recette. Expliquer que la recette s’applique au prochain fichier de même structure.

## Démontrer la répétabilité

Les fichiers `examples/ventes_demo.csv`, `examples/ventes_suivantes.csv` et `examples/recette_ventes.json` sont fournis. Importer le second lot, charger la recette dans Préparer puis appliquer. Résultat attendu : 3 lignes valides, aucun rejet. Le ZIP doit aussi être générable sans case d’acceptation de quarantaine.

## Positionnement honnête

Présenter cette version comme un pilote local opérationnel. Les formats annoncés sont testés sur des exemples contrôlés ; les mises en page PDF arbitraires et les classeurs complexes nécessitent une validation sur les documents du client. La promesse est la répétabilité de traitements explicites, pas une compréhension automatique de n’importe quel fichier.

## Recette avec le client

- Confirmer ses fichiers prioritaires, encodages, structure des feuilles et volumes habituels.
- Définir le sens d’un doublon, les champs obligatoires et les formats de date.
- Contrôler un export dans son outil d’analyse, notamment les types, les décimales et les identifiants.
- Décider si un résultat partiel est acceptable et qui contrôle la quarantaine.
- Valider la nécessité d’OCR, de planification, de SQL ou d’un historique durable pour la phase suivante.

