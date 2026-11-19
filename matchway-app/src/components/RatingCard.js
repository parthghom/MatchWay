// Rating widgets for riders and drivers. The number is the EMA score kept by the server:
// every review moves it, and newer reviews count more.
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useMyRating } from '../ratings';
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

// small "★ 4.2" badge for the home screens (tap = open the profile)
export function RatingPill({ onPress }) {
  const { rating } = useMyRating();
  let label = '★ …';
  if (rating) label = rating.count === 0 ? '★ New' : `★ ${rating.score.toFixed(1)}`;
  return (
    <TouchableOpacity style={s.pill} onPress={onPress} activeOpacity={0.8}>
      <Text style={s.pillText}>{label}</Text>
    </TouchableOpacity>
  );
}

// the big card on the profile page. It is always shown, so you can tell what is going on.
export default function RatingCard({ initial }) {
  const { rating, failed } = useMyRating(initial);

  if (!rating) {
    return (
      <View style={s.card}>
        <View style={{ flex: 1 }}>
          <Text style={s.line}>{failed ? 'Could not load your rating' : 'Loading your rating…'}</Text>
          {failed ? <Text style={s.note}>Check your connection. If this stays, the server needs the latest update.</Text> : null}
        </View>
      </View>
    );
  }

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
  pill: {
    height: 40, paddingHorizontal: 12, borderRadius: 20, backgroundColor: C.card, borderWidth: 1.5,
    borderColor: C.line, alignItems: 'center', justifyContent: 'center', marginRight: 10,
  },
  pillText: { color: C.yellow, fontSize: 14, fontWeight: '800' },
});
