// The signed-in person's own EMA rating, as kept by the server.
// Asked once when a screen opens and again every 20 seconds, so a rating you just received shows up
// without restarting the app.
import { useEffect, useState } from 'react';
import { api } from './api';

export function useMyRating(initial) {
  const [rating, setRating] = useState(initial || null);   // { score, count }
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let alive = true;
    async function load() {
      try {
        const res = await api.get('/ratings/me');
        if (alive) { setRating(res.data); setFailed(false); }
      } catch (e) {
        if (alive) setFailed(true);   // e.g. the server has not been updated yet
      }
    }
    load();
    const t = setInterval(load, 20000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  return { rating, failed };
}
