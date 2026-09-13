export default async function handler(req, res) {
    const { sport = '1', category = '1', level = '1,2,3,4,5,6,7,8,9,10,11,12', type = '1', limit = '300' } = req.query;

    try {
        const kitiUrl = `https://kiti.ampumaurheiluliitto.fi/api/resultlist/?fields!=partial&sport=${sport}&category=${category}&level=${level}&type=${type}&limit=${limit}`;
        
        const response = await fetch(kitiUrl);
        if (!response.ok) {
            return res.status(response.status).json({ error: `KITI API error: ${response.status}` });
        }

        const data = await response.json();
        return res.status(200).json(data);
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
}
