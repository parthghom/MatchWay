// The driver's main shell: Home (map) and History, with a footer to switch.
// The profile page opens from the icon on the home screen.
import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, BackHandler } from 'react-native';
import { C } from '../../theme';
import { HomeIcon, HistoryIcon } from '../../components/icons';
import DriverHome from './DriverHome';
import DriverHistory from './DriverHistory';
import DriverProfile from './DriverProfile';

export default function DriverTabs({ profile, email, onSignOut }) {
  const [tab, setTab] = useState('home');
  const [showProfile, setShowProfile] = useState(false);

  useEffect(() => {
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {
      if (showProfile) { setShowProfile(false); return true; }
      if (tab === 'history') { setTab('home'); return true; }
      return false;
    });
    return () => sub.remove();
  }, [showProfile, tab]);

  const homeVisible = tab === 'home' && !showProfile;

  return (
    <View style={s.root}>
      <View style={s.content}>
        {/* kept mounted (just hidden) so the map does not reload when you switch */}
        <View style={[s.fill, !homeVisible && s.hidden]}>
          <DriverHome
            vehicleType={profile?.vehicle?.vehicle_type}
            driverId={profile?.user_id}
            driverName={profile?.profile?.full_name}
            visible={homeVisible}
            onProfile={() => setShowProfile(true)}
          />
        </View>
        {tab === 'history' && !showProfile && <DriverHistory userId={profile?.user_id} />}
        {showProfile && (
          <DriverProfile
            profile={profile}
            email={email}
            onBack={() => setShowProfile(false)}
            onSignOut={onSignOut}
          />
        )}
      </View>

      {!showProfile && (
        <View style={s.footer}>
          <TouchableOpacity style={s.tab} onPress={() => setTab('home')} activeOpacity={0.7}>
            <HomeIcon color={tab === 'home' ? C.yellow : C.muted} />
            <Text style={[s.tabText, tab === 'home' && s.tabOn]}>Home</Text>
          </TouchableOpacity>
          <TouchableOpacity style={s.tab} onPress={() => setTab('history')} activeOpacity={0.7}>
            <HistoryIcon color={tab === 'history' ? C.yellow : C.muted} size={22} />
            <Text style={[s.tabText, tab === 'history' && s.tabOn]}>History</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  content: { flex: 1 },
  fill: { flex: 1 },
  hidden: { display: 'none' },
  footer: {
    flexDirection: 'row', backgroundColor: C.bg, borderTopWidth: 1, borderTopColor: C.line,
    paddingTop: 10, paddingBottom: 18,
  },
  tab: { flex: 1, alignItems: 'center', justifyContent: 'center', height: 46 },
  tabText: { color: C.muted, fontSize: 12, marginTop: 4, fontWeight: '600' },
  tabOn: { color: C.yellow },
});
