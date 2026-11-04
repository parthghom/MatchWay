import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { C } from '../../theme';

export default function StepHeader({ index, total }) {
  return (
    <View style={s.container}>
      <Text style={s.text}>Step {index} of {total}</Text>
      <View style={s.barRow}>
        {Array.from({ length: total }).map((_, i) => (
          <View
            key={i}
            style={[s.bar, i < index ? { backgroundColor: C.yellow } : { backgroundColor: '#2B2B2B' }]}
          />
        ))}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  container: { marginBottom: 24 },
  text: { color: C.muted, fontSize: 14, marginBottom: 8, textAlign: 'center' },
  barRow: { flexDirection: 'row', gap: 4, justifyContent: 'center' },
  bar: { flex: 1, height: 3, borderRadius: 2 },
});
