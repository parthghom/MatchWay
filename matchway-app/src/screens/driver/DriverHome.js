// Driver home: MatchWay on the left, profile button on the right, and the live map.
// The driver is shown on the map as an emoji of his own vehicle (cab, auto or bike).
import React, { useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, Linking, StatusBar } from 'react-native';
import { C } from '../../theme';
import { useDriverLocation } from './useDriverLocation';
import LocationProbe from './LocationProbe';
import OlaMap from '../../components/OlaMap';
import { TargetIcon, ProfileIcon } from '../../components/icons';
import { RatingPill } from '../../components/RatingCard';
import { useDriverRide } from './useDriverRide';
import DriverRideCard from './DriverRideCard';

const HEADER_H = 100;
export const VEHICLE_ICON = { bike: '🏍️', auto: '🛺', cab: '🚕' };

export default function DriverHome({ vehicleType, driverId, driverName, onProfile, visible = true }) {
  const { coords: user, status, debug, feed, note } = useDriverLocation();
  const trip = useDriverRide({ driverId, name: driverName, vehicleType, coords: user });
  const mapRef = useRef(null);

  return (
    <View style={s.screen}>
      <StatusBar barStyle="light-content" backgroundColor={C.bg} />
      <LocationProbe onFix={feed} onNote={note} />

      <OlaMap
        ref={mapRef}
        user={user}
        userIcon={VEHICLE_ICON[vehicleType]}
        route={trip.route}
        pickup={trip.ride && trip.ride.status !== 'in_progress' ? trip.ride.pickup : null}
        drop={trip.ride && trip.ride.status !== 'confirmed' ? trip.ride.drop : null}
        visible={visible}
        style={s.map}
      >
        {!user && (
          <View style={s.pill}>
            {status === 'loading' && <ActivityIndicator color={C.yellow} size="small" style={{ marginRight: 8 }} />}
            <Text style={s.pillText}>
              {status === 'denied' ? 'Location is off' : status === 'error' ? 'Could not find you' : 'Trying to find where you are… (b4)'}
            </Text>
            {status === 'denied' && (
              <TouchableOpacity onPress={() => Linking.openSettings()}>
                <Text style={s.pillLink}>  Turn on</Text>
              </TouchableOpacity>
            )}
          </View>
        )}
        {!user && !!debug && <Text style={s.debug}>{debug}</Text>}
        <TouchableOpacity
          style={s.locate}
          onPress={() => user && mapRef.current && mapRef.current.flyTo(user.lat, user.lon, 16)}
        >
          <TargetIcon />
        </TouchableOpacity>
      </OlaMap>

      <View style={s.header}>
        <View style={s.headerRow}>
          <Text style={s.logo}>Match<Text style={{ color: C.yellow }}>Way</Text></Text>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <RatingPill onPress={onProfile} />
            <TouchableOpacity style={s.profileBtn} onPress={onProfile} activeOpacity={0.8}>
              <ProfileIcon size={22} />
            </TouchableOpacity>
          </View>
        </View>
      </View>

      <DriverRideCard
        top={HEADER_H + 4}
        ride={trip.ride}
        busy={trip.busy}
        error={trip.error}
        earned={trip.earned}
        onDismissEarned={trip.dismissEarned}
        onAccept={trip.accept}
        onReject={trip.reject}
        onStart={trip.start}
        onComplete={trip.complete}
      />
    </View>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg },
  map: { position: 'absolute', top: HEADER_H, bottom: 0, left: 0, right: 0 },

  header: { position: 'absolute', top: 0, left: 0, right: 0, height: HEADER_H, backgroundColor: C.bg, paddingTop: 52, paddingHorizontal: 16 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  logo: { fontSize: 22, fontWeight: '800', color: C.text, letterSpacing: 0.5 },
  profileBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: C.card, borderWidth: 1.5, borderColor: C.yellow, alignItems: 'center', justifyContent: 'center' },

  pill: {
    position: 'absolute', bottom: 16, alignSelf: 'center', flexDirection: 'row', alignItems: 'center',
    backgroundColor: C.card, borderRadius: 24, borderWidth: 1, borderColor: C.line, paddingVertical: 10, paddingHorizontal: 18,
  },
  debug: { position: 'absolute', bottom: 66, left: 16, right: 16, textAlign: 'center', color: '#DDDDDD', fontSize: 12 },
  pillText: { color: C.text, fontSize: 14 },
  pillLink: { color: C.yellow, fontWeight: '700', fontSize: 14 },
  locate: {
    position: 'absolute', right: 14, bottom: 14, width: 44, height: 44, borderRadius: 22,
    backgroundColor: C.card, borderWidth: 1, borderColor: C.line, alignItems: 'center', justifyContent: 'center',
  },
});
