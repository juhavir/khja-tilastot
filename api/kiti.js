export default async function handler(req, res) {
    // Sallitaan pyynnöt omalta sivustoltasi
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET');

    const { id } = req.query;
    if (!id) {
        return res.status(400).json({ error: 'Sportti-ID puuttuu' });
    }

    try {
        // 1. Etsitään sisäinen ID Sportti-ID:llä
        const searchRes = await fetch(`https://kiti.ampumaurheiluliitto.fi/api/athletes/?search=${id}&limit=5&page=1`);
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

        // 2. Haetaan viralliset tulokset sisäisellä ID:llä
        const resultsRes = await fetch(`https://kiti.ampumaurheiluliitto.fi/api/resultlist/?athlete&ordering=competition_start_date&athlete=${internalId}`);
        const resultsData = await resultsRes.json();

        return res.status(200).json(resultsData);
    } catch (error) {
        return res.status(500).json({ error: 'Virhe yhteydessä KITI-palveluun.' });
    }
}
