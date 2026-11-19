// The rider's screen once a driver accepted: a full-screen map with the pickup, the drop and the
// route between them, and a card at the bottom. Before the ride starts the card shows the driver
// and the 4-digit OTP to tell him; after he starts the ride it shows the trip is on.
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, StatusBar, ActivityIndicator } from 'react-native';
import { api } from '../../api';
import { C } from '../../theme';
import OlaMap from '../../components/OlaMap';

const FIT_PAD = { top: 90, bottom: 380, left: 40, right: 40 };
const rupee = (n) => `₹${Number(n).toFixed(Number.isInteger(Number(n)) ? 0 : 2)}`;

export default function RideTripScreen({ ride, trip, started }) {
  const [route, setRoute] = useState(null);

  // the line from pickup to drop
  useEffect(() => {
    let alive = true;
    const { pickup, drop } = trip;
    api.get('/maps/route', {
      params: { origin_lat: pickup.lat, origin_lon: pickup.lon, dest_lat: drop.lat, dest_lon: drop.lon },
    }).then((res) => {
      if (alive) setRoute(res.data.points && res.data.points.length > 1 ? res.data.points : [[pickup.lat, pickup.lon], [drop.lat, drop.lon]]);
    }).catch(() => {
      if (alive) setRoute([[pickup.lat, pickup.lon], [drop.lat, drop.lon]]);
    });
    return () => { alive = false; };
  }, [trip]);

  return (
    <View style={s.screen}>
      <StatusBar barStyle="light-content" backgroundColor={C.bg} />
      <OlaMap
        pickup={trip.pickup}
        drop={trip.drop}
        route={route}
        fitPad={FIT_PAD}
        style={StyleSheet.absoluteFillObject}
      />

      <View style={s.sheet}>
        <Text style={s.title}>{started ? 'Ride in progress' : 'Driver is on the way'}</Text>

        <View style={s.place}>
          <View style={s.dotPick} />
          <Text style={s.placeName} numberOfLines={1}>{trip.pickup.name}</Text>
        </View>
        <View style={s.line} />
        <View style={s.place}>
          <View style={s.dotDrop} />
          <Text style={s.placeName} numberOfLines={1}>{trip.drop.name}</Text>
        </View>

        <View style={s.row}>
          <View style={{ flex: 1 }}>
            <Text style={s.mute}>Driver</Text>
            <Text style={s.value} numberOfLines={1}>{ride.driver_name || 'Your driver'}</Text>
            <Text style={s.driverRating}>
              {ride.driver_rating && ride.driver_rating.count > 0
                ? `★ ${ride.driver_rating.score.toFixed(1)} · ${ride.driver_rating.count} review${ride.driver_rating.count === 1 ? '' : 's'}`
                : 'New driver'}
            </Text>
          </View>
          <View style={{ alignItems: 'flex-end' }}>
            <Text style={s.mute}>Your fare</Text>
            <Text style={s.fare}>{rupee(ride.exact_share)}</Text>
          </View>
        </View>

        {!started ? (
          <View style={s.otpBox}>
            <Text style={s.mute}>Tell this OTP to the driver when he arrives</Text>
            <Text style={s.otp}>{ride.otp}</Text>
          </View>
        ) : (
          <View style={s.otpBox}>
            <ActivityIndicator color={C.yellow} />
            <Text style={[s.mute, { marginTop: 8 }]}>The trip ends when the driver reaches your drop</Text>
          </View>
        )}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg },
  sheet: {
    position: 'absolute', left: 0, right: 0, bottom: 0, backgroundColor: C.card,
    borderTopLeftRadius: 24, borderTopRightRadius: 24, borderTopWidth: 1, borderColor: C.line,
    paddingHorizontal: 20, paddingTop: 18, paddingBottom: 28,
  },
  title: { color: C.text, fontSize: 20, fontWeight: '800', marginBottom: 14 },
  place: { flexDirection: 'row', alignItems: 'center' },
  dotPick: { width: 12, height: 12, borderRadius: 6, backgroundColor: '#35D07F', marginRight: 12 },
  dotDrop: { width: 12, height: 12, borderRadius: 3, backgroundColor: C.yellow, marginRight: 12 },
  placeName: { color: C.text, fontSize: 14, fontWeight: '600', flex: 1 },
  line: { width: 2, height: 10, backgroundColor: C.line, marginLeft: 5, marginVertical: 3 },
  row: { flexDirection: 'row', marginTop: 16, paddingTop: 14, borderTopWidth: 1, borderTopColor: C.line },
  mute: { color: C.muted, fontSize: 12 },
  value: { color: C.text, fontSize: 16, fontWeight: '700', marginTop: 2 },
  driverRating: { color: C.yellow, fontSize: 12, fontWeight: '700', marginTop: 2 },
  fare: { color: C.yellow, fontSize: 24, fontWeight: '800', marginTop: 2 },
  otpBox: { alignItems: 'center', marginTop: 14, paddingVertical: 12, borderRadius: 14, backgroundColor: C.bg, borderWidth: 1, borderColor: C.line },
  otp: { color: C.yellow, fontSize: 42, fontWeight: '800', letterSpacing: 12, marginTop: 4 },
});
