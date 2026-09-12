import requests
import json

BASE_URL = "https://kiti.ampumaurheiluliitto.fi/api"

# Tunnistetaan KhjA eri kirjoitusasuisina
CLUB_NAMES = ["KHJA", "KAUHAJOEN AMPUJAT", "KAUHAJOKI", "KAUHAJOEN"]

def check_club(row):
    # Käydään läpi kaikki mahdolliset seuranimen kentät KITI:ssä
    club_val = str(row.get("club") or row.get("clubName") or row.get("seura") or row.get("organization") or "").upper()
    return any(name in club_val for name in CLUB_NAMES)

def run():
    print("Haetaan kilpailulista KITI-järjestelmästä...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    
    khja_results = []

    try:
        r = requests.get(f"{BASE_URL}/competitions", headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"KITI API virhe: {r.status_code}")
            return
        
        comps = r.json()
        if isinstance(comps, dict):
            comps = comps.get("content") or comps.get("competitions") or []
    except Exception as e:
        print(f"Virhe kilpailulistan haussa: {e}")
        comps = []

    print(f"Löytyi {len(comps)} kilpailua. Etsitään aitoja KhjA-ampujia...")

    # Käydään läpi kilpailut
    for comp in comps:
        if not isinstance(comp, dict):
            continue

        comp_id = comp.get("id")
        comp_date = (comp.get("startDate") or comp.get("date") or comp.get("endDate") or "2026-01-01")[:10]
        comp_name = comp.get("name") or comp.get("title") or "Kilpailu"

        if not comp_id:
            continue

        # Haetaan kisan tulokset
        try:
            res = requests.get(f"{BASE_URL}/competitions/{comp_id}/results", headers=headers, timeout=5)
            if res.status_code != 200:
                continue

            data = res.json()
            rows = []
            
            if isinstance(data, list):
                rows = data
            elif isinstance(data, dict):
                rows = data.get("results") or data.get("content") or data.get("rows") or []

            for row in rows:
                if not isinstance(row, dict):
                    continue

                if check_club(row):
                    # Haetaan ampujan nimi KITI:n eri rakennevaihtoehdoista
                    firstName = row.get("firstName") or row.get("first_name") or ""
                    lastName = row.get("lastName") or row.get("last_name") or ""
                    full_name = f"{lastName} {firstName}".strip()
                    
                    if not full_name:
                        full_name = row.get("athleteName") or row.get("name") or row.get("competitor") or "Tuntematon Ampuja"

                    laji = row.get("eventName") or row.get("sport") or comp.get("sportName") or "Ampumaurheilu"
                    tulos = row.get("score") or row.get("totalScore") or row.get("result") or row.get("total", 0)

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

    print(f"Löytyi yhteensä {len(khja_results)} aitoa KhjA-tulosriviä.")
    
    # Tallennetaan löydetyt tulokset data.json-tiedostoon
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(khja_results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run()
