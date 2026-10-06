"""Rejoue la logique du pipeline PL_Deliveries_Express sur les fichiers de data/
et imprime les chiffres que vous devez retrouver dans Fabric.

Règles reproduites :
  - chaque fichier du manifeste est copié, puis comparé à min_rows ;
  - un fichier incomplet est retiré de la zone brute ; la boucle termine les
    autres hubs puis est marquée en échec, et la table n'est pas touchée ;
  - la table deliveries est reconstruite à partir de toute la zone brute.
"""
import csv
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
RUNS = ["2026-10-05", "2026-10-06", "2026-10-07", "2026-10-05"]


def read(name):
    with open(DATA / name, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    raw = {}   # (load_date, hub) -> rows présentes dans la zone brute
    for day in RUNS:
        print(f"\n=== Exécution load_date = {day} ===")
        manifest = read(f"manifest_{day}.csv")
        report = []
        failed = False
        for entry in manifest:
            rows = read(entry["file"])
            raw[(day, entry["hub"])] = rows
            if len(rows) >= int(entry["min_rows"]):
                report.append(f"{entry['hub']} : {len(rows)} lignes")
                print(f"  Copy hub file  {entry['hub']:<11} rowsCopied = {len(rows):>4}  >= {entry['min_rows']}  OK")
            else:
                del raw[(day, entry["hub"])]
                print(f"  Copy hub file  {entry['hub']:<11} rowsCopied = {len(rows):>4}  <  {entry['min_rows']}  -> Delete data + Fail")
                failed = True
        if failed:
            print("  For each hub en échec : Send failure alert. Load table ignoré, la table n'est pas touchée.")
            continue
        table = [r for rows in raw.values() for r in rows]
        print(f"  Load table     rowsCopied = {len(table)}  (table deliveries reconstruite)")
        print(f"  Send report    « {' ; '.join(report)} »")
        delivered = sum(1 for r in table if r["status"] == "delivered")
        on_time = sum(1 for r in table if r["on_time"] == "yes")
        print(f"  Vérification SQL : {len(table)} lignes, {delivered} livrées ({delivered / len(table):.1%}), {on_time} à l'heure ({on_time / len(table):.1%})")
        per_hub = {}
        for r in table:
            per_hub[r["hub"]] = per_hub.get(r["hub"], 0) + 1
        print("  Par hub : " + ", ".join(f"{h} {n}" for h, n in sorted(per_hub.items())))
    print("\nZone brute finale : " + ", ".join(f"{d}/{h} ({len(r)})" for (d, h), r in sorted(raw.items())))


if __name__ == "__main__":
    main()
