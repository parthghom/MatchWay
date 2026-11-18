// Live position of the driver, for the driver home map.
// Like Google Maps, it first asks for a quick Wi-Fi / mobile-network fix (works indoors),
// keeps retrying until it gets one, and uses high-accuracy GPS to sharpen it when available.
// status: 'loading' | 'ok' | 'denied' | 'error'
import { useEffect, useState } from 'react';
import { PermissionsAndroid, Platform } from 'react-native';
import Geolocation from '@react-native-community/geolocation';

Geolocation.setRNConfiguration({ skipPermissionRequests: true, authorizationLevel: 'whenInUse' });

export function useDriverLocation() {
  const [coords, setCoords] = useState(null);
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    let alive = true;
    let have = false;
    let watchId = null;
    let retry = null;

    const got = (pos) => {
      if (!alive) return;
      have = true;
      setCoords({ lat: pos.coords.latitude, lon: pos.coords.longitude });
      setStatus('ok');
      if (retry) { clearInterval(retry); retry = null; }
    };

    const quick = () => {
      Geolocation.getCurrentPosition(got, () => {}, {
        enableHighAccuracy: false, timeout: 10000, maximumAge: 120000,
      });
    };

    async function start() {
      if (Platform.OS === 'android') {
        const res = await PermissionsAndroid.request(PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION);
        if (res !== PermissionsAndroid.RESULTS.GRANTED) {
          if (alive) setStatus('denied');
          return;
        }
      }
      quick();
      retry = setInterval(() => { if (!have) quick(); }, 12000);
      watchId = Geolocation.watchPosition(
        got,
        (err) => {
          if (!alive || have) return;
          setStatus(err && err.code === 1 ? 'denied' : 'error');
        },
        { enableHighAccuracy: true, distanceFilter: 10, interval: 5000, fastestInterval: 3000 }
      );
    }
    start();

    return () => {
      alive = false;
      if (retry) clearInterval(retry);
      if (watchId !== null) Geolocation.clearWatch(watchId);
    };
  }, []);

  return { coords, status };
}
