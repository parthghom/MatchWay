import React, { useCallback, useEffect, useState } from 'react';
import {
  SafeAreaView, ScrollView, View, Text, TextInput, TouchableOpacity,
  StyleSheet, Alert, StatusBar, ActivityIndicator,
} from 'react-native';
import { api } from '../api';
import WaitingScreen from './ride/WaitingScreen';
import DriverSearchScreen from './ride/DriverSearchScreen';
import MainTabs from './ride/MainTabs';
import RideTripScreen from './ride/RideTripScreen';


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


function Field({ label, ...props }) {
  return (
    <View>
      <Text style={s.label}>{label}</Text>
      <TextInput style={s.input} placeholderTextColor="#666" {...props} />
    </View>
  );
}

export default function RideFlow({ profile, email, onSignOut }) {
  const [step, setStep] = useState('request');
  const [busy, setBusy] = useState(false);

  // name and gender come from the profile made during sign-up
  const name = profile?.profile?.full_name || 'Rider';
  const gender = profile?.profile?.gender === 'male' ? 'male' : 'female';
  const [vehicle, setVehicle] = useState('cab');
  const [trip, setTrip] = useState(null);   // { pickup, drop } of the booked ride

  const [riderId, setRiderId] = useState('');
  const [result, setResult] = useState(null);
  const [ride, setRide] = useState(null);
  const [started, setStarted] = useState(false);
  const [driverPos, setDriverPos] = useState(null);   // where the driver's vehicle is right now
  const [picked, setPicked] = useState(0);            // stars tapped, sent only when he presses Submit
  const [payments, setPayments] = useState([]);
  const [rating, setRating] = useState(0);

  async function run(fn) {
    setBusy(true);
    try { await fn(); } catch (e) { Alert.alert('Error', errorText(e)); } finally { setBusy(false); }
  }

  const requestRide = ({ vehicle: vehicleType, sameOnly, pickup: from, drop, km }) => run(async () => {
    const id = 'r' + Date.now();
    const res = await api.post('/rides/request', {
      rider: {
        id, name, gender,
        preference: sameOnly ? (gender === 'male' ? 'male_only' : 'female_only') : 'mix',
      },
      request: {
        id: 'q' + id, rider_id: id, flow: 'campus_to_destination',
        destination: drop.name, vehicle_type: vehicleType,
        time_window_start: 600, time_window_end: 660,
      },
      route: [from.name, drop.name],
      pickup_lat: from.lat, pickup_lon: from.lon, km,
      pickup_name: from.name, drop_lat: drop.lat, drop_lon: drop.lon, drop_name: drop.name,
      user_id: profile?.user_id,
    });
    setVehicle(vehicleType); setTrip({ pickup: from, drop, km });
    // a bike has one seat: straight to the driver search. Auto and cab look for peers first.
    setRiderId(id); setResult({ ...res.data, riders: 1 }); setStep(vehicleType === 'bike' ? 'finding' : 'matched');
  });

  // a driver was found (called by the driver-search screen)
  const driverFound = useCallback((data) => {
    setRide(data); setStarted(false); setStep('ride');
  }, []);
  // the group is final: nobody else can join, so show one exact price (full fare / riders)
  const groupReady = useCallback((room) => {
    if (room && typeof room.exact_share === 'number') {
      setResult((r) => (r ? { ...r, fare_low: room.exact_share, fare_high: room.exact_share, riders: room.members.length } : r));
    }
    setStep('finding');
  }, []);

  const cancelRide = () => run(async () => {
    await api.post('/rides/cancel', { rider_id: riderId });
    reset();
  });

  // after the driver accepted: the driver starts (with the OTP) and ends the trip on his phone,
  // so here we just follow the ride: confirmed -> in_progress -> completed
  useEffect(() => {
    if (step !== 'ride' || !ride) return undefined;
    let alive = true;
    async function load() {
      try {
        const res = await api.get(`/rides/${ride.ride_id}`);
        if (!alive) return;
        setStarted(res.data.status === 'in_progress');
        if (res.data.driver_lat != null) setDriverPos({ lat: res.data.driver_lat, lon: res.data.driver_lon });
        if (res.data.status === 'completed') {
          const pays = res.data.payments || [];
          setPayments(pays); setRating(0); setPicked(0); setStep('done');
        }
      } catch (e) {
        // keep the last status if the network blinks
      }
    }
    load();
    const t = setInterval(load, 3000);
    return () => { alive = false; clearInterval(t); };
  }, [step, ride]);

  const review = (stars) => run(async () => {
    await api.post('/rides/review', {
      ride_id: ride.ride_id, reviewer_id: riderId, target_id: ride.driver_id, stars,
    });
    setRating(stars);
  });

  function reset() {
    setStep('request'); setResult(null); setRide(null); setTrip(null);
    setPayments([]); setRating(0); setPicked(0); setStarted(false); setDriverPos(null);
  }

  if (step === 'request') {
    return (
      <MainTabs
        gender={gender}
        busy={busy}
        onBook={requestRide}
        profile={profile}
        email={email}
        onSignOut={onSignOut}
      />
    );
  }

  if (step === 'finding' && result && trip) {
    return (
      <>
        <StatusBar barStyle="light-content" backgroundColor={C.bg} />
        <DriverSearchScreen
          pickup={trip.pickup}
          drop={trip.drop}
          vehicle={vehicle}
          fareLow={result.fare_low}
          fareHigh={result.fare_high}
          riders={result.riders}
          roomId={result.room_id}
          busy={busy}
          onCancel={cancelRide}
          onFound={driverFound}
        />
      </>
    );
  }

  if (step === 'matched' && result && trip) {
    return (
      <>
        <StatusBar barStyle="light-content" backgroundColor={C.bg} />
        <WaitingScreen
          pickup={trip.pickup}
          drop={trip.drop}
          vehicle={vehicle}
          fareLow={result.fare_low}
          fareHigh={result.fare_high}
          roomId={result.room_id}
          riderId={riderId}
          busy={busy}
          onCancel={cancelRide}
          onReady={groupReady}
        />
      </>
    );
  }

  if (step === 'ride' && ride && trip) {
    return <RideTripScreen ride={ride} trip={trip} started={started} driverPos={driverPos} vehicle={vehicle} />;
  }

  return (
    <SafeAreaView style={s.screen}>
      <StatusBar barStyle="light-content" backgroundColor={C.bg} />
      <ScrollView contentContainerStyle={s.body} keyboardShouldPersistTaps="handled">
        {step === 'done' && (
          <View>
            <Text style={s.h2}>Ride completed</Text>
            <View style={s.card}>
              <Text style={s.mute}>You paid</Text>
              {payments.filter((p) => p.rider_id === riderId).map((p) => (
                <Text key={p.rider_id} style={s.fare}>₹{p.amount}</Text>
              ))}
            </View>
            <View style={s.card}>
              <Text style={s.mute}>Rate your driver</Text>
              <View style={[s.row, { marginTop: 10 }]}>
                {[1, 2, 3, 4, 5].map((n) => (
                  <TouchableOpacity key={n} disabled={busy || rating > 0} onPress={() => setPicked(n)}>
                    <Text style={[s.star, n <= (rating || picked) && { color: C.yellow }]}>★</Text>
                  </TouchableOpacity>
                ))}
              </View>
              {rating === 0 && picked > 0 && (
                <View style={{ marginTop: 14 }}>
                  <Btn title="Submit review" onPress={() => review(picked)} loading={busy} />
                </View>
              )}
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
  body: { padding: 20, paddingTop: 64, paddingBottom: 40 },
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