export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET');

    const sporttiId = req.query.id;
    if (!sporttiId) {
        return res.status(400).json({ error: 'Sportti-ID puuttuu' });
    }

    const headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json, text/plain, */*'
    };

    try {
        const searchUrl = `https://kiti.ampumaurheiluliitto.fi/api/athletes/?search=${sporttiId}`;
        const searchRes = await fetch(searchUrl, { headers });
        
        if (!searchRes.ok) {
            return res.status(searchRes.status).json({ error: `KITI-haku epäonnistui (${searchRes.status})` });
        }

        const searchData = await searchRes.json();
        const athletes = Array.isArray(searchData) ? searchData : (searchData.results || searchData.content || searchData.data || []);

        let internalId = null;
        for (let ath of athletes) {
            if (String(ath.sportti_id) === String(sporttiId) || String(ath.license_code) === String(sporttiId) || String(ath.id) === String(sporttiId)) {
                internalId = ath.id || ath.person_id || ath.personId;
                break;
            }
        }

        if (!internalId && athletes.length > 0) {
            internalId = athletes[0].id || athletes[0].person_id || athletes[0].personId;
        }

        if (!internalId) {
            return res.status(404).json({ error: `Ei löytynyt ampujaa Sportti-ID:llä ${sporttiId}.` });
        }

        const resultsUrl = `https://kiti.ampumaurheiluliitto.fi/api/resultlist/?athlete=${internalId}&ordering=-competition_start_date`;
        const resultsRes = await fetch(resultsUrl, { headers });

        if (!resultsRes.ok) {
            return res.status(resultsRes.status).json({ error: `Tulosten haku epäonnistui (${resultsRes.status})` });
        }

        const resultsData = await resultsRes.json();
        const rows = Array.isArray(resultsData) ? resultsData : (resultsData.results || resultsData.content || resultsData.data || []);

        // Varmistetaan, että jokaiselle riville poimitaan KITI:n taulukossa näkyvä päivämäärä
        const formatoidutRows = rows.map(row => {
            let pvm = "";
            if (row.start_date) pvm = row.start_date;
            else if (row.competition_start_date) pvm = row.competition_start_date;
            else if (row.startDate) pvm = row.startDate;
            else if (row.competitionStartDate) pvm = row.competitionStartDate;
            else if (row.competition && typeof row.competition === 'object') {
                pvm = row.competition.start_date || row.competition.startDate || row.competition.date || "";
            }
            else if (row.date) pvm = row.date;

            return {
                ...row,
                pvm_kiti: String(pvm).substring(0, 10)
            };
        });

        return res.status(200).json(formatoidutRows);

    } catch (error) {
        return res.status(500).json({ error: `Palvelinvirhe: ${error.message}` });
    }
}
