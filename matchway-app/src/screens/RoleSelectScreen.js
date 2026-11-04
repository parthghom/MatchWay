import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { C } from '../theme';
import { Logo, Btn } from '../components/ui';

export default function RoleSelectScreen({ onSelect }) {
  const [role, setRole] = useState(null);

  return (
    <ScrollView contentContainerStyle={s.container}>
      <View style={s.header}>
        <Logo />
        <Text style={s.title}>Who are you?</Text>
        <Text style={s.subtitle}>Choose how you will use MatchWay</Text>
      </View>

      <View style={s.cards}>
        <TouchableOpacity
          onPress={() => setRole('student')}
          style={[s.card, role === 'student' && s.cardSelected]}
        >
          <View style={s.cardContent}>
            <Text style={s.cardEmoji}>🎓</Text>
            <View style={s.textGroup}>
              <Text style={s.cardTitle}>Student</Text>
              <Text style={s.cardDesc}>Share rides with classmates, verified with your college email</Text>
            </View>
          </View>
          {role === 'student' && <Text style={s.tick}>✅</Text>}
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => setRole('driver')}
          style={[s.card, role === 'driver' && s.cardSelected]}
        >
          <View style={s.cardContent}>
            <Text style={s.cardEmoji}>🚕</Text>
            <View style={s.textGroup}>
              <Text style={s.cardTitle}>Driver</Text>
              <Text style={s.cardDesc}>Earn by driving students, verified with your documents</Text>
            </View>
          </View>
          {role === 'driver' && <Text style={s.tick}>✅</Text>}
        </TouchableOpacity>
      </View>

      <Btn
        title="Continue"
        onPress={() => onSelect(role)}
        disabled={!role}
      />
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: { flexGrow: 1, padding: 20, paddingTop: 56, backgroundColor: C.bg },
  header: { alignItems: 'center', marginBottom: 32 },
  title: { fontSize: 28, fontWeight: '800', color: C.text, marginTop: 16 },
  subtitle: { fontSize: 16, color: C.muted, textAlign: 'center', marginTop: 8 },
  cards: { marginBottom: 32 },
  card: {
    backgroundColor: C.card,
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: C.line,
    marginBottom: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between'
  },
  cardSelected: { borderColor: C.yellow },
  cardContent: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  cardEmoji: { fontSize: 32, marginRight: 16 },
  textGroup: { flex: 1 },
  cardTitle: { fontSize: 20, fontWeight: '700', color: C.text },
  cardDesc: { fontSize: 14, color: C.muted, marginTop: 4 },
  tick: { fontSize: 20, marginLeft: 10 },
});
