// Live GPS position of the rider.
// status: 'loading' (waiting for first fix) | 'ok' | 'denied' | 'error'
import { useEffect, useState } from 'react';
import { PermissionsAndroid, Platform } from 'react-native';
import Geolocation from '@react-native-community/geolocation';

Geolocation.setRNConfiguration({ skipPermissionRequests: true, authorizationLevel: 'whenInUse' });

export function useLocation() {
  const [coords, setCoords] = useState(null);
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    let alive = true;
    let watchId = null;

    async function start() {
      if (Platform.OS === 'android') {
        const res = await PermissionsAndroid.request(PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION);
        if (res !== PermissionsAndroid.RESULTS.GRANTED) {
          if (alive) setStatus('denied');
          return;
        }
      }
      watchId = Geolocation.watchPosition(
        (pos) => {
          if (!alive) return;
          setCoords({ lat: pos.coords.latitude, lon: pos.coords.longitude });
          setStatus('ok');
        },
        () => {
          if (alive) setStatus((s) => (s === 'ok' ? s : 'error'));
        },
        { enableHighAccuracy: true, distanceFilter: 10, interval: 5000, fastestInterval: 3000 }
      );
    }
    start();

    return () => {
      alive = false;
      if (watchId !== null) Geolocation.clearWatch(watchId);
    };
  }, []);

  return { coords, status };
}
