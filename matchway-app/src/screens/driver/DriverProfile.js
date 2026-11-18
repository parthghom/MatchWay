// Driver profile: his details, his vehicle, the photos he uploaded, and the Log out button at the end.
import React, { useEffect, useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet, StatusBar, Image, Modal, ActivityIndicator,
} from 'react-native';
import { C } from '../../theme';
import { API } from '../../config';
import { supabase } from '../../supabase';
import { BackArrow } from '../../components/icons';
import { VEHICLE_ICON } from './DriverHome';

const TOP = (StatusBar.currentHeight || 24) + 10;
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const STATUS = { approved: 'Verified', pending: 'Under review', rejected: 'Rejected' };
const DOC_ORDER = ['aadhaar', 'pan', 'licence', 'rc', 'vehicle_photo'];
const DOC_NAME = {
  aadhaar: 'Aadhaar card', pan: 'PAN card', licence: 'Driving licence',
  rc: 'Vehicle RC', vehicle_photo: 'Vehicle photo',
};

const cap = (t) => (t ? t.charAt(0).toUpperCase() + t.slice(1) : '—');

function birthday(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || '');
  return m ? `${parseInt(m[3], 10)} ${MONTHS[parseInt(m[2], 10) - 1]} ${m[1]}` : '—';
}

function Row({ label, value, last }) {
  return (
    <View style={[s.row, last && s.rowLast]}>
      <Text style={s.label}>{label}</Text>
      <Text style={s.value} numberOfLines={2}>{value || '—'}</Text>
    </View>
  );
}

// one uploaded photo, loaded from our server with the driver's login token
function DocPhoto({ docType, token, onOpen }) {
  const [state, setState] = useState('loading');   // loading | ok | bad
  const uri = `${API}/profile/document/${docType}`;
  const source = { uri, headers: { Authorization: `Bearer ${token}` } };
  return (
    <TouchableOpacity activeOpacity={0.9} disabled={state !== 'ok'} onPress={() => onOpen(source)} style={s.photoBox}>
      <Image
        source={source}
        style={s.photo}
        resizeMode="cover"
        onLoad={() => setState('ok')}
        onError={() => setState('bad')}
      />
      {state === 'loading' && <ActivityIndicator color={C.yellow} style={s.photoOverlay} />}
      {state === 'bad' && <Text style={[s.photoOverlay, s.photoBad]}>Photo not available</Text>}
    </TouchableOpacity>
  );
}

export default function DriverProfile({ profile, email, onBack, onSignOut }) {
  const p = profile?.profile || {};
  const vehicle = profile?.vehicle;
  const docs = profile?.documents || [];
  const name = p.full_name || 'Driver';
  const [token, setToken] = useState('');
  const [viewing, setViewing] = useState(null);   // image source shown full screen

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setToken(data?.session?.access_token || ''));
  }, []);

  const ordered = DOC_ORDER.map((t) => docs.find((d) => d.doc_type === t)).filter(Boolean);

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
        <Text style={s.role}>Driver</Text>

        <View style={s.card}>
          <Row label="Full name" value={p.full_name} />
          <Row label="Email" value={email} />
          <Row label="Phone" value={p.phone} />
          <Row label="Gender" value={cap(p.gender)} />
          <Row label="Date of birth" value={birthday(p.date_of_birth)} />
          <Row label="Account" value={STATUS[p.status] || cap(p.status)} last />
        </View>

        {vehicle && (
          <>
            <Text style={s.section}>Vehicle</Text>
            <View style={s.card}>
              <Row label="Type" value={`${VEHICLE_ICON[vehicle.vehicle_type] || ''} ${cap(vehicle.vehicle_type)}`.trim()} />
              <Row label="Number plate" value={vehicle.plate_number} last />
            </View>
          </>
        )}

        {ordered.length > 0 && <Text style={s.section}>Documents</Text>}
        {ordered.map((d) => (
          <View key={d.doc_type} style={s.docCard}>
            <View style={s.docTop}>
              <Text style={s.docName}>{DOC_NAME[d.doc_type] || cap(d.doc_type)}</Text>
              <Text style={s.docStatus}>{STATUS[d.status] || cap(d.status)}</Text>
            </View>
            {d.doc_number ? <Text style={s.docNumber}>{d.doc_number}</Text> : null}
            {token ? <DocPhoto docType={d.doc_type} token={token} onOpen={setViewing} /> : null}
          </View>
        ))}

        <TouchableOpacity style={s.logout} onPress={onSignOut} activeOpacity={0.85}>
          <Text style={s.logoutText}>Log out</Text>
        </TouchableOpacity>
      </ScrollView>

      <Modal visible={!!viewing} transparent animationType="fade" onRequestClose={() => setViewing(null)}>
        <TouchableOpacity style={s.modal} activeOpacity={1} onPress={() => setViewing(null)}>
          {viewing && <Image source={viewing} style={s.full} resizeMode="contain" />}
          <Text style={s.tapClose}>Tap anywhere to close</Text>
        </TouchableOpacity>
      </Modal>
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
  rowLast: { borderBottomWidth: 0 },
  label: { color: C.muted, fontSize: 14 },
  value: { color: C.text, fontSize: 15, fontWeight: '600', flexShrink: 1, textAlign: 'right', marginLeft: 16 },

  docCard: { backgroundColor: C.card, borderRadius: 18, borderWidth: 1, borderColor: C.line, padding: 16, marginBottom: 12 },
  docTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  docName: { color: C.text, fontSize: 16, fontWeight: '700' },
  docStatus: { color: C.yellow, fontSize: 13, fontWeight: '700' },
  docNumber: { color: C.muted, fontSize: 14, marginTop: 6 },
  photoBox: { height: 190, borderRadius: 12, overflow: 'hidden', backgroundColor: '#1A1A1A', marginTop: 14, justifyContent: 'center', alignItems: 'center' },
  photo: { width: '100%', height: '100%' },
  photoOverlay: { position: 'absolute' },
  photoBad: { color: C.muted, fontSize: 14 },

  logout: { marginTop: 28, borderWidth: 1.5, borderColor: C.yellow, borderRadius: 14, paddingVertical: 15, alignItems: 'center' },
  logoutText: { color: C.yellow, fontSize: 17, fontWeight: '800' },

  modal: { flex: 1, backgroundColor: 'rgba(0,0,0,0.94)', justifyContent: 'center', alignItems: 'center' },
  full: { width: '100%', height: '80%' },
  tapClose: { color: C.muted, fontSize: 13, marginTop: 12 },
});
