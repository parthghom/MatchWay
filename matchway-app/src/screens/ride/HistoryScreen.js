// "History" tab: the rides you have completed, newest first.
// The list comes from the backend, where every person's trips are kept in our own Stack
// (GET /history/rider/<id> or /history/driver/<id>). If the server can not be reached, a rider
// still sees the copy saved on this phone.
import React, { useCallback, useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, StatusBar } from 'react-native';
import { C } from '../../theme';
import { api } from '../../api';
import { loadHistory } from '../../history';
import { StarRow } from '../../components/RatingCard';

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
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    if (userId) {
      try {
        const res = await api.get(`/history/${driver ? 'driver' : 'rider'}/${userId}`);
        setRides(res.data.trips || []);
        return;
      } catch (e) {
        // server not reachable: fall through to the copy on this phone
      }
    }
    setRides(driver ? [] : await loadHistory());
  }, [userId, driver]);

  useEffect(() => { load(); }, [load]);

  async function refresh() {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }

  return (
    <View style={s.screen}>
      <Text style={s.title}>{title}</Text>
      <FlatList
        data={rides || []}
        refreshing={refreshing}
        onRefresh={refresh}
        keyExtractor={(r) => r.id}
        contentContainerStyle={{ paddingBottom: 20, flexGrow: 1 }}
        ListEmptyComponent={
          rides ? (
            <View style={s.emptyBox}>
              <Text style={s.emptyTitle}>No completed rides yet</Text>
              <Text style={s.emptyText}>Rides you finish will show up here.</Text>
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
                {driver
                  ? `${v[0]} ${v[1]} · ${r.km} km · ${r.riders} ${r.riders === 1 ? 'rider' : 'riders'} · total fare`
                  : `${v[0]} ${v[1]} · ${r.km} km · ${r.riders > 1 ? `shared with ${r.riders - 1}` : 'solo'}`}
              </Text>

              {!driver && (
              <View style={s.rateBox}>
                <Text style={s.rateTitle}>Your ratings</Text>
                {r.ratings && (r.ratings.driver || (r.ratings.riders && r.ratings.riders.length > 0)) ? (
                  <>
                    {r.ratings.driver ? (
                      <View style={s.rateRow}>
                        <Text style={s.rateWho} numberOfLines={1}>{v[0]} Driver · {r.ratings.driver.name}</Text>
                        <StarRow value={r.ratings.driver.stars} size={15} />
                      </View>
                    ) : null}
                    {(r.ratings.riders || []).map((p, i) => (
                      <View key={i} style={s.rateRow}>
                        <Text style={s.rateWho} numberOfLines={1}>👤 {p.name}</Text>
                        <StarRow value={p.stars} size={15} />
                      </View>
                    ))}
                  </>
                ) : (
                  <Text style={s.rateNone}>You did not rate this ride.</Text>
                )}
              </View>
              )}
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
  rateBox: { marginTop: 14, paddingTop: 12, borderTopWidth: 1, borderTopColor: C.line },
  rateTitle: { color: C.muted, fontSize: 12, marginBottom: 8 },
  rateRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 },
  rateWho: { color: C.text, fontSize: 14, fontWeight: '600', flex: 1, marginRight: 12 },
  rateNone: { color: C.muted, fontSize: 13 },
  emptyBox: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingBottom: 80 },
  emptyTitle: { color: C.text, fontSize: 18, fontWeight: '700' },
  emptyText: { color: C.muted, fontSize: 14, marginTop: 6 },
});
