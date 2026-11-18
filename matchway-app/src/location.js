// Live GPS position of the rider.
// status: 'loading' (waiting for first fix) | 'ok' | 'denied' | 'error'
// First asks for a quick Wi-Fi / mobile-network fix (works indoors, like Google Maps),
// retries until it gets one, and uses high-accuracy GPS to sharpen it when available.
import { useEffect, useState } from 'react';
import { PermissionsAndroid, Platform } from 'react-native';
import Geolocation from '@react-native-community/geolocation';

const CONFIG = { skipPermissionRequests: true, authorizationLevel: 'whenInUse' };
Geolocation.setRNConfiguration(CONFIG);

export function useLocation() {
  const [coords, setCoords] = useState(null);
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    let alive = true;
    let have = false;
    let watchId = null;
    let retry = null;
    let tries = 0;

    const got = (pos) => {
      if (!alive) return;
      have = true;
      setCoords({ lat: pos.coords.latitude, lon: pos.coords.longitude });
      setStatus('ok');
      if (retry) { clearInterval(retry); retry = null; }
    };

    // every other try uses Android's own location service instead of Google's, in case one of them hangs
    const quick = () => {
      tries += 1;
      Geolocation.setRNConfiguration({ ...CONFIG, locationProvider: tries % 2 === 1 ? 'auto' : 'android' });
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
      Geolocation.setRNConfiguration({ ...CONFIG, locationProvider: 'auto' });
    };
  }, []);

  return { coords, status };
}
