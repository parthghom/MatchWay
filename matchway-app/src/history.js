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

// ride = { id, pickup, drop, vehicle, fare, km, riders, date }
export async function saveRideToHistory(ride) {
  const old = await loadHistory();
  const next = [ride, ...old.filter((r) => r.id !== ride.id)].slice(0, MAX);
  try {
    await AsyncStorage.setItem(KEY, JSON.stringify(next));
  } catch (e) {}
  return next;
}

// ---- the driver's finished trips (kept on the driver's phone) ----
const DRIVER_KEY = 'matchway_driver_history';

export async function loadDriverHistory() {
  try {
    const raw = await AsyncStorage.getItem(DRIVER_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

// trip = { id, pickup, drop, vehicle, fare (total for the trip), km, riders, date }
export async function saveDriverTrip(trip) {
  const old = await loadDriverHistory();
  const next = [trip, ...old.filter((r) => r.id !== trip.id)].slice(0, MAX);
  try {
    await AsyncStorage.setItem(DRIVER_KEY, JSON.stringify(next));
  } catch (e) {}
  return next;
}
