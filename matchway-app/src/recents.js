// Remembers the last places the rider picked, so they show under the map.
import AsyncStorage from '@react-native-async-storage/async-storage';

const KEY = 'matchway_recent_places';
const MAX = 8;

export async function loadRecents() {
  try {
    const raw = await AsyncStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

// Puts the place first and drops any older copy of it.
export async function saveRecent(place) {
  const old = await loadRecents();
  const same = (p) => Math.abs(p.lat - place.lat) < 0.0005 && Math.abs(p.lon - place.lon) < 0.0005;
  const next = [place, ...old.filter((p) => !same(p))].slice(0, MAX);
  try {
    await AsyncStorage.setItem(KEY, JSON.stringify(next));
  } catch (e) {}
  return next;
}
