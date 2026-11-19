// The box at the top of the driver's home screen, under "MatchWay" and the profile button.
//  offered      : a new request. Pickup, drop, fare, how many people, Accept / Reject.
//  confirmed    : accepted. He drives to the pickup (route on the map), then taps
//                 "I have reached the pickup" and types the 4-digit OTP the riders see.
//  in_progress  : OTP was right. He drives to the drop and taps "Reached drop" to finish.
import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { C } from '../../theme';
import { CodeInput } from '../../components/ui';

const rupee = (n) => `₹${Number(n).toFixed(Number.isInteger(Number(n)) ? 0 : 2)}`;

function Place({ kind, name }) {
  return (
    <View style={s.place}>
      <View style={kind === 'pickup' ? s.dotPick : s.dotDrop} />
      <View style={{ flex: 1 }}>
        <Text style={s.placeLabel}>{kind === 'pickup' ? 'Pickup' : 'Drop'}</Text>
        <Text style={s.placeName} numberOfLines={2}>{name}</Text>
      </View>
    </View>
  );
}

function Button({ title, onPress, ghost, danger, disabled, loading, flex }) {
  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.8}
      style={[s.btn, ghost && s.btnGhost, danger && s.btnDanger, flex && { flex: 1 }, (disabled || loading) && { opacity: 0.5 }]}
    >
      {loading
        ? <ActivityIndicator color={ghost || danger ? C.yellow : C.black} />
        : <Text style={[s.btnText, (ghost || danger) && { color: danger ? '#FF6B6B' : C.yellow }]}>{title}</Text>}
    </TouchableOpacity>
  );
}

export default function DriverRideCard({ top, ride, busy, error, earned, onDismissEarned, onAccept, onReject, onStart, onComplete }) {
  const [arrived, setArrived] = useState(false);
  const [otp, setOtp] = useState('');
  const [left, setLeft] = useState(0);

  // a different ride: start the card fresh
  const rideId = ride ? ride.ride_id : null;
  useEffect(() => { setArrived(false); setOtp(''); }, [rideId]);

  // the 30 s to accept, counting down every second
  const offered = ride && ride.status === 'offered';
  const secondsLeft = ride ? ride.seconds_left : null;
  useEffect(() => {
    if (!offered) return undefined;
    setLeft(secondsLeft || 0);
    const t = setInterval(() => setLeft((n) => Math.max(0, n - 1)), 1000);
    return () => clearInterval(t);
  }, [offered, rideId, secondsLeft]);

  if (earned !== null && !ride) {
    return (
      <View style={[s.card, { top }]}>
        <Text style={s.title}>Ride completed</Text>
        <Text style={s.bigFare}>{rupee(earned)}</Text>
        <Text style={s.sub}>Total fare for this trip</Text>
        <Button title="OK" onPress={onDismissEarned} />
      </View>
    );
  }
  if (!ride) return null;

  const people = ride.riders;
  const fareLine = (
    <View style={s.statsRow}>
      <View style={s.stat}>
        <Text style={s.statLabel}>Fare</Text>
        <Text style={s.statValue}>{rupee(ride.total_fare)}</Text>
        {people > 1 && <Text style={s.statSub}>{rupee(ride.fare_each)} each</Text>}
      </View>
      <View style={s.stat}>
        <Text style={s.statLabel}>People</Text>
        <Text style={s.statValue}>{people}</Text>
        <Text style={s.statSub} numberOfLines={1}>{ride.rider_names.join(', ')}</Text>
      </View>
      <View style={s.stat}>
        <Text style={s.statLabel}>Distance</Text>
        <Text style={s.statValue}>{Number(ride.km).toFixed(1)} km</Text>
      </View>
    </View>
  );

  if (ride.status === 'offered') {
    return (
      <View style={[s.card, { top }]}>
        <View style={s.titleRow}>
          <Text style={s.title}>New ride request</Text>
          <Text style={s.timer}>{left}s</Text>
        </View>
        <Place kind="pickup" name={ride.pickup.name} />
        <View style={s.line} />
        <Place kind="drop" name={ride.drop ? ride.drop.name : 'Drop'} />
        {fareLine}
        {!!error && <Text style={s.error}>{error}</Text>}
        <View style={s.btnRow}>
          <Button title="Reject" danger onPress={onReject} disabled={busy} flex />
          <View style={{ width: 10 }} />
          <Button title="Accept" onPress={onAccept} loading={busy} disabled={left === 0} flex />
        </View>
      </View>
    );
  }

  if (ride.status === 'confirmed') {
    return (
      <View style={[s.card, { top }]}>
        <Text style={s.title}>Go to the pickup</Text>
        <Place kind="pickup" name={ride.pickup.name} />
        {fareLine}
        {!arrived ? (
          <Button title="I have reached the pickup" onPress={() => setArrived(true)} />
        ) : (
          <View>
            <Text style={s.sub}>Ask the rider for the 4-digit OTP shown on their phone</Text>
            <CodeInput value={otp} onChange={setOtp} length={4} />
            {!!error && <Text style={s.error}>{error}</Text>}
            <Button title="Start ride" onPress={async () => { const r = await onStart(otp); if (r === null) setOtp(''); }} loading={busy} disabled={otp.length < 4} />
          </View>
        )}
      </View>
    );
  }

  // in_progress
  return (
    <View style={[s.card, { top }]}>
      <Text style={s.title}>Ride in progress</Text>
      <Place kind="drop" name={ride.drop ? ride.drop.name : 'Drop'} />
      {fareLine}
      {!!error && <Text style={s.error}>{error}</Text>}
      <Button title="Reached drop, end ride" onPress={onComplete} loading={busy} />
    </View>
  );
}

