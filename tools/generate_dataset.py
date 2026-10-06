"""Génère le jeu de données « livraisons » du projet Fabric Pipeline Express 2.

Pour chaque journée, un manifeste liste les fichiers à charger (un par hub)
et le nombre minimal de lignes attendu. La journée du 2026-10-07 contient
volontairement un fichier incomplet pour le hub NANCY, afin de montrer
l'arrêt propre du pipeline par l'activité Fail.

Génération déterministe (graine fixe) : relancer ce script produit
exactement les mêmes fichiers.
"""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "data"
SEED = 2026

HUBS = {
    "METZ": {"rows": (430, 470), "cities": ["Metz", "Montigny-lès-Metz", "Woippy", "Marly", "Augny", "Ars-sur-Moselle", "Amnéville"], "cp": "57"},
    "NANCY": {"rows": (380, 420), "cities": ["Nancy", "Vandœuvre-lès-Nancy", "Laxou", "Villers-lès-Nancy", "Essey-lès-Nancy", "Tomblaine", "Maxéville"], "cp": "54"},
    "THIONVILLE": {"rows": (300, 340), "cities": ["Thionville", "Yutz", "Hayange", "Terville", "Florange", "Fameck", "Uckange"], "cp": "57"},
}
DAYS = ["2026-10-05", "2026-10-06", "2026-10-07"]
MIN_ROWS = {"METZ": 400, "NANCY": 350, "THIONVILLE": 280}
SERVICES = [("standard", 0.72), ("express", 0.28)]
STATUS = [("delivered", 0.91), ("failed", 0.06), ("returned", 0.03)]
TRUNCATED = {("2026-10-07", "NANCY"): 48}   # fichier volontairement incomplet


def pick(rng, options):
    r = rng.random()
    acc = 0.0
    for value, p in options:
        acc += p
        if r <= acc:
            return value
    return options[-1][0]


def make_rows(rng, hub, day, n):
    cfg = HUBS[hub]
    base = datetime.strptime(day, "%Y-%m-%d").replace(hour=7, minute=30)
    rows = []
    for i in range(n):
        service = pick(rng, SERVICES)
        status = pick(rng, STATUS)
        minutes_from_start = int(rng.triangular(0, 660, 300))
        when = base + timedelta(minutes=minutes_from_start)
        distance = round(rng.uniform(1.2, 38.0), 1)
        duration = int(distance * rng.uniform(1.8, 3.2) + rng.uniform(4, 14))
        sla = 45 if service == "express" else 120
        on_time = "yes" if (status == "delivered" and duration <= sla) else "no"
        city = rng.choice(cfg["cities"])
        rows.append({
            "parcel_id": f"{hub[:3]}-{day.replace('-', '')}-{i + 1:04d}",
            "hub": hub,
            "delivery_datetime": when.strftime("%Y-%m-%d %H:%M:%S"),
            "driver_id": f"D{hub[:1]}{rng.randint(1, 18):02d}",
            "customer_city": city,
            "postal_code": f"{cfg['cp']}{rng.randint(0, 999):03d}",
            "service": service,
            "weight_kg": round(rng.lognormvariate(0.6, 0.7), 2),
            "distance_km": distance,
            "delivery_minutes": duration,
            "status": status,
            "on_time": on_time,
        })
    rows.sort(key=lambda r: r["delivery_datetime"])
    for i, r in enumerate(rows, start=1):
        r["parcel_id"] = f"{hub[:3]}-{day.replace('-', '')}-{i:04d}"
    return rows


def main():
    rng = random.Random(SEED)
    ROOT.mkdir(parents=True, exist_ok=True)
    summary = []
    for day in DAYS:
        manifest = []
        for hub in HUBS:
            n = rng.randint(*HUBS[hub]["rows"])
            rows = make_rows(rng, hub, day, n)
            keep = TRUNCATED.get((day, hub))
            if keep:
                rows = rows[:keep]
            name = f"deliveries_{hub}_{day}.csv"
            with open(ROOT / name, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
            manifest.append({"hub": hub, "file": name, "min_rows": MIN_ROWS[hub]})
            summary.append((day, hub, len(rows), MIN_ROWS[hub]))
        with open(ROOT / f"manifest_{day}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["hub", "file", "min_rows"])
            w.writeheader()
            w.writerows(manifest)
    for day, hub, n, m in summary:
        flag = "" if n >= m else "   <-- incomplet"
        print(f"{day}  {hub:<11} {n:>4} lignes  (minimum {m}){flag}")


if __name__ == "__main__":
    main()
