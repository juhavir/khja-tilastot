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
        // 1. Hae urheilija
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

        // 2. Hae tuloslista
        const resultsUrl = `https://kiti.ampumaurheiluliitto.fi/api/resultlist/?athlete=${internalId}`;
        const resultsRes = await fetch(resultsUrl, { headers });
        if (!resultsRes.ok) throw new Error(`Tulosten haku epäonnistui (${resultsRes.status})`);

        const resultsData = await resultsRes.json();
        const rows = Array.isArray(resultsData) ? resultsData : (resultsData.results || resultsData.content || resultsData.data || []);

        // 3. Etsitään kilpailutunnisteet (competition ID)
        const getCompId = (r) => {
            if (r.competition_id) return r.competition_id;
            if (r.competitionId) return r.competitionId;
            if (typeof r.competition === 'number' || typeof r.competition === 'string') return r.competition;
            if (r.competition && r.competition.id) return r.competition.id;
            if (r.event_id) return r.event_id;
            if (r.event && r.event.id) return r.event.id;
            return null;
        };

        const compIds = [...new Set(rows.map(getCompId).filter(Boolean))];

        // 4. Haetaan jokaiselle kilpailulle sen virallinen alkamispäivä KITI:n competition API:sta
        const compDateMap = {};
        await Promise.all(compIds.map(async (cId) => {
            try {
                const cRes = await fetch(`https://kiti.ampumaurheiluliitto.fi/api/competitions/${cId}/`, { headers });
                if (cRes.ok) {
                    const cData = await cRes.json();
                    const pvm = cData.start_date || cData.competition_start_date || cData.date || cData.startDate || "";
                    if (pvm) compDateMap[cId] = String(pvm).substring(0, 10);
                }
            } catch (e) {
                // Sivuutetaan yksittäisen kisan hakuvirhe
            }
        }));

        // 5. Muodostetaan lopullinen data
        const formatoidutRows = rows.map(row => {
            const cId = getCompId(row);
            let pvm = compDateMap[cId] || "";

            // Varalla rekursiivinen haku jos competition API ei palauttanut pvm:ää
            if (!pvm) {
                if (row.competition_start_date) pvm = row.competition_start_date;
                else if (row.start_date) pvm = row.start_date;
                else if (row.startDate) pvm = row.startDate;
                else if (row.competition && typeof row.competition === 'object') {
                    pvm = row.competition.start_date || row.competition.competition_start_date || row.competition.date || "";
                }
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
