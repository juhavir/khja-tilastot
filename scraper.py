import requests
import json
import os

BASE_URL = "https://kiti.ampumaurheiluliitto.fi/api"
CLUB_KEYWORDS = ["KHJA", "KAUHAJOEN"]

def is_khja(seura_str):
    if not seura_str:
        return False
    seura = str(seura_str).upper()
    return any(kw in seura for kw in CLUB_KEYWORDS)

def run():
    print("Haetaan KITI-kilpailut...")
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        r = requests.get(f"{BASE_URL}/competitions", headers=headers, timeout=15)
        competitions = r.json() if r.status_code == 200 else []
    except Exception as e:
        print(f"Virhe: {e}")
        return

    khja_results = []

    # Käydään läpi tuoreet kilpailut
    for comp in competitions[:50]: # Haetaan 50 uusinta kilpailua
        comp_id = comp.get("id")
        comp_date = (comp.get("startDate") or "2026-01-01")[:10]
        comp_name = comp.get("name", "Kilpailu")

        if not comp_id:
            continue

        try:
            res = requests.get(f"{BASE_URL}/competitions/{comp_id}/results", headers=headers, timeout=5)
            if res.status_code != 200:
                continue

            rows = res.json()
            if isinstance(rows, dict):
                rows = rows.get("results", [])

            for row in rows:
                seura = row.get("club") or row.get("seura") or row.get("clubName", "")
                if is_khja(seura):
                    ampuja = row.get("athleteName") or f"{row.get('firstName', '')} {row.get('lastName', '')}".strip()
                    laji = row.get("eventName") or row.get("sport") or comp.get("sportName") or "Ammunta"
                    tulos = row.get("score") or row.get("totalScore") or row.get("result", 0)

                    try:
                        tulos_val = float(str(tulos).replace(",", "."))
                    except ValueError:
                        continue

                    khja_results.append({
                        "pvm": comp_date,
                        "kilpailu": comp_name,
                        "ampuja": ampuja,
                        "laji": laji,
                        "tulos": tulos_val
                    })
        except Exception:
            continue

    # Tallennetaan JSON-tiedostoon
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(khja_results, f, ensure_ascii=False, indent=2)
    
    print(f"Valmis! Päivitetty {len(khja_results)} KhjA-tulosta.")

if __name__ == "__main__":
    run()
