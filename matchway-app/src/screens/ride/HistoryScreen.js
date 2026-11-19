// "History" tab: the rides you have completed.
import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, StatusBar } from 'react-native';
import { C } from '../../theme';
import { loadTrips } from '../../history';

const TOP = (StatusBar.currentHeight || 24) + 16;
const VEHICLE = { bike: ['🏍️', 'Bike'], auto: ['🛺', 'Auto'], cab: ['🚕', 'Cab'] };
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function when(iso) {
  const d = new Date(iso);
  let h = d.getHours();
  const ap = h >= 12 ? 'pm' : 'am';
  h = h % 12 || 12;
  return `${d.getDate()} ${MONTHS[d.getMonth()]} · ${h}:${String(d.getMinutes()).padStart(2, '0')} ${ap}`;
}

export default function HistoryScreen({ title = 'Ride history', userId, driver = false }) {
  const [rides, setRides] = useState(null);
  const [failed, setFailed] = useState(false);

  // the backend keeps the history; this asks for it each time the tab opens
  useEffect(() => {
    let alive = true;
    loadTrips(driver ? 'driver' : 'rider', userId)
      .then((t) => { if (alive) setRides(t); })
      .catch(() => { if (alive) { setRides([]); setFailed(true); } });
    return () => { alive = false; };
  }, [driver, userId]);

  return (
    <View style={s.screen}>
      <Text style={s.title}>{title}</Text>
      <FlatList
        data={rides || []}
        keyExtractor={(r) => r.id}
        contentContainerStyle={{ paddingBottom: 20, flexGrow: 1 }}
        ListEmptyComponent={
          rides ? (
            <View style={s.emptyBox}>
              <Text style={s.emptyTitle}>{failed ? 'Could not load history' : driver ? 'No completed trips yet' : 'No completed rides yet'}</Text>
              <Text style={s.emptyText}>{failed ? 'Check your internet and try again.' : driver ? 'Trips you finish will show up here.' : 'Rides you finish will show up here.'}</Text>
            </View>
          ) : null
        }
        renderItem={({ item: r }) => {
          const v = VEHICLE[r.vehicle] || VEHICLE.cab;
          return (
            <View style={s.card}>
              <View style={s.topRow}>
                <Text style={s.date}>{when(r.date)}</Text>
                <Text style={s.fare}>₹{Math.round(r.fare)}</Text>
              </View>
              <View style={s.stop}>
                <View style={s.dotPick} />
                <Text style={s.place} numberOfLines={1}>{r.pickup}</Text>
              </View>
              <View style={s.line} />
              <View style={s.stop}>
                <View style={s.dotDrop} />
                <Text style={s.place} numberOfLines={1}>{r.drop}</Text>
              </View>
              <Text style={s.meta}>
                {v[0]} {v[1]} · {Number(r.km).toFixed(1)} km · {driver ? `${r.riders} ${r.riders > 1 ? 'riders' : 'rider'}` : (r.riders > 1 ? `shared with ${r.riders - 1}` : 'solo')}
              </Text>
            </View>
          );
        }}
      />
    </View>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg, paddingTop: TOP, paddingHorizontal: 16 },
  title: { color: C.text, fontSize: 26, fontWeight: '800', marginBottom: 14, marginLeft: 4 },
  card: { backgroundColor: C.card, borderRadius: 18, borderWidth: 1, borderColor: C.line, padding: 16, marginBottom: 12 },
  topRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  date: { color: C.muted, fontSize: 13 },
  fare: { color: C.yellow, fontSize: 20, fontWeight: '800' },
  stop: { flexDirection: 'row', alignItems: 'center' },
  dotPick: { width: 12, height: 12, borderRadius: 6, backgroundColor: '#fff', borderWidth: 3, borderColor: C.yellow, marginRight: 12 },
  dotDrop: { width: 12, height: 12, backgroundColor: C.yellow, marginRight: 12 },
  line: { width: 2, height: 14, backgroundColor: C.line, marginLeft: 5, marginVertical: 3 },
  place: { flex: 1, color: C.text, fontSize: 15, fontWeight: '600' },
  meta: { color: C.muted, fontSize: 13, marginTop: 12 },
  emptyBox: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingBottom: 80 },
  emptyTitle: { color: C.text, fontSize: 18, fontWeight: '700' },
  emptyText: { color: C.muted, fontSize: 14, marginTop: 6 },
});
