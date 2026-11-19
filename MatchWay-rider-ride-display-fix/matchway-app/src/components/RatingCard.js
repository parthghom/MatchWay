// "Your rating" card for the profile pages (rider and driver).
// The number is the EMA score kept by the server: every review moves it, and newer reviews count more.
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { api } from '../api';
import { C } from '../theme';

export function StarRow({ value, size = 16 }) {
  const full = Math.round(value);
  return (
    <Text style={{ fontSize: size, letterSpacing: 2 }}>
      {[1, 2, 3, 4, 5].map((n) => (
        <Text key={n} style={{ color: n <= full ? C.yellow : C.line }}>★</Text>
      ))}
    </Text>
  );
}

export default function RatingCard({ initial }) {
  const [rating, setRating] = useState(initial || null);   // { score, count }

  useEffect(() => {
    let alive = true;
    api.get('/ratings/me')
      .then((res) => { if (alive) setRating(res.data); })
      .catch(() => {});
    return () => { alive = false; };
  }, []);

  if (!rating) return null;
  const isNew = rating.count === 0;

  return (
    <View style={s.card}>
      <View style={s.left}>
        <Text style={s.score}>{isNew ? '—' : rating.score.toFixed(1)}</Text>
        <Text style={s.outOf}>{isNew ? 'New' : 'out of 5'}</Text>
      </View>
      <View style={s.right}>
        <StarRow value={isNew ? 0 : rating.score} size={20} />
        <Text style={s.line}>
          {isNew ? 'No reviews yet' : `Based on ${rating.count} review${rating.count === 1 ? '' : 's'}`}
        </Text>
        <Text style={s.note}>Recent rides count the most.</Text>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  card: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: C.card, borderRadius: 18,
    borderWidth: 1, borderColor: C.line, padding: 16, marginBottom: 14,
  },
  left: { alignItems: 'center', paddingRight: 18, marginRight: 18, borderRightWidth: 1, borderRightColor: C.line, minWidth: 74 },
  score: { color: C.yellow, fontSize: 36, fontWeight: '800' },
  outOf: { color: C.muted, fontSize: 12, marginTop: 2 },
  right: { flex: 1 },
  line: { color: C.text, fontSize: 14, fontWeight: '600', marginTop: 6 },
  note: { color: C.muted, fontSize: 12, marginTop: 2 },
});
