export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET');
    res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate');

    const sporttiId = req.query.id;
    if (!sporttiId) {
        return res.status(400).json({ error: 'Sportti-ID puuttuu' });
    }

    const headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json, text/plain, */*'
    };

    try {
        // 1. Hae urheilijan sisäinen KITI-ID
        const searchUrl = `https://kiti.ampumaurheiluliitto.fi/api/athletes/?search=${sporttiId}`;
        const searchRes = await fetch(searchUrl, { headers });
        if (!searchRes.ok) throw new Error(`KITI-haku epäonnistui (${searchRes.status})`);

        const searchData = await searchRes.json();
        const athletes = Array.isArray(searchData) ? searchData : (searchData.results || searchData.content || searchData.data || []);

        let internalId = null;
        for (let ath of athletes) {
            if (String(ath.sportti_id) === String(sporttiId) || String(ath.license_code) === String(sporttiId) || String(ath.id) === String(sporttiId)) {
                internalId = ath.id || ath.person_id || ath.personId;
                break;
            }
        }
        if (!internalId && athletes.length > 0) internalId = athletes[0].id || athletes[0].person_id || athletes[0].personId;
        if (!internalId) return res.status(404).json({ error: `Ei löytynyt ampujaa Sportti-ID:llä ${sporttiId}.` });

        // 2. Hae urheilijan tulokset
        const resultsUrl = `https://kiti.ampumaurheiluliitto.fi/api/resultlist/?athlete=${internalId}`;
        const resultsRes = await fetch(resultsUrl, { headers });
        if (!resultsRes.ok) throw new Error(`Tulosten haku epäonnistui (${resultsRes.status})`);

        const resultsData = await resultsRes.json();
        const rows = Array.isArray(resultsData) ? resultsData : (resultsData.results || resultsData.content || resultsData.data || []);

        // 3. kerätään uniikit kilpailu-ID:t ja haetaan niiden viralliset kilpailupäivät KITI:stä
        const compIds = [...new Set(rows.map(r => r.competition_id || r.competitionId || (typeof r.competition === 'number' || typeof r.competition === 'string' ? r.competition : (r.competition && r.competition.id ? r.competition.id : null))).filter(Boolean))];
        
        const compMap = {};
        await Promise.all(compIds.map(async (cId) => {
            try {
                const cRes = await fetch(`https://kiti.ampumaurheiluliitto.fi/api/competitions/${cId}/`, { headers });
                if (cRes.ok) {
                    const cData = await cRes.json();
                    compMap[cId] = cData.start_date || cData.competition_start_date || cData.date || "";
                }
            } catch (e) {
                // Sivuutetaan yksittäiset virheet
            }
        }));

        // 4. Yhdistetään täsmällinen kisa-päivämäärä jokaiseen tulosriviin
        const formatoidutRows = rows.map(row => {
            const compId = row.competition_id || row.competitionId || (typeof row.competition === 'number' || typeof row.competition === 'string' ? row.competition : (row.competition && row.competition.id ? row.competition.id : null));
            
            let pvm = compMap[compId] || row.competition_start_date || row.start_date || "";
            if (!pvm && row.competition && typeof row.competition === 'object') {
                pvm = row.competition.start_date || row.competition.competition_start_date || row.competition.date || "";
            }

            return {
                ...row,
                todellinen_pvm: String(pvm).substring(0, 10)
            };
        });

        return res.status(200).json(formatoidutRows);

    } catch (error) {
        return res.status(500).json({ error: `Palvelinvirhe: ${error.message}` });
    }
}
