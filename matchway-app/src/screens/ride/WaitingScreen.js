// Shown after you book: waiting for riders going the same way.
// Pickup, drop, approx fare, drivers around you (2 km, widening to 10 km), Cancel.
import React, { useEffect, useRef, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, StatusBar, Animated, Modal } from 'react-native';
import { api } from '../../api';
import { C } from '../../theme';

const TOP = (StatusBar.currentHeight || 24) + 16;
const rupee = (n) => `₹${Math.round(n)}`;

const WORD = { bike: 'bike', auto: 'auto', cab: 'cab' };

export default function WaitingScreen({ pickup, drop, vehicle, fareLow, fareHigh, busy, onCancel }) {
  const [drivers, setDrivers] = useState(null);   // { count, radius_km }
  const [confirming, setConfirming] = useState(false);   // the "Cancel this ride?" sheet
  const pulse = useRef(new Animated.Value(0)).current;

  // soft pulsing ring while we wait
  useEffect(() => {
    const loop = Animated.loop(
      Animated.timing(pulse, { toValue: 1, duration: 1600, useNativeDriver: true })
    );
    loop.start();
    return () => loop.stop();
  }, [pulse]);

  // drivers near the pickup: ask again every 10 seconds
  useEffect(() => {
    let alive = true;
    async function load() {
      try {
        const res = await api.get('/drivers/nearby', {
          params: { lat: pickup.lat, lon: pickup.lon, vehicle_type: vehicle },
        });
        if (alive) setDrivers(res.data);
      } catch (e) {
        // keep the last number if the network blinks
      }
    }
    load();
    const t = setInterval(load, 10000);
    return () => { alive = false; clearInterval(t); };
  }, [pickup, vehicle]);

  const ring = {
    opacity: pulse.interpolate({ inputRange: [0, 1], outputRange: [0.6, 0] }),
    transform: [{ scale: pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 2.2] }) }],
  };

  let driverLine = 'Looking for drivers…';
  let driverSub = '';
  if (drivers) {
    if (drivers.count > 0) {
      driverLine = `${drivers.count} ${WORD[vehicle]} driver${drivers.count > 1 ? 's' : ''} nearby`;
      driverSub = `within ${drivers.radius_km} km of your pickup`;
    } else {
      driverLine = 'No drivers nearby yet';
      driverSub = 'We checked up to 10 km around your pickup';
    }
  }

  return (
    <View style={s.screen}>
      <View style={s.hero}>
        <View style={s.pulseBox}>
          <Animated.View style={[s.ring, ring]} />
          <View style={s.core}><View style={s.coreDot} /></View>
        </View>
        <Text style={s.title}>Waiting for peers on the same way</Text>
        <Text style={s.sub}>We will group you with riders heading the same direction.</Text>
      </View>

      <View style={s.card}>
        <View style={s.stop}>
          <View style={s.dotPick} />
          <View style={{ flex: 1 }}>
            <Text style={s.label}>Pickup</Text>
            <Text style={s.place} numberOfLines={2}>{pickup.name}</Text>
          </View>
        </View>
        <View style={s.line} />
        <View style={s.stop}>
          <View style={s.dotDrop} />
          <View style={{ flex: 1 }}>
            <Text style={s.label}>Drop</Text>
            <Text style={s.place} numberOfLines={2}>{drop.name}</Text>
          </View>
        </View>
        <View style={s.divider} />
        <View style={s.fareRow}>
          <Text style={s.label}>Approx. fare</Text>
          <Text style={s.fare}>
            {Math.round(fareLow) === Math.round(fareHigh) ? rupee(fareHigh) : `${rupee(fareLow)} – ${rupee(fareHigh)}`}
          </Text>
        </View>
        <Text style={s.hint}>The more riders join, the lower your fare.</Text>
      </View>

      <View style={s.card}>
        <Text style={s.driverLine}>{driverLine}</Text>
        {driverSub ? <Text style={s.hint}>{driverSub}</Text> : null}
      </View>

      <View style={{ flex: 1 }} />

      <TouchableOpacity style={[s.cancel, busy && { opacity: 0.55 }]} onPress={() => setConfirming(true)} disabled={busy} activeOpacity={0.8}>
        {busy ? <ActivityIndicator color={C.yellow} /> : <Text style={s.cancelText}>Cancel ride</Text>}
      </TouchableOpacity>

      {/* our own black + yellow confirmation sheet */}
      <Modal visible={confirming} transparent animationType="slide" onRequestClose={() => setConfirming(false)}>
        <View style={s.backdrop}>
          <TouchableOpacity style={{ flex: 1 }} activeOpacity={1} onPress={() => setConfirming(false)} />
          <View style={s.sheet}>
            <View style={s.grabber} />
            <Text style={s.sheetTitle}>Cancel this ride?</Text>
            <Text style={s.sheetText}>You will leave the group and lose your place with the riders going your way.</Text>
            <TouchableOpacity style={s.keep} onPress={() => setConfirming(false)} activeOpacity={0.85}>
              <Text style={s.keepText}>Keep waiting</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={s.confirmCancel}
              onPress={() => { setConfirming(false); onCancel(); }}
              activeOpacity={0.85}
            >
              <Text style={s.confirmCancelText}>Yes, cancel ride</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg, paddingTop: TOP, paddingHorizontal: 20, paddingBottom: 24 },
  hero: { alignItems: 'center', marginBottom: 22 },
  pulseBox: { width: 90, height: 90, alignItems: 'center', justifyContent: 'center', marginBottom: 14 },
  ring: { position: 'absolute', width: 54, height: 54, borderRadius: 27, backgroundColor: C.yellow },
  core: { width: 54, height: 54, borderRadius: 27, backgroundColor: C.yellow, alignItems: 'center', justifyContent: 'center' },
  coreDot: { width: 18, height: 18, borderRadius: 9, backgroundColor: C.bg },
  title: { color: C.text, fontSize: 22, fontWeight: '800', textAlign: 'center' },
  sub: { color: C.muted, fontSize: 14, textAlign: 'center', marginTop: 6 },

  card: { backgroundColor: C.card, borderRadius: 18, borderWidth: 1, borderColor: C.line, padding: 16, marginBottom: 14 },
  stop: { flexDirection: 'row', alignItems: 'center' },
  dotPick: { width: 14, height: 14, borderRadius: 7, backgroundColor: '#fff', borderWidth: 4, borderColor: C.yellow, marginRight: 14 },
  dotDrop: { width: 14, height: 14, backgroundColor: C.yellow, marginRight: 14 },
  line: { width: 2, height: 18, backgroundColor: C.line, marginLeft: 6, marginVertical: 4 },
  label: { color: C.muted, fontSize: 12 },
  place: { color: C.text, fontSize: 16, fontWeight: '600', marginTop: 2 },
  divider: { height: 1, backgroundColor: C.line, marginVertical: 14 },
  fareRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  fare: { color: C.yellow, fontSize: 24, fontWeight: '800' },
  hint: { color: C.muted, fontSize: 12, marginTop: 6 },
  driverLine: { color: C.text, fontSize: 17, fontWeight: '700' },

  backdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)' },
  sheet: {
    backgroundColor: C.bg, borderTopLeftRadius: 22, borderTopRightRadius: 22, borderTopWidth: 1, borderColor: C.line,
    paddingHorizontal: 20, paddingTop: 10, paddingBottom: 26,
  },
  grabber: { alignSelf: 'center', width: 40, height: 4, borderRadius: 2, backgroundColor: C.line, marginBottom: 16 },
  sheetTitle: { color: C.text, fontSize: 20, fontWeight: '800' },
  sheetText: { color: C.muted, fontSize: 14, marginTop: 6, marginBottom: 18 },
  keep: { backgroundColor: C.yellow, borderRadius: 14, paddingVertical: 15, alignItems: 'center' },
  keepText: { color: C.black, fontSize: 17, fontWeight: '800' },
  confirmCancel: { borderWidth: 1.5, borderColor: C.line, borderRadius: 14, paddingVertical: 15, alignItems: 'center', marginTop: 10 },
  confirmCancelText: { color: C.text, fontSize: 16, fontWeight: '700' },

  cancel: { borderWidth: 1.5, borderColor: C.yellow, borderRadius: 14, paddingVertical: 15, alignItems: 'center' },
  cancelText: { color: C.yellow, fontSize: 17, fontWeight: '800' },
});