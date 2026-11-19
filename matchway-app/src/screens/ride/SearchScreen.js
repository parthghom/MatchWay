// Pickup + drop search, laid out like Rapido:
//   pickup box (your current address, tap it to search another pickup)  +  drop box (cursor here)
//   target button on each box to pick that place on the map
//   recent places, or related places (nearest first) while you type.
// Results come from our backend (Ola Maps autocomplete), limited to RADIUS_KM.
import React, { useEffect, useRef, useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, ActivityIndicator, Alert, StatusBar,
} from 'react-native';
import { api, errorText } from '../../api';
import { C } from '../../theme';
import { RADIUS_KM, distanceKm } from '../../geo';
import { BackArrow, ClockIcon, PinIcon, TargetIcon } from '../../components/icons';

const TOP = (StatusBar.currentHeight || 24) + 10;

function kmText(m) {
  if (m == null) return '';
  return m < 1000 ? `${Math.round(m)} m` : `${(m / 1000).toFixed(1)} km`;
}

export default function SearchScreen({ user, pickup, recents, onBack, onSelect, onSelectPickup, onPickOnMap }) {
  const [text, setText] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [opening, setOpening] = useState(false);
  const [pickupName, setPickupName] = useState('Current location');
  const [active, setActive] = useState('drop');        // which box you are typing in: 'pickup' or 'drop'
  const [pickupText, setPickupText] = useState('');
  const seq = useRef(0);
  const dropInput = useRef(null);
  const pickupLabel = pickup ? (pickup.address || pickup.name) : pickupName;

  // when you are not typing a pickup, its box shows the current pickup address
  useEffect(() => { if (active !== 'pickup') setPickupText(pickupLabel); }, [pickupLabel, active]);
  const query = active === 'pickup' ? pickupText : text;

  // your current address goes in the pickup box
  useEffect(() => {
    if (!user || pickup) return;
    api.get('/maps/reverse', { params: { lat: user.lat, lon: user.lon } })
      .then((res) => { if (res.data.address) setPickupName(res.data.address); })
      .catch(() => {});
  }, [user, pickup]);

  useEffect(() => {
    const q = query.trim();
    if (q.length < 2 || (active === 'pickup' && q === pickupLabel.trim())) {
      setResults([]); setError(''); setLoading(false);
      return undefined;
    }
    const mine = ++seq.current;
    setLoading(true);
    const t = setTimeout(async () => {
      try {
        const res = await api.get('/maps/search', { params: { q, lat: user?.lat, lon: user?.lon } });
        if (mine !== seq.current) return;
        const list = res.data
          .map((p) => ({
            ...p,
            // distance: Ola's own number, else worked out from the coordinates
            dist: p.distance_m != null ? p.distance_m
              : (user && p.lat != null ? distanceKm(user.lat, user.lon, p.lat, p.lon) * 1000 : null),
          }))
          .filter((p) => p.dist == null || p.dist <= RADIUS_KM * 1000)
          .sort((a, b) => (a.dist ?? 1e12) - (b.dist ?? 1e12));  // nearest first
        setResults(list); setError('');
      } catch (e) {
        if (mine === seq.current) { setResults([]); setError(errorText(e)); }
      } finally {
        if (mine === seq.current) setLoading(false);
      }
    }, 300);
    return () => clearTimeout(t);
  }, [query, user, active, pickupLabel]);

  async function choose(p) {
    if (opening) return;
    let place = p;
    if (p.lat == null || p.lon == null) {
      setOpening(true);
      try {
        const res = await api.get('/maps/place', { params: { place_id: p.place_id } });
        place = { ...p, ...res.data, name: p.name || res.data.name, address: p.address || res.data.address };
      } catch (e) {
        setOpening(false);
        Alert.alert('Error', errorText(e));
        return;
      }
      setOpening(false);
    }
    if (user && distanceKm(user.lat, user.lon, place.lat, place.lon) > RADIUS_KM) {
      Alert.alert('Too far', `Pick a place within ${RADIUS_KM} km of you.`);
      return;
    }
    const chosen = { name: place.name, address: place.address, lat: place.lat, lon: place.lon };
    if (active === 'pickup') {
      onSelectPickup(chosen);          // new pickup: stay here and go on to the drop box
      setActive('drop'); setResults([]);
      setTimeout(() => dropInput.current && dropInput.current.focus(), 50);
      return;
    }
    onSelect(chosen);
  }

  function useCurrentLocation() {
    onSelectPickup(null);
    setActive('drop'); setResults([]);
    setTimeout(() => dropInput.current && dropInput.current.focus(), 50);
  }

  const typing = query.trim().length >= 2 && !(active === 'pickup' && query.trim() === pickupLabel.trim());
  const data = typing ? results : recents;

  return (
    <View style={s.screen}>
      <TouchableOpacity onPress={onBack} style={s.back} hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}>
        <BackArrow />
      </TouchableOpacity>

      <View style={s.pair}>
        <View style={s.dots}>
          <View style={s.dotGreen} />
          <View style={s.dotLine} />
          <View style={s.dotDrop} />
        </View>
        <View style={{ flex: 1 }}>
          <View style={[s.pickup, active === 'pickup' && s.boxOn]}>
            <TextInput
              value={pickupText}
              onChangeText={setPickupText}
              onFocus={() => setActive('pickup')}
              selectTextOnFocus
              placeholder="Pickup location"
              placeholderTextColor={C.muted}
              style={[s.pickupText, active === 'pickup' && { color: C.text }]}
              returnKeyType="search"
            />
            {active === 'pickup' && loading && <ActivityIndicator color={C.yellow} size="small" />}
            <TouchableOpacity style={s.mapIcon} onPress={() => onPickOnMap('pickup')} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
              <TargetIcon size={20} />
            </TouchableOpacity>
          </View>
          <View style={[s.dropBox, active !== 'drop' && s.dropOff]}>
            <TextInput
              ref={dropInput}
              autoFocus
              value={text}
              onChangeText={setText}
              onFocus={() => setActive('drop')}
              placeholder="Drop location"
              placeholderTextColor={C.muted}
              style={s.input}
              returnKeyType="search"
            />
            {((active === 'drop' && loading) || opening) && <ActivityIndicator color={C.yellow} size="small" />}
            {text.length > 0 && !(active === 'drop' && loading) && !opening && (
              <TouchableOpacity onPress={() => setText('')}><Text style={s.clear}>✕</Text></TouchableOpacity>
            )}
            <TouchableOpacity style={s.mapIcon} onPress={() => onPickOnMap('drop')} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
              <TargetIcon size={20} />
            </TouchableOpacity>
          </View>
        </View>
      </View>

      <View style={{ height: 14 }} />

      <FlatList
        style={s.list}
        data={data}
        keyboardShouldPersistTaps="handled"
        keyExtractor={(p, i) => `${p.place_id || p.lat + ',' + p.lon}-${i}`}
        ListHeaderComponent={
          <>
          {active === 'pickup' && !typing && (
            <TouchableOpacity style={s.row} onPress={useCurrentLocation} activeOpacity={0.7}>
              <View style={s.iconCol}><TargetIcon size={22} /></View>
              <View style={{ flex: 1 }}>
                <Text style={s.name}>Use my current location</Text>
                <Text style={s.addr} numberOfLines={1}>Pick me up where I am now</Text>
              </View>
            </TouchableOpacity>
          )}
          <Text style={s.section}>
            {typing ? `Places within ${RADIUS_KM} km` : 'Recent places'}
          </Text>
          </>
        }
        ListEmptyComponent={
          <Text style={s.empty}>
            {error || (typing ? (loading ? '' : 'No places found nearby.') : 'Places you pick will show up here.')}
          </Text>
        }
        renderItem={({ item }) => (
          <TouchableOpacity style={s.row} onPress={() => choose(item)} activeOpacity={0.7}>
            <View style={s.iconCol}>
              {typing ? <PinIcon size={22} /> : <ClockIcon size={20} />}
              {typing && item.dist != null && <Text style={s.dist}>{kmText(item.dist)}</Text>}
            </View>
            <View style={{ flex: 1 }}>
              <Text style={s.name} numberOfLines={1}>{item.name}</Text>
              <Text style={s.addr} numberOfLines={1}>{item.address}</Text>
            </View>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg, paddingTop: TOP },
  back: { width: 44, height: 40, justifyContent: 'center', paddingLeft: 16 },

  pair: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, marginTop: 8 },
  dots: { width: 26, alignItems: 'center', marginRight: 6 },
  dotGreen: { width: 12, height: 12, borderRadius: 6, backgroundColor: '#fff', borderWidth: 3, borderColor: C.yellow },
  dotLine: { width: 2, height: 34, backgroundColor: C.line },
  dotDrop: { width: 12, height: 12, backgroundColor: C.yellow },

  pickup: { height: 46, flexDirection: 'row', alignItems: 'center', backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, marginBottom: 10 },
  pickupText: { flex: 1, color: C.muted, fontSize: 15, paddingVertical: 0 },
  boxOn: { borderWidth: 1.5, borderColor: C.yellow },
  dropOff: { borderWidth: 1, borderColor: C.line },
  mapIcon: { width: 32, height: 32, alignItems: 'center', justifyContent: 'center', marginLeft: 6 },
  dropBox: {
    height: 48, flexDirection: 'row', alignItems: 'center', borderRadius: 12, paddingHorizontal: 14,
    backgroundColor: C.card, borderWidth: 1.5, borderColor: C.yellow,
  },
  input: { flex: 1, color: C.text, fontSize: 16, paddingVertical: 0 },
  clear: { color: C.muted, fontSize: 16, paddingHorizontal: 6 },

  list: { flex: 1, borderTopWidth: 1, borderTopColor: C.line },
  section: { color: C.muted, fontSize: 13, paddingHorizontal: 20, paddingTop: 12, paddingBottom: 4 },
  empty: { color: C.muted, textAlign: 'center', marginTop: 30, paddingHorizontal: 30 },
  row: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: C.line },
  iconCol: { width: 56, alignItems: 'center', marginRight: 8 },
  dist: { color: C.muted, fontSize: 11, marginTop: 3 },
  name: { color: C.text, fontSize: 16, fontWeight: '600' },
  addr: { color: C.muted, fontSize: 13, marginTop: 2 },
});
