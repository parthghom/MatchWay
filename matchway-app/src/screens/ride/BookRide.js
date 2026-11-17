// Rapido-style booking screen (black + yellow).
//   home    : search bar on top, live map, recent places below
//   search  : type a place (within 50 km) or choose "Select on map"
//   pick    : drag the map under the pin, confirm the drop
//   options : route on the map + bike / auto / cab with fares, then "Book"
// One map stays mounted the whole time so it never reloads between steps.
import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator,
  Alert, Linking, StatusBar, BackHandler,
} from 'react-native';
import { api, errorText } from '../../api';
import { C } from '../../theme';
import { useLocation } from '../../location';
import { RADIUS_KM, distanceKm, dropTime } from '../../geo';
import { loadRecents, saveRecent } from '../../recents';
import OlaMap from '../../components/OlaMap';
import { SearchIcon, ClockIcon, TargetIcon, BackArrow, ProfileIcon } from '../../components/icons';
import SearchScreen from './SearchScreen';

const HOME_TOP = 186;     // header + search bar (+ a little air above the map)
const HOME_BOTTOM = 222;  // recent places: title + exactly 3 rows
const FIT_PAD = { top: 120, bottom: 360, left: 40, right: 40 };

const VEHICLES = {
  bike: { label: 'Bike', icon: '🏍️', note: 'Quick bike rides' },
  auto: { label: 'Auto', icon: '🛺', note: 'Share an auto' },
  cab: { label: 'Cab', icon: '🚕', note: 'Share a cab' },
};

const rupee = (n) => `₹${Math.round(n)}`;
const shortName = (addr) => (addr || '').split(',')[0].trim();

