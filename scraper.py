import requests
import json

BASE_URL = "https://kiti.ampumaurheiluliitto.fi/api"

# 1. Kauhajoen Ampujien tunnistus ja tunnetut ampujat
KHJA_ALIASES = ["KHJA", "KAUHAJOEN AMPUJAT", "KAUHAJOKI"]

def is_khja_athlete(row):
    # Tarkistetaan kuuluuko seura KhjA-ryhmään
    seura = str(row.get("club") or row.get("seura") or row.get("clubName") or row.get("organization") or "").upper()
    if any(alias in seura for alias in KHJA_ALIASES):
        return True
    return False

def run():
    print("Aloitetaan KhjA-ampujien ja tulosten haku KITI:stä...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    
    khja_results = []

    try:
        r = requests.get(f"{BASE_URL}/competitions", headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"KITI API vastasi virheellä: {r.status_code}")
            return
        comps = r.json()
        if isinstance(comps, dict):
            comps = comps.get("content") or comps.get("competitions") or []
    except Exception as e:
        print(f"Virhe kisoja haettaessa: {e}")
        comps = []

    print(f"Löytyi {len(comps)} kilpailua KITI-kalenterista. Suodatetaan KhjA:n tulokset...")

    # Käydään läpi kilpailut
    for comp in comps:
        if not isinstance(comp, dict):
            continue

        comp_id = comp.get("id")
        comp_date = (comp.get("startDate") or comp.get("date") or "2026-01-01")[:10]
        comp_name = comp.get("name") or comp.get("title") or "Kilpailu"

        if not comp_id:
            continue

        try:
            res = requests.get(f"{BASE_URL}/competitions/{comp_id}/results", headers=headers, timeout=5)
            if res.status_code != 200:
                continue

            data = res.json()
            rows = data if isinstance(data, list) else (data.get("results") or data.get("content") or [])

            for row in rows:
                if not isinstance(row, dict):
                    continue

                # Jos ampuja edustaa Kauhajoen Ampujia (KhjA)
                if is_khja_athlete(row):
                    first_name = row.get("firstName") or row.get("first_name") or ""
                    last_name = row.get("lastName") or row.get("last_name") or ""
                    full_name = f"{last_name} {first_name}".strip()
                    
                    if not full_name:
                        full_name = row.get("athleteName") or row.get("name") or "KhjA Ampuja"

                    laji = row.get("eventName") or row.get("sport") or comp.get("sportName") or "Ampumaurheilu"
                    tulos = row.get("score") or row.get("totalScore") or row.get("result", 0)

                    try:
                        tulos_val = float(str(tulos).replace(",", "."))
                    except (ValueError, TypeError):
                        continue

                    khja_results.append({
                        "pvm": comp_date,
                        "kilpailu": comp_name,
                        "ampuja": full_name,
                        "laji": laji,
                        "tulos": tulos_val
                    })
        except Exception:
            continue

    print(f"Haettu yhteensä {len(khja_results)} KhjA:n tulosta.")

    # Tallennetaan löydetyt tulokset data.json tiedostoon
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(khja_results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run()
