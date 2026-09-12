export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET');

    const { id } = req.query;
    if (!id) {
        return res.status(400).json({ error: 'Sportti-ID puuttuu' });
    }

    // Otsakkeet, joilla varmistetaan, että KITI hyväksyy pyynnön
    const headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json, text/plain, */*'
    };

    try {
        const searchRes = await fetch(`https://kiti.ampumaurheiluliitto.fi/api/athletes/?search=${id}&limit=5&page=1`, { headers });
        if (!searchRes.ok) throw new Error(`Haku epäonnistui statuskoodilla ${searchRes.status}`);
        
        const searchData = await searchRes.json();
        const athletes = Array.isArray(searchData) ? searchData : (searchData.content || searchData.athletes || searchData.data || [searchData]);

        let internalId = null;
        for (let ath of athletes) {
            if (ath.id || ath.personId) {
                internalId = ath.id || ath.personId;
                break;
            }
        }

        if (!internalId) {
            return res.status(404).json({ error: 'Urheilijaa ei löytynyt annetulla Sportti-ID:llä.' });
        }

        const resultsRes = await fetch(`https://kiti.ampumaurheiluliitto.fi/api/resultlist/?athlete&ordering=competition_start_date&athlete=${internalId}`, { headers });
        if (!resultsRes.ok) throw new Error(`Tulosten haku epäonnistui statuskoodilla ${resultsRes.status}`);

        const resultsData = await resultsRes.json();
        return res.status(200).json(resultsData);
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
}
