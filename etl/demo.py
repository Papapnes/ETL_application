from .engine import default_recipe, extract

CSV = """commande;client;region;montant;date;statut
0001; Atelier Nord ;Québec;1250,50;2026-01-05; PAYÉ 
0002;Studio Rivage;Montréal;820,00;2026-01-06;PAYÉ
0003;Maison Lune;Québec;430,75;2026-01-07;EN ATTENTE
0003;Maison Lune;Québec;430,75;2026-01-07;EN ATTENTE
0004;Bureau Horizon;Ottawa;2100,00;2026-01-08;PAYÉ
0005;;Montréal;650,00;2026-01-09;EN ATTENTE
0006;Collectif Azur;Québec;à vérifier;2026-01-10;PAYÉ
0007;Studio Pin;Ottawa;975,25;2026-01-11;PAYÉ
0008;Maison Élan;Montréal;310,00;2026-02-30;PAYÉ
0009; Atelier Nord ;Québec;740,00;2026-01-13; PAYÉ
0010;Bureau Horizon;Ottawa;1540,00;2026-01-14;EN ATTENTE
0011;Studio Rivage;Montréal;560,50;2026-01-15;PAYÉ
"""


def demo():
    datasets = extract("ventes_demo.csv", CSV.encode("utf-8"), {"delimiter": ";"})
    recipe = default_recipe(list(datasets[0].frame.columns))
    recipe.update(name="Préparation des ventes", deduplicate=True, duplicate_keys=["commande"])
    for rule in recipe["rules"]:
        rule["required"] = rule["column"] in ["commande", "client", "montant", "date"]
        if rule["column"] == "montant":
            rule.update(type="Décimal", decimal=",", minimum="0")
        elif rule["column"] == "date":
            rule["type"] = "Date"
        elif rule["column"] == "statut":
            rule["case"] = "Minuscules"
    return datasets, recipe
