import requests
import json

BASE_URL = "https://kiti.ampumaurheiluliitto.fi/api"

# Tähän määritellään seurattavien ampujien Sportti-ID:t ja nimet
AMPUSLISTA = [
    {"nimi": "Emma Virtanen", "id": "60332562"},
    # Voit lisätä muita ampujia tähän tyyliin:
    # {"nimi": "Matti Meikäläinen", "id": "12345678"}
]

def run():
    print("Aloitetaan täsmällinen KITI-tuloshaku...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    
    khja_results = []
    
    try:
        r = requests.get(f"{BASE_URL}/competitions", headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"KITI-rajapinta palautti virheen: {r.status_code}")
            return
        
        comps = r.json()
        if isinstance(comps, dict):
            comps = comps.get("content") or comps.get("competitions") or []
    except Exception as e:
        print(f"Virhe kilpailujen haussa: {e}")
        comps = []

    print(f"Haettu {len(comps)} kilpailua. Suodatetaan urheilijoiden ID:t...")

    target_ids = {str(a["id"]).strip(): a["nimi"] for a in AMPUSLISTA if "id" in a}

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

                # Tarkistetaan Sportti-ID eri kentistä
                row_id = str(row.get("licenseNumber") or row.get("sportId") or row.get("personId") or row.get("athleteId") or "").strip()
                row_name = str(row.get("athleteName") or f"{row.get('lastName', '')} {row.get('firstName', '')}").strip()

                matched_name = None
                if row_id in target_ids:
                    matched_name = target_ids[row_id]
                else:
                    for tid, tname in target_ids.items():
                        if tname.lower() in row_name.lower() and len(tname) > 3:
                            matched_name = tname
                            break

                if matched_name:
                    laji = row.get("eventName") or row.get("sport") or comp.get("sportName") or "Ampumaurheilu"
                    tulos = row.get("score") or row.get("totalScore") or row.get("result", 0)

                    try:
                        tulos_val = float(str(tulos).replace(",", "."))
                    except (ValueError, TypeError):
                        continue

                    khja_results.append({
                        "pvm": comp_date,
                        "kilpailu": comp_name,
                        "ampuja": matched_name,
                        "laji": laji,
                        "tulos": tulos_val
                    })
        except Exception:
            continue

    print(f"Haettu yhteensä {len(khja_results)} tulosta.")

    # Tallennetaan löydetyt tulokset data.json-tiedostoon
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(khja_results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run()
