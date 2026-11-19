// "History" tab for drivers: the trips he has completed (the fare is the total for the whole trip).
import React from 'react';
import HistoryScreen from '../ride/HistoryScreen';
import { loadDriverHistory } from '../../history';

export default function DriverHistory() {
  return <HistoryScreen title="Trip history" load={loadDriverHistory} driver />;
}
