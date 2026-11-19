// "History" tab for drivers: the trips he has completed (the fare is the total for the whole trip).
// The list comes from the backend, where it is kept in our own Stack.
import React from 'react';
import HistoryScreen from '../ride/HistoryScreen';

export default function DriverHistory({ userId }) {
  return <HistoryScreen title="Trip history" userId={userId} driver />;
}
