// After the ride: rate the driver and every co-passenger (1-5 stars).
// Each star goes to the server, where it moves that person's EMA rating (shown on their profile
// and used when riders and drivers are matched). What you gave is also saved in your ride history.
import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { api, errorText } from '../../api';
import { C } from '../../theme';
import { updateRideRatings } from '../../history';

const WORD = ['', 'Poor', 'Not good', 'Okay', 'Good', 'Excellent'];
const VEHICLE = { bike: 'Bike', auto: 'Auto', cab: 'Cab' };

function Stars({ value, onChange, disabled }) {
  return (
    <View style={s.stars}>
      {[1, 2, 3, 4, 5].map((n) => (
        <TouchableOpacity key={n} disabled={disabled} onPress={() => onChange(n)} hitSlop={{ top: 6, bottom: 6, left: 3, right: 3 }}>
          <Text style={[s.star, n <= value && s.starOn]}>★</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

function hintFor(stars) {
  if (stars === 1) return '1 star also blocks this person: you will not be matched together again.';
  if (stars === 2) return '2 stars is counted as a safety concern.';
  return '';
}

export default function ReviewCards({ ride, riderId, historyId }) {
  const coRiders = (ride.riders || []).filter((r) => r.rider_id !== riderId);
  const targets = [
    { key: ride.driver_id, role: 'driver', name: ride.driver_name || 'Your driver', sub: `${VEHICLE[ride.vehicle_type] || 'Vehicle'} driver` },
    ...coRiders.map((r) => ({ key: r.rider_id, role: 'rider', name: r.name || 'Co-passenger', sub: 'Co-passenger' })),
  ];

  const [stars, setStars] = useState({});   // target key -> stars picked
  const [sent, setSent] = useState({});     // target key -> stars already saved on the server
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const waiting = targets.filter((t) => !sent[t.key] && stars[t.key] > 0);
  const allSent = targets.every((t) => sent[t.key]);

  async function submit() {
    setSending(true); setError('');
    const nowSent = { ...sent };
    const failed = [];
    for (const t of waiting) {
      try {
        await api.post('/rides/review', { ride_id: ride.ride_id, reviewer_id: riderId, target_id: t.key, stars: stars[t.key] });
        nowSent[t.key] = stars[t.key];
      } catch (e) {
        // "already reviewed" means an earlier try got through: count it as sent
        if (e?.response?.status === 400 && /already reviewed/i.test(errorText(e))) nowSent[t.key] = stars[t.key];
        else failed.push(t.name);
      }
    }
    setSent(nowSent);

    // keep what you rated in the history, so you can look it up later
    const driver = targets[0];
    await updateRideRatings(historyId, {
      driver: nowSent[driver.key] ? { name: driver.name, stars: nowSent[driver.key] } : null,
      riders: targets.slice(1).filter((t) => nowSent[t.key]).map((t) => ({ name: t.name, stars: nowSent[t.key] })),
    });

    if (failed.length) setError(`Could not send the rating for ${failed.join(', ')}. Check your connection and try again.`);
    setSending(false);
  }

  return (
    <View>
      <Text style={s.title}>Rate your ride</Text>
      <Text style={s.sub}>Your ratings help us match you with good drivers and co-passengers.</Text>

      {targets.map((t) => {
        const done = !!sent[t.key];
        const value = done ? sent[t.key] : (stars[t.key] || 0);
        return (
          <View key={t.key} style={s.card}>
            <View style={s.head}>
              <View style={s.avatar}><Text style={s.avatarText}>{(t.name || '?').charAt(0).toUpperCase()}</Text></View>
              <View style={{ flex: 1 }}>
                <Text style={s.name} numberOfLines={1}>{t.name}</Text>
                <Text style={s.role}>{t.sub}</Text>
              </View>
              {done ? <Text style={s.sentTag}>✓ Rated</Text> : null}
            </View>
            <Stars value={value} disabled={done || sending} onChange={(n) => setStars((o) => ({ ...o, [t.key]: n }))} />
            {value > 0 ? <Text style={s.word}>{WORD[value]}</Text> : null}
            {!done && value > 0 && hintFor(value) ? <Text style={s.warn}>{hintFor(value)}</Text> : null}
          </View>
        );
      })}

      {error ? <Text style={s.error}>{error}</Text> : null}

      {allSent ? (
        <Text style={s.thanks}>Thanks! Your ratings were saved.</Text>
      ) : (
        <TouchableOpacity
          style={[s.btn, (waiting.length === 0 || sending) && { opacity: 0.5 }]}
          disabled={waiting.length === 0 || sending}
          onPress={submit}
          activeOpacity={0.85}
        >
          {sending ? <ActivityIndicator color={C.black} /> : (
            <Text style={s.btnText}>{waiting.length > 1 ? `Submit ${waiting.length} ratings` : 'Submit rating'}</Text>
          )}
        </TouchableOpacity>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  title: { color: C.text, fontSize: 20, fontWeight: '800', marginTop: 8 },
  sub: { color: C.muted, fontSize: 13, marginTop: 4, marginBottom: 12 },
  card: { backgroundColor: C.card, borderRadius: 16, borderWidth: 1, borderColor: C.line, padding: 16, marginBottom: 12 },
  head: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  avatar: { width: 40, height: 40, borderRadius: 20, backgroundColor: C.yellow, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  avatarText: { color: C.black, fontSize: 18, fontWeight: '800' },
  name: { color: C.text, fontSize: 16, fontWeight: '700' },
  role: { color: C.muted, fontSize: 12, marginTop: 1 },
  sentTag: { color: '#35D07F', fontSize: 12, fontWeight: '700' },
  stars: { flexDirection: 'row' },
  star: { fontSize: 38, color: C.line, marginRight: 8 },
  starOn: { color: C.yellow },
  word: { color: C.text, fontSize: 13, fontWeight: '600', marginTop: 6 },
  warn: { color: C.muted, fontSize: 12, marginTop: 6 },
  error: { color: '#FF6B6B', fontSize: 13, marginBottom: 8 },
  thanks: { color: C.yellow, fontSize: 15, fontWeight: '700', textAlign: 'center', marginVertical: 8 },
  btn: { backgroundColor: C.yellow, paddingVertical: 15, borderRadius: 14, alignItems: 'center' },
  btnText: { color: C.black, fontSize: 16, fontWeight: '800' },
});