const s = StyleSheet.create({
  card: {
    position: 'absolute', left: 12, right: 12, backgroundColor: C.card, borderRadius: 18,
    borderWidth: 1.5, borderColor: C.yellow, padding: 14, elevation: 8, zIndex: 20,
  },
  titleRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { color: C.text, fontSize: 17, fontWeight: '800', marginBottom: 10 },
  timer: { color: C.yellow, fontSize: 15, fontWeight: '800', marginBottom: 10 },
  place: { flexDirection: 'row', alignItems: 'center' },
  dotPick: { width: 12, height: 12, borderRadius: 6, backgroundColor: '#35D07F', marginRight: 12 },
  dotDrop: { width: 12, height: 12, borderRadius: 3, backgroundColor: C.yellow, marginRight: 12 },
  placeLabel: { color: C.muted, fontSize: 11 },
  placeName: { color: C.text, fontSize: 14, fontWeight: '600' },
  line: { width: 2, height: 10, backgroundColor: C.line, marginLeft: 5, marginVertical: 3 },
  statsRow: { flexDirection: 'row', marginTop: 12, marginBottom: 12, paddingTop: 10, borderTopWidth: 1, borderTopColor: C.line },
  stat: { flex: 1 },
  statLabel: { color: C.muted, fontSize: 11 },
  statValue: { color: C.yellow, fontSize: 18, fontWeight: '800', marginTop: 2 },
  statSub: { color: C.muted, fontSize: 11, marginTop: 1 },
  sub: { color: C.muted, fontSize: 12, marginTop: 8, marginBottom: 6 },
  bigFare: { color: C.yellow, fontSize: 34, fontWeight: '800' },
  error: { color: '#FF6B6B', fontSize: 13, marginTop: 6, marginBottom: 4 },
  btnRow: { flexDirection: 'row' },
  btn: { backgroundColor: C.yellow, borderRadius: 12, paddingVertical: 13, alignItems: 'center', marginTop: 6 },
  btnGhost: { backgroundColor: 'transparent', borderWidth: 1, borderColor: C.yellow },
  btnDanger: { backgroundColor: 'transparent', borderWidth: 1, borderColor: '#FF6B6B' },
  btnText: { color: C.black, fontSize: 15, fontWeight: '800' },
});
