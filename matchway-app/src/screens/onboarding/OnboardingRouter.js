import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { C } from '../../theme';
import DetailsScreen from './DetailsScreen';
import DocumentScreen from './DocumentScreen';
import SelfieScreen from './SelfieScreen';
import StatusScreen from '../StatusScreen';

const STUDENT_ORDER = ['details', 'college_id', 'selfie'];
const DRIVER_ORDER = ['details', 'aadhaar', 'pan', 'licence', 'vehicle', 'rc', 'vehicle_photo'];

export default function OnboardingRouter({ profile, onRefresh, onSignOut }) {
  if (!profile || !profile.profile) {
    return (
      <StatusScreen
        title="Setting up your account"
        message="One moment..."
        onSignOut={onSignOut}
        onRefresh={onRefresh}
      />
    );
  }
  const role = profile.profile.role;
  const order = role === 'student' ? STUDENT_ORDER : DRIVER_ORDER;
  const step = profile.next_step;
  const index = order.indexOf(step) + 1;
  const total = order.length;

  const renderStep = () => {
    if (step === 'details') {
      return <DetailsScreen index={index} total={total} onDone={onRefresh} />;
    }
    if (step === 'college_id') {
      return (
        <DocumentScreen
          index={index} total={total} onDone={onRefresh}
          title="Upload your college ID"
          subtitle="Take a clear photo of the front of your ID card"
          docType="college_id"
          tips={['Make sure your name and photo are readable', 'Avoid glare and shadows']}
          needsNumber={false}
        />
      );
    }
    if (step === 'selfie') {
      return <SelfieScreen index={index} total={total} onDone={onRefresh} />;
    }

    return (
      <StatusScreen
        title={`Next: ${step}`}
        message="This screen is coming next."
      />
    );
  };

  return (
    <View style={s.container}>
      <TouchableOpacity style={s.signOutBtn} onPress={onSignOut}>
        <Text style={s.signOutText}>Sign out</Text>
      </TouchableOpacity>
      {renderStep()}
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  signOutBtn: {
    position: 'absolute',
    top: 56,
    right: 20,
    zIndex: 10
  },
  signOutText: { color: C.yellow, fontSize: 16, fontWeight: '600' },
});
