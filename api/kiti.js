module.exports = async (req, res) => {
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
        const searchUrl = `https://kiti.ampumaurheiluliitto.fi/api/athletes/?search=${id}&limit=5&page=1`;
        const searchRes = await fetch(searchUrl, { headers });
        
        if (!searchRes.ok) {
            return res.status(searchRes.status).json({ error: `Kiti vastasi virheellä ${searchRes.status}` });
        }
        
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

        const resultsUrl = `https://kiti.ampumaurheiluliitto.fi/api/resultlist/?athlete&ordering=competition_start_date&athlete=${internalId}`;
        const resultsRes = await fetch(resultsUrl, { headers });
        
        if (!resultsRes.ok) {
            return res.status(resultsRes.status).json({ error: `Tuloshaku epäonnistui statuskoodilla ${resultsRes.status}` });
        }

        const resultsData = await resultsRes.json();
        return res.status(200).json(resultsData);
    } catch (error) {
        return res.status(500).json({ error: `Palvelinvirhe: ${error.message}` });
    }
};
