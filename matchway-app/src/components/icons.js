// Tiny icons drawn with plain Views (no icon library needed).
import React from 'react';
import { View } from 'react-native';
import { C } from '../theme';

export function SearchIcon({ color = C.yellow, size = 20 }) {
  const ring = size * 0.7;
  return (
    <View style={{ width: size, height: size }}>
      <View style={{ width: ring, height: ring, borderRadius: ring / 2, borderWidth: 2, borderColor: color }} />
      <View style={{
        position: 'absolute', right: 0, bottom: 1, width: size * 0.4, height: 2.5, borderRadius: 2,
        backgroundColor: color, transform: [{ rotate: '45deg' }],
      }} />
    </View>
  );
}

export function ClockIcon({ color = C.muted, size = 18 }) {
  return (
    <View style={{ width: size, height: size, borderRadius: size / 2, borderWidth: 2, borderColor: color, alignItems: 'center' }}>
      <View style={{ position: 'absolute', top: 2, width: 2, height: size * 0.35, backgroundColor: color }} />
      <View style={{ position: 'absolute', top: size * 0.38, left: size * 0.4, width: size * 0.25, height: 2, backgroundColor: color }} />
    </View>
  );
}

export function PinIcon({ color = C.yellow, size = 18 }) {
  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <View style={{
        width: size * 0.75, height: size * 0.75, borderRadius: size * 0.375,
        borderBottomRightRadius: 0, transform: [{ rotate: '45deg' }], backgroundColor: color,
        alignItems: 'center', justifyContent: 'center',
      }}>
        <View style={{ width: size * 0.25, height: size * 0.25, borderRadius: size * 0.125, backgroundColor: C.bg }} />
      </View>
    </View>
  );
}

export function TargetIcon({ color = C.yellow, size = 20 }) {
  return (
    <View style={{ width: size, height: size, borderRadius: size / 2, borderWidth: 2, borderColor: color, alignItems: 'center', justifyContent: 'center' }}>
      <View style={{ width: size * 0.3, height: size * 0.3, borderRadius: size * 0.15, backgroundColor: color }} />
    </View>
  );
}

export function BackArrow({ color = C.text, size = 20 }) {
  return (
    <View style={{ width: size, height: size, justifyContent: 'center' }}>
      <View style={{ height: 2.5, backgroundColor: color, borderRadius: 2 }} />
      <View style={{
        position: 'absolute', left: 1, width: size * 0.5, height: size * 0.5, borderLeftWidth: 2.5, borderBottomWidth: 2.5,
        borderColor: color, transform: [{ rotate: '45deg' }], top: size * 0.25,
      }} />
    </View>
  );
}

export function HomeIcon({ color = C.yellow, size = 24 }) {
  return (
    <View style={{ width: size, height: size, alignItems: 'center' }}>
      <View style={{
        position: 'absolute', top: size * 0.12, width: size * 0.5, height: size * 0.5,
        borderLeftWidth: 2.5, borderTopWidth: 2.5, borderColor: color, transform: [{ rotate: '45deg' }],
      }} />
      <View style={{
        position: 'absolute', bottom: 1, width: size * 0.66, height: size * 0.46,
        borderLeftWidth: 2.5, borderRightWidth: 2.5, borderBottomWidth: 2.5, borderColor: color,
      }} />
    </View>
  );
}

export function HistoryIcon({ color = C.yellow, size = 24 }) {
  return <ClockIcon color={color} size={size} />;
}

export function ProfileIcon({ color = C.yellow, size = 24 }) {
  return (
    <View style={{ width: size, height: size, alignItems: 'center' }}>
      <View style={{ width: size * 0.4, height: size * 0.4, borderRadius: size * 0.2, borderWidth: 2.2, borderColor: color }} />
      <View style={{
        position: 'absolute', bottom: 1, width: size * 0.8, height: size * 0.36,
        borderTopLeftRadius: size * 0.4, borderTopRightRadius: size * 0.4,
        borderWidth: 2.2, borderBottomWidth: 0, borderColor: color,
      }} />
    </View>
  );
}
