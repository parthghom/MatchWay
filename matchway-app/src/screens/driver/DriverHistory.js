// "History" tab for drivers: the trips he has completed (none yet).
import React from 'react';
import { View, Text, StyleSheet, StatusBar } from 'react-native';
import { C } from '../../theme';

const TOP = (StatusBar.currentHeight || 24) + 16;

export default function DriverHistory() {
  return (
    <View style={s.screen}>
      <Text style={s.title}>Trip history</Text>
      <View style={s.emptyBox}>
        <Text style={s.emptyTitle}>No completed trips yet</Text>
        <Text style={s.emptyText}>Trips you finish will show up here.</Text>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg, paddingTop: TOP, paddingHorizontal: 16 },
  title: { color: C.text, fontSize: 26, fontWeight: '800', marginBottom: 14, marginLeft: 4 },
  emptyBox: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingBottom: 80 },
  emptyTitle: { color: C.text, fontSize: 18, fontWeight: '700' },
  emptyText: { color: C.muted, fontSize: 14, marginTop: 6 },
});
