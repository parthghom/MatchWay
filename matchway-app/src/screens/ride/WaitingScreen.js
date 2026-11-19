// Shown after you book an auto or cab: waiting for riders going the same way.
// Trip card (ride type, pickup, drop, fare), a box with the riders found so far,
// and the buttons: Continue alone / Continue with N / Accept (15 s when the vehicle is full).
// The server keeps the group; this screen asks it for news every 2 seconds.
import React, { useEffect, useRef, useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, StatusBar, Animated, Modal, ScrollView, Image,
} from 'react-native';
import { api } from '../../api';
import { API } from '../../config';
import { supabase } from '../../supabase';
import { C } from '../../theme';

const TOP = (StatusBar.currentHeight || 24) + 16;
const rupee = (n) => `₹${Math.round(n)}`;

const WORD = { bike: 'bike', auto: 'auto', cab: 'cab' };
const KIND = { bike: '🏍️ Bike', auto: '🛺 Auto', cab: '🚕 Cab' };

// round profile picture, or the first letter if there is no photo
function Avatar({ name, userId, token }) {
  const [bad, setBad] = useState(false);
  return (
    <View style={s.avatar}>
      {userId && token && !bad ? (
        <Image
          source={{ uri: `${API}/profile/avatar/${userId}`, headers: { Authorization: `Bearer ${token}` } }}
          style={s.avatarImg}
          onError={() => setBad(true)}
        />
      ) : (
        <Text style={s.avatarLetter}>{(name || '?').charAt(0).toUpperCase()}</Text>
      )}
    </View>
  );
}

