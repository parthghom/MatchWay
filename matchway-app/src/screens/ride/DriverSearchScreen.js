// Last screen before the ride: the group is agreed, now we look for a driver.
// Asks the server to confirm the ride every 4 seconds until a driver is found.
import React, { useEffect, useRef, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, StatusBar, Animated } from 'react-native';
import { api } from '../../api';
import { C } from '../../theme';

const TOP = (StatusBar.currentHeight || 24) + 16;
const rupee = (n) => `₹${Math.round(n)}`;
const KIND = { bike: '🏍️ Bike', auto: '🛺 Auto', cab: '🚕 Cab' };

export default function DriverSearchScreen({ pickup, drop, vehicle, fareLow, fareHigh, roomId, busy, onCancel, onFound }) {
  const [drivers, setDrivers] = useState(null);
  const [tries, setTries] = useState(0);
  const pulse = useRef(new Animated.Value(0)).current;
  const found = useRef(false);

  useEffect(() => {
    const loop = Animated.loop(Animated.timing(pulse, { toValue: 1, duration: 1400, useNativeDriver: true }));
    loop.start();
    return () => loop.stop();
  }, [pulse]);

  // try to get a driver now, and again every 4 seconds
  useEffect(() => {
    let alive = true;
    async function attempt() {
      try {
        const res = await api.post('/rides/confirm', { room_id: roomId });
        if (alive && res.data.confirmed && !found.current) {
          found.current = true;
          onFound(res.data);
          return;
        }
      } catch (e) {
        // try again on the next round
      }
      if (alive) setTries((n) => n + 1);
    }
    attempt();
    const t = setInterval(attempt, 4000);
    return () => { alive = false; clearInterval(t); };
  }, [roomId, onFound]);

  useEffect(() => {
    let alive = true;
    api.get('/drivers/nearby', { params: { lat: pickup.lat, lon: pickup.lon, vehicle_type: vehicle } })
      .then((res) => { if (alive) setDrivers(res.data); })
      .catch(() => {});
    return () => { alive = false; };
  }, [pickup, vehicle, tries]);

  const ring = {
    opacity: pulse.interpolate({ inputRange: [0, 1], outputRange: [0.6, 0] }),
    transform: [{ scale: pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 2.4] }) }],
  };

  return (
    <View style={s.screen}>
      <View style={s.hero}>
        <View style={s.pulseBox}>
          <Animated.View style={[s.ring, ring]} />
          <View style={s.core}><Text style={{ fontSize: 26 }}>{KIND[vehicle].split(' ')[0]}</Text></View>
        </View>
        <Text style={s.title}>Finding your driver</Text>
        <Text style={s.sub}>
          {drivers && drivers.count > 0
            ? `${drivers.count} ${vehicle} driver${drivers.count > 1 ? 's' : ''} nearby`
            : 'Looking for a driver near your pickup…'}
        </Text>
      </View>

      <View style={s.card}>
        <Text style={s.kind}>{KIND[vehicle]}</Text>
        <Text style={s.label}>Pickup</Text>
        <Text style={s.place} numberOfLines={2}>{pickup.name}</Text>
        <Text style={[s.label, { marginTop: 12 }]}>Drop</Text>
        <Text style={s.place} numberOfLines={2}>{drop.name}</Text>
        <View style={s.divider} />
        <View style={s.fareRow}>
          <Text style={s.label}>Approx. fare</Text>
          <Text style={s.fare}>
            {Math.round(fareLow) === Math.round(fareHigh) ? rupee(fareHigh) : `${rupee(fareLow)} – ${rupee(fareHigh)}`}
          </Text>
        </View>
      </View>

      <View style={{ flex: 1 }} />
      <TouchableOpacity style={[s.cancel, busy && { opacity: 0.55 }]} onPress={onCancel} disabled={busy} activeOpacity={0.8}>
        {busy ? <ActivityIndicator color={C.yellow} /> : <Text style={s.cancelText}>Cancel ride</Text>}
      </TouchableOpacity>
    </View>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg, paddingTop: TOP, paddingHorizontal: 20, paddingBottom: 24 },
  hero: { alignItems: 'center', marginVertical: 24 },
  pulseBox: { width: 100, height: 100, alignItems: 'center', justifyContent: 'center', marginBottom: 14 },
  ring: { position: 'absolute', width: 64, height: 64, borderRadius: 32, backgroundColor: C.yellow },
  core: { width: 64, height: 64, borderRadius: 32, backgroundColor: C.yellow, alignItems: 'center', justifyContent: 'center' },
  title: { color: C.text, fontSize: 24, fontWeight: '800' },
  sub: { color: C.muted, fontSize: 14, marginTop: 6, textAlign: 'center' },
  card: { backgroundColor: C.card, borderRadius: 18, borderWidth: 1, borderColor: C.line, padding: 16 },
  kind: { color: C.yellow, fontSize: 18, fontWeight: '800', marginBottom: 12 },
  label: { color: C.muted, fontSize: 12 },
  place: { color: C.text, fontSize: 16, fontWeight: '600', marginTop: 2 },
  divider: { height: 1, backgroundColor: C.line, marginVertical: 14 },
  fareRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  fare: { color: C.yellow, fontSize: 24, fontWeight: '800' },
  cancel: { borderWidth: 1.5, borderColor: C.yellow, borderRadius: 14, paddingVertical: 15, alignItems: 'center' },
  cancelText: { color: C.yellow, fontSize: 17, fontWeight: '800' },
});