export default function BookRide({ gender, busy, onBook, onProfile, onStage, visible = true }) {
  const { coords: user, status } = useLocation();
  const mapRef = useRef(null);

  const [stage, setStage] = useState('home');
  const [recents, setRecents] = useState([]);

  const [drop, setDrop] = useState(null);
  const [pickup, setPickup] = useState(null);
  const [info, setInfo] = useState(null);       // { km, minutes, points, approx }
  const [fares, setFares] = useState([]);
  const [loadingOpts, setLoadingOpts] = useState(false);
  const [vehicle, setVehicle] = useState('bike');
  const [customPickup, setCustomPickup] = useState(null);   // pickup the rider fixed on the map
  const [pickTarget, setPickTarget] = useState('drop');         // map picking for 'drop' or 'pickup'
  const [askPref, setAskPref] = useState(false);   // second sheet: who to share with
  const [pref, setPref] = useState('mix');           // 'same' = own gender only, 'mix' = both

  const [center, setCenter] = useState(null);   // map centre while picking
  const [centerAddr, setCenterAddr] = useState('');
  const [moving, setMoving] = useState(false);
  const geoSeq = useRef(0);

  useEffect(() => { loadRecents().then(setRecents); }, []);
  useEffect(() => { if (onStage) onStage(stage); }, [stage, onStage]);
  useEffect(() => { if (stage === 'home') setCustomPickup(null); }, [stage]);

  // "Matchway Spot" pins at college entrances
  const [spots, setSpots] = useState([]);
  useEffect(() => {
    api.get('/spots').then((res) => setSpots(res.data)).catch(() => {});
  }, []);

  const goHome = useCallback(() => {
    setAskPref(false); setPref('mix');
    setStage('home'); setDrop(null); setInfo(null); setFares([]); setPickup(null);
  }, []);

  // Android back button follows the same steps as the on-screen arrows
  useEffect(() => {
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {
      if (stage === 'home') return false;
      if (askPref) setAskPref(false);
      else if (stage === 'search') setStage('home');
      else if (stage === 'pick') setStage('search');
      else goHome();
      return true;
    });
    return () => sub.remove();
  }, [stage, askPref, goHome]);

  function needLocation() {
    if (user) return false;
    if (status === 'denied') {
      Alert.alert('Location is off', 'Allow location so we know where to pick you up.', [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Open settings', onPress: () => Linking.openSettings() },
      ]);
    } else {
      Alert.alert('Please wait', 'Still finding where you are.');
    }
    return true;
  }

  function openSearch() {
    if (needLocation()) return;
    setStage('search');
  }

  // ---- pick on map ----------------------------------------------------
  function startPick(target) {
    setPickTarget(target);
    const start = target === 'pickup' && customPickup ? customPickup : user;
    setCenter(start ? { lat: start.lat, lon: start.lon } : null);
    setCenterAddr('');
    setStage('pick');
    if (start) mapRef.current && mapRef.current.flyTo(start.lat, start.lon, 16);
  }

  const onMoved = useCallback((c) => {
    setMoving(false);
    if (stage !== 'pick') return;
    setCenter(c);
    setCenterAddr('');
    const mine = ++geoSeq.current;
    api.get('/maps/reverse', { params: { lat: c.lat, lon: c.lon } })
      .then((res) => { if (mine === geoSeq.current) setCenterAddr(res.data.address || ''); })
      .catch(() => { if (mine === geoSeq.current) setCenterAddr(''); });
  }, [stage]);

  const pickDistance = center && user ? distanceKm(user.lat, user.lon, center.lat, center.lon) : 0;
  const pickTooFar = pickDistance > RADIUS_KM;

  function confirmPick() {
    const place = {
      name: shortName(centerAddr) || 'Pinned location',
      address: centerAddr || 'Pinned on map',
      lat: center.lat, lon: center.lon,
    };
    if (pickTarget === 'pickup') {
      setCustomPickup(place);   // back to the search boxes with the corrected pickup
      setStage('search');
    } else {
      selectDrop(place);
    }
  }

  // ---- choose a drop, then load route + fares --------------------------
  async function selectDrop(place) {
    const from = customPickup
      ? { lat: customPickup.lat, lon: customPickup.lon, name: customPickup.name }
      : { lat: user.lat, lon: user.lon, name: 'Current location' };
    setDrop(place); setPickup(from); setInfo(null); setFares([]);
    setVehicle('bike'); setStage('options'); setLoadingOpts(true);
    saveRecent(place).then(setRecents);

    if (!customPickup) {
      api.get('/maps/reverse', { params: { lat: from.lat, lon: from.lon } })
        .then((res) => {
          const n = shortName(res.data.address);
          if (n) setPickup((p) => (p ? { ...p, name: n } : p));
        }).catch(() => {});
    }

    let route;
    try {
      const res = await api.get('/maps/route', {
        params: { origin_lat: from.lat, origin_lon: from.lon, dest_lat: place.lat, dest_lon: place.lon },
      });
      route = { ...res.data, approx: false };
    } catch (e) {
      // no route service: fall back to a straight line so booking still works
      const km = distanceKm(from.lat, from.lon, place.lat, place.lon);
      route = {
        km: Math.round(km * 1.3 * 100) / 100, minutes: Math.round(km * 1.3 * 3),
        points: [[from.lat, from.lon], [place.lat, place.lon]], approx: true,
      };
    }
    try {
      const res = await api.get('/fare/options', { params: { km: route.km } });
      setFares(res.data);
    } catch (e) {
      Alert.alert('Error', errorText(e));
    }
    setInfo(route);
    setLoadingOpts(false);
  }

  function confirmBooking() {
    onBook({ vehicle, sameOnly: pref === 'same', pickup, drop, km: info.km });
  }

  const mapStyle = stage === 'home'
    ? { position: 'absolute', top: HOME_TOP, bottom: HOME_BOTTOM, left: 0, right: 0 }
    : stage === 'search'
      ? { position: 'absolute', top: 0, left: 0, width: 1, height: 1, opacity: 0 }
      : StyleSheet.absoluteFillObject;

  const chosen = fares.find((f) => f.vehicle_type === vehicle);
  const cheapest = fares.length
    ? fares.reduce((a, b) => (b.fare_low < a.fare_low ? b : a)).vehicle_type : null;

  return (
    <View style={s.screen}>
      <StatusBar barStyle="light-content" backgroundColor={C.bg} />

      <OlaMap
        ref={mapRef}
        user={user}
        pickup={stage === 'options' ? pickup : null}
        drop={stage === 'options' ? drop : null}
        spots={stage === 'home' || stage === 'pick' ? spots : null}
        route={stage === 'options' && info ? info.points : null}
        fitPad={FIT_PAD}
        onMoved={onMoved}
        onMoveStart={() => setMoving(true)}
        visible={visible}
        style={mapStyle}
      >
        {stage === 'home' && (
          <>
            {!user && (
              <View style={s.pill}>
                {status === 'loading' && <ActivityIndicator color={C.yellow} size="small" style={{ marginRight: 8 }} />}
                <Text style={s.pillText}>
                  {status === 'denied' ? 'Location is off' : status === 'error' ? 'Could not find you' : 'Trying to find where you are…'}
                </Text>
                {status === 'denied' && (
                  <TouchableOpacity onPress={() => Linking.openSettings()}>
                    <Text style={s.pillLink}>  Turn on</Text>
                  </TouchableOpacity>
                )}
              </View>
            )}
            <TouchableOpacity
              style={s.locate}
              onPress={() => user && mapRef.current && mapRef.current.flyTo(user.lat, user.lon, 16)}
            >
              <TargetIcon />
            </TouchableOpacity>
          </>
        )}

        {stage === 'pick' && (
          <View pointerEvents="none" style={s.pinWrap}>
            <View style={[s.pinHead, moving && { transform: [{ translateY: -10 }] }]}>
              <View style={s.pinDot} />
            </View>
            <View style={s.pinStem} />
            <View style={s.pinShadow} />
          </View>
        )}
      {/* PICK ON MAP */}
      {stage === 'pick' && (
        <>
          <TouchableOpacity style={s.roundBack} onPress={() => setStage('search')}>
            <BackArrow />
          </TouchableOpacity>
          <View style={s.sheet}>
            <Text style={s.sheetLabel}>{pickTarget === 'pickup' ? 'Pickup location' : 'Drop location'}</Text>
            <Text style={s.pickAddr} numberOfLines={2}>
              {pickTooFar
                ? `That is ${Math.round(pickDistance)} km away. Choose a place within ${RADIUS_KM} km.`
                : centerAddr || (moving ? 'Move the map…' : 'Finding address…')}
            </Text>
            <TouchableOpacity
              style={[s.book, (pickTooFar || !center || moving) && { opacity: 0.45 }]}
              disabled={pickTooFar || !center || moving}
              onPress={confirmPick}
            >
              <Text style={s.bookText}>{pickTarget === 'pickup' ? 'Confirm pickup' : 'Confirm drop'}</Text>
            </TouchableOpacity>
          </View>
        </>
      )}

      {/* OPTIONS */}
      {stage === 'options' && drop && pickup && (
        <>
          <TouchableOpacity style={s.roundBack} onPress={() => (askPref ? setAskPref(false) : goHome())}>
            <BackArrow />
          </TouchableOpacity>
          <View style={s.chips} pointerEvents="none">
            <View style={s.chip}><Text style={s.chipText} numberOfLines={1}>From: {pickup.name}</Text></View>
            <View style={s.chip}><Text style={s.chipText} numberOfLines={1}>To: {drop.name}</Text></View>
          </View>

          <View style={[s.sheet, { maxHeight: '62%' }]}>
            {askPref ? (
              <>
                <Text style={s.prefTitle}>Who can you share this ride with?</Text>
                {[
                  { key: 'same', label: gender === 'male' ? 'Men only' : 'Women only' },
                  { key: 'mix', label: 'Both' },
                ].map((o) => (
                  <TouchableOpacity
                    key={o.key}
                    style={[s.vrow, pref === o.key && s.vrowOn]}
                    activeOpacity={0.8}
                    onPress={() => setPref(o.key)}
                  >
                    <Text style={s.prefLabel}>{o.label}</Text>
                    <View style={[s.radio, pref === o.key && s.radioOn]} />
                  </TouchableOpacity>
                ))}
                <TouchableOpacity
                  style={[s.book, busy && { opacity: 0.55 }]}
                  disabled={busy}
                  onPress={confirmBooking}
                >
                  {busy
                    ? <ActivityIndicator color={C.black} />
                    : <Text style={s.bookText}>Confirm</Text>}
                </TouchableOpacity>
              </>
            ) : loadingOpts && fares.length === 0 ? (
              <View style={{ paddingVertical: 40 }}>
                <ActivityIndicator color={C.yellow} size="large" />
              </View>
            ) : (
              <>
                <ScrollView keyboardShouldPersistTaps="handled">
                  {fares.map((f) => {
                    const v = VEHICLES[f.vehicle_type];
                    const on = vehicle === f.vehicle_type;
                    const price = f.capacity === 1 || Math.round(f.fare_low) === Math.round(f.fare_high)
                      ? rupee(f.fare_high) : `${rupee(f.fare_low)}–${rupee(f.fare_high)}`;
                    return (
                      <TouchableOpacity
                        key={f.vehicle_type}
                        style={[s.vrow, on && s.vrowOn]}
                        activeOpacity={0.8}
                        onPress={() => setVehicle(f.vehicle_type)}
                      >
                        <Text style={s.vIcon}>{v.icon}</Text>
                        <View style={{ flex: 1 }}>
                          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                            <Text style={s.vName}>{v.label}</Text>
                            {cheapest === f.vehicle_type && <Text style={s.tag}>CHEAPEST</Text>}
                          </View>
                          <Text style={s.vSub}>
                            {f.capacity === 1 ? 'Solo ride' : `Shared · up to ${f.capacity} riders`}
                            {info ? ` · Drop ${dropTime(info.minutes)}` : ''}
                          </Text>
                        </View>
                        <Text style={s.vPrice}>{price}</Text>
                      </TouchableOpacity>
                    );
                  })}
                </ScrollView>

                {info && (
                  <Text style={s.meta}>
                    {info.km} km · about {Math.round(info.minutes)} min{info.approx ? ' (estimate)' : ''}
                  </Text>
                )}

                <TouchableOpacity
                  style={[s.book, (busy || !chosen || !info) && { opacity: 0.55 }]}
                  disabled={busy || !chosen || !info}
                  onPress={() => setAskPref(true)}
                >
                  {busy
                    ? <ActivityIndicator color={C.black} />
                    : <Text style={s.bookText}>Book {VEHICLES[vehicle].label}</Text>}
                </TouchableOpacity>
              </>
            )}
          </View>
        </>
      )}
      </OlaMap>

      {/* SEARCH */}
      {stage === 'search' && (
        <SearchScreen
          user={user}
          recents={recents}
          onBack={() => setStage('home')}
          onSelect={selectDrop}
          pickup={customPickup}
          onPickOnMap={startPick}
        />
      )}


      {/* HOME: search bar on top, recents under the map */}
      {stage === 'home' && (
        <>
          <View style={s.header}>
            <View style={s.headerRow}>
              <Text style={s.logo}>Match<Text style={{ color: C.yellow }}>Way</Text></Text>
              <TouchableOpacity style={s.profileBtn} onPress={onProfile} activeOpacity={0.8}>
                <ProfileIcon size={22} />
              </TouchableOpacity>
            </View>
            <TouchableOpacity style={s.search} activeOpacity={0.8} onPress={openSearch}>
              <SearchIcon />
              <Text style={s.searchText}>Where do you want to go?</Text>
            </TouchableOpacity>
          </View>

          <View style={s.recents}>
            <Text style={s.recentsTitle}>Recent places</Text>
            <ScrollView keyboardShouldPersistTaps="handled">
              {recents.length === 0 && (
                <Text style={s.empty}>Places you pick will show up here.</Text>
              )}
              {recents.slice(0, 3).map((p, i) => (
                <TouchableOpacity
                  key={`${p.lat},${p.lon},${i}`}
                  style={s.recentRow}
                  onPress={() => { if (!needLocation()) selectDrop(p); }}
                >
                  <View style={s.bubble}><ClockIcon /></View>
                  <View style={{ flex: 1 }}>
                    <Text style={s.recentName} numberOfLines={1}>{p.name}</Text>
                    <Text style={s.recentAddr} numberOfLines={1}>{p.address}</Text>
                  </View>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </>
      )}

    </View>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg },

  header: { position: 'absolute', top: 0, left: 0, right: 0, height: HOME_TOP, backgroundColor: C.bg, paddingTop: 52, paddingHorizontal: 16 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 },
  logo: { fontSize: 22, fontWeight: '800', color: C.text, letterSpacing: 0.5 },
  profileBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: C.card, borderWidth: 1.5, borderColor: C.yellow, alignItems: 'center', justifyContent: 'center' },
  search: {
    flexDirection: 'row', alignItems: 'center', height: 52, borderRadius: 16, paddingHorizontal: 16,
    backgroundColor: C.card, borderWidth: 1.5, borderColor: C.yellow,
  },
  searchText: { color: C.text, fontSize: 17, fontWeight: '600', marginLeft: 12 },

  recents: { position: 'absolute', bottom: 0, left: 0, right: 0, height: HOME_BOTTOM, backgroundColor: C.bg, paddingTop: 14, borderTopWidth: 1, borderTopColor: C.line },
  recentsTitle: { color: C.muted, fontSize: 13, paddingHorizontal: 20, marginBottom: 4 },
  empty: { color: C.muted, paddingHorizontal: 20, paddingTop: 16 },
  recentRow: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingVertical: 10 },
  bubble: { width: 38, height: 38, borderRadius: 19, backgroundColor: C.card, borderWidth: 1, borderColor: C.line, alignItems: 'center', justifyContent: 'center', marginRight: 14 },
  recentName: { color: C.text, fontSize: 16, fontWeight: '600' },
  recentAddr: { color: C.muted, fontSize: 13, marginTop: 2 },

  pill: {
    position: 'absolute', bottom: 16, alignSelf: 'center', flexDirection: 'row', alignItems: 'center',
    backgroundColor: C.card, borderRadius: 24, borderWidth: 1, borderColor: C.line, paddingVertical: 10, paddingHorizontal: 18,
  },
  pillText: { color: C.text, fontSize: 14 },
  pillLink: { color: C.yellow, fontWeight: '700', fontSize: 14 },
  locate: {
    position: 'absolute', right: 14, bottom: 14, width: 44, height: 44, borderRadius: 22,
    backgroundColor: C.card, borderWidth: 1, borderColor: C.line, alignItems: 'center', justifyContent: 'center',
  },

  pinWrap: { ...StyleSheet.absoluteFillObject, alignItems: 'center', justifyContent: 'center' },
  pinHead: { width: 34, height: 34, borderRadius: 17, backgroundColor: C.yellow, alignItems: 'center', justifyContent: 'center', marginBottom: -2 },
  pinDot: { width: 12, height: 12, borderRadius: 6, backgroundColor: C.bg },
  pinStem: { width: 3, height: 18, backgroundColor: C.yellow },
  pinShadow: { width: 10, height: 4, borderRadius: 5, backgroundColor: 'rgba(0,0,0,0.5)', marginTop: -1 },

  roundBack: {
    position: 'absolute', top: 48, left: 16, width: 44, height: 44, borderRadius: 22, backgroundColor: C.card,
    borderWidth: 1, borderColor: C.line, alignItems: 'center', justifyContent: 'center',
  },
  chips: { position: 'absolute', top: 48, left: 70, right: 16 },
  chip: { backgroundColor: C.card, borderRadius: 12, borderWidth: 1, borderColor: C.line, paddingVertical: 8, paddingHorizontal: 12, marginBottom: 6, alignSelf: 'flex-start', maxWidth: '100%' },
  chipText: { color: C.text, fontSize: 13, fontWeight: '600' },

  sheet: {
    position: 'absolute', left: 0, right: 0, bottom: 0, backgroundColor: C.bg, borderTopLeftRadius: 22, borderTopRightRadius: 22,
    borderTopWidth: 1, borderColor: C.line, paddingHorizontal: 16, paddingTop: 16, paddingBottom: 18,
  },
  sheetLabel: { color: C.muted, fontSize: 13 },
  pickAddr: { color: C.text, fontSize: 17, fontWeight: '600', marginTop: 4, marginBottom: 6, minHeight: 44 },

  vrow: { flexDirection: 'row', alignItems: 'center', padding: 12, borderRadius: 14, borderWidth: 1.5, borderColor: 'transparent', marginBottom: 6 },
  vrowOn: { borderColor: C.yellow, backgroundColor: C.card },
  vIcon: { fontSize: 32, width: 52, textAlign: 'center', marginRight: 10 },
  vName: { color: C.text, fontSize: 17, fontWeight: '700' },
  tag: { marginLeft: 8, backgroundColor: 'rgba(255,200,0,0.18)', color: C.yellow, fontSize: 11, fontWeight: '800', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, overflow: 'hidden' },
  vSub: { color: C.muted, fontSize: 13, marginTop: 3 },
  vPrice: { color: C.text, fontSize: 18, fontWeight: '800', marginLeft: 8 },
  meta: { color: C.muted, fontSize: 12, textAlign: 'center', marginTop: 4 },

  prefTitle: { color: C.text, fontSize: 18, fontWeight: '800', marginBottom: 12 },
  prefLabel: { flex: 1, color: C.text, fontSize: 17, fontWeight: '600', paddingVertical: 6 },
  radio: { width: 22, height: 22, borderRadius: 11, borderWidth: 2, borderColor: C.muted },
  radioOn: { borderColor: C.yellow, backgroundColor: C.yellow },

  book: { backgroundColor: C.yellow, paddingVertical: 15, borderRadius: 14, alignItems: 'center', marginTop: 12 },
  bookText: { color: C.black, fontSize: 17, fontWeight: '800' },
});