export default function WaitingScreen({ pickup, drop, vehicle, fareLow, fareHigh, roomId, riderId, busy, onCancel, onReady }) {
  const [drivers, setDrivers] = useState(null);   // { count, radius_km }
  const [confirming, setConfirming] = useState(false);   // the "Cancel this ride?" sheet
  const pulse = useRef(new Animated.Value(0)).current;
  const [room, setRoom] = useState(null);     // group status from the server
  const [token, setToken] = useState('');
  const [voting, setVoting] = useState(false);
  const readyDone = useRef(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setToken(data.session ? data.session.access_token : ''));
  }, []);

  // ask the server who is in the group (every 2 seconds)
  useEffect(() => {
    let alive = true;
    async function load() {
      try {
        const res = await api.get(`/rooms/${roomId}`);
        if (!alive) return;
        setRoom(res.data);
        if (res.data.ready && !readyDone.current) {
          readyDone.current = true;
          onReady(res.data);
        }
      } catch (e) {
        // keep the last status if the network blinks
      }
    }
    load();
    const t = setInterval(load, 2000);
    return () => { alive = false; clearInterval(t); };
  }, [roomId, onReady]);

  async function vote() {
    setVoting(true);
    try {
      const res = await api.post('/rooms/continue', { rider_id: riderId });
      setRoom(res.data);
      if (res.data.ready && !readyDone.current) { readyDone.current = true; onReady(res.data); }
    } catch (e) {
      // the next poll will show the real state
    } finally {
      setVoting(false);
    }
  }

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

  const members = room ? room.members : [];
  const cap = room ? room.capacity : 1;
  const n = members.length;
  const full = n >= cap;
  const iAccepted = !!room && room.accepted.indexOf(riderId) !== -1;
  const slots = [];
  for (let i = 0; i < cap; i++) slots.push(members[i] || null);

  let action = null;
  let note = '';
  if (n <= 1) {
    action = { label: 'Continue alone', ghost: true };
    note = 'Looking for riders going your way…';
  } else if (!iAccepted) {
    action = full
      ? { label: 'Accept' }
      : { label: `Continue with ${n}` };
    note = full ? 'Your ride is full. Everyone must accept.' : 'You can continue now, or wait for more riders (lower fare).';
  } else {
    note = full ? 'Waiting for the others to accept…' : `Waiting for the other ${n - 1} to confirm…`;
  }

  return (
    <View style={s.screen}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 12 }}>
      <View style={s.hero}>
        <View style={s.pulseBox}>
          <Animated.View style={[s.ring, ring]} />
          <View style={s.core}><View style={s.coreDot} /></View>
        </View>
        <Text style={s.title}>Waiting for peers on the same way</Text>
        <Text style={s.sub}>We will group you with riders heading the same direction.</Text>
      </View>

      <View style={s.card}>
        <View style={s.kindRow}>
          <Text style={s.kind}>{KIND[vehicle]}</Text>
        </View>
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
        <Text style={s.peersTitle}>Riders on your way ({n}/{cap})</Text>
        <View style={s.peersRow}>
          {slots.map((m, i) => (
            <View key={m ? m.rider_id : `empty${i}`} style={s.peer}>
              {m ? (
                <Avatar name={m.name} userId={m.user_id} token={token} />
              ) : (
                <View style={[s.avatar, s.avatarEmpty]}><Text style={s.plus}>+</Text></View>
              )}
              <Text style={s.peerName} numberOfLines={1}>
                {m ? (m.rider_id === riderId ? 'You' : m.name) : 'Waiting'}
              </Text>
              {m && typeof m.rating === 'number' ? <Text style={s.peerRating}>★ {m.rating.toFixed(1)}</Text> : null}
              {m && room.accepted.indexOf(m.rider_id) !== -1 ? <Text style={s.ok}>✓ Ready</Text> : null}
            </View>
          ))}
        </View>
        {note ? <Text style={s.hint}>{note}</Text> : null}
        {full && !iAccepted && room && room.seconds_left != null ? (
          <Text style={s.timer}>Accept within {room.seconds_left}s</Text>
        ) : null}
        {action ? (
          <TouchableOpacity
            style={[s.go, action.ghost && s.goGhost, voting && { opacity: 0.55 }]}
            onPress={vote}
            disabled={voting}
            activeOpacity={0.85}
          >
            {voting ? <ActivityIndicator color={action.ghost ? C.yellow : C.black} /> : (
              <Text style={[s.goText, action.ghost && { color: C.yellow }]}>{action.label}</Text>
            )}
          </TouchableOpacity>
        ) : null}
      </View>

      <View style={s.card}>
        <Text style={s.driverLine}>{driverLine}</Text>
        {driverSub ? <Text style={s.hint}>{driverSub}</Text> : null}
      </View>
      </ScrollView>

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
  peerRating: { color: C.yellow, fontSize: 12, fontWeight: '700', marginTop: 2 },
  screen: { flex: 1, backgroundColor: C.bg, paddingTop: TOP, paddingHorizontal: 20, paddingBottom: 24 },
  hero: { alignItems: 'center', marginBottom: 22 },
  kindRow: { marginBottom: 12 },
  kind: { color: C.yellow, fontSize: 18, fontWeight: '800' },
  peersTitle: { color: C.text, fontSize: 16, fontWeight: '700', marginBottom: 14 },
  peersRow: { flexDirection: 'row', justifyContent: 'space-around' },
  peer: { alignItems: 'center', width: 80 },
  avatar: { width: 60, height: 60, borderRadius: 30, backgroundColor: C.line, alignItems: 'center', justifyContent: 'center', overflow: 'hidden', borderWidth: 2, borderColor: C.yellow },
  avatarImg: { width: 60, height: 60 },
  avatarLetter: { color: C.yellow, fontSize: 24, fontWeight: '800' },
  avatarEmpty: { backgroundColor: 'transparent', borderStyle: 'dashed', borderColor: C.line },
  plus: { color: C.muted, fontSize: 24 },
  peerName: { color: C.text, fontSize: 13, marginTop: 6 },
  ok: { color: C.yellow, fontSize: 11, marginTop: 2, fontWeight: '700' },
  timer: { color: C.yellow, fontSize: 15, fontWeight: '800', marginTop: 10, textAlign: 'center' },
  go: { backgroundColor: C.yellow, borderRadius: 14, paddingVertical: 14, alignItems: 'center', marginTop: 14 },
  goGhost: { backgroundColor: 'transparent', borderWidth: 1.5, borderColor: C.yellow },
  goText: { color: C.black, fontSize: 16, fontWeight: '800' },
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
