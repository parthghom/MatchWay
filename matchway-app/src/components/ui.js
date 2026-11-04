import React, { useState, useRef } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator
} from 'react-native';
import { C } from '../theme';

export function Btn({ title, onPress, ghost, loading, disabled }) {
  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled || loading}
      style={[s.btn, ghost && s.btnGhost, (disabled || loading) && { opacity: 0.55 }]}
    >
      {loading ? (
        <ActivityIndicator color={ghost ? C.yellow : C.black} />
      ) : (
        <Text style={[s.btnText, ghost && { color: C.yellow }]}>{title}</Text>
      )}
    </TouchableOpacity>
  );
}

export function Field({ label, ...props }) {
  return (
    <View style={s.fieldContainer}>
      <Text style={s.label}>{label}</Text>
      <TextInput
        style={s.input}
        placeholderTextColor={C.muted}
        {...props}
      />
    </View>
  );
}

export function Choice({ options, value, onChange }) {
  return (
    <View style={s.row}>
      {options.map((o) => (
        <TouchableOpacity
          key={o}
          onPress={() => onChange(o)}
          style={[s.chip, value === o && s.chipOn]}
        >
          <Text style={[s.chipText, value === o && s.chipTextOn]}>{o}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

export function Logo() {
  return (
    <Text style={s.logo}>
      Match<Text style={{ color: C.yellow }}>Way</Text>
    </Text>
  );
}

export function CodeInput({ value, onChange, length }) {
  const inputs = useRef([]);

  const handleTextChange = (text) => {
    if (text.length <= length) {
      onChange(text);
    }
  };

  return (
    <View style={s.codeContainer}>
      <View style={s.boxesRow}>
        {Array.from({ length }).map((_, i) => (
          <View
            key={i}
            style={[
              s.box,
              i === value?.length && s.boxActive
            ]}
          >
            <Text style={s.boxText}>{value?.[i] || ''}</Text>
          </View>
        ))}
      </View>
      <TextInput
        ref={inputs}
        style={s.hiddenInput}
        keyboardType="number-pad"
        maxLength={length}
        autoFocus
        value={value}
        onChangeText={handleTextChange}
      />
    </View>
  );
}

const s = StyleSheet.create({
  fieldContainer: { marginBottom: 14 },
  label: { color: C.muted, marginBottom: 8, fontSize: 13 },
  input: {
    backgroundColor: '#0F0F0F',
    color: C.text,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: C.line,
    paddingHorizontal: 12,
    paddingVertical: 11,
    fontSize: 16
  },
  row: { flexDirection: 'row', flexWrap: 'wrap' },
  chip: {
    paddingVertical: 9,
    paddingHorizontal: 18,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: C.line,
    marginRight: 8,
    marginBottom: 8,
    backgroundColor: '#0F0F0F'
  },
  chipOn: { backgroundColor: C.yellow, borderColor: C.yellow },
  chipText: { color: C.text },
  chipTextOn: { color: C.black, fontWeight: '700' },
  logo: { fontSize: 34, fontWeight: '800', color: C.text, letterSpacing: 0.5 },
  btn: {
    backgroundColor: C.yellow,
    paddingVertical: 15,
    borderRadius: 14,
    alignItems: 'center',
    marginTop: 12
  },
  btnGhost: { backgroundColor: 'transparent', borderWidth: 1, borderColor: C.yellow },
  btnText: { color: C.black, fontSize: 16, fontWeight: '800' },
  codeContainer: { alignItems: 'center', marginVertical: 20 },
  boxesRow: { flexDirection: 'row', justifyContent: 'center', marginBottom: 10 },
  box: {
    width: 45,
    height: 45,
    backgroundColor: '#0F0F0F',
    borderWidth: 1,
    borderColor: C.line,
    borderRadius: 8,
    marginHorizontal: 5,
    justifyContent: 'center',
    alignItems: 'center'
  },
  boxActive: { borderColor: C.yellow, borderWidth: 2 },
  boxText: { color: C.text, fontSize: 20, fontWeight: '700' },
  hiddenInput: { position: 'absolute', opacity: 0, width: 1, height: 1 },
});
