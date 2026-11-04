import React, { useState, useEffect } from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { C } from './src/theme';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { supabase } from './src/supabase';
import { api, errorText } from './src/api';
import RoleSelectScreen from './src/screens/RoleSelectScreen';
import LoginScreen from './src/screens/LoginScreen';
import StatusScreen from './src/screens/StatusScreen';
import RideFlow from './src/screens/RideFlow';
import OnboardingRouter from './src/screens/onboarding/OnboardingRouter';


export default function App() {
  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState(null);
  const [role, setRole] = useState(null);
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function init() {
      try {
        const storedRole = await AsyncStorage.getItem('matchway_role');
        setRole(storedRole);

        const { data: { session } } = await supabase.auth.getSession();
        setSession(session);

        const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
          setSession(session);
        });

        return () => subscription.unsubscribe();
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  useEffect(() => {
    async function fetchProfile() {
      if (!session) return;
      try {
        const res = await api.get('/profile/me');
        const data = res.data;
        setProfile(data);

        if (!data.exists) {
          await api.post('/profile/role', { role });
          const res2 = await api.get('/profile/me');
          setProfile(res2.data);
        }
      } catch (e) {
        if (e.response?.status === 403 || e.response?.status === 409) {
          setError(errorText(e));
        } else {
          console.error(e);
        }
      }
    }
    fetchProfile();
  }, [session, role]);

  const onSignOut = async () => {
    await supabase.auth.signOut();
    await AsyncStorage.removeItem('matchway_role');
    setSession(null);
    setProfile(null);
    setRole(null);
    setError(null);
  };

  const onSelectRole = async (selectedRole) => {
    await AsyncStorage.setItem('matchway_role', selectedRole);
    setRole(selectedRole);
  };

  const onBackFromLogin = async () => {
    await AsyncStorage.removeItem('matchway_role');
    setRole(null);
  };

  if (loading) {
    return (
      <View style={s.center}>
        <ActivityIndicator size="large" color={C.yellow} />
      </View>
    );
  }

  if (error) {
    return (
      <StatusScreen
        title="Account Error"
        message={error}
        onSignOut={onSignOut}
        onRefresh={() => { setError(null); }}
      />
    );
  }

  if (!session && !role) {
    return <RoleSelectScreen onSelect={onSelectRole} />;
  }

  if (!session && role) {
    return <LoginScreen role={role} onBack={onBackFromLogin} />;
  }

  if (session) {
    if (!profile) return (
      <View style={s.center}>
        <ActivityIndicator size="large" color={C.yellow} />
      </View>
    );

    const nextStep = profile.next_step;
    if (nextStep === 'done') {
      if (role === 'student') {
        return profile.status === 'approved'
          ? <RideFlow onSignOut={onSignOut} />
          : <StatusScreen title="Under review" message="Your documents are being checked." onSignOut={onSignOut} onRefresh={() => {}} />;
      } else {
        return <StatusScreen title="You are all set" message="The driver home is coming soon." onSignOut={onSignOut} onRefresh={() => {}} />;
      }
    }

    return (
      <OnboardingRouter
        profile={profile}
        onRefresh={() => {
          const fetchProfile = async () => {
            if (!session) return;
            try {
              const res = await api.get('/profile/me');
              setProfile(res.data);
            } catch (e) {
              console.error(e);
            }
          };
          fetchProfile();
        }}
        onSignOut={onSignOut}
      />
    );
  }

  return null;
}

const s = StyleSheet.create({
  center: {
    flex: 1,
    backgroundColor: C.bg,
    justifyContent: 'center',
    alignItems: 'center'
  },
});
