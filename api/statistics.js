export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version'
  );

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  const { sport, category, level, page } = req.query;

  const sportParam = sport || '1';
  const categoryParam = category || '8';
  const pageParam = page || '1';

  // Jos level-parametria ei anneta erikseen, ei rajata luokituksia (kaikki luokitukset mukana)
  const levelQuery = level ? `&level=${level}` : '';
  const targetUrl = `https://kiti.ampumaurheiluliitto.fi/api/resultlist/?fields!=partial&sport=${sportParam}&category=${categoryParam}${levelQuery}&type=1&limit=25&page=${pageParam}`;

  try {
    const kitiResponse = await fetch(targetUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json'
      }
    });

    if (!kitiResponse.ok) {
      return res.status(kitiResponse.status).json({ error: `KITI API virhe: ${kitiResponse.status}` });
    }

    const data = await kitiResponse.json();
    return res.status(200).json(data);
  } catch (error) {
    return res.status(500).json({ error: `Palvelinvirhe: ${error.message}` });
  }
}
