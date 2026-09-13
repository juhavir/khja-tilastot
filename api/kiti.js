export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET');

    const id = req.query.id;
    if (!id) {
        return res.status(400).json({ error: 'Sportti-ID puuttuu' });
    }

    const headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json, text/plain, */*'
    };

    try {
        // 1. Haetaan suoraan tulokset Sportti-ID:llä tai urheilijahaulla
        let resultsUrl = `https://kiti.ampumaurheiluliitto.fi/api/resultlist/?athlete_id=${id}&ordering=-competition_start_date`;
        let resultsRes = await fetch(resultsUrl, { headers });
        let resultsData = await resultsRes.json();
        
        let rows = Array.isArray(resultsData) ? resultsData : (resultsData.results || resultsData.content || resultsData.data || []);

        // 2. Jos suora haku ei tärpännyt, etsitään sisäinen ID urheilijalistauksesta
        if (rows.length === 0) {
            const searchUrl = `https://kiti.ampumaurheiluliitto.fi/api/athletes/?sportti_id=${id}`;
            const searchRes = await fetch(searchUrl, { headers });
            
            if (searchRes.ok) {
                const searchData = await searchRes.json();
                const athletes = Array.isArray(searchData) ? searchData : (searchData.results || searchData.content || searchData.data || []);
                
                if (athletes.length > 0 && (athletes[0].id || athletes[0].personId)) {
                    const internalId = athletes[0].id || athletes[0].personId;
                    resultsUrl = `https://kiti.ampumaurheiluliitto.fi/api/resultlist/?athlete=${internalId}&ordering=-competition_start_date`;
                    resultsRes = await fetch(resultsUrl, { headers });
                    resultsData = await resultsRes.json();
                    rows = Array.isArray(resultsData) ? resultsData : (resultsData.results || resultsData.content || resultsData.data || []);
                }
            }
        }

        // 3. Kolmas oljenkorsi: yleishaku
        if (rows.length === 0) {
            const searchUrl2 = `https://kiti.ampumaurheiluliitto.fi/api/athletes/?search=${id}`;
            const searchRes2 = await fetch(searchUrl2, { headers });
            if (searchRes2.ok) {
                const searchData2 = await searchRes2.json();
                const athletes2 = Array.isArray(searchData2) ? searchData2 : (searchData2.results || searchData2.content || searchData2.data || []);
                if (athletes2.length > 0 && (athletes2[0].id || athletes2[0].personId)) {
                    const internalId = athletes2[0].id || athletes2[0].personId;
                    resultsUrl = `https://kiti.ampumaurheiluliitto.fi/api/resultlist/?athlete=${internalId}&ordering=-competition_start_date`;
                    resultsRes = await fetch(resultsUrl, { headers });
                    resultsData = await resultsRes.json();
                    rows = Array.isArray(resultsData) ? resultsData : (resultsData.results || resultsData.content || resultsData.data || []);
                }
            }
        }

        if (rows.length === 0) {
            return res.status(404).json({ error: `Ei tuloksia Sportti-ID:llä ${id}. Varmista numero.` });
        }

        return res.status(200).json(rows);

    } catch (error) {
        return res.status(500).json({ error: `Palvelinvirhe: ${error.message}` });
    }
}
