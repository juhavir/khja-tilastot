import requests
import json

BASE_URL = "https://kiti.ampumaurheiluliitto.fi/api"

# Tähän määritellään seurattavat ampujat ja heidän Sportti-ID:nsä
AMPUSLISTA = [
    {"nimi": "Emma Virtanen", "id": "60332562"}
]

def etsi_tulokset_syvalta(data, nykyinen_laji="Ampumaurheilu"):
    """
    Rekursiivinen haku, joka kaivaa tulosrivit esiin riippumatta 
    siitä, kuinka monen kansion tai sarjan taakse KITI on ne piilottanut.
    """
    results = []
    
    if isinstance(data, dict):
        # Päivitetään lajitieto, jos tasolta löytyy lajin tai sarjan nimi
        laji = data.get("eventName") or data.get("categoryName") or data.get("seriesName") or data.get("sportName") or nykyinen_laji
        
        # Tunnistetaan, onko tämä solmu yksittäisen urheilijan tulosrivi
        has_athlete = any(k in data for k in ["firstName", "lastName", "athleteName", "sportId", "licenseNumber", "personId"])
        has_score = any(k in data for k in ["score", "totalScore", "result", "total"])
        
        if has_athlete and has_score:
            data["_loytyi_laji"] = laji
            results.append(data)
        
        # Jatketaan porautumista syvemmälle sanakirjaan
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                results.extend(etsi_tulokset_syvalta(v, laji))
                
    elif isinstance(data, list):
        # Jatketaan porautumista listan sisälle
        for item in data:
            if isinstance(item, (dict, list)):
                results.extend(etsi_tulokset_syvalta(item, nykyinen_laji))
                
    return results

def run():
    print("Käynnistetään syvä KITI-haku (Deep Search)...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    
    khja_results = []
    target_ids = {str(a["id"]).strip(): a["nimi"] for a in AMPUSLISTA if a.get("id")}
    
    try:
        # Haetaan isompi massa kilpailuja kerralla
        r = requests.get(f"{BASE_URL}/competitions?size=150", headers=headers, timeout=15)
        if r.status_code != 200:
            print("KITI API virhe kilpailuhaussa.")
            return
            
        comps_data = r.json()
        comps = comps_data.get("content") or comps_data.get("competitions") or (comps_data if isinstance(comps_data, list) else [])
    except Exception as e:
        print(f"Verkkovirhe: {e}")
        return

    print(f"Tutkitaan {len(comps)} kilpailua...")

    for comp in comps:
        if not isinstance(comp, dict): continue
        comp_id = comp.get("id")
        if not comp_id: continue
        
        comp_date = str(comp.get("startDate") or comp.get("date") or "2026-01-01")[:10]
        comp_name = str(comp.get("name") or comp.get("title") or "Kilpailu")

        try:
            res = requests.get(f"{BASE_URL}/competitions/{comp_id}/results", headers=headers, timeout=10)
            if res.status_code != 200: continue
            
            # Päästetään syvähaku irti KITI:n palauttamaan rakenteeseen
            kaikki_rivit = etsi_tulokset_syvalta(res.json())
            
            for row in kaikki_rivit:
                row_id = str(row.get("licenseNumber") or row.get("sportId") or row.get("personId") or row.get("athleteId") or "").strip()
                row_name = str(row.get("athleteName") or f"{row.get('lastName', '')} {row.get('firstName', '')}").strip().lower()
                
                # Osuma 1: Sportti-ID
                match_name = target_ids.get(row_id)
                
                # Osuma 2: Nimi (jos ID:tä ei KITI-kisaan ole jostain syystä kirjattu)
                if not match_name:
                    for a in AMPUSLISTA:
                        if a["nimi"].lower() in row_name and len(a["nimi"]) > 4:
                            match_name = a["nimi"]
                            break

                if match_name:
                    laji = row.get("_loytyi_laji", "Ammunta")
                    tulos_raw = row.get("score") or row.get("totalScore") or row.get("result") or row.get("total", 0)
                    
                    try:
                        tulos_val = float(str(tulos_raw).replace(",", "."))
                        # Hylätään nollatulokset/virheet
                        if tulos_val > 0:
                            khja_results.append({
                                "pvm": comp_date,
                                "kilpailu": comp_name,
                                "ampuja": match_name,
                                "laji": laji,
                                "tulos": tulos_val
                            })
                    except (ValueError, TypeError):
                        continue
        except Exception:
            continue

    # Suodatetaan mahdolliset duplikaattirivit (KITI saattaa palauttaa saman rivin eri tasoilla)
    uniikit_tulokset = []
    seen = set()
    for r in khja_results:
        uid = f"{r['pvm']}_{r['ampuja']}_{r['laji']}_{r['tulos']}"
        if uid not in seen:
            seen.add(uid)
            uniikit_tulokset.append(r)

    print(f"Löydettiin {len(uniikit_tulokset)} tulosriviä!")
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(uniikit_tulokset, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run()import requests
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
