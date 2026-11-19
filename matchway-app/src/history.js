// Completed rides are kept by the backend, in our own Stack (newest trip on top).
// The app only asks for them: nothing is stored on the phone any more.
import { api } from './api';

// role is "rider" or "driver"; userId is the signed-in user's id
export async function loadTrips(role, userId) {
  if (!userId) return [];
  const res = await api.get(`/history/${role}/${userId}`);
  return res.data.trips || [];
}
