// Keeps the rider's completed rides on this phone, newest first.
import AsyncStorage from '@react-native-async-storage/async-storage';

const KEY = 'matchway_ride_history';
const MAX = 50;

export async function loadHistory() {
  try {
    const raw = await AsyncStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

// ride = { id, pickup, drop, vehicle, fare, km, riders, date,
//          ratings: { driver: { name, stars } | null, riders: [{ name, stars }] } | undefined }
export async function saveRideToHistory(ride) {
  const old = await loadHistory();
  const next = [ride, ...old.filter((r) => r.id !== ride.id)].slice(0, MAX);
  try {
    await AsyncStorage.setItem(KEY, JSON.stringify(next));
  } catch (e) {}
  return next;
}

// remember how many stars you gave the driver and the co-passengers of one ride
export async function updateRideRatings(id, ratings) {
  const old = await loadHistory();
  const next = old.map((r) => (r.id === id ? { ...r, ratings } : r));
  try {
    await AsyncStorage.setItem(KEY, JSON.stringify(next));
  } catch (e) {}
  return next;
}
