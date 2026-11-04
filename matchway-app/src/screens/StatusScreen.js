import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { C } from '../theme';
import { Btn } from '../components/ui';

export default function StatusScreen({ title, message, onSignOut, onRefresh }) {
  return (
    <ScrollView contentContainerStyle={s.container}>
      <View style={s.card}>
        <Text style={s.title}>{title}</Text>
        <Text style={s.message}>{message}</Text>

        <Btn title="Refresh" onPress={onRefresh} />
        <Btn title="Sign out" ghost onPress={onSignOut} />
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: 20,
    paddingTop: 56,
    backgroundColor: C.bg,
    justifyContent: 'center',
    alignItems: 'center'
  },
  card: {
    backgroundColor: C.card,
    borderRadius: 16,
    padding: 24,
    borderWidth: 1,
    borderColor: C.line,
    width: '100%',
    maxWidth: 400,
    alignItems: 'center',
    textAlign: 'center'
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    color: C.text,
    marginBottom: 12,
    textAlign: 'center'
  },
  message: {
    fontSize: 16,
    color: C.muted,
    marginBottom: 24,
    textAlign: 'center'
  },
});
