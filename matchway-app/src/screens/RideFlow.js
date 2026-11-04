import React, { useState } from 'react';
import {
  SafeAreaView, ScrollView, View, Text, TextInput, TouchableOpacity,
  StyleSheet, Alert, StatusBar, ActivityIndicator,
} from 'react-native';
import { api } from '../api';


const C = {
  bg: '#0B0B0B', card: '#161616', line: '#2B2B2B',
  yellow: '#FFC800', text: '#F5F5F5', mute: '#9A9A9A', black: '#0B0B0B',
};

function errorText(e) {
  const d = e?.response?.data?.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d)) return d.map((x) => x.msg).join('\n');
  return e.message || 'Something went wrong';
}

function Btn({ title, onPress, ghost, disabled, loading }) {
  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.8}
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

function Choice({ options, value, onChange }) {
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

function Field({ label, ...props }) {
  return (
    <View>
      <Text style={s.label}>{label}</Text>
      <TextInput style={s.input} placeholderTextColor="#666" {...props} />
    </View>
  );
}

function Stepper({ index }) {
  const names = ['Request', 'Match', 'Ride', 'Pay'];
  return (
    <View style={s.stepper}>
      {names.map((n, i) => (
        <View key={n} style={s.stepItem}>
          <View style={[s.bar, i <= index && s.barOn]} />
          <Text style={[s.stepText, i <= index && { color: C.yellow }]}>{n}</Text>
        </View>
      ))}
    </View>
  );
}

export default function RideFlow({ onSignOut }) {
  const [step, setStep] = useState('request');
  const [busy, setBusy] = useState(false);

  const [name, setName] = useState('');
  const [gender, setGender] = useState('female');
  const [vehicle, setVehicle] = useState('cab');
  const [sameOnly, setSameOnly] = useState(false);
  const [destination, setDestination] = useState('');
  const [km, setKm] = useState('5');

  const [riderId, setRiderId] = useState('');
  const [result, setResult] = useState(null);
  const [ride, setRide] = useState(null);
  const [otp, setOtp] = useState('');
  const [started, setStarted] = useState(false);
  const [payments, setPayments] = useState([]);
  const [rating, setRating] = useState(0);

  async function run(fn) {
    setBusy(true);
    try { await fn(); } catch (e) { Alert.alert('Error', errorText(e)); } finally { setBusy(false); }
  }

  const addDemoDriver = () => run(async () => {
    await api.post('/drivers', {
      id: 'd' + Date.now(), name: 'Demo Driver', vehicle_type: vehicle,
      is_busy: false, latitude: 18.7603, longitude: 73.3814,
    });
    Alert.alert('Done', 'A demo ' + vehicle + ' driver was added near the campus.');
  });

  const requestRide = () => run(async () => {
    if (!destination.trim()) throw new Error('Enter a destination');
    const kmNum = parseFloat(km);
    if (isNaN(kmNum) || kmNum <= 0) throw new Error('Enter the distance in km');
    const id = 'r' + Date.now();
    const res = await api.post('/rides/request', {
      rider: {
        id, name: name.trim() || 'Rider', gender,
        preference: sameOnly ? (gender === 'male' ? 'male_only' : 'female_only') : 'mix',
      },
      request: {
        id: 'q' + id, rider_id: id, flow: 'campus_to_destination',
        destination: destination.trim(), vehicle_type: vehicle,
        time_window_start: 600, time_window_end: 660,
      },
      route: ['Campus Gate', 'Station Road', destination.trim()],
      pickup_lat: 18.7603, pickup_lon: 73.3814, km: kmNum,
    });
    setRiderId(id); setResult(res.data); setStep('matched');
  });

  const confirmRide = () => run(async () => {
    const res = await api.post('/rides/confirm', { room_id: result.room_id });
    if (!res.data.confirmed) {
      Alert.alert('No driver', res.data.message + '. Go back and tap "Add demo driver".');
      return;
    }
    setRide(res.data); setStarted(false); setOtp(''); setStep('ride');
  });

  const startRide = () => run(async () => {
    await api.post('/rides/start', { ride_id: ride.ride_id, otp });
    setStarted(true);
  });

  const completeRide = () => run(async () => {
    const res = await api.post('/rides/complete', { ride_id: ride.ride_id });
    setPayments(res.data.payments); setRating(0); setStep('done');
  });

  const review = (stars) => run(async () => {
    await api.post('/rides/review', {
      ride_id: ride.ride_id, reviewer_id: riderId, target_id: ride.driver_id, stars,
    });
    setRating(stars);
  });

  function reset() {
    setStep('request'); setResult(null); setRide(null);
    setPayments([]); setRating(0); setStarted(false); setOtp('');
  }

  const index = { request: 0, matched: 1, ride: 2, done: 3 }[step];

  return (
    <SafeAreaView style={s.screen}>
      <StatusBar barStyle="light-content" backgroundColor={C.bg} />
      <ScrollView contentContainerStyle={s.body} keyboardShouldPersistTaps="handled">
        <Text style={s.logo}>Match<Text style={{ color: C.yellow }}>Way</Text></Text>
        <View style={s.topRight}>
          <TouchableOpacity onPress={onSignOut}>
            <Text style={s.signOut}>Sign out</Text>
          </TouchableOpacity>
        </View>
        <Text style={s.tag}>Share rides. Split fares.</Text>
        <Stepper index={index} />

        {step === 'request' && (
          <View>
            <Text style={s.h2}>Where to?</Text>
            <View style={s.card}>
              <Field label="Your name" value={name} onChangeText={setName} placeholder="Asha" />
              <Text style={s.label}>Gender</Text>
              <Choice options={['female', 'male']} value={gender} onChange={setGender} />
              <Text style={s.label}>Vehicle</Text>
              <Choice options={['cab', 'auto', 'bike']} value={vehicle} onChange={setVehicle} />
              <Text style={s.label}>Share only with the same gender?</Text>
              <Choice options={['No', 'Yes']} value={sameOnly ? 'Yes' : 'No'} onChange={(v) => setSameOnly(v === 'Yes')} />
              <Field label="Destination" value={destination} onChangeText={setDestination} placeholder="City Mall" />
              <Field label="Distance (km)" value={km} onChangeText={setKm} keyboardType="numeric" />
            </View>
            <Btn title="Find my ride" onPress={requestRide} loading={busy} />
            <Btn title="Add demo driver" onPress={addDemoDriver} ghost disabled={busy} />
          </View>
        )}

        {step === 'matched' && result && (
          <View>
            <Text style={s.h2}>You are in a virtual room</Text>
            <View style={s.card}>
              <Text style={s.mute}>Room</Text>
              <Text style={s.big}>{result.room_id}</Text>
              <Text style={[s.mute, { marginTop: 14 }]}>Compatible co-riders</Text>
              <Text style={s.value}>{result.matches.length ? result.matches.join(', ') : 'None yet'}</Text>
              <Text style={[s.mute, { marginTop: 14 }]}>Your fare range</Text>
              <Text style={s.fare}>₹{result.fare_low} to ₹{result.fare_high}</Text>
              <Text style={s.hint}>The more riders join, the lower your fare.</Text>
            </View>
            <Btn title="Confirm and find a driver" onPress={confirmRide} loading={busy} />
            <Btn title="Back" onPress={reset} ghost disabled={busy} />
          </View>
        )}

        {step === 'ride' && ride && (
          <View>
            <Text style={s.h2}>{started ? 'Ride in progress' : 'Driver assigned'}</Text>
            <View style={s.card}>
              <Text style={s.mute}>Driver</Text>
              <Text style={s.value}>{ride.driver_id}</Text>
              <Text style={[s.mute, { marginTop: 14 }]}>Your exact fare</Text>
              <Text style={s.fare}>₹{ride.exact_share}</Text>
            </View>
            {!started ? (
              <View>
                <View style={s.card}>
                  <Text style={s.mute}>Demo OTP (the driver would tell you)</Text>
                  <Text style={s.otp}>{ride.otp}</Text>
                  <Field label="Enter the OTP to start" value={otp} onChangeText={setOtp} keyboardType="numeric" maxLength={4} />
                </View>
                <Btn title="Start ride" onPress={startRide} loading={busy} />
              </View>
            ) : (
              <Btn title="Reach destination and pay" onPress={completeRide} loading={busy} />
            )}
          </View>
        )}

        {step === 'done' && (
          <View>
            <Text style={s.h2}>Ride completed</Text>
            <View style={s.card}>
              <Text style={s.mute}>You paid</Text>
              {payments.map((p) => (
                <Text key={p.rider_id} style={s.fare}>₹{p.amount}</Text>
              ))}
            </View>
            <View style={s.card}>
              <Text style={s.mute}>Rate your driver</Text>
              <View style={[s.row, { marginTop: 10 }]}>
                {[1, 2, 3, 4, 5].map((n) => (
                  <TouchableOpacity key={n} disabled={busy || rating > 0} onPress={() => review(n)}>
                    <Text style={[s.star, n <= rating && { color: C.yellow }]}>★</Text>
                  </TouchableOpacity>
                ))}
              </View>
              {rating > 0 && <Text style={s.hint}>Thanks for your review.</Text>}
            </View>
            <Btn title="Book another ride" onPress={reset} />
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg },
  body: { padding: 20, paddingTop: 56, paddingBottom: 40 },
  logo: { fontSize: 34, fontWeight: '800', color: C.text, letterSpacing: 0.5 },
  topRight: { position: 'absolute', right: 0, top: 56 },
  signOut: { color: C.yellow, fontWeight: '700', fontSize: 14 },
  tag: { color: C.mute, marginTop: 2, marginBottom: 18 },
  stepper: { flexDirection: 'row', marginBottom: 6 },
  stepItem: { flex: 1, marginRight: 6 },
  bar: { height: 4, borderRadius: 2, backgroundColor: C.line },
  barOn: { backgroundColor: C.yellow },
  stepText: { color: C.mute, fontSize: 11, marginTop: 6 },
  h2: { fontSize: 24, fontWeight: '700', color: C.text, marginTop: 18, marginBottom: 12 },
  card: { backgroundColor: C.card, borderRadius: 16, padding: 16, borderWidth: 1, borderColor: C.line, marginBottom: 12 },
  label: { color: C.mute, marginTop: 14, marginBottom: 8, fontSize: 13 },
  mute: { color: C.mute, fontSize: 13 },
  value: { color: C.text, fontSize: 17, marginTop: 4 },
  big: { color: C.yellow, fontSize: 28, fontWeight: '800', marginTop: 4 },
  fare: { color: C.yellow, fontSize: 30, fontWeight: '800', marginTop: 4 },
  otp: { color: C.yellow, fontSize: 44, fontWeight: '800', letterSpacing: 10, marginVertical: 8 },
  hint: { color: C.mute, fontSize: 12, marginTop: 10 },
  input: { backgroundColor: '#0F0F0F', color: C.text, borderRadius: 10, borderWidth: 1, borderColor: C.line, paddingHorizontal: 12, paddingVertical: 11, fontSize: 16 },
  row: { flexDirection: 'row', flexWrap: 'wrap' },
  chip: { paddingVertical: 9, paddingHorizontal: 18, borderRadius: 22, borderWidth: 1, borderColor: C.line, marginRight: 8, marginBottom: 8, backgroundColor: '#0F0F0F' },
  chipOn: { backgroundColor: C.yellow, borderColor: C.yellow },
  chipText: { color: C.text },
  chipTextOn: { color: C.black, fontWeight: '700' },
  btn: { backgroundColor: C.yellow, paddingVertical: 15, borderRadius: 14, alignItems: 'center', marginTop: 12 },
  btnGhost: { backgroundColor: 'transparent', borderWidth: 1, borderColor: C.yellow },
  btnText: { color: C.black, fontSize: 16, fontWeight: '800' },
  star: { fontSize: 40, color: C.line, marginRight: 10 },
});