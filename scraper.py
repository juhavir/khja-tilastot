import requests
import json

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
    khja_results = []
    
    try:
        r = requests.get(f"{BASE_URL}/competitions", headers=headers, timeout=15)
        res_data = r.json() if r.status_code == 200 else []
    except Exception as e:
        print(f"Kilpailulistan haussa virhe: {e}")
        res_data = []

    # Varmistetaan, että saadaan lista kilpailuista
    if isinstance(res_data, dict):
        competitions = res_data.get("competitions") or res_data.get("content") or res_data.get("data") or []
    elif isinstance(res_data, list):
        competitions = res_data
    else:
        competitions = []

    print(f"Löytyi {len(competitions)} kilpailua. Suodatetaan KhjA:n tulokset...")

    # Käydään läpi kilpailut
    for comp in competitions[:50]:
        if not isinstance(comp, dict):
            continue

        comp_id = comp.get("id")
        comp_date = (comp.get("startDate") or comp.get("date") or "2026-01-01")[:10]
        comp_name = comp.get("name", "Kilpailu")

        if not comp_id:
            continue

        try:
            res = requests.get(f"{BASE_URL}/competitions/{comp_id}/results", headers=headers, timeout=5)
            if res.status_code != 200:
                continue

            rows = res.json()
            if isinstance(rows, dict):
                rows = rows.get("results") or rows.get("content") or rows.get("data") or []

            if isinstance(rows, list):
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    
                    seura = row.get("club") or row.get("seura") or row.get("clubName", "")
                    if is_khja(seura):
                        ampuja = row.get("athleteName") or f"{row.get('firstName', '')} {row.get('lastName', '')}".strip() or "KhjA Ampuja"
                        laji = row.get("eventName") or row.get("sport") or comp.get("sportName") or "Ampumaurheilu"
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
        except Exception as err:
            print(f"Virhe kisan {comp_id} haussa: {err}")
            continue

    print(f"Löytyi {len(khja_results)} tulosta. Kirjoitetaan data.json...")
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(khja_results, f, ensure_ascii=False, indent=2)
    print("Valmis!")

if __name__ == "__main__":
    run()
