// Everything the driver app needs to talk to the server about rides:
//  - tells the server where the driver is (every 6 s) so he can be offered rides,
//  - asks every 3 s whether there is a ride for him (offer -> accepted -> on the road),
//  - the route to draw: to the pickup after he accepts, to the drop after the OTP,
//  - accept / reject / start (with the OTP) / complete.
import { useCallback, useEffect, useRef, useState } from 'react';
import { api, errorText } from '../../api';
import { saveDriverTrip } from '../../history';

export function useDriverRide({ driverId, name, vehicleType, coords }) {
  const [ride, setRide] = useState(null);
  const [route, setRoute] = useState(null);     // [[lat, lon], ...]
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [earned, setEarned] = useState(null);   // set when a trip is finished: total fare
  const coordsRef = useRef(coords);
  coordsRef.current = coords;
  const hasCoords = !!coords;

  // keep the server up to date with where the driver is
  useEffect(() => {
    if (!driverId || !vehicleType || !hasCoords) return undefined;
    const beat = () => {
      const c = coordsRef.current;
      if (!c) return;
      api.post('/drivers/location', {
        driver_id: driverId, name: name || 'Driver', vehicle_type: vehicleType,
        latitude: c.lat, longitude: c.lon,
      }).catch(() => {});
    };
    beat();
    const t = setInterval(beat, 6000);
    return () => clearInterval(t);
  }, [driverId, name, vehicleType, hasCoords]);

  // is there a ride for me?
  const load = useCallback(async () => {
    if (!driverId) return;
    try {
      const res = await api.get(`/drivers/${driverId}/ride`);
      setRide(res.data || null);
    } catch (e) {
      // keep what we have if the network blinks
    }
  }, [driverId]);

  useEffect(() => {
    load();
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, [load]);

  // the route on the map: to the pickup first, then to the drop
  const status = ride ? ride.status : null;
  const rideId = ride ? ride.ride_id : null;
  useEffect(() => {
    if (status !== 'confirmed' && status !== 'in_progress') { setRoute(null); return undefined; }
    const c = coordsRef.current;
    const target = status === 'confirmed' ? ride.pickup : ride.drop;
    if (!c || !target) return undefined;
    let alive = true;
    api.get('/maps/route', {
      params: { origin_lat: c.lat, origin_lon: c.lon, dest_lat: target.lat, dest_lon: target.lon },
    }).then((res) => {
      if (alive) setRoute(res.data.points && res.data.points.length > 1 ? res.data.points : [[c.lat, c.lon], [target.lat, target.lon]]);
    }).catch(() => {
      // no route service: a straight line so the driver still sees where to go
      if (alive) setRoute([[c.lat, c.lon], [target.lat, target.lon]]);
    });
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, rideId, hasCoords]);

  async function act(fn) {
    setBusy(true);
    setError('');
    try { return await fn(); } catch (e) { setError(errorText(e)); return null; } finally { setBusy(false); }
  }

  const accept = () => act(async () => {
    await api.post('/rides/driver/accept', { ride_id: ride.ride_id, driver_id: driverId });
    await load();
  });

  const reject = () => act(async () => {
    await api.post('/rides/driver/reject', { ride_id: ride.ride_id, driver_id: driverId });
    setRide(null);
  });

  const start = (otp) => act(async () => {
    await api.post('/rides/start', { ride_id: ride.ride_id, otp });
    await load();
  });

  const complete = () => act(async () => {
    const res = await api.post('/rides/complete', { ride_id: ride.ride_id });
    const total = Math.round((res.data.payments || []).reduce((sum, p) => sum + p.amount, 0) * 100) / 100;
    await saveDriverTrip({
      id: ride.ride_id, pickup: ride.pickup.name, drop: ride.drop ? ride.drop.name : 'Drop',
      vehicle: ride.vehicle_type, fare: total, km: ride.km, riders: ride.riders, date: new Date().toISOString(),
    });
    setEarned(total);
    setRide(null);
  });

  return { ride, route, busy, error, earned, dismissEarned: () => setEarned(null), accept, reject, start, complete };
}
