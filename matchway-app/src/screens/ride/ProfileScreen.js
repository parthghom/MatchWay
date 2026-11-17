// Profile page: what you gave when you signed up, and the only Log out button in the app.
import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, StatusBar } from 'react-native';
import { C } from '../../theme';
import { BackArrow } from '../../components/icons';

const TOP = (StatusBar.currentHeight || 24) + 10;
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function cap(t) {
  return t ? t.charAt(0).toUpperCase() + t.slice(1) : '—';
}

function birthday(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || '');
  return m ? `${parseInt(m[3], 10)} ${MONTHS[parseInt(m[2], 10) - 1]} ${m[1]}` : '—';
}

function docName(t) {
  if (t === 'id_card') return 'College ID card';
  return cap((t || '').replace(/_/g, ' '));
}

const STATUS = { approved: 'Verified', pending: 'Under review', rejected: 'Rejected' };

function Row({ label, value }) {
  return (
    <View style={s.row}>
      <Text style={s.label}>{label}</Text>
      <Text style={s.value} numberOfLines={2}>{value || '—'}</Text>
    </View>
  );
}

export default function ProfileScreen({ profile, email, onBack, onSignOut }) {
  const p = profile?.profile || {};
  const docs = profile?.documents || [];
  const name = p.full_name || 'Rider';

  return (
    <View style={s.screen}>
      <View style={s.bar}>
        <TouchableOpacity onPress={onBack} style={s.back} hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}>
          <BackArrow />
        </TouchableOpacity>
        <Text style={s.barTitle}>Profile</Text>
      </View>

      <ScrollView contentContainerStyle={s.body}>
        <View style={s.avatar}><Text style={s.avatarText}>{name.charAt(0).toUpperCase()}</Text></View>
        <Text style={s.name}>{name}</Text>
        <Text style={s.role}>{cap(p.role)}</Text>

        <View style={s.card}>
          <Row label="Full name" value={p.full_name} />
          <Row label="Email" value={email} />
          <Row label="Phone" value={p.phone} />
          <Row label="Gender" value={cap(p.gender)} />
          <Row label="Date of birth" value={birthday(p.date_of_birth)} />
          <Row label="Account" value={STATUS[p.status] || cap(p.status)} />
        </View>

        {docs.length > 0 && (
          <>
            <Text style={s.section}>Documents</Text>
            <View style={s.card}>
              {docs.map((d) => (
                <Row
                  key={d.doc_type}
                  label={docName(d.doc_type)}
                  value={`${STATUS[d.status] || cap(d.status)}${d.doc_number ? ` · ${d.doc_number}` : ''}`}
                />
              ))}
            </View>
          </>
        )}

        <TouchableOpacity style={s.logout} onPress={onSignOut} activeOpacity={0.85}>
          <Text style={s.logoutText}>Log out</Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg, paddingTop: TOP },
  bar: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, height: 44 },
  back: { width: 40, justifyContent: 'center' },
  barTitle: { color: C.text, fontSize: 20, fontWeight: '800' },
  body: { padding: 16, paddingBottom: 40 },
  avatar: { alignSelf: 'center', width: 88, height: 88, borderRadius: 44, backgroundColor: C.yellow, alignItems: 'center', justifyContent: 'center', marginTop: 10 },
  avatarText: { color: C.black, fontSize: 38, fontWeight: '800' },
  name: { color: C.text, fontSize: 22, fontWeight: '800', textAlign: 'center', marginTop: 12 },
  role: { color: C.yellow, fontSize: 14, fontWeight: '700', textAlign: 'center', marginTop: 2, marginBottom: 20 },
  section: { color: C.muted, fontSize: 13, marginTop: 20, marginBottom: 8, marginLeft: 4 },
  card: { backgroundColor: C.card, borderRadius: 18, borderWidth: 1, borderColor: C.line, paddingHorizontal: 16 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: C.line },
  label: { color: C.muted, fontSize: 14 },
  value: { color: C.text, fontSize: 15, fontWeight: '600', flexShrink: 1, textAlign: 'right', marginLeft: 16 },
  logout: { marginTop: 28, borderWidth: 1.5, borderColor: C.yellow, borderRadius: 14, paddingVertical: 15, alignItems: 'center' },
  logoutText: { color: C.yellow, fontSize: 17, fontWeight: '800' },
});
